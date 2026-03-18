# QQ 消息发送

> QQ 平台的消息发送方式 — sugar 便捷方法、合并转发与实战示例。

---

## Quick Start

### 最便捷：event.reply()

处理器内直接回复，自动引用原消息并 @发送者：

```python
from ncatbot.plugin import NcatBotPlugin
from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent


class MyPlugin(NcatBotPlugin):
    name = "my_plugin"
    version = "1.0.0"

    @registrar.on_group_command("hello")
    async def on_hello(self, event: GroupMessageEvent):
        await event.reply(text="你好！", image="welcome.jpg")
```

### 语法糖：post_group_msg / post_private_msg

关键字自动组装 `MessageArray`，适合不在事件上下文中发送消息：

```python
# 群消息 — 文本 + 图片
await self.api.qq.post_group_msg(group_id, text="看图", image="/path/to/img.jpg")

# 群消息 — @某人 + 回复引用
await self.api.qq.post_group_msg(group_id, text="收到", at=user_id, reply=message_id)

# 私聊消息
await self.api.qq.post_private_msg(user_id, text="私聊消息")
```

### MessageArray：复杂消息构造

链式构造多类型混合消息：

```python
from ncatbot.types import MessageArray

msg = MessageArray().add_text("这是图文消息\n").add_image("photo.jpg").add_at(user_id)
await self.api.qq.post_group_array_msg(group_id, msg)
```

---

## Quick Reference

| 方式 | 调用 | 适用场景 |
|------|------|---------|
| `event.reply()` | `await event.reply(text=, at=, image=, video=, rtf=)` | 处理器内回复 |
| `post_group_msg()` | `await self.api.qq.post_group_msg(group_id, text=, at=, reply=, image=)` | 关键字快捷 |
| `MessageArray` | `MessageArray().add_text(...).add_image(...)` | 复杂消息 |

### 单类型快捷方法

| 方法 | 参数 | 说明 |
|------|------|------|
| `send_group_text(group_id, text)` | | 纯文本 |
| `send_group_image(group_id, image)` | | 图片 |
| `send_group_record(group_id, file)` | | 语音 |
| `send_group_video(group_id, video)` | | 视频 |
| `send_group_file(group_id, file, name=)` | | 文件 |
| `send_group_sticker(group_id, image)` | | 动画表情 |
| `send_private_text(user_id, text)` | | 私聊纯文本 |
| `send_private_image(user_id, image)` | | 私聊图片 |

### 合并转发

```python
from ncatbot.types.qq import ForwardConstructor

fc = ForwardConstructor(user_id="123456", nickname="Bot")
fc.attach_text("第一条消息")
fc.attach_text("第二条消息")
fc.attach_image("photo.jpg")

await self.api.qq.post_group_forward_msg(group_id, fc.build())
```

---

## 本目录索引

| 文档 | 内容 |
|------|------|
| [便捷接口参考](1_sugar.md) | event.reply()、所有 sugar 方法完整清单 |
| [合并转发](2_forward.md) | ForwardNode / Forward / ForwardConstructor 构造器 |
| [实战示例](3_examples.md) | 常见场景速查：纯文本、图文、回复、转发等 |

---

> **相关**：[通用消息概念](../common/README.md) · [QQ API 使用指南](../../api_usage/qq/README.md)
