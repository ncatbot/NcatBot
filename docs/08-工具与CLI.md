# 工具模块与 CLI

本文档覆盖 NcatBot 的基础工具层（`ncatbot/utils/`）、命令行界面（`ncatbot/cli/`）、测试框架（`ncatbot/utils/testing/`）以及 MCP 集成（`ncatbot/mcp/`）。

## 目录结构

```
ncatbot/utils/
├── __init__.py
├── logger.py              # 日志系统（FoldedLogger、ColoredFormatter）
├── status.py              # 全局状态管理
├── network_io.py          # 网络 I/O 工具
├── error.py               # 异常体系
├── config/                # 三层配置系统
│   ├── manager.py         # 配置管理器（公共 API）
│   ├── models.py          # Pydantic 模型
│   └── storage.py         # 文件 I/O
└── testing/               # 测试框架
    ├── factory.py          # 事件工厂
    ├── mixins.py           # 测试混入
    └── suite.py            # E2E 测试套件

ncatbot/cli/
├── main.py                # CLI 入口
└── commands/
    ├── registry.py         # 命令注册表
    ├── config_commands.py  # 配置命令
    ├── info_commands.py    # 信息命令
    ├── system_commands.py  # 系统命令
    └── plugin_commands.py  # 插件命令

ncatbot/mcp/
└── main.py                # MCP 服务器
```

---

## 1. 日志系统

**文件**: `ncatbot/utils/logger.py`

### 核心组件

#### FoldedLogger

自定义 Logger，具备以下增强能力：

- **大消息截断**：超过 1000 字符的消息自动截断
- **Base64 折叠**：自动检测并折叠 Base64 编码内容
- **调用栈采集**：通过 `stacklevel` 记录正确的调用位置

#### ColoredFormatter

为日志输出添加 ANSI 颜色：

| 元素 | 着色 |
|------|------|
| `colored_levelname` | 按日志级别着色 |
| `colored_name` | 日志器名称着色 |
| `colored_time` | 时间戳着色 |

#### RegisteredLoggerFilter

Debug 级别日志过滤器，只允许通过 `get_log()` 注册的日志器输出 DEBUG 日志，防止第三方库的调试信息污染输出。

### 日志架构

```
get_log(name)                        # 入口函数
    │
    └── 返回 FoldedLogger 实例
            │
            ├── TimedRotatingFileHandler  # 文件输出
            │   └── 每日轮转，保留 7 天
            │
            └── StreamHandler             # 控制台输出
                └── ColoredFormatter (ANSI 颜色)
```

支持基于正则的日志路由规则。

### 进度条

内置 `tqdm` 封装类，提供语义化颜色映射（BLACK、RED、GREEN 等）。

### 入口函数

```python
def get_log(name: Optional[str] = None) -> FoldedLogger
```

返回 FoldedLogger 实例，并自动注册到全局 `status` 对象。

---

## 2. 全局状态管理

**文件**: `ncatbot/utils/status.py`

```python
class Status:
    """线程安全的全局状态持有器"""
```

使用 `threading.Lock` 保护所有状态变更。

### 管理的状态

| 属性 | 类型 | 说明 |
|------|------|------|
| `exit` | `bool` | 退出标志 |
| `current_github_proxy` | `str` | 当前 GitHub 代理 |
| `global_access_manager` | - | RBAC 全局访问管理器 |
| `_registered_loggers` | `dict` | 已注册的日志器 |

### 日志管理方法

- 注册日志器
- 同步所有日志器级别（配置变更时）

全局单例：`status = Status()`

---

## 3. 网络 I/O 工具

**文件**: `ncatbot/utils/network_io.py`

### 函数列表

| 函数 | 签名 | 说明 |
|------|------|------|
| `post_json` | `(url, payload, headers, timeout=5.0)` | JSON POST 请求（自动添加 User-Agent） |
| `get_json` | `(url, headers, timeout=5.0)` | JSON GET 请求 |
| `download_file` | `(url, file_name)` | 流式下载，带 tqdm 进度条 |
| `get_proxy_url` | `()` | 检测 GitHub 代理可用性（主选 ghfast.top），结果缓存 |
| `gen_url_with_proxy` | `(original_url)` | 为 URL 添加代理前缀 |

### 代理机制

自动检测 GitHub 代理的可用性，检测结果缓存到 `status.current_github_proxy`，避免重复检测。

---

## 4. 异常体系

**文件**: `ncatbot/utils/error.py`

