"""
NapCat 诊断工具 — 综合状态对比

同时检测 WebSocket 和 WebUI, 对比两者的状态报告, 发现不一致时给出结论。
这是排查 "WebUI 报告未登录但实际已登录" 问题的核心工具。

用法:
    python -m ncatbot.adapter.napcat.debug.diagnose
"""

import asyncio
import hashlib
import json
import sys
import urllib.error
import urllib.request

try:
    import websockets
except ImportError:
    print("[ERROR] websockets 未安装")
    sys.exit(1)

SALT = "napcat"


def post(url, payload=None, headers=None, timeout=5.0):
    req_headers = {"User-Agent": "ncatbot-debug", "Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    body = json.dumps(payload).encode("utf-8") if payload else None
    if body:
        req_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


async def check_ws(uri: str, token: str = "") -> dict:
    import urllib.parse

    ws_uri = (
        f"{uri}?access_token={urllib.parse.quote(token, safe='')}" if token else uri
    )
    result = {"reachable": False, "status": None, "retcode": None, "error": None}
    try:
        async with websockets.connect(ws_uri, open_timeout=5) as ws:
            result["reachable"] = True
            raw = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(raw)
            result["status"] = data.get("status")
            result["retcode"] = data.get("retcode")
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
    return result


def check_webui(base_uri: str, token: str) -> dict:
    result = {
        "auth_ok": False,
        "is_login": None,
        "uin": None,
        "online": None,
        "error": None,
    }

    hashed = hashlib.sha256(f"{token}.{SALT}".encode()).hexdigest()
    resp = post(f"{base_uri}/api/auth/login", payload={"hash": hashed})
    if not resp or resp.get("code") != 0:
        result["error"] = f"认证失败: {resp}"
        return result

    credential = resp.get("data", {}).get("Credential")
    if not credential:
        result["error"] = "认证响应缺少 Credential"
        return result
    result["auth_ok"] = True
    auth_header = {"Authorization": f"Bearer {credential}"}

    # CheckLoginStatus
    resp = post(f"{base_uri}/api/QQLogin/CheckLoginStatus", headers=auth_header)
    if resp:
        result["is_login"] = resp.get("data", {}).get("isLogin")

    # GetQQLoginInfo
    resp = post(f"{base_uri}/api/QQLogin/GetQQLoginInfo", headers=auth_header)
    if resp:
        data = resp.get("data", {})
        result["uin"] = data.get("uin")
        result["online"] = data.get("online")

    return result


async def diagnose():
    # 加载配置
    try:
        from ncatbot.utils import ncatbot_config
        from ncatbot.utils.config.models import NapCatConfig

        # 从 adapters 列表中提取 napcat 适配器配置
        nc = None
        for entry in ncatbot_config.config.adapters:
            if entry.type == "napcat":
                nc = NapCatConfig.model_validate(entry.config)
                break
        if nc is None:
            print("[ERROR] 配置中未找到 napcat 适配器")
            return

        ws_uri = nc.ws_uri
        ws_token = nc.ws_token or ""
        webui_token = nc.webui_token
        webui_uri = getattr(nc, "webui_uri", None)
        if webui_uri:
            webui_base = webui_uri
        else:
            webui_host = nc.webui_host
            webui_port = nc.webui_port
            webui_base = f"http://{webui_host}:{webui_port}"
        bot_uin = str(ncatbot_config.bot_uin)
    except Exception as e:
        print(f"[ERROR] 无法加载配置: {e}")
        print("提示: 确保 dev/config.yaml 或 config.yaml 存在")
        return

    print(f"{'=' * 60}")
    print("NapCat 综合诊断")
    print(f"  WebSocket URI : {ws_uri}")
    print(f"  WebUI URI     : {webui_base}")
    print(f"  bot_uin       : {bot_uin}")
    print(f"{'=' * 60}\n")

    # ── WebSocket 检测 ──
    print("[1] WebSocket 连接检测...")
    ws_result = await check_ws(ws_uri, ws_token)
    ws_ok = ws_result["reachable"] and ws_result.get("status") != "failed"
    print(f"    可达: {ws_result['reachable']}")
    print(f"    状态: {ws_result.get('status', 'N/A')}")
    if ws_result.get("error"):
        print(f"    错误: {ws_result['error']}")
    print(f"    结论: {'QQ 已登录, OneBot11 可用' if ws_ok else 'WS 不可用'}")
    print()

    # ── WebUI 检测 ──
    print("[2] WebUI API 检测...")
    webui_result = check_webui(webui_base, webui_token)
    print(f"    认证: {'OK' if webui_result['auth_ok'] else 'FAILED'}")
    print(f"    CheckLoginStatus.isLogin : {webui_result.get('is_login')}")
    print(f"    GetQQLoginInfo.uin       : {webui_result.get('uin')}")
    print(f"    GetQQLoginInfo.online    : {webui_result.get('online')}")
    if webui_result.get("error"):
        print(f"    错误: {webui_result['error']}")
    print()

    # ── 对比分析 ──
    print(f"{'=' * 60}")
    print("对比分析:")
    print()

    webui_login = webui_result.get("is_login") is True
    webui_online = webui_result.get("online") is True
    webui_uin_match = str(webui_result.get("uin", "")) == bot_uin

    indicators = {
        "WS 连接正常": ws_ok,
        "WebUI isLogin": webui_login,
        "WebUI online": webui_online,
        "WebUI UIN 匹配": webui_uin_match,
    }

    for label, ok in indicators.items():
        symbol = "OK" if ok else "!!"
        print(f"  [{symbol}] {label}")

    print()

    if ws_ok and not webui_login:
        print("  >>> 诊断: WebUI 状态不同步 <<<")
        print("  WebSocket 正常 = QQ 已登录, 但 WebUI 报告 isLogin=false。")
        print("  原因: NapCat 通过缓存 session 自动登录时,")
        print("        WebUiDataRuntime 的状态未被更新。")
        print("  建议: launcher._verify_account 应在此场景下跳过登录。")
    elif ws_ok and webui_login and not webui_uin_match:
        print("  >>> 诊断: UIN 不匹配 <<<")
        print(
            f"  WebUI 报告登录的 QQ 为 {webui_result.get('uin')}, 与 bot_uin={bot_uin} 不同。"
        )
    elif ws_ok and webui_login and webui_online and webui_uin_match:
        print("  >>> 诊断: 一切正常 <<<")
        print("  WebSocket 和 WebUI 状态完全一致, 无异常。")
    elif not ws_ok and not webui_login:
        print("  >>> 诊断: 未登录 <<<")
        print("  WS 和 WebUI 都不可用, QQ 确实未登录。")
    elif not ws_ok and webui_login:
        print("  >>> 诊断: WS 异常 <<<")
        print("  WebUI 报告已登录但 WS 连接失败, 可能是 OneBot11 WS 配置问题。")
    else:
        print("  >>> 诊断: 状态不明 <<<")
        print(
            f"  WS={ws_ok}, isLogin={webui_login}, online={webui_online}, uin_match={webui_uin_match}"
        )

    print(f"{'=' * 60}")


def main():
    asyncio.run(diagnose())


if __name__ == "__main__":
    main()
