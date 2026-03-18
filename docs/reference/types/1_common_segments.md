# 通用消息段

> 跨平台通用的消息段类型，所有平台共享。

**导入路径：** `from ncatbot.types import MessageSegment, PlainText, At, Reply, Image, Record, Video, File`

**源码：** `ncatbot/types/common/segment/`

---

## MessageSegment 基类

所有消息段的抽象基类。子类通过 `_type` ClassVar 自动注册到 `SEGMENT_MAP`。

| 属性/方法 | 类型 | 说明 |
|-----------|------|------|
| `_type` | `ClassVar[str]` | 协议 type 标识（如 `"text"`, `"image"`） |
| `to_dict()` | `Dict[str, Any]` | 序列化为 OB11 格式 `{"type": ..., "data": {...}}` |
| `from_dict(data)` | `MessageSegment` (classmethod) | 从协议原始 dict 解析为具体子类 |

```python
class MessageSegment(BaseModel):
    _type: ClassVar[str]
```

### 解析函数

```python
from ncatbot.types import parse_segment, SEGMENT_MAP

seg = parse_segment({"type": "text", "data": {"text": "hello"}})
# → PlainText(text="hello")
```

| 名称 | 说明 |
|------|------|
| `parse_segment(raw)` | 从 `{"type": ..., "data": {...}}` 解析为具体 `MessageSegment` |
| `SEGMENT_MAP` | `Dict[str, Type[MessageSegment]]` — type 字符串 → 段类的全局注册表 |

---

## 文本类

### PlainText

纯文本消息段。

| 字段 | 类型 | 说明 |
|------|------|------|
| `text` | `str` | 文本内容 |

```python
PlainText(text="你好")
```

### At

@某人。

| 字段 | 类型 | 说明 |
|------|------|------|
| `user_id` | `str` | 目标用户 ID，`"all"` 表示 @全体 |

- 接受 `user_id` 或 `qq` 作为输入（`AliasChoices`）
- 序列化时使用 OB11 的 `"qq"` key

```python
At(user_id="123456")   # @指定用户
At(user_id="all")      # @全体成员
```

### Reply

引用回复。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `str` | 被引用的消息 ID（自动转 str） |

```python
Reply(id="12345")
```

---

## 媒体类

所有媒体段继承自 `DownloadableSegment`，共享以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `file` | `str` | 文件路径或 URL |
| `url` | `str?` | 下载 URL |
| `file_id` | `str?` | 文件 ID |
| `file_size` | `int?` | 文件大小 (bytes) |
| `file_name` | `str?` | 文件名 |

### Image

图片消息段。`_type = "image"`

```python
Image(file="https://example.com/img.png")
Image(file="/path/to/local.jpg")
```

### Record

语音消息段。`_type = "record"`

```python
Record(file="https://example.com/voice.mp3")
```

### Video

视频消息段。`_type = "video"`

```python
Video(file="https://example.com/video.mp4")
```

### File

文件消息段。`_type = "file"`

```python
File(file="/path/to/document.pdf")
```

---

## 继承关系

```
MessageSegment (base)
├── PlainText          _type="text"
├── At                 _type="at"
├── Reply              _type="reply"
└── DownloadableSegment (base)
    ├── Image          _type="image"
    ├── Record         _type="record"
    ├── Video          _type="video"
    └── File           _type="file"
```

---

## 交叉引用

- [MessageArray 容器](2_message_array.md) — 消息段的有序容器
- [QQ 平台消息段](3_qq_segments.md) — QQ 专属消息段（Face, Forward, Music 等）
