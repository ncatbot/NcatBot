# NapCat 调试工具

用于排查 NapCat 连接、登录、状态同步等问题的独立诊断脚本。

## 脚本列表

| 脚本 | 用途 |
|------|------|
| `check_ws.py` | WebSocket 连接检测 |
| `check_webui.py` | WebUI API 逐项检测 |
| `diagnose.py` | 综合对比诊断 (推荐) |

## 使用方式

```bash
# 确保已激活虚拟环境
.venv\Scripts\activate.ps1  # Windows

# 综合诊断 (自动从 config.yaml 读取配置)
python -m ncatbot.adapter.napcat.debug.diagnose

# 单独检测 WebSocket
python -m ncatbot.adapter.napcat.debug.check_ws
python -m ncatbot.adapter.napcat.debug.check_ws ws://localhost:3001 napcat_ws

# 单独检测 WebUI API
python -m ncatbot.adapter.napcat.debug.check_webui
python -m ncatbot.adapter.napcat.debug.check_webui --host localhost --port 6099 --token YOUR_TOKEN
```

## 常见问题诊断

### WebSocket 正常但 WebUI 报告未登录

**现象**: `diagnose.py` 输出:
```
  [OK] WS 连接正常
  [!!] WebUI isLogin
```

**原因**: NapCat 通过缓存 session 自动登录时, WebUI 内部的 `WebUiDataRuntime` 状态
未同步更新 `isLogin` 标志。OneBot11 WebSocket 能正常通信说明 QQ 已登录。

**影响**: `launcher._verify_account()` 调用 `auth.report_status()` 时,
`CheckLoginStatus` 返回 `isLogin=false`, 导致误判为未登录并触发不必要的登录流程。

### WebUI 认证失败

检查:
- WebUI 是否启动 (`enable_webui: true`)
- `webui_token` 配置是否与 `napcat/config/webui.json` 中的 `token` 一致
- WebUI 端口 (默认 6099) 是否被占用

### WebSocket 连接失败

检查:
- NapCat 是否已启动
- `ws_uri` 和 `ws_token` 配置是否正确
- `napcat/config/onebot11_*.json` 中的 WebSocket 监听端口和 token
