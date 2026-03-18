# Bilibili 消息发送

> Bilibili 平台的消息发送方式 — 弹幕、私信与评论。

---

## Quick Start

### 发送弹幕

```python
from ncatbot.plugin import NcatBotPlugin
from ncatbot.core import registrar


class MyPlugin(NcatBotPlugin):
    name = "my_plugin"
    version = "1.0.0"

    async def on_load(self):
        # 向直播间发送弹幕
        await self.api.bilibili.send_danmu(room_id=12345, text="Hello!")
```

### 发送私信

```python
# 文字私信
await self.api.bilibili.send_private_msg(user_id=67890, content="你好")

# 图片私信
await self.api.bilibili.send_private_image(user_id=67890, image_url="https://example.com/pic.jpg")
```

### 发送评论与回复

```python
# 发送视频评论
await self.api.bilibili.send_comment(resource_id="BV1xxx", resource_type="video", text="好看！")

# 回复已有评论
await self.api.bilibili.reply_comment(
    resource_id="BV1xxx",
    resource_type="video",
    root_id=100,
    parent_id=200,
    text="同意！",
)
```

---

## Quick Reference

| 类型 | 方法 | 说明 |
|------|------|------|
| 弹幕 | `send_danmu(room_id, text)` | 直播间弹幕 |
| 私信 | `send_private_msg(user_id, content)` | 文字私信 |
| 私信图片 | `send_private_image(user_id, image_url)` | 图片私信 |
| 评论 | `send_comment(resource_id, resource_type, text)` | 视频/动态评论 |
| 回复评论 | `reply_comment(resource_id, resource_type, root_id, parent_id, text)` | 回复已有评论 |
| 删除评论 | `delete_comment(resource_id, resource_type, comment_id)` | 删除评论 |
| 点赞评论 | `like_comment(resource_id, resource_type, comment_id)` | 点赞评论 |

> 所有方法通过 `self.api.bilibili` 访问。与 QQ 不同，Bilibili 的消息以纯文本为主，不需要 MessageArray 或消息段构造。

---

## 本目录索引

| 文档 | 内容 |
|------|------|
| [消息发送详解](1_messaging.md) | 弹幕、私信、评论的发送方式与示例 |

---

> **相关**：[Bilibili API 使用指南](../../api_usage/bilibili/README.md)
