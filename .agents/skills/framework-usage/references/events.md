# 事件系统参考

> 参考文档：`guide/3. 插件开发/4. 事件注册.md`、`reference/4. 核心模块/1. 内部实现.md`

## 装饰器注册（最常用）

```python
from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent
```

### 跨平台装饰器

| 装饰器 | 匹配事件 |
|--------|--------|
| `@registrar.on(event_type, priority=0)` | 任意事件 |
| `@registrar.on_message()` | 所有消息 |
| `@registrar.on_group_message()` | 群消息 |
| `@registrar.on_private_message()` | 私聊消息 |
| `@registrar.on_message_sent()` | Bot 发出的消息 |
| `@registrar.on_command(*names)` | 命令（群+私聊） |
| `@registrar.on_group_command(*names)` | 群命令 |
| `@registrar.on_private_command(*names)` | 私聊命令 |
| `@registrar.on_notice()` | 所有通知 |
| `@registrar.on_request()` | 所有请求 |
| `@registrar.on_meta()` | 元事件 |

### QQ 平台装饰器 (`registrar.qq`)

| 装饰器 | 匹配事件 |
|--------|--------|
| `@registrar.qq.on_group_increase()` | 群成员增加 |
| `@registrar.qq.on_group_decrease()` | 群成员减少 |
| `@registrar.qq.on_group_recall()` | 群消息撤回 |
| `@registrar.qq.on_group_admin()` | 群管理员变动 |
| `@registrar.qq.on_group_ban()` | 群禁言 |
| `@registrar.qq.on_poke()` | 戳一戳 |
| `@registrar.qq.on_friend_request()` | 好友请求 |
| `@registrar.qq.on_group_request()` | 群请求 |
| `@registrar.qq.on_friend_add()` | 好友已添加 |

### Bilibili 平台装饰器 (`registrar.bilibili`)

| 装饰器 | 匹配事件 |
|--------|--------|
| `@registrar.bilibili.on_live()` | 所有直播间事件 |
| `@registrar.bilibili.on_danmu()` | 弹幕消息 |
| `@registrar.bilibili.on_superchat()` | 醒目留言 (SC) |
| `@registrar.bilibili.on_gift()` | 礼物 |
| `@registrar.bilibili.on_guard_buy()` | 大航海 |
| `@registrar.bilibili.on_interact()` | 互动（进入/关注/分享） |
| `@registrar.bilibili.on_like()` | 点赞 |
| `@registrar.bilibili.on_comment()` | 评论 |

### GitHub 平台装饰器 (`registrar.github`)

| 装饰器 | 匹配事件 |
|--------|--------|
| `@registrar.github.on_push()` | Push |
| `@registrar.github.on_issue()` | Issue |
| `@registrar.github.on_pr()` | Pull Request |
| `@registrar.github.on_star()` | Star |
| `@registrar.github.on_fork()` | Fork |
| `@registrar.github.on_release()` | Release |
| `@registrar.github.on_comment()` | Comment |

所有装饰器均支持 `platform` 参数，用于限定只接收特定平台的事件：

```python
@registrar.on_group_message(platform="qq")  # 仅 QQ 平台
@registrar.on_message()                     # 所有平台
```

## 事件流（EventStream）

适用于后台持续监听事件。

```python
import asyncio

async def on_load(self):
    self._task = asyncio.create_task(self._monitor())

async def on_close(self):
    if self._task:
        self._task.cancel()

async def _monitor(self):
    async with self.events("message.group") as stream:
        async for event in stream:
            if "敏感词" in event.data.message.text:
                await self.api.qq.messaging.delete_msg(event.data.message_id)
```

**events() 参数**：
- `None` — 接收全部事件
- `"message"` — 前缀匹配 `"message"` 及所有子类型
- `"message.group"` — 精确匹配

## 一次性等待（wait_event）

适用于多步对话。

```python
from ncatbot.core import from_event, msg_equals

@registrar.on_group_command("confirm")
async def on_confirm(self, event: GroupMessageEvent):
    await event.reply("请输入确认密码：")
    try:
        reply = await self.wait_event(
            predicate=from_event(event) * msg_equals("yes"),
            timeout=30.0,
        )
        await event.reply("已确认")
    except asyncio.TimeoutError:
        await event.reply("超时，已取消")
```

### Predicate DSL

`ncatbot.core` 提供可组合的 Predicate DSL，用运算符替代冗长的 lambda。

**运算符**

| 运算符 | 含义 |
|--------|------|
| `p1 * p2` 或 `p1 & p2` | AND |
| `p1 + p2` 或 `p1 \| p2` | OR |
| `~p` | NOT |

**工厂函数**

