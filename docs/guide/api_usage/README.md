# Bot API 使用指南

> 掌握 `BotAPIClient` 的全部能力 — 跨平台通用方法与各平台专属 API。

---

## Quick Reference

### 多平台 API 访问

```python
# 通用 — 任何平台
await event.reply(text="收到")

# QQ 平台
await self.api.qq.post_group_msg(group_id, text="Hello!")
await self.api.qq.messaging.send_group_msg(group_id, message)
await self.api.qq.manage.set_group_ban(group_id, user_id, 600)

# Bilibili 平台
await self.api.bilibili.send_danmu(room_id, "弹幕内容")
await self.api.bilibili.send_private_msg(user_id, "私信内容")
```

### API 架构总览

```text
BotAPIClient                        ← 多平台路由（纯门面）
├── .qq : QQAPIClient               ← QQ 平台 API
│   ├── .messaging : QQMessaging    ← 消息收发
│   ├── .manage : QQManage          ← 群管理
│   ├── .query : QQQuery            ← 信息查询
│   ├── .file : QQFile              ← 文件操作
│   └── post_group_msg() ...        ← Sugar 便捷方法
├── .bilibili : IBiliAPIClient      ← Bilibili 平台 API
│   ├── send_danmu()                ← 弹幕
│   ├── send_private_msg()          ← 私信
│   ├── send_comment()              ← 评论
│   └── ban_user() ...              ← 直播间管理
├── .platform("xxx")                ← 按名称获取平台 API
└── .platforms                      ← 所有已注册平台
```

### 插件模式示例

```python
from ncatbot.plugin import NcatBotPlugin
from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent

class DemoPlugin(NcatBotPlugin):
    name = "demo"
    version = "1.0.0"

    @registrar.on_group_command("ping")
    async def on_ping(self, event: GroupMessageEvent):
        await event.reply(text="pong!", image="photo.jpg")
        await self.api.qq.post_group_msg(event.group_id, text="Hello!", at=event.user_id)
```

---

## 本目录索引

### 通用

| 文档 | 内容 |
|------|------|
| [通用 API](common/README.md) | 跨平台事件方法与 Trait 协议 |
| [事件方法](common/1_event_methods.md) | `event.reply()`, `event.delete()`, `event.kick()` 等 |
| [API Trait 协议](common/2_traits.md) | `IMessaging`, `IGroupManage`, `IQuery`, `IFileTransfer` |

### QQ 平台

| 文档 | 内容 |
|------|------|
| [QQ API 概览](qq/README.md) | QQ 平台 API 分层结构与速查 |
| [消息发送详解](qq/1_messaging.md) | sugar 方法、原子 messaging API、合并转发 |
| [群管理详解](qq/2_manage.md) | .manage 每个方法的参数与示例 |
| [查询与文件操作](qq/3_query_support.md) | .query + .file 方法详解 |

### Bilibili 平台

| 文档 | 内容 |
|------|------|
| [Bilibili API 概览](bilibili/README.md) | Bilibili 平台 API 功能分类与速查 |
| [直播间操作](bilibili/1_live_room.md) | 弹幕、禁言、房间信息 |
| [私信操作](bilibili/2_private_msg.md) | 私信文字/图片、历史记录 |
| [评论操作](bilibili/3_comment.md) | 发送/回复/删除/点赞评论 |
| [数据源与查询](bilibili/4_source_query.md) | 监听管理、用户信息查询 |