```
NcatBotError                          # 基础异常
├── 自动日志记录
├── Debug 模式下自动采集调用栈
│
├── NcatBotValueError                 # 值验证异常
│   └── "{var_name} 的值(必须|不能)为 {val_name}"
│
├── NcatBotConnectionError            # 网络连接异常
│   └── "网络连接错误" 前缀
│
└── AdapterEventError                 # 事件处理异常
```

### 特点

- **自动日志**：异常创建时自动通过全局日志记录
- **调用栈采集**：Debug 模式下自动捕获创建位置的调用栈
- **结构化消息**：子类提供模板化的错误消息格式

---

## 5. 配置系统（三层架构）

**文件**: `ncatbot/utils/config/`

### 架构

```
┌───────────────────────────────────┐
│  manager.py — ConfigManager      │  公共 API 层
│  · get/set/save/reload           │
│  · 嵌套键更新                     │
│  · 交互式验证                     │
└──────────────┬────────────────────┘
               │
┌──────────────▼────────────────────┐
│  models.py — Pydantic 模型       │  数据验证层
│  · Config / NapCatConfig         │
│  · PluginConfig                  │
│  · 字段验证 + 安全检查            │
└──────────────┬────────────────────┘
               │
┌──────────────▼────────────────────┐
│  storage.py — ConfigStorage      │  文件 I/O 层
│  · YAML 读写                     │
│  · 原子写入（临时文件 → 替换）    │
└───────────────────────────────────┘
```

### 模型层（models.py）

#### BaseConfig

```python
class BaseConfig:
    def get_field_paths(self) -> dict    # 递归生成嵌套字段路径映射
    def to_dict(self) -> dict            # 导出为字典
```

#### NapCatConfig

```python
@dataclass
class NapCatConfig(BaseConfig):
    ws_uri: str            # WebSocket URI（自动补 ws:// 前缀）
    ws_token: str          # WebSocket Token
    webui_uri: str         # WebUI URI（自动补 http:// 前缀）
    webui_token: str       # WebUI Token
    enable_webui: bool     # 是否启用 WebUI
    remote_mode: bool      # 远端模式
    # ...
```

解析属性（从 URI 中提取）：

| 属性 | 说明 |
|------|------|
| `ws_host` | 从 `ws_uri` 解析主机 |
| `ws_port` | 从 `ws_uri` 解析端口 |
| `webui_host` | 从 `webui_uri` 解析主机 |
| `webui_port` | 从 `webui_uri` 解析端口 |

安全检查：

```python
def get_security_issues(self, auto_fix=True) -> list
```

Token 强度要求：长度 ≥12、含大写、小写、数字、特殊字符。

#### PluginConfig

```python
@dataclass
class PluginConfig(BaseConfig):
    plugins_dir: str              # 插件目录
    plugin_whitelist: list        # 白名单
    plugin_blacklist: list        # 黑名单
    load_plugin: bool             # 是否加载插件
```

#### Config（主配置）

```python
@dataclass
class Config(BaseConfig):
    napcat: NapCatConfig          # NapCat 配置
    plugin: PluginConfig          # 插件配置
    bot_uin: int                  # Bot QQ 号
    root: int                     # 管理员 QQ 号
    debug: bool                   # 调试模式
```

### 存储层（storage.py）

```python
class ConfigStorage:
    # 原子写入：先写临时文件，再替换目标文件
    # 路径：环境变量 CONFIG_PATH 或 ${CWD}/config.yaml
```

### 管理层（manager.py）

```python
class ConfigManager:
    def update_value(self, key: str, value: Any) -> None   # 支持嵌套键 "napcat.ws_uri"
    def save(self) -> None                                  # 持久化到 YAML
    def reload(self) -> None                                # 从文件重新加载
```

惰性加载：`_config` 在首次访问时从文件加载。

单例获取：

```python
def get_config_manager(path=None) -> ConfigManager
```

### 密码工具

| 函数 | 说明 |
|------|------|
| `strong_password_check(pwd)` | 验证密码强度（≥12字符 + 数字 + 大小写 + 特殊字符） |
| `generate_strong_token(length=16)` | 生成符合要求的随机 Token |

### 交互式配置

```python
def fix_invalid_config_interactive()
```

未设置 QQ 号时自动提示用户输入。

---

## 6. 测试框架

**文件**: `ncatbot/utils/testing/`

### EventFactory — 事件工厂

静态工厂类，用于构造测试用事件对象：