| 函数 | 说明 |
|------|------|
| `from_event(event)` | 核心语法糖：自动推导同 session（同 user + 群消息同群 / 私聊同私聊） |
| `same_user(uid)` | 匹配 user_id |
| `same_group(gid)` | 匹配 group_id |
| `is_group()` / `is_private()` / `is_message()` | 匹配事件类型 |
| `msg_equals(text)` | raw_message.strip() 完全匹配 |
| `msg_in(*options)` | raw_message.strip() 匹配选项之一 |
| `has_keyword(*words)` | raw_message 含任一关键词 |
| `msg_matches(pattern)` | raw_message 正则匹配 |
| `event_type(prefix)` | event.type 前缀匹配 |
| `P.of(lambda)` | 将普通 callable 升级为可组合的 P |

**组合示例**

```python
from ncatbot.core import from_event, msg_in, has_keyword, same_user, P

# 等“确认”或“取消”
pred = from_event(event) * msg_in("确认", "取消")

# 含关键词
pred = from_event(event) * has_keyword("帮助", "help")

# 排除某用户
pred = from_event(event) * ~same_user(bot_id)

# 混用 lambda
pred = from_event(event) * P.of(lambda e: int(e.data.raw_message) > 0)
```

## 事件类型字符串完整列表

| 事件类型 | 说明 | 数据类 |
|---------|------|--------|
| `"message.private"` | 私聊消息 | `PrivateMessageEventData` |
| `"message.group"` | 群消息 | `GroupMessageEventData` |
| `"message_sent.private"` | 私聊已发送 | — |
| `"message_sent.group"` | 群消息已发送 | — |
| `"notice.group_upload"` | 群文件上传 | `GroupUploadNoticeEventData` |
| `"notice.group_admin"` | 群管理员变更 | `GroupAdminNoticeEventData` |
| `"notice.group_decrease"` | 群成员减少 | `GroupDecreaseNoticeEventData` |
| `"notice.group_increase"` | 群成员增加 | `GroupIncreaseNoticeEventData` |
| `"notice.group_ban"` | 群禁言 | `GroupBanNoticeEventData` |
| `"notice.friend_add"` | 好友已添加 | `FriendAddNoticeEventData` |
| `"notice.group_recall"` | 群消息撤回 | `GroupRecallNoticeEventData` |
| `"notice.friend_recall"` | 好友消息撤回 | `FriendRecallNoticeEventData` |
| `"notice.poke"` | 戳一戳 | `PokeNotifyEventData` |
| `"notice.lucky_king"` | 幸运王 | `LuckyKingNotifyEventData` |
| `"notice.honor"` | 群荣誉 | `HonorNotifyEventData` |
| `"request.friend"` | 好友请求 | `FriendRequestEventData` |
| `"request.group"` | 群请求 | `GroupRequestEventData` |
| `"meta_event.lifecycle"` | 生命周期 | `LifecycleMetaEventData` |
| `"meta_event.heartbeat"` | 心跳 | `HeartbeatMetaEventData` |
| `"meta_event.heartbeat_timeout"` | 心跳超时 | `HeartbeatTimeoutMetaEventData` |

## 前缀匹配规则

```json
"message"        → 匹配 "message" + "message.group" + "message.private"
"notice"         → 匹配 "notice" + "notice.group_increase" + ...
"notice.group"   → 匹配 "notice.group_increase" + "notice.group_decrease" + ...
```

## 事件实体层

### QQ 事件实体

| 实体类 | 便捷方法 |
|--------|---------|
| `MessageEvent` | `reply()`, `delete()`, `is_group_msg()` |
| `PrivateMessageEvent` | 继承 MessageEvent |
| `GroupMessageEvent` | `reply()`, `delete()`, `kick()`, `ban()` |
| `NoticeEvent` | — |
| `GroupIncreaseEvent` | `kick()` |
| `RequestEvent` | `approve()`, `reject()` |
| `FriendRequestEvent` | `approve()`, `reject()` |
| `GroupRequestEvent` | `approve()`, `reject()` |

### GitHub 事件实体

```python
from ncatbot.event.github import (
    GitHubIssueEvent, GitHubIssueCommentEvent,
    GitHubPREvent, GitHubPRReviewCommentEvent,
    GitHubPushEvent, GitHubStarEvent, GitHubForkEvent, GitHubReleaseEvent,
)
```

