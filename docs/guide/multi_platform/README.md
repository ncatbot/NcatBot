# 多平台开发指南

> NcatBot 5.2 起支持跨平台运行 — 通过 Adapter/Platform/Trait 三层抽象实现多平台统一开发。

---

## Quick Reference

### 核心三层抽象

| 层 | 说明 |
|----|------|
| **Platform** | 适配器的 `platform` 标识（如 `"qq"`），用于事件路由、API 注入、Handler 过滤 |
| **API Trait** | 跨平台 API 能力协议：`IMessaging`（消息）、`IGroupManage`（群管理）、`IQuery`（查询）、`IFileTransfer`（文件） |
| **事件 Trait** | 事件实体通用能力：`Replyable`、`Deletable`、`GroupScoped`、`Kickable`、`Bannable`、`HasSender`、`Approvable` |

### 多平台 API 访问

| 操作 | 调用方式 |
|------|---------|
| QQ 平台 API | `self.api.qq.messaging.*` / `self.api.qq.manage.*` 等 |
| 按名称访问 | `self.api.platform("telegram").*` |
| 查看已注册平台 | `self.api.platforms` → `Dict[str, IAPIClient]` |

### 平台过滤

所有装饰器支持 `platform` 参数限定事件来源：

| 示例 | 说明 |
|------|------|
| `@registrar.on_group_command("hello", platform="qq")` | 仅 QQ 群命令 |
| `@registrar.on_message(platform="qq")` | 仅 QQ 消息 |
| `@registrar.on_notice()` | 所有平台通知（不设 platform） |

### 跨平台插件编写

使用 Trait 协议检查事件能力：`isinstance(event, Replyable)` → 可调用 `event.reply()`。

---

## 核心概念

### 平台 (Platform)

每个适配器有一个 `platform` 标识符（如 `"qq"`、`"telegram"`），用于：
- 事件路由：`event.platform` 区分事件来源
- API 注入：`HandlerDispatcher` 自动为事件实体注入对应平台的 API
- Handler 过滤：`@bot.on("message", platform="qq")` 仅接收 QQ 消息

### Trait 协议

跨平台 API 按功能拆分为 Trait 协议（`api/traits/`）：

| Trait | 功能 |
|---|---|
| `IMessaging` | 发送/撤回消息、转发 |
| `IGroupManage` | 群管理（踢人、禁言、设管理） |
| `IQuery` | 信息查询（好友列表、群信息） |
| `IFileTransfer` | 文件上传/下载 |

事件实体也有 Trait 协议（`event/traits.py`）：

| Trait | 功能 |
|---|---|
| `Replyable` | 可回复（`reply()`, `send()`） |
| `Deletable` | 可撤回（`delete()`） |
| `HasSender` | 有发送者信息 |
| `GroupScoped` | 群相关（有 `group_id`） |
| `Kickable` | 可踢出群成员 |
| `Bannable` | 可禁言 |

### 多平台运行

单个 `BotClient` 可同时运行多个适配器，共享插件和服务：

```python
from ncatbot.app import BotClient
from ncatbot.adapter import NapCatAdapter

bot = BotClient(adapters=[
    NapCatAdapter(),           # platform="qq"
    # TelegramAdapter(),       # platform="telegram" (未来)
])
bot.run()
```

---

## 单平台用法（默认）

对于只使用 QQ 的场景，用法与 5.0 完全相同：

```python
from ncatbot.app import BotClient

bot = BotClient()  # 默认 NapCatAdapter

@bot.on("message.group")
async def on_msg(event):
    await event.reply("hello")

bot.run()
```

---

## 多平台 API 访问

`plugin.api`（`BotAPIClient`）是多平台门面，提供三种访问方式：

```python
# 方式 1: 直接属性访问（推荐，有类型提示）
await self.api.qq.messaging.send_group_msg(group_id, message)
await self.api.bilibili.send_danmu(room_id, text)

# 方式 2: 动态平台访问（按名称获取）
client = self.api.platform("qq")        # → IQQAPIClient
await client.messaging.send_group_msg(group_id, message)

# 方式 3: 查看已注册的平台
print(self.api.platforms)  # {"qq": <IQQAPIClient>, "bilibili": <IBiliAPIClient>, ...}
```

**选择建议**：

| 方式 | 适用场景 |
|------|---------|
| `api.qq.*` / `api.bilibili.*` | 平台确定、需要 IDE 自动补全 |
| `api.platform(name)` | 平台名来自变量或运行时动态决定 |
| `api.platforms` | 遍历/列出所有已注册平台 |

---

## 平台过滤

通过 `platform` 参数限定 handler 只接收特定平台的事件：

```python
@bot.on("message.group", platform="qq")
async def qq_only(event):
    """仅处理 QQ 群消息"""
    await event.reply("QQ!")

@bot.on("message")
async def all_platforms(event):
    """处理所有平台的消息"""
    print(f"来自 {event.platform} 的消息")
```

所有便捷装饰器都支持 `platform` 参数：

```python
@bot.on_group_message(platform="qq")
@bot.on_command("/help", platform="qq")
@bot.on_notice(platform="qq")
```

---

## 编写跨平台插件

使用 Trait 协议编写跨平台逻辑：

```python
from ncatbot.event import Replyable, GroupScoped

@bot.on("message")
async def cross_platform(event):
    if isinstance(event, Replyable):
        await event.reply("hello from any platform!")

    if isinstance(event, GroupScoped):
        print(f"群 {event.group_id} 的消息")
```

---

## 参考

- [架构文档](../../architecture.md) — 整体设计
- [ADR-005: 多平台架构](../../contributing/design_decisions/1_architecture.md#adr-005多平台架构--组合优于继承) — 设计决策
- [ADR-006: 多适配器运行时](../../contributing/design_decisions/1_architecture.md#adr-006多适配器运行时) — 运行时设计
