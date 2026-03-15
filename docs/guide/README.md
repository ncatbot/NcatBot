# 使用指南

> NcatBot 从入门到进阶的完整指南

---

## Quick Start

### 1. 安装与配置

```bash
pip install ncatbot5
mkdir my-bot && cd my-bot
```

创建 `config.yaml`：

```yaml
bt_uin: "你的QQ号"
ws_uri: "ws://localhost:3001"
```

### 2. 编写入口文件

创建 `main.py`：

```python
from ncatbot.app import BotClient
from ncatbot.core.registry import registrar
from ncatbot.event import GroupMessageEvent

bot = BotClient()

@registrar.on_group_command("hello", ignore_case=True)
async def on_hello(event: GroupMessageEvent):
    await event.reply(text="Hello, NcatBot!")

if __name__ == "__main__":
    bot.run()
```

### 3. 启动

确保 NapCat 已运行，然后 `python main.py`。发送 `hello` 给 Bot，收到回复即成功。

---

## 框架使用

NcatBot 提供两种使用模式：**非插件模式** 和 **插件模式**。

| | 非插件模式 | 插件模式 |
|---|---|---|
| 适合场景 | 快速原型、简单 Bot | 功能丰富、可维护的 Bot |
| 代码组织 | 全部写在 `main.py` | 插件目录 + `manifest.toml` |
| 装饰器 | `@registrar.on_xxx()` | `@registrar.on_xxx()`（相同） |
| Mixin 能力 | 无 | 配置、数据持久化、RBAC、定时任务 |
| 热重载 | 不支持 | 支持 |

### 非插件模式

直接在入口文件中用 `registrar` 注册回调。适合快速验证想法。

#### 命令匹配 — `on_command`

`on_command` 是最常用的装饰器，匹配用户发送的命令文本，支持**参数自动绑定**：

```python
from ncatbot.app import BotClient
from ncatbot.core.registry import registrar
from ncatbot.event import GroupMessageEvent, PrivateMessageEvent

bot = BotClient()

# 群 + 私聊命令
@registrar.on_command("ping", ignore_case=True)
async def on_ping(event):
    await event.reply(text="pong!")

# 仅群聊命令 — 发送 "echo 你好" → 回复 "你好"
@registrar.on_group_command("echo")
async def on_echo(event: GroupMessageEvent, content: str):
    await event.reply(text=content)

# 仅私聊命令
@registrar.on_private_command("hello")
async def on_hello(event: PrivateMessageEvent):
    await event.reply(text="你好！")

if __name__ == "__main__":
    bot.run()
```

> `content: str` 由 CommandHook 自动提取命令后的文本，支持 `str`、`int`、`At` 类型。

#### 参数自动绑定

CommandHook 根据函数签名的**类型注解**自动从消息中提取参数：

```python
from ncatbot.types import At

# "禁言 @某人 60" → target=At对象, duration=60
@registrar.on_group_command("禁言")
async def on_ban(event: GroupMessageEvent, target: At = None, duration: int = 60):
    if target is None:
        await event.reply(text="请 @一个用户，例如: 禁言 @xxx 60")
        return
    await event.reply(text=f"已禁言 {target.qq}，{duration} 秒")

# "设置前缀 !" → new_prefix="!"
@registrar.on_group_command("设置前缀")
async def on_set_prefix(event: GroupMessageEvent, new_prefix: str):
    await event.reply(text=f"前缀已更新为: {new_prefix}")
```

#### 消息监听 — `on_group_message`

不匹配命令，监听所有群消息：

```python
@registrar.on_group_message(priority=50)
async def on_keyword(event: GroupMessageEvent):
    if "关键词" in event.message.text:
        await event.reply(text="检测到关键词！")
```

> `priority` 越大越先执行。多个 handler 按优先级排序。

#### 通知与请求事件

```python
from ncatbot.event import NoticeEvent, FriendRequestEvent
from ncatbot.types import MessageArray

@registrar.on_group_increase()
async def on_welcome(event):
    msg = MessageArray()
    msg.add_at(event.user_id)
    msg.add_text(" 欢迎加入！")
    await event.reply(rtf=msg)

@registrar.on_poke()
async def on_poke(event: NoticeEvent):
    if str(event.data.target_id) == str(event.self_id):
        await event.reply(text="别戳我！")

@registrar.on_friend_request()
async def on_friend(event: FriendRequestEvent):
    await event.approve()
```

#### 多步对话 — `wait_event`