| 方法 | 生成事件 |
|------|----------|
| `create_group_message(message, group_id, user_id, ...)` | GroupMessageEvent |
| `create_private_message(message, user_id, ...)` | PrivateMessageEvent |
| `create_notice_event(notice_type, user_id, ...)` | NoticeEvent |
| `create_request_event(request_type, user_id, ...)` | RequestEvent |
| `create_friend_request_event(...)` | 好友请求事件 |
| `create_group_add_request_event(...)` | 入群请求事件 |
| `create_group_increase_notice_event(...)` | 群成员增加通知 |

自动生成唯一 `message_id` 和时间戳。

### 测试混入（Mixin 模式）

| 混入 | 提供能力 |
|------|----------|
| **PluginMixin** | `index_plugin()`、`register_plugin()`、`unregister_plugin()` |
| **InjectorMixin** | `inject_event()`、`inject_group_message()`、`inject_private_message()`、`inject_*_notice()` |
| **AssertionMixin** | `assert_api_called()`、`assert_api_called_with()`、`assert_reply_sent()`、`get_api_calls()` |

### E2ETestSuite — 端到端测试套件

组合所有 Mixin，提供完整的端到端测试能力：

```python
class E2ETestSuite(PluginMixin, InjectorMixin, AssertionMixin):
    async def setup(self):
        # 创建 MockServer + 配置 BotClient
        pass

    async def teardown(self):
        # 清理资源，恢复配置
        pass
```

支持上下文管理器：

```python
async with E2ETestSuite() as suite:
    await suite.inject_group_message("hello")
    suite.assert_reply_sent()
```

属性访问：`.client`、`.event_bus`、`.services`、`.api`、`.mock_server`

自动端口分配：`_port_counter` 从 16700 递增。

---

## 7. CLI 命令行界面

**文件**: `ncatbot/cli/`

### 入口流程

```python
def main():
    # 1. 解析参数：-c 命令、-a 参数、-w 工作目录、-d 调试、--version
    # 2. 版本标志 → 显示元信息并退出
    # 3. 验证工作目录
    # 4. 检查 QQ 号是否已设置（未设置则提示 set_qq()）
    # 5. 命令模式 or 交互式 REPL
```

### 运行模式

| 模式 | 触发方式 | 说明 |
|------|----------|------|
| **命令模式** | `ncatbot -c start` | 执行单条命令后退出 |
| **交互模式** | `ncatbot` | 进入 REPL，显示 `> ` 提示符 |

### 命令注册系统

```python
class CommandRegistry:
    commands: Dict[str, Command]           # 命令名 → 命令定义
    aliases: Dict[str, str]                # 别名 → 规范名
    categories: Dict[str, List[str]]       # 分类 → 命令列表
```

使用装饰器注册命令：

```python
@registry.register(
    name="start",
    description="启动机器人",
    usage="start",
    aliases=["s", "run"],
    category="system"
)
def start_bot():
    client = BotClient()
    client.run()
```

| 方法 | 说明 |
|------|------|
| `execute(command_name, *args)` | 解析别名并执行命令 |
| `get_help(category, only_important)` | 生成格式化帮助文本 |
| `get_categories()` | 获取所有分类 |
| `get_commands_by_category(cat)` | 获取分类下的命令列表 |

### 内置命令

#### 配置命令

| 命令 | 别名 | 用法 | 说明 |
|------|------|------|------|
| `setqq` | `qq` | `setqq [QQ号]` | 设置 Bot QQ 号 |
| `setroot` | `root` | `setroot [QQ号]` | 设置管理员 QQ 号 |
| `config` | `cfg` | `config` | 显示当前配置（QQ号、URI、插件目录等） |

#### 信息命令

| 命令 | 别名 | 说明 |
|------|------|------|
| `help` | `h`, `?` | 显示帮助（通用或特定命令） |
| `meta` | `version`, `v` | 显示版本信息（ncatbot版本、Python、OS、工作目录、QQ号） |
| `categories` | `cat` | 列出/筛选命令分类，显示每分类的命令数量 |

#### 系统命令

| 命令 | 别名 | 说明 |
|------|------|------|
| `start` | `s`, `run` | 实例化 BotClient 并启动 |
| `update` | `u`, `upgrade` | 通过阿里云镜像 `pip install --upgrade ncatbot` |
| `exit` | `q`, `quit` | 抛出 `CLIExit` 异常退出 REPL |

#### 插件命令

| 命令 | 别名 | 说明 |
|------|------|------|
| `create` | `new`, `template` | 创建插件模板（验证名称正则，复制模板，替换 manifest.toml 占位符） |
| `remove` | `rm`, `uninstall` | 删除插件（确认后 `shutil.rmtree`） |
| `list` | `ls` | 列出所有插件目录，解析 manifest.toml 显示信息 |

### CLI 颜色系统

