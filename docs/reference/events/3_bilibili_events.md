# Bilibili 事件实体

> Bilibili 平台的事件实体完整参考。覆盖直播间、私信、评论三大场景。

**导入路径：** `from ncatbot.event.bilibili import DanmuMsgEvent, BiliPrivateMessageEvent, ...`

**源码：** `ncatbot/event/bilibili/`

---

## 直播间事件

所有直播间事件继承自 `BiliLiveEvent`，自带 `GroupScoped` trait（`group_id` 返回 `room_id`）。

### BiliLiveEvent

直播间事件基类。**Trait：** `GroupScoped`

| 属性 | 类型 | 说明 |
|------|------|------|
| `group_id` | `str` | 直播间 ID (`room_id`) |
| `api` | `IBiliAPIClient` | Bilibili API 客户端 |

### DanmuMsgEvent

弹幕消息事件。**Traits：** `Replyable`, `HasSender`, `Bannable`, `GroupScoped`

| 属性 | 类型 | 说明 |
|------|------|------|
| `user_id` | `str` | 发送者 UID |
| `sender` | `BiliSender` | 发送者信息 |

| 方法 | 签名 | 说明 |
|------|------|------|
| `reply()` | `async (text: str)` | 发送弹幕到直播间 |
| `ban()` | `async (duration=1)` | 禁言用户（小时） |

```python
@bot.on_event(DanmuMsgEvent)
async def handle(event: DanmuMsgEvent):
    await event.reply("已收到弹幕")
    # await event.ban(duration=1)  # 禁言 1 小时
```

> **注意：** `ban()` 的 `duration` 单位是**小时**（QQ 平台是秒）。

### SuperChatEvent

醒目留言 (SC) 事件。**Traits：** `HasSender`, `GroupScoped`

| 属性 | 类型 | 说明 |
|------|------|------|
| `user_id` | `str` | 发送者 UID |
| `sender` | `BiliSender` | 发送者信息 |

数据层额外字段（通过 `event.data` 访问）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `content` | `str` | SC 内容 |
| `price` | `int` | 金额 |
| `duration` | `int` | 持续时间 (秒) |

### GiftEvent

礼物事件。**Traits：** `HasSender`, `GroupScoped`

| 属性 | 类型 | 说明 |
|------|------|------|
| `user_id` | `str` | 发送者 UID |
| `sender` | `BiliSender` | 发送者信息 |

数据层额外字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `gift_name` | `str` | 礼物名称 |
| `gift_id` | `str` | 礼物 ID |
| `num` | `int` | 数量 |
| `price` | `int` | 价格 |
| `coin_type` | `str` | 币种（`"gold"` / `"silver"`） |

### GuardBuyEvent

大航海购买事件。**Traits：** `HasSender`, `GroupScoped`

| 属性 | 类型 | 说明 |
|------|------|------|
| `user_id` | `str` | 购买者 UID |
| `sender` | `BiliSender` | 购买者信息 |

数据层额外字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `guard_level` | `int` | 等级（`1`=总督, `2`=提督, `3`=舰长） |
| `price` | `int` | 价格 |

### InteractEvent

互动事件（进入直播间 / 关注 / 分享）。**Traits：** `HasSender`, `GroupScoped`

| 属性 | 类型 | 说明 |
|------|------|------|
| `user_id` | `str` | 用户 UID |
| `sender` | `BiliSender` | 用户信息 |

数据层额外字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `interact_type` | `int` | 互动类型 |

### LikeEvent

点赞事件。**Traits：** `HasSender`, `GroupScoped`

| 属性 | 类型 | 说明 |
|------|------|------|
| `user_id` | `str` | 用户 UID |
| `sender` | `BiliSender` | 用户信息 |

数据层额外字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `like_count` | `int` | 点赞数 |

### LiveNoticeEvent

直播间通知事件（兜底）。**Trait：** `GroupScoped`

用于没有专属实体类的直播间通知。通过 `event.data` 访问具体字段。以下数据模型均降级为 `BiliLiveEvent`：

#### WatchedChangeEventData

观看人数变化。`live_event_type = "WATCHED_CHANGE"`

| 字段 | 类型 | 说明 |
|------|------|------|
| `num` | `int` | 观看人数 |
| `text_small` | `str` | 简短文本（如 `"2.3万"`） |
| `text_large` | `str` | 完整文本（如 `"2.3万人看过"`） |

#### LikeUpdateEventData

点赞数更新（全局累计）。`live_event_type = "LIKE_INFO_V3_UPDATE"`

| 字段 | 类型 | 说明 |
|------|------|------|
| `click_count` | `int` | 累计点赞数 |

#### OnlineRankCountEventData

在线排名人数。`live_event_type = "ONLINE_RANK_COUNT"`

| 字段 | 类型 | 说明 |
|------|------|------|
| `count` | `int` | 在线人数 |

#### OnlineRankV3EventData

在线排名列表。`live_event_type = "ONLINE_RANK_V3"`

| 字段 | 类型 | 说明 |
|------|------|------|
| `online_list` | `list` | 排名列表（uid、score、uname 等） |

#### DanmuAggregationEventData

弹幕聚合（节日/活动弹幕）。`live_event_type = "DANMU_AGGREGATION"`