```python
import asyncio

@registrar.on_group_command("注册")
async def on_register(event: GroupMessageEvent):
    await event.reply(text="请输入你的名字（30秒内）：")
    try:
        reply = await bot.dispatcher.wait_event(
            predicate=lambda e: (
                str(e.data.user_id) == str(event.user_id)
                and str(e.data.group_id) == str(event.group_id)
            ),
            timeout=30.0,
        )
        await event.reply(text=f"你好，{reply.data.raw_message.strip()}！")
    except asyncio.TimeoutError:
        await event.reply(text="超时，注册已取消")
```

---

### 插件模式（推荐）

插件模式将功能封装为独立目录，支持配置管理、数据持久化、RBAC、定时任务和热重载。

#### 最小插件结构

```
plugins/
  hello_world/
    __init__.py       # 插件代码
    manifest.toml     # 插件清单
```

`manifest.toml`：

```toml
name = "hello_world"
version = "1.0.0"
description = "Hello World 插件"
author = "you"
main = "__init__"
entry_class = "HelloWorldPlugin"
```

`__init__.py`：

```python
from ncatbot.core.registry import registrar
from ncatbot.event import GroupMessageEvent, PrivateMessageEvent
from ncatbot.plugin import NcatBotPlugin

class HelloWorldPlugin(NcatBotPlugin):
    name = "hello_world"

    async def on_load(self):
        pass  # 插件加载时执行

    async def on_close(self):
        pass  # 插件卸载时执行

    @registrar.on_group_command("hello", ignore_case=True)
    async def on_hello(self, event: GroupMessageEvent):
        await event.reply(text="Hello, World!")

    @registrar.on_private_command("hello", ignore_case=True)
    async def on_private_hello(self, event: PrivateMessageEvent):
        await event.reply(text="你好！")
```

> 插件模式的装饰器与非插件模式**完全相同**，只是方法多了 `self` 参数。

#### 配置与数据持久化

```python
class MyPlugin(NcatBotPlugin):
    async def on_load(self):
        # 配置（config.yaml 自动读写）
        if not self.get_config("prefix"):
            self.set_config("prefix", "/")
        # 数据（data.json 自动持久化）
        self.data.setdefault("counter", 0)

    @registrar.on_group_command("统计")
    async def on_stats(self, event: GroupMessageEvent):
        self.data["counter"] += 1
        await event.reply(text=f"调用次数: {self.data['counter']}")
```

#### 定时任务

```python
class MyPlugin(NcatBotPlugin):
    async def on_load(self):
        self.add_scheduled_task("heartbeat", "30s")           # 每 30 秒
        self.add_scheduled_task("morning", "07:30")            # 每天 07:30
        self.add_scheduled_task("once", 60, max_runs=1)        # 60 秒后执行一次

    async def heartbeat(self):  # 方法名 = 任务名
        print("heartbeat!")
```

#### Hook 机制

Hook 可在 handler 执行前 / 后 / 出错时介入：

```python
from ncatbot.core.registry.hook import Hook, HookAction, HookContext, HookStage, add_hooks

class KeywordFilter(Hook):
    stage = HookStage.BEFORE_CALL
    async def execute(self, ctx: HookContext) -> HookAction:
        if "违禁词" in (ctx.event.data.message.text or ""):
            return HookAction.SKIP     # 拦截，不执行 handler
        return HookAction.CONTINUE

@add_hooks(KeywordFilter())
@registrar.on_group_command("echo")
async def on_echo(self, event: GroupMessageEvent, content: str):
    await event.reply(text=content)
```

#### 多步对话（插件模式）

插件模式通过 `self.wait_event()` 实现多步交互：

```python
@registrar.on_group_command("注册")
async def on_register(self, event: GroupMessageEvent):
    await event.reply(text="请输入名字：")
    try:
        reply = await self.wait_event(
            predicate=lambda e: str(e.data.user_id) == str(event.user_id),
            timeout=30.0,
        )
        name = reply.data.raw_message.strip()
        self.data[str(event.user_id)] = {"name": name}
        await event.reply(text=f"注册成功，{name}！")
    except asyncio.TimeoutError:
        await event.reply(text="超时已取消")
```

---

### 装饰器速查

| 装饰器 | 说明 | 事件类型 |
|--------|------|---------|
| `@registrar.on_command("cmd")` | 匹配命令（群+私聊） | `GroupMessageEvent` / `PrivateMessageEvent` |
| `@registrar.on_group_command("cmd")` | 仅匹配群命令 | `GroupMessageEvent` |
| `@registrar.on_private_command("cmd")` | 仅匹配私聊命令 | `PrivateMessageEvent` |
| `@registrar.on_group_message()` | 监听所有群消息 | `GroupMessageEvent` |
| `@registrar.on_private_message()` | 监听所有私聊消息 | `PrivateMessageEvent` |
| `@registrar.on_message()` | 监听所有消息 | 消息事件 |
| `@registrar.on_group_increase()` | 群成员增加 | `GroupIncreaseEvent` |
| `@registrar.on_group_decrease()` | 群成员减少 | `NoticeEvent` |
| `@registrar.on_poke()` | 戳一戳 | `NoticeEvent` |
| `@registrar.on_friend_request()` | 好友请求 | `FriendRequestEvent` |
| `@registrar.on_group_request()` | 群请求 | `GroupRequestEvent` |
| `@registrar.on("event.type")` | 通用事件注册 | 任意 |

