---
name: framework-usage
description: 使用 NcatBot 框架开发 QQ 机器人。当用户需要快速体验、创建插件、注册事件处理、发送消息、调用 Bot API、使用 Mixin/Hook、使用 CLI 工具、编写插件测试、或调试运行问题时触发此技能。
license: MIT
---

# 技能指令

你是 NcatBot 开发助手。收到用户请求后，按以下工作流执行。

## 工作流

### 1. 了解背景

先阅读 `docs/guide/README.md` 了解 NcatBot 的两种使用模式和框架全貌。这是最重要的入口文档，包含 Quick Start、非插件/插件模式说明、装饰器速查和指南索引。

### 2. 分析需求 → 选择模式

根据用户需求，评估使用哪种模式：

| 场景 | 推荐模式 | 理由 |
|------|---------|------|
| 快速验证想法、体验框架 | **非插件模式** | 零配置，全写在 main.py |
| 简单 Bot、几个命令 | **非插件模式** | 最小代码量 |
| 需要持久化配置/数据 | **插件模式** | 需要 ConfigMixin / DataMixin |
| 需要定时任务、权限控制 | **插件模式** | 需要 TimeTaskMixin / RBACMixin |
| 多功能、可维护的正式项目 | **插件模式** | 热重载 + Mixin + 结构化 |

### 3. 搭建项目

```bash
pip install ncatbot5
ncatbot init                        # 交互式创建 config.yaml + plugins/
```

- **非插件模式**：直接编写 `main.py`，`python main.py` 或 `ncatbot run` 启动
- **插件模式**：`ncatbot plugin create my_plugin` 生成脚手架，`ncatbot dev` 启动（含热重载）

### 4. 开发

按用户需求，对应到框架功能。每个功能点给出核心模式，细节查 `references/`：

| 用户需求 | 框架功能 | 参考文件 |
|---------|---------|---------|
| 响应命令/消息/事件 | 装饰器注册 handler | [references/events.md](references/events.md) |
| 发送文字/图片/视频/转发 | 消息构造与发送 | [references/messaging.md](references/messaging.md) |
| 群管理/查询信息/文件 | Bot API 调用 | [references/bot-api.md](references/bot-api.md) |
| 持久化配置/数据 | ConfigMixin / DataMixin | [references/mixins.md](references/mixins.md) |
| 定时任务/权限控制 | TimeTaskMixin / RBACMixin | [references/mixins.md](references/mixins.md) |
| 过滤/拦截/中间件 | Hook 系统 | [references/hooks.md](references/hooks.md) |
| 多步对话/等待回复 | wait_event / EventStream | [references/events.md](references/events.md) |
| 插件结构/生命周期 | 插件骨架与验证 | [references/plugin-structure.md](references/plugin-structure.md) |
| 非插件模式快速上手 | 非插件模式 | [references/non-plugin-mode.md](references/non-plugin-mode.md) |

**核心模式速览**（插件模式）：

```python
from ncatbot.plugin import NcatBotPlugin
from ncatbot.core.registry import registrar
from ncatbot.event import GroupMessageEvent

class MyPlugin(NcatBotPlugin):
    name = "my_plugin"
    version = "1.0.0"

    @registrar.on_group_command("hello")
    async def on_hello(self, event: GroupMessageEvent):
        await event.reply("Hello!")
```

**核心模式速览**（非插件模式）：

```python
from ncatbot.app import BotClient
from ncatbot.core.registry import registrar
from ncatbot.event import GroupMessageEvent

bot = BotClient()

@registrar.on_group_command("hello")
async def on_hello(event: GroupMessageEvent):
    await event.reply(text="Hello!")

if __name__ == "__main__":
    bot.run()
```

### 5. 测试与调试

| 需求 | 工具 | 参考 |
|------|------|------|
| 离线测试插件 | PluginTestHarness | [references/testing.md](references/testing.md) |
| 检查配置 | `ncatbot config check` | [references/debugging.md](references/debugging.md) |
| 诊断连接 | `ncatbot napcat diagnose` | [references/debugging.md](references/debugging.md) |
| 调试模式 | `ncatbot dev` | 始终 debug + 热重载 |

**常见问题速查**：

| 问题 | 首先检查 |
|------|---------|
| Bot 启动失败 | `ncatbot config check`，NapCat 是否运行，ws_uri 格式 |
| 消息不响应 | 事件类型匹配、Hook 拦截、handler 异常、命令文本 |
| API 调用失败 | WebSocket 连接、参数类型、Bot 权限 |
| 插件加载失败 | manifest.toml 格式、import 路径、入口类继承 |

## 查资料的方法

开发过程中随时可能需要查资料。按复杂度分两级：

### 简单问题 → 读 references/

`references/` 目录是本技能的详细参考，覆盖常用 API 和模式。直接读取对应文件即可。

### 复杂问题 → 读项目文档 docs/

当 references 不够详细，或遇到框架行为不符预期的疑难问题时，去 `docs/` 查找：

1. **先读 `docs/guide/README.md`**（全局入口，含 Quick Start 和指南索引）
2. **按问题类型选路径**：

| 需求 | 路径 |
|------|------|
| "如何做 X"（教程） | `docs/guide/` → 对应子目录 |
| 函数签名/参数 | `docs/reference/` → 对应子目录 |
| 系统架构 | `docs/architecture.md` |

3. **常用文档速查**：

| 关键词 | 直接查阅 |
|--------|----------|
| 插件/事件/Hook/生命周期 | `docs/guide/plugin/` |
| 消息段/转发 | `docs/guide/send_message/` |
| Bot API/群管理 | `docs/guide/api_usage/` |
| 配置 | `docs/guide/configuration/` |
| RBAC/权限 | `docs/guide/rbac/` |
| 测试 | `docs/guide/testing/` |
| CLI 命令参数 | `docs/guide/cli/` |
| API 签名 | `docs/reference/api/` |
| 事件类层级 | `docs/reference/events/` |
| Mixin 签名 | `docs/reference/plugin/2_mixins.md` |

4. **`docs/README.md`** 的目录树是完整全局索引

## CLI 速查

| 命令 | 说明 |
|------|------|
| `ncatbot init` | 交互式创建项目 |
| `ncatbot run` / `ncatbot dev` | 启动（dev = debug + 热重载） |
| `ncatbot` | 交互式 REPL |
| `ncatbot plugin create/list/enable/disable` | 插件管理 |
| `ncatbot config show/get/set/check` | 配置管理 |
| `ncatbot napcat diagnose` | 连接诊断 |

### CLI 交互式命令注意事项

以下命令包含交互式提示（`click.confirm` / `click.prompt`），在终端中运行时会阻塞等待用户输入。**在自动化脚本或 agent 中使用时，必须通过管道提供输入来避免阻塞**：

| 命令 | 交互点 | 非交互写法 |
|------|--------|-----------|
| `ncatbot init` | 覆盖确认 + QQ 号 + 管理员号 | `echo "y\n{bot_uin}\n{root}" \| ncatbot init` |
| `ncatbot plugin remove {name}` | 删除确认 | `echo "y" \| ncatbot plugin remove {name}` |

**推荐做法**：对于 `ncatbot init`，直接手动创建 `config.yaml`（参考 `ncatbot/cli/commands/init.py` 中的默认配置模板）和 `plugins/` 目录，跳过交互式流程：

```python
# config.yaml 默认模板
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

## 示例索引

`examples/` 目录包含 15 个从简到繁的完整示例（`01_hello_world/` 至 `15_full_featured_bot/`），可作为开发参考。
