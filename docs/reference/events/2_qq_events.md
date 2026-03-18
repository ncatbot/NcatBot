# QQ 事件实体

> QQ 平台（OneBot v11 / NapCat）的事件实体完整参考。

**导入路径：** `from ncatbot.event.qq import GroupMessageEvent, NoticeEvent, RequestEvent, ...`

**源码：** `ncatbot/event/qq/`

---

## 枚举速查

**导入：** `from ncatbot.types.qq import PostType, MessageType, NoticeType, RequestType, MetaEventType`

| 枚举 | 值 |
|------|-----|
| `PostType` | `MESSAGE`, `MESSAGE_SENT`, `NOTICE`, `REQUEST`, `META_EVENT` |
| `MessageType` | `PRIVATE`, `GROUP` |
| `NoticeType` | `GROUP_UPLOAD`, `GROUP_ADMIN`, `GROUP_DECREASE`, `GROUP_INCREASE`, `GROUP_BAN`, `FRIEND_ADD`, `GROUP_RECALL`, `FRIEND_RECALL`, `NOTIFY` |
| `NotifySubType` | `POKE`, `LUCKY_KING`, `HONOR` |
| `RequestType` | `FRIEND`, `GROUP` |
| `MetaEventType` | `LIFECYCLE`, `HEARTBEAT`, `HEARTBEAT_TIMEOUT` |

---

## 消息事件

### MessageEvent

QQ 消息事件基类。**Traits：** `Replyable`, `Deletable`, `HasSender`

| 属性 | 类型 | 说明 |
|------|------|------|
| `message_type` | `MessageType` | 消息类型（`PRIVATE` / `GROUP`） |
| `sub_type` | `str` | 子类型 |
| `message_id` | `str` | 消息 ID |
| `user_id` | `str` | 发送者 ID |
| `message` | `MessageArray` | 消息内容 |
| `raw_message` | `str` | 原始消息字符串 |
| `sender` | `BaseSender` | 发送者信息 |
| `font` | `int` | 字体 |

| 方法 | 签名 | 说明 |
|------|------|------|
| `is_group_msg()` | `() → bool` | 是否群消息 |
| `reply()` | `async (text=, *, at=, image=, video=, rtf=, at_sender=True)` | 回复消息 |
| `delete()` | `async ()` | 撤回消息 |

**`reply()` 行为详情：**
- 自动添加引用回复（`Reply` 段）
- 群消息 + `at_sender=True` 时自动 @发送者
- 群消息发到群，私聊消息发到私聊
- `rtf` 参数接受 `MessageArray`，用于追加复杂消息

```python
@bot.on_message()
async def handle(event: MessageEvent):
    await event.reply(text="收到！")
    await event.reply(image="https://example.com/img.png", at_sender=False)
    await event.reply(rtf=MessageArray().add_text("复杂").add_image("pic.jpg"))
```

### GroupMessageEvent

群消息事件。**额外 Traits：** `GroupScoped`, `Kickable`, `Bannable`

| 属性 | 类型 | 说明 |
|------|------|------|
| `group_id` | `str` | 群号 |
| `anonymous` | `Anonymous?` | 匿名信息 |
| `sender` | `GroupSender` | 群发送者（含 `card`, `role`, `title` 等） |

| 方法 | 签名 | 说明 |
|------|------|------|
| `kick()` | `async (reject_add_request=False)` | 踢出发送者 |
| `ban()` | `async (duration=1800)` | 禁言发送者（秒） |

```python
@bot.on_message()
async def handle(event: GroupMessageEvent):
    await event.ban(duration=60)   # 禁言 60 秒
    await event.kick()             # 踢出
```

### PrivateMessageEvent

私聊消息事件。接口同 `MessageEvent`，无额外属性。

---

## 通知事件

### NoticeEvent

QQ 通知事件基类。**Traits：** `HasSender`, `GroupScoped`

| 属性 | 类型 | 说明 |
|------|------|------|
| `notice_type` | `NoticeType` | 通知类型 |
| `group_id` | `str?` | 群号（非群事件为 None） |
| `user_id` | `str?` | 相关用户 ID |

### GroupIncreaseEvent

群成员增加事件。**额外 Trait：** `Kickable`

| 属性 | 类型 | 说明 |
|------|------|------|
| `sub_type` | `str` | `"approve"` (管理同意) / `"invite"` (被邀请) |
| `operator_id` | `str` | 操作者 ID |

| 方法 | 签名 | 说明 |
|------|------|------|
| `kick()` | `async (reject_add_request=False)` | 踢出新成员 |