所有装饰器均支持 `priority` 参数（越大越先执行）和 `ignore_case`（命令装饰器）。

> 完整示例见 [examples/](../../examples/) 目录，涵盖 15 个场景。

---

## 指南索引

| 目录 | 说明 | 难度 |
|------|------|------|
| [plugin/](plugin/) | 插件开发完整指南（12 篇） | ⭐ - ⭐⭐⭐ |
| [send_message/](send_message/) | 消息发送指南（6 篇） | ⭐ |
| [api_usage/](api_usage/) | Bot API 使用指南（3 篇） | ⭐⭐ |
| [configuration/](configuration/) | 配置管理指南（2 篇） | ⭐⭐ |
| [cli/](cli/) | CLI 命令行工具指南（2 篇） | ⭐ |
| [rbac/](rbac/) | RBAC 权限管理指南（2 篇） | ⭐⭐⭐ |
| [testing/](testing/) | 插件测试指南（3 篇） | ⭐⭐ |

### plugin/ — 插件开发

从快速入门到高级主题的完整路径：

1. [快速入门](plugin/1.quick-start.md) — 5 分钟跑通第一个插件
2. [插件结构](plugin/2.structure.md) — manifest.toml、目录布局、基类选择
3. [生命周期](plugin/3.lifecycle.md) — 插件加载 / 卸载流程、Mixin 钩子链
4. [事件处理](plugin/4.event-handling.md) — 三种事件消费模式
5. [Mixin 能力体系](plugin/5.mixins.md) — 配置、数据、权限、定时任务
6. [Hook 机制](plugin/6.hooks.md) — 中间件、过滤器、参数绑定
7. [高级主题](plugin/7.advanced.md) — 热重载、依赖管理、多步对话

### send_message/ — 消息发送

- [快速上手](send_message/1_quickstart.md) — 三种发送方式速览
- [消息段参考](send_message/2_segments.md) — 所有消息段类型详解
- [MessageArray](send_message/3_array.md) — 消息容器与链式构造
- [合并转发](send_message/4_forward.md) — ForwardNode / Forward 构造
- [便捷接口](send_message/5_sugar.md) — MessageSugarMixin 速查
- [实战示例](send_message/6_examples.md) — 14 个常见场景

### api_usage/ — Bot API 使用

- [API 概览](api_usage/1_overview.md) — API 分类与调用方式
- [常用接口](api_usage/2_common.md) — 消息发送、群管理、信息查询
- [文件操作](api_usage/3_file.md) — 文件上传与下载

> 另有旧版单文件指南：[api-usage.md](api-usage.md)

### configuration/ — 配置管理

- [全局配置](configuration/1_global.md) — config.yaml 全部字段说明
- [插件配置](configuration/2_plugin.md) — ConfigManager 与安全检查

> 另有旧版单文件指南：[configuration.md](configuration.md)

### cli/ — CLI 命令行工具

- [项目初始化与启动](cli/1_getting_started.md) — init / run / dev / REPL
- [插件与配置管理](cli/2_management.md) — plugin / config / napcat 命令

### rbac/ — 权限管理

- [RBAC 模型](rbac/1_model.md) — 角色权限模型、Trie 权限路径
- [RBACMixin](rbac/2_mixin.md) — 在插件中使用权限控制

> 另有旧版单文件指南：[rbac.md](rbac.md)

---

### testing/ — 插件测试

- [快速入门](testing/1.quick-start.md) — 5 分钟写出第一个插件测试
- [Harness 详解](testing/2.harness.md) — TestHarness 与 PluginTestHarness 深入使用
- [工厂与场景](testing/3.factory-scenario.md) — 事件工厂、Scenario 构建器、自动冒烟

---

## 推荐阅读顺序

| 我想… | 推荐路径 |
|-------|--------|
| **开发一个插件** | plugin/1 → plugin/2 → plugin/4 → api_usage/ |
| **发送各种消息** | send_message/1 → send_message/2 → send_message/6 |
| **了解权限控制** | rbac/1 → rbac/2 |
| **为插件编写测试** | testing/1 → testing/2 → testing/3 |
| **查 API 签名** | → [API 参考](../reference/) |
