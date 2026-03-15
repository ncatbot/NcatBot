"""
NapCat 诊断工具 — WebUI API 状态检测

逐步调用 WebUI 的各个端点, 输出完整的原始响应, 帮助排查登录状态不同步等问题。

检测项:
  1. WebUI 认证 (/api/auth/login)
  2. 登录状态 (/api/QQLogin/CheckLoginStatus)
  3. 登录信息 (/api/QQLogin/GetQQLoginInfo)
  4. 快速登录列表 (/api/QQLogin/GetQuickLoginListNew)

用法:
    python -m ncatbot.adapter.napcat.debug.check_webui
    python -m ncatbot.adapter.napcat.debug.check_webui --host localhost --port 6099 --token YOUR_TOKEN
"""

import argparse
import hashlib
import json
import socket
import urllib.error
import urllib.request

SALT = "napcat"


def post(url: str, payload: dict = None, headers: dict = None, timeout: float = 5.0):
    """发送 POST 请求并返回 (status_code, response_body_dict | raw_text)"""
    req_headers = {"User-Agent": "ncatbot-debug", "Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = getattr(resp, "status", resp.getcode())
            raw = resp.read().decode("utf-8")
            try:
                return code, json.loads(raw)
            except json.JSONDecodeError:
                return code, raw
    except urllib.error.HTTPError as e:
        raw = ""
        if e.fp:
            raw = e.fp.read().decode("utf-8", errors="replace")
        return e.code, raw
    except socket.timeout:
        return None, "TIMEOUT"
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def get(url: str, headers: dict = None, timeout: float = 5.0):
    """发送 GET 请求并返回 (status_code, response_body_dict | raw_text)"""
    req_headers = {"User-Agent": "ncatbot-debug", "Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = getattr(resp, "status", resp.getcode())
            raw = resp.read().decode("utf-8")
            try:
                return code, json.loads(raw)
            except json.JSONDecodeError:
                return code, raw
    except urllib.error.HTTPError as e:
        raw = ""
        if e.fp:
            raw = e.fp.read().decode("utf-8", errors="replace")
        return e.code, raw
    except socket.timeout:
        return None, "TIMEOUT"
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def fmt(obj) -> str:
    if isinstance(obj, dict):
        return json.dumps(obj, indent=2, ensure_ascii=False)
    return str(obj)


def run_checks(base_uri: str, token: str):
    print(f"{'=' * 60}")
    print("NapCat WebUI 诊断")
    print(f"  Base URI : {base_uri}")
    print(
        f"  Token    : {token[:4]}***{token[-4:]}"
        if len(token) > 8
        else "  Token    : ***"
    )
    print(f"{'=' * 60}\n")

    # ── 1. 认证 ──
    print("[1/4] WebUI 认证 — POST /api/auth/login")
    hashed = hashlib.sha256(f"{token}.{SALT}".encode()).hexdigest()
    code, body = post(f"{base_uri}/api/auth/login", payload={"hash": hashed})
    print(f"  HTTP {code}")
    print(f"  响应: {fmt(body)}")

    credential = None
    if isinstance(body, dict) and body.get("code") == 0:
        credential = body.get("data", {}).get("Credential")
        print(
            f"  [OK] 认证成功, Credential: {credential[:16]}..."
            if credential
            else "  [WARN] 缺少 Credential"
        )
    else:
        print("  [ERROR] 认证失败, 后续检测将跳过")
        return
    print()

    auth_header = {"Authorization": f"Bearer {credential}"}

    # ── 2. 登录状态 ──
    print("[2/4] 登录状态 — POST /api/QQLogin/CheckLoginStatus")
    code, body = post(f"{base_uri}/api/QQLogin/CheckLoginStatus", headers=auth_header)
    print(f"  HTTP {code}")
    print(f"  响应: {fmt(body)}")
    is_login = False
    if isinstance(body, dict):
        is_login = body.get("data", {}).get("isLogin", False)
        print(f"  isLogin = {is_login}")
    print()

    # ── 3. 登录信息 ──
    print("[3/4] 登录信息 — POST /api/QQLogin/GetQQLoginInfo")
    code, body = post(f"{base_uri}/api/QQLogin/GetQQLoginInfo", headers=auth_header)
    print(f"  HTTP {code}")
    print(f"  响应: {fmt(body)}")
    if isinstance(body, dict):
        data = body.get("data", {})
        uin = data.get("uin", "N/A")
        online = data.get("online", "N/A")
        nick = data.get("nick", "N/A")
        print(f"  uin={uin}, online={online}, nick={nick}")
    print()

    # ── 4. 快速登录列表 ──
    print("[4/4] 快速登录列表 — POST /api/QQLogin/GetQuickLoginListNew")
    code, body = post(
        f"{base_uri}/api/QQLogin/GetQuickLoginListNew", headers=auth_header
    )
    print(f"  HTTP {code}")
    print(f"  响应: {fmt(body)}")
    if isinstance(body, dict):
        records = body.get("data", [])
        if isinstance(records, list):
            for r in records:
                print(f"    - uin={r.get('uin')}, isQuickLogin={r.get('isQuickLogin')}")
    print()

    # ── 总结 ──
    print(f"{'=' * 60}")
    print("诊断总结:")
    print("  WebUI 认证   : OK")
    print(f"  CheckLoginStatus.isLogin : {is_login}")
    if isinstance(body, dict):
        info_data = (
            body.get("data", {}) if not isinstance(body.get("data"), list) else {}
        )
    else:
        info_data = {}
    print(f"  GetQQLoginInfo.online    : {info_data.get('online', 'N/A')}")

    if not is_login:
        print()
        print("  [!] WebUI 报告 isLogin=false")
        print("      如果 WebSocket 连接正常 (check_ws.py 通过), 说明 QQ 实际已登录,")
        print("      WebUI 的 WebUiDataRuntime 状态未同步 — 这是已知的 NapCat 行为。")
    print(f"{'=' * 60}")


def main():
    parser = argparse.ArgumentParser(description="NapCat WebUI 诊断")
    parser.add_argument(
        "--host", default="localhost", help="WebUI host (default: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=6099, help="WebUI port (default: 6099)"
    )
    parser.add_argument("--token", default=None, help="WebUI token")
    args = parser.parse_args()

    if args.token is None:
        # 尝试从 dev/config.yaml 读取
        try:
            from ncatbot.utils import ncatbot_config

            token = ncatbot_config.napcat.webui_token
            host = args.host
            port = args.port
            if hasattr(ncatbot_config.napcat, "webui_uri"):
                uri = ncatbot_config.napcat.webui_uri
                if uri:
                    # 从 uri 解析
                    from urllib.parse import urlparse

                    parsed = urlparse(uri)
                    host = parsed.hostname or host
                    port = parsed.port or port
        except Exception:
            print("[WARN] 无法从 ncatbot_config 读取配置, 请通过 --token 传入")
            token = "napcat_webui"
    else:
        token = args.token
        host = args.host
        port = args.port

    base_uri = f"http://{host}:{port}"
    run_checks(base_uri, token)


if __name__ == "__main__":
    main()