### 通知数据模型一览

> 以下通知类型在框架中解析为 `NoticeEvent` 基类实体（尚无专属实体类），通过 `notice_type` 字段区分。

| 数据模型 | notice_type | 额外字段 |
|----------|-------------|----------|
| `GroupUploadNoticeEventData` | `GROUP_UPLOAD` | `file: FileInfo` |
| `GroupAdminNoticeEventData` | `GROUP_ADMIN` | `sub_type` |
| `GroupDecreaseNoticeEventData` | `GROUP_DECREASE` | `sub_type`, `operator_id` |
| `GroupBanNoticeEventData` | `GROUP_BAN` | `sub_type`, `operator_id`, `duration` |
| `FriendAddNoticeEventData` | `FRIEND_ADD` | — |
| `GroupRecallNoticeEventData` | `GROUP_RECALL` | `operator_id`, `message_id` |
| `FriendRecallNoticeEventData` | `FRIEND_RECALL` | `message_id` |
| `PokeNotifyEventData` | `NOTIFY` (poke) | `target_id` |
| `LuckyKingNotifyEventData` | `NOTIFY` (lucky_king) | `target_id` |
| `HonorNotifyEventData` | `NOTIFY` (honor) | `honor_type` |

---

## 请求事件

### RequestEvent

请求事件基类。**Traits：** `HasSender`, `Approvable`

| 属性 | 类型 | 说明 |
|------|------|------|
| `request_type` | `RequestType` | `FRIEND` / `GROUP` |
| `user_id` | `str` | 请求者 ID |
| `comment` | `str?` | 验证信息 |
| `flag` | `str` | 请求标识（用于处理请求） |

| 方法 | 签名 | 说明 |
|------|------|------|
| `approve()` | `async (remark="", reason="")` | 同意请求 |
| `reject()` | `async (reason="")` | 拒绝请求 |

### FriendRequestEvent

好友请求事件。接口同 `RequestEvent`。

### GroupRequestEvent

群请求事件。**额外 Trait：** `GroupScoped`

| 属性 | 类型 | 说明 |
|------|------|------|
| `sub_type` | `str` | `"add"` (主动加群) / `"invite"` (被邀请) |
| `group_id` | `str` | 群号 |

```python
@bot.on_request()
async def handle(event: RequestEvent):
    if event.request_type == RequestType.FRIEND:
        await event.approve(remark="自动通过")
    elif event.request_type == RequestType.GROUP:
        await event.reject(reason="暂不接受")
```

---

## 元事件

### MetaEvent

元事件实体。无额外 Trait。

| 属性 | 类型 | 说明 |
|------|------|------|
| `meta_event_type` | `MetaEventType` | `LIFECYCLE` / `HEARTBEAT` / `HEARTBEAT_TIMEOUT` |

---

## 工厂映射

QQ 工厂 (`create_qq_entity`) 的映射规则：

**精确映射：**

| 数据模型 | → 实体类 |
|----------|----------|
| `PrivateMessageEventData` | `PrivateMessageEvent` |
| `GroupMessageEventData` | `GroupMessageEvent` |
| `FriendRequestEventData` | `FriendRequestEvent` |
| `GroupRequestEventData` | `GroupRequestEvent` |
| `GroupIncreaseNoticeEventData` | `GroupIncreaseEvent` |

**降级映射：**

| post_type | → 降级实体 |
|-----------|-----------|
| `message` / `message_sent` | `MessageEvent` |
| `notice` | `NoticeEvent` |
| `request` | `RequestEvent` |
| `meta_event` | `MetaEvent` |

---

## 继承关系

```
BaseEvent (common)
├── MessageEvent               Replyable, Deletable, HasSender
│   ├── PrivateMessageEvent
│   └── GroupMessageEvent      + GroupScoped, Kickable, Bannable
├── NoticeEvent                HasSender, GroupScoped
│   └── GroupIncreaseEvent     + Kickable
├── RequestEvent               HasSender, Approvable
│   ├── FriendRequestEvent
│   └── GroupRequestEvent      + GroupScoped
└── MetaEvent
```

---

## 交叉引用

- [通用事件基础](1_common.md) — BaseEvent、Mixin Traits
- [Bilibili 事件实体](3_bilibili_events.md) — Bilibili 平台事件
- [QQ 平台消息段](../types/3_qq_segments.md) — QQ 消息段类型
- [QQ 响应类型](../types/4_qq_responses.md) — API 返回值类型
