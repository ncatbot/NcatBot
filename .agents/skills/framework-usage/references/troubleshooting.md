# 调试排错参考

> 参考文档：`guide/6. 配置管理/`、`reference/8. 工具模块/1. 配置.md`

## 快速诊断

```bash
ncatbot config check              # 一键检查配置
ncatbot config show               # 查看完整配置
ncatbot config get napcat.ws_uri  # 查看特定项
ncatbot dev                       # 调试模式 + 热重载
```

```powershell
# 启用完整调试日志
$env:LOG_LEVEL = "DEBUG"
$env:FILE_LOG_LEVEL = "DEBUG"
ncatbot run --debug

# 实时查看日志
Get-Content logs\bot.log -Tail 50 -Wait
```

## 日志系统

### 日志位置

| 日志 | 路径 | 说明 |
|------|------|------|
| 主日志 | `./logs/bot.log.YYYY_MM_DD` | 每日轮转 |
| 数据库日志 | `./logs/db.log` | 匹配 `database` |
| 网络日志 | `./logs/network.log` | 匹配 `network` |

### 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `LOG_LEVEL` | `DEBUG` | 控制台级别 |
| `FILE_LOG_LEVEL` | `DEBUG` | 文件级别 |
| `LOG_FILE_PATH` | `./logs/bot.log` | 路径 |
| `BACKUP_COUNT` | — | 保留天数 |

### 插件中使用日志

```python
from ncatbot.utils import get_log
log = get_log("my_plugin")

log.info("插件已加载")
log.debug("调试信息", user_id="123")
log.error("操作失败", exc_info=True)

# 绑定上下文
log = get_log("my_plugin").bind(group_id="456")
```

## 配置检查清单

### 必填

```yaml
root: "123456"              # 管理员 QQ
bot_uin: "123456789"        # 机器人 QQ
```

### NapCat 连接

```yaml
napcat:
  ws_uri: ws://localhost:3001
  ws_token: napcat_ws
  ws_listen_ip: localhost
```

### 插件

```yaml
plugin:
  plugins_dir: plugins
  load_plugin: true
  auto_install_pip_deps: true
```

## dev vs 生产

| 特性 | `ncatbot run` | `ncatbot dev` |
|------|---------------|---------------|
| 调试模式 | 默认关闭 | 始终开启 |
| 热重载 | 默认关闭 | 始终启用 |

## 常见问题排查

### Bot 启动失败

1. `ncatbot config check` — 检查配置
2. 确认 NapCat 进程运行中
3. `ws_uri` 格式正确（`ws://` 非 `http://`）
4. `./logs` 目录可写

### 消息不响应

1. 事件类型匹配：`on_group_message()` 不收私聊
2. Hook 拦截：`non_self` / `group_only` 是否过于严格
3. Handler 异常：启用 `--debug` 查完整堆栈
4. 命令匹配：注意大小写，用 `ignore_case=True` 忽略
5. 插件加载：`ncatbot plugin list` 确认

### API 调用失败

1. WebSocket 断连：检查 NapCat 进程
2. 参数类型：`message` 用 `msg.to_list()` 转换
3. Bot 权限：非管理员无法踢人/禁言
4. API 位置：管理方法在 `self.api.qq.manage.*`

### 插件加载失败

1. manifest.toml：必填 `name`, `version`, `main` 须**位于 TOML 顶层**，不能放在 `[plugin]` 等 section 下（否则报"缺少必填字段"）
2. import 路径：`from ncatbot.xxx import yyy`（`ncatbot.plugin_system` 已废弃，改用 `ncatbot.plugin`）
3. pip 依赖：设 `plugin.auto_install_pip_deps: true`
4. 入口类：须继承 `NcatBotPlugin`/`BasePlugin`

### 热重载不工作

1. 使用 `ncatbot dev` 或 `ncatbot run --debug`
2. FileWatcherService 加载成功
3. 仅 `plugins/` 目录变更触发

## 异常类

| 异常 | 说明 |
|------|------|
| `NcatBotError` | 基础异常 |
| `NcatBotValueError(var, val, must_be)` | 参数值错误 |
| `NcatBotConnectionError(info)` | 连接失败 |
| `AdapterEventError` | 适配器事件异常 |
| `PluginCircularDependencyError` | 插件循环依赖 |
| `PluginMissingDependencyError` | 缺少依赖插件 |
| `PluginVersionError` | 版本约束不满足 |

## BotClient 启动序列

```text
run()
  → _startup_core()
    ├─ _setup_adapter()          → NapCat WebSocket 连接
    ├─ _setup_api()              → BotAPIClient 包装
    ├─ _setup_dispatcher()       → AsyncEventDispatcher
    ├─ _setup_handler_dispatcher() → HandlerDispatcher
    └─ _setup_services()         → 内置服务加载
  → _setup_plugins()
    ├─ load_builtin_plugins()
    ├─ load_all(plugin_dir)
    └─ setup_hot_reload()        → 仅 debug 模式
  → adapter.listen()              → 阻塞监听
  → shutdown()
```

启动卡住时按阶段定位：
- `_setup_adapter()` → WebSocket 连接问题
- `_setup_services()` → 内置服务问题
- `load_all()` → 插件加载问题
- `adapter.listen()` → 运行时断连
