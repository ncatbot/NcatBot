# 事件参考

> 事件体系完整参考。NcatBot 的事件系统采用 **数据模型 + 实体** 双层设计，插件只需操作事件实体即可。

---

## Quick Start

三种核心事件类型的注册示例：

### 消息事件

```python
from ncatbot.event import GroupMessageEvent, PrivateMessageEvent

# 群消息
async def on_group_message(event: GroupMessageEvent):
    print(event.group_id, event.raw_message)
    await event.reply("收到！")

# 私聊消息
async def on_private_message(event: PrivateMessageEvent):
    await event.reply("你好！")
```

### 通知事件

```python
from ncatbot.event import NoticeEvent, GroupIncreaseEvent

# 通用通知
async def on_notice(event: NoticeEvent):
    print(f"通知类型: {event.notice_type}")

# 群成员增加
async def on_group_increase(event: GroupIncreaseEvent):
    await event.kick(reject_add_request=True)  # 踢出并拒绝
```

### 请求事件

```python
from ncatbot.event import FriendRequestEvent, GroupRequestEvent

# 好友请求
async def on_friend_request(event: FriendRequestEvent):
    await event.approve(remark="自动通过")

# 加群请求
async def on_group_request(event: GroupRequestEvent):
    await event.reject(reason="暂不接受")
```

---

## 事件类型速查表

### 按 post_type 分类

| `post_type` | 说明 | 基类实体 |
|---|---|---|
| `message` | 收到消息 | `MessageEvent` |
| `message_sent` | Bot 自身发出的消息 | `MessageEvent` |
| `notice` | 通知（群变动、好友变动等） | `NoticeEvent` |
| `request` | 好友/加群请求 | `RequestEvent` |
| `meta_event` | 元事件（心跳、生命周期） | `MetaEvent` |

### 消息事件 (MessageEvent)

| `message_type` | 实体类 | 数据模型 | 说明 |
|---|---|---|---|
| `private` | `PrivateMessageEvent` | `PrivateMessageEventData` | 私聊消息 |
| `group` | `GroupMessageEvent` | `GroupMessageEventData` | 群消息 |

### 通知事件 (NoticeEvent)

| `notice_type` | 实体类 | 数据模型 | 说明 |
|---|---|---|---|
| `group_upload` | `NoticeEvent` | `GroupUploadNoticeEventData` | 群文件上传 |
| `group_admin` | `NoticeEvent` | `GroupAdminNoticeEventData` | 群管理员变动 |
| `group_decrease` | `NoticeEvent` | `GroupDecreaseNoticeEventData` | 群成员减少 |
| `group_increase` | `GroupIncreaseEvent` | `GroupIncreaseNoticeEventData` | 群成员增加 |
| `group_ban` | `NoticeEvent` | `GroupBanNoticeEventData` | 群禁言 |
| `friend_add` | `NoticeEvent` | `FriendAddNoticeEventData` | 好友添加 |
| `group_recall` | `NoticeEvent` | `GroupRecallNoticeEventData` | 群消息撤回 |
| `friend_recall` | `NoticeEvent` | `FriendRecallNoticeEventData` | 好友消息撤回 |
| `notify`（poke） | `NoticeEvent` | `PokeNotifyEventData` | 戳一戳 |
| `notify`（lucky_king） | `NoticeEvent` | `LuckyKingNotifyEventData` | 运气王 |
| `notify`（honor） | `NoticeEvent` | `HonorNotifyEventData` | 群荣誉 |

### 请求事件 (RequestEvent)

| `request_type` | 实体类 | 数据模型 | 说明 |
|---|---|---|---|
| `friend` | `FriendRequestEvent` | `FriendRequestEventData` | 好友请求 |
| `group` | `GroupRequestEvent` | `GroupRequestEventData` | 加群请求/邀请 |

### 元事件 (MetaEvent)

| `meta_event_type` | 实体类 | 数据模型 | 说明 |
|---|---|---|---|
| `lifecycle` | `MetaEvent` | `LifecycleMetaEventData` | 生命周期 |
| `heartbeat` | `MetaEvent` | `HeartbeatMetaEventData` | 心跳 |
| `heartbeat_timeout` | `MetaEvent` | `HeartbeatTimeoutMetaEventData` | 心跳超时 |

---

## 事件字段速查

### BaseEvent 公共字段

所有事件实体均继承自 `BaseEvent`，包含以下公共字段：