| 实体类 | Traits | 便捷方法 | 关键属性 |
|--------|--------|---------|---------|
| `GitHubIssueEvent` | HasSender, Replyable | `reply()` | `issue_number`, `issue_title`, `action`, `labels`, `repo` |
| `GitHubIssueCommentEvent` | HasSender, Replyable, Deletable | `reply()`, `delete()` | `comment_body`, `issue_number`, `repo` |
| `GitHubPREvent` | HasSender, Replyable | `reply()` | `pr_number`, `pr_title`, `action`, `merged`, `repo` |
| `GitHubPRReviewCommentEvent` | HasSender, Replyable, Deletable | `reply()`, `delete()` | `comment_body`, `pr_number`, `path`, `repo` |
| `GitHubPushEvent` | HasSender | — | `ref`, `before`, `after`, `commits`, `head_commit`, `repo` |
| `GitHubStarEvent` | HasSender | — | `repo`, `starred_at` |
| `GitHubForkEvent` | HasSender | — | `repo`, `forkee`, `forkee_full_name` |
| `GitHubReleaseEvent` | HasSender | — | `release_tag`, `release_name`, `release_body`, `prerelease`, `repo` |

### Trait 协议（5.2 新增）

跨平台事件处理使用 `ncatbot.event.common.mixins` 中的 `runtime_checkable` 协议（通过 `ncatbot.event` 重新导出）：

| Trait | 方法 |
|---|---|
| `Replyable` | `reply()`, `send()` |
| `Deletable` | `delete()` |
| `HasSender` | `sender` 属性 |
| `GroupScoped` | `group_id` 属性 |
| `Kickable` | `kick()` |
| `Bannable` | `ban()` |

```python
from ncatbot.event import Replyable

@bot.on("message")
async def handler(event):
    if isinstance(event, Replyable):
        await event.reply("收到!")
```

**属性代理**（`__getattr__` 透传到 data）：

```python
event.user_id        # → event.data.user_id
event.group_id       # → event.data.group_id
event.message        # → event.data.message (MessageArray)
event.message_id     # → event.data.message_id
event.sender         # → event.data.sender
```

## 多步对话模板

```python
from ncatbot.core import from_event, msg_in

@registrar.on_group_command("order")
async def order_flow(self, event: GroupMessageEvent):
    await event.reply("请选择: 1. 咖啡 2. 茶")
    try:
        choice_event = await self.wait_event(predicate=from_event(event), timeout=30.0)
        choice = choice_event.data.raw_message.strip()
        if choice not in ("1", "2"):
            await event.reply("无效选择，已取消")
            return
        item = "咖啡" if choice == "1" else "茶"

        await event.reply(f"确认点 {item} 吗？回复 yes/no")
        confirm_event = await self.wait_event(
            predicate=from_event(event) * msg_in("yes", "no"),
            timeout=30.0,
        )
        if confirm_event.data.raw_message.strip().lower() == "yes":
            await event.reply(f"已下单: {item}")
        else:
            await event.reply("已取消")
    except asyncio.TimeoutError:
        await event.reply("超时，已取消")
```

## 非阻塞启动 + 事件编排

`BotClient.run_async()` 完成 startup 后立即返回，`bot.api` / `bot.dispatcher` 可用于自定义的事件驱动工作流。

### 基础模板

```python
import asyncio
from ncatbot.app import BotClient

bot = BotClient()

async def main():
    await bot.run_async()  # 非阻塞，立即返回

    # 等待心跳确认连接就绪
    await bot.dispatcher.wait_event(
        predicate=lambda e: e.type == "meta_event.heartbeat",
        timeout=30.0,
    )
    print("Bot 连接就绪")

    # 持续消费事件流
    async with bot.dispatcher.events("message.group") as stream:
        async for event in stream:
            print(f"群消息: {event.data.raw_message}")

if __name__ == "__main__":
    asyncio.run(main())
```

### `run()` vs `run_async()`

| 维度 | `run()` | `run_async()` |
|------|---------|---------------|
| 阻塞性 | 同步阻塞 | 异步返回 |
| 调用 | `bot.run()` | `await bot.run_async()` |
| 适用 | 简单 Bot | 自定义编排、与异步服务集成 |
| dispatcher | handler 内可用 | 返回后立即可用 |

### 并发 wait_event

```python
# 同时等待多个条件，先到先得
tasks = [
    asyncio.create_task(bot.dispatcher.wait_event(
        predicate=lambda e: e.type == "notice.group_increase", timeout=60
    )),
    asyncio.create_task(bot.dispatcher.wait_event(
        predicate=lambda e: e.type == "request.friend", timeout=60
    )),
]
done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
for t in pending:
    t.cancel()
```

### 常用生命周期事件

| 事件类型 | 用途 |
|---------|------|
| `meta_event.heartbeat` | 确认连接就绪 |
| `meta_event.heartbeat_timeout` | 断线检测 |
| `meta_event.lifecycle` | 监控连接状态 |

> 完整模式（插件并发编排、工作流清理）→ `guide/3. 插件开发/10. 模式.md` § 事件驱动工作流编排
