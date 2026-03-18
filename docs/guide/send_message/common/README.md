# 通用消息概念

> 跨平台通用的消息构造基础 — 消息段（MessageSegment）和消息数组（MessageArray）。

---

## Quick Start

### 构造一条消息

```python
from ncatbot.types import MessageArray

# 链式构造 — 文本 + 图片 + @某人
msg = MessageArray().add_text("Hello\n").add_image("photo.jpg").add_at(user_id)

# 发送
await self.api.qq.post_group_array_msg(group_id, msg)
```

### 使用消息段

```python
from ncatbot.types import MessageSegment, MessageArray
from ncatbot.types.common.segment import PlainText, Image, At, Reply

# 手动构造消息段
text = PlainText(text="你好")
img = Image(file="https://example.com/pic.jpg")
at = At(user_id="123456")

# 组合成数组
msg = MessageArray([text, img, at])
```

### 从事件中提取消息内容

```python
@registrar.on_group_command("echo")
async def on_echo(self, event: GroupMessageEvent):
    # 获取纯文本内容
    text = event.message.text

    # 提取所有图片段
    images = event.message.filter_image()

    # 检查是否 @了某人
    if event.message.is_at("123456"):
        await event.reply(text="你 @了 TA")
```

---

## 概览

NcatBot 的消息构造体系分为两层：

| 概念 | 说明 | 适用平台 |
|------|------|---------|
| `MessageSegment` | 消息的最小单元（文本、图片、@等） | 主要用于 QQ，Bilibili 使用纯文本 |
| `MessageArray` | 消息段的有序容器，支持链式构造 | 主要用于 QQ |

### 消息段类型速查

| 类型 | 构造 | 说明 |
|------|------|------|
| `PlainText` | `PlainText(text="...")` | 纯文本 |
| `Image` | `Image(file="url或路径")` | 图片（URL / 文件路径 / base64） |
| `At` | `At(user_id="123456")` | @提及（`"all"` 为 @全体） |
| `Reply` | `Reply(id="msg_id")` | 回复引用 |
| `Video` | `Video(file="...")` | 视频 |
| `Record` | `Record(file="...")` | 语音 |
| `File` | `File(file="...")` | 文件附件 |

### MessageArray 常用方法

| 方法 | 返回 | 说明 |
|------|------|------|
| `add_text(text)` | `self` | 追加文本段 |
| `add_image(image)` | `self` | 追加图片段 |
| `add_at(user_id)` | `self` | 追加 @段 |
| `add_at_all()` | `self` | 追加 @全体 |
| `add_reply(message_id)` | `self` | 追加回复引用 |
| `add_video(video)` | `self` | 追加视频段 |
| `add_segment(seg)` | `self` | 追加任意消息段 |
| `.text` | `str` | 拼接所有纯文本内容 |
| `filter(cls)` | `list` | 按类型筛选消息段 |
| `filter_image()` | `list` | 筛选所有图片段 |
| `to_list()` | `list[dict]` | 序列化为 API 格式 |
| `from_list(data)` | `MessageArray` | 从 API 格式反序列化 |

对于 Bilibili 平台，消息以纯文本为主（弹幕、私信、评论），不需要复杂的消息段构造。

---

## 本目录索引

| 文档 | 内容 |
|------|------|
| [消息段参考](1_segments.md) | 所有消息段类型的字段、构造方式和序列化格式 |
| [MessageArray 消息数组](2_array.md) | 容器：创建、链式构造、查询过滤、序列化 |
