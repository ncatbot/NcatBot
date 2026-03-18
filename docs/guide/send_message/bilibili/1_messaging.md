# Bilibili 消息发送详解

> Bilibili 平台三种消息形式的发送方式与实战示例。

---

## 弹幕发送

直播间弹幕是 Bilibili 最常用的消息形式。

```python
# 发送弹幕
await self.api.bilibili.send_danmu(room_id=12345, text="Hello!")
```

在事件处理器中，也可以使用通用的 `event.reply()`：

```python
@registrar.on_message(platform="bilibili")
async def on_danmu(self, event):
    await event.reply(text="收到弹幕！")
```

---

## 私信发送

### 文字私信

```python
await self.api.bilibili.send_private_msg(user_id=67890, content="你好！")
```

### 图片私信

```python
await self.api.bilibili.send_private_image(
    user_id=67890,
    image_url="https://example.com/img.png",
)
```

---

## 评论发送

### 发送新评论

```python
await self.api.bilibili.send_comment(
    resource_id="BV1xx411c7mD",
    resource_type="video",
    text="好视频！",
)
```

### 回复评论

```python
await self.api.bilibili.reply_comment(
    resource_id="BV1xx411c7mD",
    resource_type="video",
    root_id=123456,
    parent_id=789012,
    text="谢谢！",
)
```

---

## 与 QQ 的对比

| 特性 | QQ | Bilibili |
|------|:--:|:--------:|
| 富文本消息（图文混排） | ✅ MessageArray | ❌ 纯文本 |
| 消息段构造 | ✅ MessageSegment | ❌ |
| 合并转发 | ✅ Forward | ❌ |
| event.reply() | ✅ | ✅ |
| 语法糖方法 | ✅ post_group_msg 等 | ❌ 直接调用 API |

---

## 实战示例

```python
class BiliMessenger(NcatBotPlugin):
    name = "bili_messenger"
    version = "1.0.0"

    @registrar.on_message(platform="bilibili")
    async def on_danmu(self, event):
        """弹幕自动回复"""
        if event.content == "签到":
            await event.reply(text=f"签到成功！欢迎 {event.sender.nickname}")

    @registrar.on_notice(platform="bilibili")
    async def on_comment(self, event):
        """新评论通知"""
        if hasattr(event, "comment_id"):
            await self.api.bilibili.reply_comment(
                resource_id=event.resource_id,
                resource_type=event.resource_type,
                root_id=event.comment_id,
                parent_id=event.comment_id,
                text="感谢评论！",
            )
```

---

> **返回**：[Bilibili 消息发送](README.md) · **相关**：[Bilibili API 指南](../../api_usage/bilibili/README.md)
