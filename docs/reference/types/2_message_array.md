# MessageArray 详解

> 消息段数组的完整方法详解、高级用法与 Pydantic 集成。

---

## 概述

`MessageArray` 是 NcatBot 的消息容器，封装了 `List[MessageSegment]`，提供：

- **链式构造** — 流畅地拼接消息段
- **类型过滤** — 按消息段类型提取内容
- **序列化** — 与 OB11 协议格式互转
- **Pydantic 集成** — 直接用作事件模型字段类型

```python
from ncatbot.types import MessageArray, PlainText, At, Image
```

---

## 创建方式

### 构造函数

```python
# 空消息
msg = MessageArray()

# 从消息段列表创建
msg = MessageArray([PlainText(text="你好"), At(qq="123456")])
```

### from_list

从 OB11 协议格式的字典列表创建：

```python
msg = MessageArray.from_list([
    {"type": "text", "data": {"text": "你好"}},
    {"type": "at", "data": {"qq": "123456"}},
])
```

### from_any

通用工厂方法，自动识别输入格式：

```python
# 从 CQ 码字符串
msg = MessageArray.from_any("你好[CQ:at,qq=123456]")

# 从 OB11 字典列表
msg = MessageArray.from_any([{"type": "text", "data": {"text": "hi"}}])

# 从单个消息段
msg = MessageArray.from_any(PlainText(text="hi"))
```

---

## 链式构造

所有 `add_*` 方法返回 `self`，支持链式调用：

```python
msg = (
    MessageArray()
    .add_text("你好 ")
    .add_at(123456)
    .add_text(" 请看这张图：")
    .add_image("https://example.com/photo.jpg")
)
```

### add_text

```python
add_text(text: str) -> MessageArray
```

追加纯文本。支持 CQ 码自动解析 — 如果 `text` 中包含 CQ 码，会被解析为对应的消息段。

```python
msg = MessageArray()
msg.add_text("普通文本")
msg.add_text("[CQ:face,id=178]")   # CQ 码会被解析为 Face 段
```

### add_image

```python
add_image(image: str | Image) -> MessageArray
```

追加图片。传入字符串时自动包装为 `Image(file=...)`：

```python
msg.add_image("https://example.com/photo.jpg")
msg.add_image(Image(file="https://example.com/photo.jpg", type=1))  # 闪照
```

### add_video

```python
add_video(video: str | Video) -> MessageArray
```

追加视频。用法同 `add_image`。

### add_at / add_at_all

```python
add_at(user_id: str | int) -> MessageArray
add_at_all() -> MessageArray
```

```python
msg.add_at(123456)     # @某人
msg.add_at_all()       # @全体成员
```

### add_reply

```python
add_reply(message_id: str | int) -> MessageArray
```

追加引用回复：

```python
msg.add_reply(event.message_id)
```

### add_segment / add_segments

```python
add_segment(segment: MessageSegment) -> MessageArray
add_segments(data: Any) -> MessageArray
```

追加任意消息段或任意可解析输入：

```python
from ncatbot.types import Share

msg.add_segment(Share(url="https://ncatbot.dev", title="NcatBot"))
msg.add_segments([{"type": "text", "data": {"text": "hi"}}])
```

---

## 查询与过滤

### text 属性

```python
@property
text -> str
```

拼接所有 `PlainText` 段的文本：

```python
msg = MessageArray.from_any("你好[CQ:at,qq=123456]世界")
msg.text  # "你好世界"
```

### filter

```python
filter(cls: Type[T] = None) -> List[T]
```

按类型过滤。不传参时返回所有消息段（副本）：

```python
from ncatbot.types import Image, At

all_segs = msg.filter()          # 所有消息段
images   = msg.filter(Image)     # 仅图片段
ats      = msg.filter(At)        # 仅 @段
```

### 快捷过滤方法

| 方法 | 等价于 | 返回类型 |
|---|---|---|
| `filter_text()` | `filter(PlainText)` | `List[PlainText]` |
| `filter_at()` | `filter(At)` | `List[At]` |
| `filter_image()` | `filter(Image)` | `List[Image]` |
| `filter_video()` | `filter(Video)` | `List[Video]` |
| `filter_face()` | `filter(Face)` | `List[Face]` |

### is_at

```python
is_at(user_id: str | int, all_except: bool = False) -> bool
```

判断消息中是否 @了指定用户：

- 精确 @：消息中有 `At(qq=user_id)` → `True`
- @全体：消息中有 `At(qq="all")` 时，默认也返回 `True`
- 设 `all_except=True` 可排除 @全体的匹配

```python
msg = MessageArray([At(qq="all"), PlainText(text="Hello")])

msg.is_at("123456")                    # True（被 @all 覆盖）
msg.is_at("123456", all_except=True)   # False（排除 @all）
```

### is_forward_msg

```python
is_forward_msg() -> bool
```

判断消息中是否包含合并转发段。

---

## 序列化

### to_list

```python
to_list() -> List[Dict[str, Any]]
```

将消息数组序列化为 OB11 协议格式：

```python
msg = MessageArray([PlainText(text="hi"), At(qq="123")])
msg.to_list()
# [
#   {"type": "text", "data": {"text": "hi"}},
#   {"type": "at", "data": {"qq": "123"}}
# ]
```

---

## 容器协议

`MessageArray` 实现了标准容器协议：

```python
msg = MessageArray([PlainText(text="a"), PlainText(text="b")])

len(msg)           # 2
for seg in msg:    # 可迭代
    print(seg)
```

### 拼接

`+` 运算符创建新的 `MessageArray`，不修改原对象：

```python
msg1 = MessageArray([PlainText(text="Hello ")])
msg2 = MessageArray([PlainText(text="World")])

combined = msg1 + msg2              # MessageArray([PlainText("Hello "), PlainText("World")])
combined = msg1 + [At(qq="123")]    # 右侧会自动解析
combined = "前缀" + msg1             # __radd__ 支持
```

---

## Pydantic 集成

`MessageArray` 实现了 `__get_pydantic_core_schema__`，可直接用作 Pydantic 模型字段：

```python
from pydantic import BaseModel
from ncatbot.types import MessageArray

class MyModel(BaseModel):
    message: MessageArray

# 自动从列表验证
m = MyModel(message=[{"type": "text", "data": {"text": "hi"}}])

# 自动从 CQ 码验证
m = MyModel(message="你好[CQ:at,qq=123]")

# 序列化
m.model_dump()  # {"message": [{"type": "text", ...}, ...]}
```

事件模型中的 `message` 字段就利用了这一特性，会自动将 `list`、CQ 码字符串、`MessageArray` 统一转为 `MessageArray`。

---

## CQ 码解析

`parse_cq_code_to_onebot11` 函数将 CQ 码字符串解析为 OB11 消息数组格式：

```python
from ncatbot.types import parse_cq_code_to_onebot11

result = parse_cq_code_to_onebot11("你好[CQ:at,qq=123456]世界")
# [
#   {"type": "text", "data": {"text": "你好"}},
#   {"type": "at", "data": {"qq": "123456"}},
#   {"type": "text", "data": {"text": "世界"}}
# ]
```

支持 HTML 反转义：`&amp;` → `&`，`&#91;` → `[`，`&#93;` → `]`，`&#44;` → `,`。
