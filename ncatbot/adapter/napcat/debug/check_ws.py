"""
NapCat 诊断工具 — WebSocket 连接检测

检测 NapCat OneBot11 WebSocket 服务是否可达, 以及其返回的第一条消息内容。
WebSocket 能正常通信意味着 QQ 已登录且 OneBot11 协议就绪。

用法:
    python -m ncatbot.adapter.napcat.debug.check_ws
    python -m ncatbot.adapter.napcat.debug.check_ws ws://localhost:3001
    python -m ncatbot.adapter.napcat.debug.check_ws ws://localhost:3001 napcat_ws
"""

import asyncio
import json
import sys

try:
    import websockets
except ImportError:
    print("[ERROR] websockets 未安装, 请执行: pip install websockets")
    sys.exit(1)


async def check_ws(uri: str, token: str = "") -> None:
    ws_uri = f"{uri}?access_token={token}" if token else uri
    print(f"[INFO] 正在连接: {uri}")
    if token:
        print(f"[INFO] Token: {token[:4]}***")

    try:
        async with websockets.connect(ws_uri, open_timeout=5) as ws:
            print("[OK] WebSocket 连接成功")
            raw = await asyncio.wait_for(ws.recv(), timeout=5)
            try:
                data = json.loads(raw)
                print(
                    f"[OK] 收到消息: {json.dumps(data, indent=2, ensure_ascii=False)}"
                )

                if data.get("status") == "failed":
                    retcode = data.get("retcode")
                    msg = data.get("message", "")
                    print(f"[WARN] 服务端返回失败: retcode={retcode}, message={msg}")
                    if retcode == 1403:
                        print("[ERROR] Token 错误!")
                else:
                    print("[OK] WebSocket 状态正常 — QQ 已登录且 OneBot11 可用")
            except json.JSONDecodeError:
                print(f"[WARN] 收到非 JSON 消息: {raw[:200]}")
    except asyncio.TimeoutError:
        print("[ERROR] 连接或接收超时")
    except ConnectionRefusedError:
        print("[ERROR] 连接被拒绝 — NapCat 服务未运行或端口错误")
    except Exception as e:
        print(f"[ERROR] 连接失败: {type(e).__name__}: {e}")


def main():
    uri = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:3001"
    token = sys.argv[2] if len(sys.argv) > 2 else ""
    asyncio.run(check_ws(uri, token))


if __name__ == "__main__":
    main()