| 属性 | 类型 | 说明 |
|---|---|---|
| `data` | `BaseEventData` | 底层纯数据模型（可序列化） |
| `api` | `IBotAPI` | Bot API 接口，可用于直接调用任意 API |
| `time` | `int` | 事件发生时间戳（Unix） |
| `self_id` | `str` | 收到事件的机器人 QQ 号 |
| `post_type` | `PostType` | 事件上报类型 |

> **说明**：`BaseEventData` 的 Pydantic 配置为 `extra="allow"`，因此上游传递的非标准字段也会保留在 `data` 中，可通过 `event.data.field_name` 访问。

### MessageEvent 字段

| 属性 | 类型 | 说明 |
|---|---|---|
| `message_type` | `MessageType` | 消息类型（`"private"` / `"group"`） |
| `sub_type` | `str` | 消息子类型（`"friend"` / `"normal"` / `"anonymous"`） |
| `message_id` | `str` | 消息 ID |
| `user_id` | `str` | 发送者 QQ 号 |
| `message` | `MessageArray` | 消息内容（消息段数组） |
| `raw_message` | `str` | CQ 码原始消息字符串 |
| `sender` | `BaseSender` | 发送者信息 |
| `font` | `int` | 字体（默认 `0`） |

**GroupMessageEvent 附加字段**：`group_id`、`anonymous`（`Anonymous | None`）、`sender`（`GroupSender`）

### NoticeEvent 字段

| 属性 | 类型 | 说明 |
|---|---|---|
| `notice_type` | `NoticeType` | 通知类型 |
| `group_id` | `str \| None` | 群号（部分通知无此字段） |
| `user_id` | `str \| None` | 相关用户 QQ 号 |

**各 notice_type 附加字段**：

| `notice_type` | 附加字段 |
|---|---|
| `group_upload` | `file: FileInfo` |
| `group_admin` | `sub_type: str` |
| `group_decrease` | `sub_type`, `operator_id` |
| `group_increase` | `sub_type`, `operator_id` |
| `group_ban` | `sub_type`, `operator_id`, `duration` |
| `friend_add` | — |
| `group_recall` | `operator_id`, `message_id` |
| `friend_recall` | `message_id` |
| `notify`（poke） | `target_id` |
| `notify`（lucky_king） | `target_id` |
| `notify`（honor） | `honor_type` |

### RequestEvent 字段

| 属性 | 类型 | 说明 |
|---|---|---|
| `request_type` | `RequestType` | 请求类型（`"friend"` / `"group"`） |
| `user_id` | `str` | 请求发送者 QQ 号 |
| `comment` | `str \| None` | 验证消息 |
| `flag` | `str` | 请求标识，用于处理请求时传入 |

**GroupRequestEvent 附加字段**：`sub_type`（`"add"` / `"invite"`）、`group_id`

### MetaEvent 字段

| 属性 | 类型 | 说明 |
|---|---|---|
| `meta_event_type` | `MetaEventType` | 元事件类型 |

**附加字段**：

| `meta_event_type` | 附加字段 |
|---|---|
| `lifecycle` | `sub_type: str` |
| `heartbeat` | `status: Status`, `interval: int` |
| `heartbeat_timeout` | `last_heartbeat_time: int`, `timeout_seconds: int` |

---

## 枚举类型速查

所有枚举定义于 `ncatbot.types.enums`，均继承自 `str, Enum`，可直接与字符串比较。

| 枚举 | 成员 |
|---|---|
| `PostType` | `MESSAGE`=`"message"`, `MESSAGE_SENT`=`"message_sent"`, `NOTICE`=`"notice"`, `REQUEST`=`"request"`, `META_EVENT`=`"meta_event"` |
| `MessageType` | `PRIVATE`=`"private"`, `GROUP`=`"group"` |
| `NoticeType` | `GROUP_UPLOAD`, `GROUP_ADMIN`, `GROUP_DECREASE`, `GROUP_INCREASE`, `GROUP_BAN`, `FRIEND_ADD`, `GROUP_RECALL`, `FRIEND_RECALL`, `NOTIFY` |
| `RequestType` | `FRIEND`=`"friend"`, `GROUP`=`"group"` |
| `MetaEventType` | `LIFECYCLE`=`"lifecycle"`, `HEARTBEAT`=`"heartbeat"`, `HEARTBEAT_TIMEOUT`=`"heartbeat_timeout"` |

---

## 深入阅读

| 文档 | 内容 |
|---|---|
| [事件类详解](1_event_classes.md) | 事件类继承体系、每个事件类的完整属性/方法表、`create_entity()` 工厂函数、类型判断方法 |
