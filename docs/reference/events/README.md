# 事件参考

> 事件体系完整参考。按 **通用层 → QQ 平台 → Bilibili 平台** 组织。
>
> NcatBot 事件系统采用 **数据模型 + 实体** 双层设计，插件只需操作事件实体即可。

---

## Quick Reference

### 事件架构

```
ncatbot.event                     # 通用层导出
├── ncatbot.event.common          #   BaseEvent, Mixin traits, create_entity 工厂
├── ncatbot.event.qq              # QQ 事件实体
└── ncatbot.event.bilibili        # Bilibili 事件实体
```

### Mixin Trait 速查

| Trait | 能力 | 方法/属性 |
|-------|------|-----------|
| `Replyable` | 可回复 | `async reply(...)` |
| `Deletable` | 可撤回 | `async delete()` |
| `HasSender` | 有发送者 | `user_id`, `sender` |
| `GroupScoped` | 群/频道相关 | `group_id` |
| `Kickable` | 可踢人 | `async kick(...)` |
| `Bannable` | 可禁言 | `async ban(duration=...)` |
| `Approvable` | 可审批 | `async approve(...)`, `async reject(...)` |

### QQ 事件速查

```python
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent, NoticeEvent, RequestEvent
```

| 事件类 | Trait 组合 | 关键属性 |
|--------|-----------|----------|
| `MessageEvent` | Replyable, Deletable, HasSender | `message_id`, `message`, `raw_message` |
| `GroupMessageEvent` | + GroupScoped, Kickable, Bannable | `group_id`, `anonymous` |
| `PrivateMessageEvent` | *(同 MessageEvent)* | — |
| `NoticeEvent` | HasSender, GroupScoped | `notice_type`, `group_id?` |
| `GroupIncreaseEvent` | + Kickable | `sub_type`, `operator_id` |
| `RequestEvent` | HasSender, Approvable | `request_type`, `flag` |
| `MetaEvent` | — | `meta_event_type` |

### Bilibili 事件速查

```python
from ncatbot.event.bilibili import DanmuMsgEvent, BiliPrivateMessageEvent, BiliCommentEvent
```

| 事件类 | Trait 组合 | 关键属性 |
|--------|-----------|----------|
| `DanmuMsgEvent` | Replyable, HasSender, Bannable, GroupScoped | `user_id`, `sender`, `group_id`(=room_id) |
| `SuperChatEvent` | HasSender, GroupScoped | `user_id`, `sender` |
| `GiftEvent` | HasSender, GroupScoped | `user_id`, `sender` |
| `GuardBuyEvent` | HasSender, GroupScoped | `user_id`, `sender` |
| `InteractEvent` | HasSender, GroupScoped | `user_id`, `sender` |
| `LikeEvent` | HasSender, GroupScoped | `user_id`, `sender` |
| `BiliPrivateMessageEvent` | Replyable, HasSender | `user_id`, `sender` |
| `BiliCommentEvent` | Replyable, HasSender, Deletable | `user_id`, `sender` |

---

## 本目录索引

| 文件 | 层级 | 说明 |
|------|------|------|
| [1_common.md](1_common.md) | 通用 | BaseEvent 基类、Mixin Traits、工厂函数 |
| [2_qq_events.md](2_qq_events.md) | QQ | QQ 事件实体完整参考 |
| [3_bilibili_events.md](3_bilibili_events.md) | Bilibili | Bilibili 事件实体完整参考 |

---

## 交叉引用

| 如果你在找… | 去这里 |
|------------|--------|
| 消息段类型 | [types/](../types/) |
| Bot API 方法 | [api/](../api/) |
| 事件注册方式 | [guide/plugin/4a.event-registration.md](../../guide/plugin/4a.event-registration.md) |
