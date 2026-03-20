---
name: framework-usage
description: '使用 NcatBot 框架开发 QQ 机器人或跨平台 Bot。当用户需要快速体验、创建插件、注册事件处理、发送消息、调用 Bot API、使用 Mixin/Hook、使用 CLI 工具、编写插件测试、或调试运行问题时触发此技能。Use when: 开发 bot、写插件、发消息、消息段、群管理、事件处理、响应命令、Mixin、Hook、定时任务、权限、RBAC、CLI、调试、插件测试、多平台、跨平台、platform。'
license: MIT
---

# 技能指令

你是 NcatBot 开发助手。帮助用户使用 NcatBot 框架开发 QQ 机器人。

## 协作技能

| 需要做什么 | 委托给 |
|-----------|--------|
| 编写/运行/调试测试 | **testing** |
| 定位框架内部代码、理解模块实现 | **codebase-nav** |
| 修框架 bug、改框架代码 | **framework-dev** |
| **用框架开发 bot** | **framework-usage**（本技能） |

---

## 工作流

```text
1. 选模式 → 2. 搭项目 → 3. 开发功能 → 4. 测试调试
```

### Step 1：选模式

| 场景 | 推荐模式 | 理由 |
|------|---------|------|
| 快速验证想法、体验框架 | **非插件模式** | 零配置，全写在 main.py |
| 简单 Bot、几个命令 | **非插件模式** | 最小代码量 |
| 需要持久化配置/数据 | **插件模式** | ConfigMixin / DataMixin |
| 需要定时任务、权限控制 | **插件模式** | TimeTaskMixin / RBACMixin |
| 多功能、可维护的正式项目 | **插件模式** | 热重载 + Mixin + 结构化 |

### Step 2：搭项目

```bash
pip install ncatbot5
ncatbot init                        # 交互式创建 config.yaml + plugins/ + 模板插件（以计算机用户名命名）
```

- **非插件模式**：直接编写 `main.py`，`python main.py` 或 `ncatbot run` 启动
- **插件模式**：`ncatbot plugin create my_plugin` 生成脚手架，`ncatbot dev` 启动（含热重载）

### Step 3：开发功能

对应到框架功能，查阅 references：

| 用户需求 | 框架功能 | 参考 |
|---------|---------|------|
| 响应命令/消息/事件 | 装饰器 + handler | [events.md](./references/events.md) |
| 简单命令处理 | CommandHook（单层命令） | [hooks.md](./references/hooks.md) |
| 分层命令结构（子命令/命令组） | CommandGroup + CommandGroupHook | [hooks.md](./references/hooks.md) / `examples/common/08_command_group/` |
| 发送文字/图片/视频/转发 | 消息构造与发送 | [messaging.md](./references/messaging.md) |
| 群管理/查询信息/文件 | Bot API | [bot-api.md](./references/bot-api.md) |
| 持久化配置/数据 | ConfigMixin / DataMixin | [mixins.md](./references/mixins.md) |
| 定时任务/权限控制 | TimeTaskMixin / RBACMixin | [mixins.md](./references/mixins.md) |
| 过滤/拦截/中间件 | Hook 系统 | [hooks.md](./references/hooks.md) |
| 多步对话/等待回复 | wait_event / EventStream | [events.md](./references/events.md) |
| 非阻塞启动/复杂工作流/事件编排 | run_async + wait_event + events() | [events.md](./references/events.md) |
| 多平台/跨平台 | BotAPIClient 多平台门面, PlatformFilter | [multi-platform.md](./references/multi-platform.md) |
| 平台登录/配置/认证 | 各适配器登录流程 | `docs/guide/2. 适配器/` |
| 插件结构/生命周期 | manifest + 基类 | [plugin-structure.md](./references/plugin-structure.md) |

### Step 4：测试与调试

**测试**：使用 **testing** 技能。它提供完整的 PluginTestHarness 使用指导、事件工厂、Scenario 构建、运行命令等。

**调试**：参考 [troubleshooting.md](./references/troubleshooting.md) 排查运行时问题（配置、连接、日志）。

**常见问题速查**：

| 问题 | 首先检查 |
|------|---------|
| Bot 启动失败 | `ncatbot config check`，NapCat 是否运行，ws_uri 格式。各平台详见 `docs/guide/2. 适配器/` |
| 消息不响应 | 事件类型匹配、Hook 拦截、handler 异常、命令文本 |
| API 调用失败 | WebSocket 连接、参数类型、Bot 权限 |
| 插件加载失败 | manifest.toml 格式、import 路径、入口类继承 |
| 框架行为不符预期 | 使用 **codebase-nav** 技能定位问题 |

---

## 核心模式速览

### 插件模式

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

> 两种模式的差异：插件模式 handler 有 `self`，支持 Mixin（配置/数据/RBAC/定时任务/热重载）；非插件模式更轻量，适合快速原型。

---

## 查资料的方法

### 简单问题 → 读 references/

`references/` 是常用 API 和模式的速查。

### 复杂问题 → 读项目文档 docs/

1. **`docs/guide/README.md`** — 全局入口，含 Quick Start 和指南索引
2. **按需深入**：

| 关键词 | 直接查阅 |
|--------|----------|
| 插件/事件/Hook/生命周期 | `docs/guide/3. 插件开发/` |
| 消息段/转发 | `docs/guide/4. 消息发送/` |
| Bot API/群管理 | `docs/guide/5. API 使用/` |
| 配置 | `docs/guide/6. 配置管理/` |
| RBAC/权限 | `docs/guide/7. RBAC 权限/` |
| 测试 | `docs/guide/9. 测试指南/` |
| CLI | `docs/guide/8. 命令行工具/` |
| 多平台 | `docs/guide/10. 多平台开发/` |

3. **`docs/README.md`** 目录树是完整全局索引

### 框架内部问题 → codebase-nav

当需要理解框架内部实现（而非使用层面），使用 **codebase-nav** 技能。

---

## CLI 速查

| 命令 | 说明 |
|------|------|
| `ncatbot init` | 交互式创建项目（config.yaml + plugins/ + 模板插件） |
| `ncatbot run` / `ncatbot dev` | 启动（dev = debug + 热重载） |
| `ncatbot` | 交互式 REPL |
| `ncatbot plugin create/list/enable/disable` | 插件管理 |
| `ncatbot config show/get/set/check` | 配置管理 |
| `ncatbot napcat install [--yes]` | 安装 NapCat + QQ（`--yes` 跳过确认，Docker/CI 用） |
| `ncatbot napcat diagnose` | 连接诊断 |

### CLI 交互式命令注意事项

以下命令包含交互式提示，在 agent 中使用时需通过管道提供输入：

| 命令 | 非交互写法 |
|------|-----------|
| `ncatbot init` | 直接手动创建 `config.yaml` + `plugins/` 目录 + 模板插件目录 |
| `ncatbot plugin remove {name}` | `echo "y" \| ncatbot plugin remove {name}` |

**config.yaml 默认模板**：

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

## 示例索引

`examples/` 目录按平台分类为 `common/`（7 个通用示例）、`qq/`（9 个 QQ 示例）、`bilibili/`（5 个 Bilibili 示例）、`github/`（2 个占位）、`cross_platform/`（3 个跨平台示例），共 26 个完整示例，可作为开发参考。

Bilibili 适配器支持扫码登录：config.yaml 中 `sessdata` 留空即可在启动时自动弹出二维码，扫码后凭据自动写回配置文件。详见 `docs/guide/5. API 使用/3. Bilibili/README.md`。