| 字段 | 类型 | 说明 |
|------|------|------|
| `activity_identity` | `str` | 活动 ID |
| `msg` | `str` | 聚合弹幕内容 |
| `aggregation_num` | `int` | 参与人数 |

#### DmInteractionEventData

互动消息（分享直播间等）。`live_event_type = "DM_INTERACTION"`

| 字段 | 类型 | 说明 |
|------|------|------|
| `interaction_type` | `int` | 互动类型 |
| `suffix_text` | `str` | 描述文本 |

#### EntryEffectEventData

进场特效。`live_event_type = "ENTRY_EFFECT"`

| 字段 | 类型 | 说明 |
|------|------|------|
| `user_id` | `str` | 进场用户 UID |
| `user_name` | `str` | 用户名 |
| `sender` | `BiliSender` | 发送者信息 |

```python
@registrar.on("live", platform="bilibili")
async def on_notice(event):
    from ncatbot.types.bilibili.events import WatchedChangeEventData
    if isinstance(event.data, WatchedChangeEventData):
        print(f"观看人数: {event.data.text_large}")
```

> **静默忽略的事件：** `STOP_LIVE_ROOM_LIST`（停播房间列表推送，无业务价值）。

---

## 私信事件

### BiliPrivateMessageEvent

B 站私信消息事件。**Traits：** `Replyable`, `HasSender`

| 属性 | 类型 | 说明 |
|------|------|------|
| `user_id` | `str` | 发送者 UID |
| `sender` | `BiliSender` | 发送者信息 |

| 方法 | 签名 | 说明 |
|------|------|------|
| `reply()` | `async (text: str)` | 回复私信 |

数据层额外字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `message` | `MessageArray` | 消息内容 |
| `msg_type` | `str` | 消息类型 |
| `msg_key` | `str` | 消息 key |
| `receiver_id` | `str` | 接收者 ID |

```python
@bot.on_event(BiliPrivateMessageEvent)
async def handle(event: BiliPrivateMessageEvent):
    await event.reply("收到你的私信")
```

### BiliPrivateMessageWithdrawEvent

B 站私信撤回事件。无额外 Trait。

数据层字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `user_id` | `str` | 撤回者 UID |
| `msg_key` | `str` | 被撤回消息的 key |

---

## 评论事件

### BiliCommentEvent

B 站评论事件。**Traits：** `Replyable`, `HasSender`, `Deletable`

| 属性 | 类型 | 说明 |
|------|------|------|
| `user_id` | `str` | 评论者 UID |
| `sender` | `BiliSender` | 评论者信息 |

| 方法 | 签名 | 说明 |
|------|------|------|
| `reply()` | `async (text: str)` | 回复评论 |
| `delete()` | `async ()` | 删除评论 |

数据层额外字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `resource_id` | `str` | 资源 ID |
| `resource_type` | `str` | 资源类型 |
| `comment_id` | `str` | 评论 ID |
| `content` | `str` | 评论内容 |
| `root_id` | `str` | 根评论 ID |
| `parent_id` | `str` | 父评论 ID |
| `like_count` | `int` | 点赞数 |

```python
@bot.on_event(BiliCommentEvent)
async def handle(event: BiliCommentEvent):
    await event.reply("感谢评论")
    # await event.delete()  # 删除评论
```

---

## 工厂映射

Bilibili 工厂 (`create_bili_entity`) 的映射规则：

**精确映射：**

| 数据模型 | → 实体类 |
|----------|----------|
| `DanmuMsgEventData` | `DanmuMsgEvent` |
| `SuperChatEventData` | `SuperChatEvent` |
| `GiftEventData` | `GiftEvent` |
| `GuardBuyEventData` | `GuardBuyEvent` |
| `InteractEventData` | `InteractEvent` |
| `LikeEventData` | `LikeEvent` |
| `BiliPrivateMessageEventData` | `BiliPrivateMessageEvent` |
| `BiliPrivateMessageWithdrawEventData` | `BiliPrivateMessageWithdrawEvent` |
| `BiliCommentEventData` | `BiliCommentEvent` |

**降级映射：**

| post_type | → 降级实体 |
|-----------|-----------|
| `live` | `BiliLiveEvent` |
| `message` | `BaseEvent` |
| `comment` | `BaseEvent` |
| `system` | `BaseEvent` |

---

## 继承关系

```
BaseEvent (common)
├── BiliLiveEvent                    GroupScoped
│   ├── DanmuMsgEvent                + Replyable, HasSender, Bannable
│   ├── SuperChatEvent               + HasSender
│   ├── GiftEvent                    + HasSender
│   ├── GuardBuyEvent                + HasSender
│   ├── InteractEvent                + HasSender
│   ├── LikeEvent                    + HasSender
│   └── LiveNoticeEvent              (无额外 trait)
├── BiliPrivateMessageEvent          Replyable, HasSender
├── BiliPrivateMessageWithdrawEvent  (无 trait)
└── BiliCommentEvent                 Replyable, HasSender, Deletable
```

---

## 交叉引用

- [通用事件基础](1_common.md) — BaseEvent、Mixin Traits
- [QQ 事件实体](2_qq_events.md) — QQ 平台事件
- [Bilibili 平台类型](../types/5_bilibili_types.md) — BiliSender、枚举、数据模型
