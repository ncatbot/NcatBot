# 搭建与启动参考

> 参考文档：`docs/docs/notes/guide/1. 快速开始/`、`docs/docs/notes/guide/2. 适配器/`、`docs/docs/notes/guide/8. 命令行工具/`

## 安装

```bash
pip install ncatbot5
```

## 工作区检测（搭建前必做）

在创建或修改项目之前，先判断当前工作区状态：

| 工作区状态 | 操作 |
|-----------|------|
| 已有 `config.yaml` + `plugins/` | 直接开发插件，不要重新搭建项目 |
| 已有 `config.yaml`，无 `plugins/` | 手动创建 `plugins/` 目录，然后开发 |
| NcatBot 框架源码仓库 | 在 `plugins/` 目录下开发插件，**不要在仓库外新建项目** |
| 空目录 | 用 `ncatbot init` 或手动搭建（见下方） |

> **核心规则**：不要在已有项目的工作区外新建独立项目目录。插件开发在当前工作区的 `plugins/` 下进行。

## 项目搭建

### 方式 1：CLI 交互式（推荐）

```bash
ncatbot init    # 交互式创建 config.yaml + plugins/ + 模板插件
```

### 方式 2：手动创建

创建项目目录，包含 `config.yaml` 和 `plugins/` 目录即可。

## config.yaml 默认模板

```yaml
bot_uin: "{QQ号}"
root: "{管理员QQ号}"
debug: false
napcat:
  ws_uri: ws://localhost:3001
  ws_token: napcat_ws
  webui_uri: http://localhost:6099
  webui_token: napcat_webui
  enable_webui: true
plugin:
  plugins_dir: plugins
  load_plugin: true
  plugin_whitelist: []
  plugin_blacklist: []
```

多平台适配器配置见 [multi-platform.md](./multi-platform.md)。

## 两种模式最小代码

### 插件模式（推荐）

```python
from ncatbot.plugin import NcatBotPlugin
from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent

class MyPlugin(NcatBotPlugin):
    name = "my_plugin"
    version = "1.0.0"

    @registrar.on_group_command("hello")
    async def on_hello(self, event: GroupMessageEvent):
        await event.reply("Hello!")
```

配合 `manifest.toml`：

```toml
name = "my_plugin"
version = "1.0.0"
main = "main.py"
```

> 插件模式 handler 有 `self`，支持 Mixin（配置/数据/RBAC/定时任务/热重载）。

### 非插件模式

```python
from ncatbot.app import BotClient
from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent

bot = BotClient()

@registrar.on_group_command("hello")
async def on_hello(event: GroupMessageEvent):
    await event.reply(text="Hello!")

if __name__ == "__main__":
    bot.run()
```

> 非插件模式更轻量，适合快速原型。handler 无 `self`，不支持 Mixin。

## 启动方式

| 方式 | 命令 | 说明 |
|------|------|------|
| 生产 | `ncatbot run` 或 `python main.py` | 正常启动 |
| 开发 | `ncatbot dev` | debug 模式 + 热重载 |

## CLI 速查

| 命令 | 说明 |
|------|------|
| `ncatbot init` | 交互式创建项目（config.yaml + plugins/ + 模板插件） |
| `ncatbot run` / `ncatbot dev` | 启动（dev = debug + 热重载） |
| `ncatbot` | 交互式 REPL |
| `ncatbot plugin create <name>` | 创建插件脚手架 |
| `ncatbot plugin list` | 列出所有插件 |
| `ncatbot plugin enable/disable <name>` | 启用/禁用插件 |
| `ncatbot config show` | 查看完整配置 |
| `ncatbot config get <key>` | 查看特定配置项 |
| `ncatbot config set <key> <value>` | 设置配置项 |
| `ncatbot config check` | 一键检查配置有效性 |
| `ncatbot napcat install [--yes]` | 安装 NapCat + QQ（`--yes` 跳过确认，Docker/CI 用） |
| `ncatbot napcat diagnose` | 连接诊断 |

> ⚠️ **NapCat 自动安装说明**：NapCat 由 NcatBot Setup 模式（首次 `ncatbot run` 或 `ncatbot dev`）自动安装，无需手动安装。`ncatbot napcat install --yes` 仅用于 CI/Docker 等无交互环境。启动后通过 WebUI 扫码登录 QQ。

### CLI 交互式命令注意事项

以下命令包含交互式提示，在 agent 中使用时需通过管道提供输入：

| 命令 | 非交互写法 |
|------|-----------|
| `ncatbot init` | 直接手动创建 `config.yaml` + `plugins/` 目录 + 模板插件目录 |
| `ncatbot plugin remove {name}` | `echo "y" \| ncatbot plugin remove {name}` |

## 核心导入路径

| 导入 | 说明 |
|------|------|
| `from ncatbot.app import BotClient` | 应用入口 |
| `from ncatbot.core import registrar` | 全局事件注册器 |
| `from ncatbot.plugin import NcatBotPlugin` | 插件基类 |
| `from ncatbot.event.qq import GroupMessageEvent` | QQ 群消息事件 |
| `from ncatbot.event.qq import PrivateMessageEvent` | QQ 私聊事件 |
| `from ncatbot.types import MessageArray` | 消息数组 |
| `from ncatbot.utils import get_log` | 日志工具 |

## 示例索引

`docs/docs/examples/` 目录按平台分类，共 27 个完整示例：

| 分类 | 数量 | 说明 |
|------|------|------|
| `common/` | 8 | 通用示例（hello_world、config_data、hook、rbac、定时任务、多步对话、外部 API、命令组） |
| `qq/` | 9 | QQ 平台示例（事件处理、消息类型、Bot API、群管理、全功能 Bot 等） |
| `bilibili/` | 5 | Bilibili 示例（直播间、私信、评论等） |
| `github/` | 2 | GitHub 示例（hello_world、issue_bot） |
| `cross_platform/` | 3 | 跨平台示例（多适配器、Trait 编程、GitHub↔QQ 桥接） |

> 完整索引与特性覆盖矩阵：`docs/docs/examples/README.md`