```python
class ColorScheme:
    HEADER   # 青色加粗
    TITLE    # 蓝色加粗
    COMMAND  # 绿色加粗
    # ...
```

自动检测终端颜色支持（`NO_COLOR`、`FORCE_COLOR`、`WT_SESSION`、ANSI 能力等）。

语义化颜色函数：`command()`、`category()`、`error()`、`success()`、`warning()`、`info()`

### CLI 常量

```python
PYPI_SOURCE = "https://mirrors.aliyun.com/pypi/simple/"  # 阿里云 PyPI 镜像
```

---

## 8. MCP 集成

**文件**: `ncatbot/mcp/main.py`

MCP（Model Context Protocol）集成允许 AI 模型直接与 NcatBot 交互。

### NcatBotClient 包装器

```python
class NcatBotClient:
    bot_qq: int
    admin_qq: int
    bot: BotClient
    api: BotAPI
    messages: List[Dict]     # 消息缓存
    initialized: bool
```

| 方法 | 说明 |
|------|------|
| `initialize()` | 调用 `bot.run_backend()`，支持同步/异步结果自动检测 |
| `send_group_message(group_id, message)` | 发送群消息，记录到缓存 |
| `send_private_message(user_id, message)` | 发送私聊消息，记录到缓存 |
| `get_group_list()` | 获取群列表 |
| `get_messages(message_type)` | 按类型筛选消息缓存 |

### MCP 服务器

全局实例：`server = Server("ncatbot")`

#### 资源

| URI | 说明 |
|-----|------|
| `ncatbot://messages` | 消息列表（JSON） |
| `ncatbot://groups` | 群列表（JSON） |

#### 工具

| 工具名 | 参数 | 说明 |
|--------|------|------|
| `send_group_message` | `group_id`, `message` | 发送群消息 |
| `send_private_message` | `user_id`, `message` | 发送私聊消息 |
| `get_group_list` | 无 | 获取群列表 |
| `get_messages` | `message_type?` | 获取消息（可选类型筛选） |

#### 入口

```python
async def main(bot_qq_, admin_qq_):
    # 异步入口，启动 stdio_server

def start(admin_qq, bot_qq):
    # 同步包装器，调用 asyncio.run(main())
```

---

## 9. 跨模块集成关系

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Config     │────▶│   Logger     │────▶│   Status     │
│  (3-layer)   │     │ (FoldedLogger)     │ (全局状态)   │
└──────┬───────┘     └──────────────┘     └──────────────┘
       │
       │  config.debug 变更 → status.update_logger_level()
       │
┌──────▼───────┐
│     CLI      │
│ (命令系统)   │───── 操作 ncatbot_config 单例并调用 .save()
└──────┬───────┘
       │
       │  start 命令 → BotClient().run()
       │
┌──────▼───────┐     ┌──────────────┐
│   BotClient  │     │    Testing   │
│  (核心引擎)  │◀────│ (E2E 套件)  │
└──────────────┘     │ 配置 MockWS  │
                     └──────────────┘
       │
       │  run_backend → NcatBotClient 包装
       │
┌──────▼───────┐
│     MCP      │
│ (AI 集成)    │
└──────────────┘
```

### 关键集成点

| 集成路径 | 说明 |
|----------|------|
| Config → Logger | 调试模式变更时同步所有日志器级别 |
| CLI → Config | 命令直接操作 `ncatbot_config` 单例 |
| CLI → BotClient | `start` 命令实例化并启动 BotClient |
| Testing → Config | E2E 套件将 MockServer URI 注入 `ncatbot_config.napcat.ws_uri`，测试后恢复 |
| MCP → BotClient | NcatBotClient 包装 BotClient，对外暴露 MCP 工具 |

---

## 10. 设计要点

### 单例模式的统一使用

- `ConfigManager`：全局唯一配置实例
- `Status`：全局状态管理
- `CommandRegistry`：命令注册中心
- `MCP Server`：全局 MCP 服务实例

### 线程安全

`Status` 类使用 `threading.Lock` 保护所有状态变更，确保多线程环境下的数据一致性。

### 配置原子写入

`ConfigStorage` 使用临时文件 → 替换的原子写入策略，防止配置文件在写入过程中损坏。

### 装饰器驱动的命令注册

CLI 命令通过 `@registry.register()` 装饰器声明式注册，新增命令只需添加装饰器即可自动纳入帮助系统和分类体系。

### 组合式测试框架

测试框架采用 Mixin 模式组合 Plugin、Injector、Assertion 三类能力，E2ETestSuite 通过多继承获得完整的端到端测试能力。
