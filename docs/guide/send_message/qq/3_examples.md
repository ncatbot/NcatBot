# 实战示例

> 核心消息发送场景速查，完整代码请参考 `examples/` 目录。

---

## 核心示例

### 发送纯文本 / event.reply()

```python
# 1. post_group_msg 直接发送
await self.api.qq.post_group_msg(event.group_id, text="Hello, World! 👋")

# 2. event.reply() 自动引用 + @发送者
await event.reply(text="你好呀！🎉")
```

### 图文混排（MessageArray）

```python
from ncatbot.types import MessageArray

msg = MessageArray()
msg.add_text("📸 这是一条图文混排消息:\n")
msg.add_image(str(EXAMPLE_IMAGE))  # 本地路径或 URL
msg.add_text("\n以上是示例图片！")
await self.api.qq.post_group_array_msg(event.group_id, msg)
```

### 合并转发

```python
from ncatbot.types import ForwardConstructor, MessageArray

fc = ForwardConstructor(user_id=str(event.self_id), nickname="Bot")
fc.attach_text("第一条消息 📝")
fc.attach_text("第二条消息 📝")

msg = MessageArray().add_text("图片: ").add_image(str(EXAMPLE_IMAGE))
fc.attach_message(msg)

forward = fc.build()
await self.api.qq.post_group_forward_msg(event.group_id, forward)
```

### 回复消息（引用）

```python
# 方式一：event.reply()（推荐）
await event.reply(text="收到！")

# 方式二：reply 参数
await self.api.qq.post_group_msg(event.group_id, text="收到！", reply=event.message_id)

# 方式三：MessageArray
msg = MessageArray().add_reply(event.message_id).add_text("收到！")
await self.api.qq.post_group_array_msg(event.group_id, msg)
```

---

## 更多场景

### 发送 URL 图片

```python
msg = MessageArray()
msg.add_image("https://example.com/photo.jpg")
await self.api.qq.post_group_array_msg(event.group_id, msg)
```

### 发送视频

```python
await self.api.qq.post_group_msg(event.group_id, video="/path/to/video.mp4")
```

### 发送文件

```python
await self.api.qq.send_group_file(event.group_id, "/path/to/file.pdf", name="文件名.pdf")
```

### 动画表情

```python
await self.api.qq.send_group_sticker(event.group_id, "/path/to/image.jpg")
```

### 嵌套合并转发

```python
from ncatbot.types import ForwardConstructor

bot_id = str(event.self_id)

# 构造内层转发
inner_fc = ForwardConstructor(user_id=bot_id, nickname="Bot 内层")
inner_fc.attach_text("🔹 内层第一条消息")
inner_fc.attach_text("🔹 内层第二条消息")
inner_forward = inner_fc.build()

# 构造外层转发，嵌套进去
outer_fc = ForwardConstructor(user_id=bot_id, nickname="Bot")
outer_fc.attach_text("🔸 外层第一条消息")
outer_fc.attach_forward(inner_forward)  # 关键：嵌套内层
outer_fc.attach_text("🔸 外层第三条消息")

await self.api.qq.post_group_forward_msg(event.group_id, outer_fc.build())
```

### 提取消息中图片

```python
from ncatbot.types import Image

images = event.message.filter(Image)
for img in images:
    url = getattr(img, "url", None) or getattr(img, "file", "未知")
    print(url)
```

### @全体成员

```python
msg = MessageArray()
msg.add_at_all()
msg.add_text(" 全体注意！")
await self.api.qq.post_group_array_msg(event.group_id, msg)
```

### 戳一戳

```python
await self.api.qq.send_poke(event.group_id, target_user_id)
```

---

[← 上一篇：便捷接口](1_sugar.md) | [返回目录](../README.md)
