# Bilibili 平台类型

> Bilibili 平台专属的类型定义：发送者、枚举。

**导入路径：** `from ncatbot.types.bilibili import BiliSender, BiliPostType, BiliLiveEventType, ...`

**源码：** `ncatbot/types/bilibili/`

> **注意：** Bilibili 平台没有专属消息段类型，使用通用的 `MessageArray` + `PlainText` / `Image` 等。

---

## BiliSender

Bilibili 用户信息，扩展自 `BaseSender`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `user_id` | `str?` | 用户 UID *(继承)* |
| `nickname` | `str?` | 昵称 *(继承)* |
| `face_url` | `str?` | 头像 URL |
| `medal_name` | `str?` | 粉丝勋章名称 |
| `medal_level` | `int` | 勋章等级，默认 `0` |
| `guard_level` | `int` | 大航海等级（`0`=无, `1`=总督, `2`=提督, `3`=舰长） |
| `admin` | `bool` | 是否为房管 |

---

## 枚举类型

### BiliPostType

Bilibili 事件的顶层分类。

| 值 | 说明 |
|----|------|
| `LIVE` = `"live"` | 直播间事件 |
| `MESSAGE` = `"message"` | 私信消息 |
| `COMMENT` = `"comment"` | 评论事件 |
| `SYSTEM` = `"system"` | 系统事件 |

### BiliLiveEventType

直播间事件的子类型，值与 bilibili-api 的 cmd 一致。

| 值 | 说明 |
|----|------|
| `DANMU_MSG` | 弹幕消息 |
| `SEND_GIFT` | 礼物 |
| `COMBO_SEND` | 连击礼物 |
| `GUARD_BUY` | 大航海 |
| `SUPER_CHAT_MESSAGE` | 醒目留言 (SC) |
| `SUPER_CHAT_MESSAGE_JPN` | SC 日文翻译 |
| `SUPER_CHAT_MESSAGE_DELETE` | SC 删除 |
| `INTERACT_WORD_V2` | 互动（进入/关注/分享） |
| `ENTRY_EFFECT` | 入场效果 |
| `LIKE_INFO_V3_CLICK` | 点赞 |
| `LIKE_INFO_V3_UPDATE` | 点赞数据更新 |
| `VIEW` | 人气值 |
| `WATCHED_CHANGE` | 看过人数变化 |
| `ROOM_CHANGE` | 房间信息变更 |
| `LIVE` | 开播 |
| `PREPARING` | 下播 |
| `ROOM_BLOCK_MSG` | 用户被封禁 |
| `ROOM_SILENT_ON` | 开启全员禁言 |
| `ROOM_SILENT_OFF` | 关闭全员禁言 |
| `WARNING` | 超管警告 |
| `CUT_OFF` / `CUT_OFF_V2` | 直播被切断 |
| `ANCHOR_LOT_START` / `END` / `AWARD` | 天选之人 |
| `DANMU_AGGREGATION` | 弹幕聚合（节日/活动弹幕） |
| `DM_INTERACTION` | 互动消息（分享直播间等） |
| `ONLINE_RANK_COUNT` | 在线排名人数 |
| `ONLINE_RANK_V3` | 在线排名列表 |
| `STOP_LIVE_ROOM_LIST` | 停播房间列表（静默忽略） |

### BiliSessionEventType

私信消息类型，值与 bilibili-api 的 `EventType.value` 一致。

| 值 | 说明 |
|----|------|
| `TEXT` = `"1"` | 文本消息 |
| `PICTURE` = `"2"` | 图片消息 |
| `WITHDRAW` = `"5"` | 撤回 |
| `GROUPS_PICTURE` = `"6"` | 群发图片 |
| `SHARE_VIDEO` = `"7"` | 分享视频 |
| `NOTICE` = `"10"` | 通知 |
| `PUSHED_VIDEO` = `"11"` | 推送视频 |

### BiliCommentEventType

评论事件类型。

| 值 | 说明 |
|----|------|
| `NEW_REPLY` = `"new_reply"` | 新评论 |
| `NEW_SUB_REPLY` = `"new_sub_reply"` | 新子评论 |

---

## 事件数据模型一览

> 以下是 `ncatbot.types.bilibili` 导出的数据模型类，用于框架内部 Parser → Factory 流程。
> 插件开发者通常通过[事件实体](../events/3_bilibili_events.md)交互，无需直接使用数据模型。

### 直播间事件

| 数据模型 | 说明 | 关键字段 |
|----------|------|----------|
| `BiliLiveEventData` | 直播间事件基类 | `room_id`, `live_event_type` |
| `DanmuMsgEventData` | 弹幕消息 | `user_id`, `message`, `sender` |
| `SuperChatEventData` | 醒目留言 | `user_id`, `content`, `price`, `duration` |
| `GiftEventData` | 礼物 | `user_id`, `gift_name`, `gift_id`, `num`, `price`, `coin_type` |
| `GuardBuyEventData` | 大航海 | `user_id`, `guard_level`, `price` |
| `InteractEventData` | 互动 | `user_id`, `interact_type` |
| `LikeEventData` | 点赞 | `user_id`, `like_count` |
| `ViewEventData` | 人气值 | `view` |
| `LiveStatusEventData` | 开播/下播 | `status` |
| `RoomChangeEventData` | 房间变更 | `title`, `area_name` |
| `RoomBlockEventData` | 用户封禁 | `user_id`, `user_name` |
| `RoomSilentEventData` | 全员禁言 | `silent_type`, `level`, `second` |
| `WatchedChangeEventData` | 观看人数变化 | `num`, `text_small`, `text_large` |
| `LikeUpdateEventData` | 点赞数更新 | `click_count` |
| `OnlineRankCountEventData` | 在线排名人数 | `count` |
| `OnlineRankV3EventData` | 在线排名列表 | `online_list` |
| `DanmuAggregationEventData` | 弹幕聚合 | `activity_identity`, `msg`, `aggregation_num` |
| `DmInteractionEventData` | 互动消息 | `interaction_type`, `suffix_text` |
| `EntryEffectEventData` | 进场特效 | `user_id`, `user_name`, `sender` |

### 私信 / 评论 / 系统

| 数据模型 | 说明 | 关键字段 |
|----------|------|----------|
| `BiliPrivateMessageEventData` | 私信 | `user_id`, `message`, `msg_type`, `receiver_id` |
| `BiliPrivateMessageWithdrawEventData` | 私信撤回 | `user_id`, `msg_key` |
| `BiliCommentEventData` | 评论 | `resource_id`, `comment_id`, `content`, `root_id`, `parent_id` |
| `BiliConnectionEventData` | 连接事件 | `event_type`, `room_id` |

---

## 交叉引用

- [通用消息段](1_common_segments.md) — Bilibili 使用的基础消息段
- [Bilibili 事件实体](../events/3_bilibili_events.md) — 事件实体层级参考
