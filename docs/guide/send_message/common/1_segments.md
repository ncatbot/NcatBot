# 消息段参考

> 消息段的分类、构造方式和常用示例。完整字段表见 [通用消息段](../../../reference/types/1_common_segments.md) 和 [QQ 消息段](../../../reference/types/3_qq_segments.md)。

---

## 基类 MessageSegment

所有消息段继承自 `MessageSegment`（Pydantic `BaseModel`），提供 `to_dict()` / `from_dict()` 序列化。

```python
from ncatbot.types import PlainText, parse_segment

seg = PlainText(text="Hello")
seg.to_dict()  # {"type": "text", "data": {"text": "Hello"}}

seg = parse_segment({"type": "at", "data": {"qq": "123456"}})  # → At(user_id='123456')
```

---

## 基础消息段

| 类型 | 构造示例 | 关键字段 |
|------|---------|---------|
| `PlainText` | `PlainText(text="你好")` | `text: str` |
| `At` | `At(user_id="123456")` / `At(user_id="all")` | `user_id: str`（数字或 `"all"`，别名 `qq` 兼容 OB11） |
| `Face` | `Face(id=178)` | `id: str`（自动转换） |
| `Reply` | `Reply(id=12345)` | `id: str`（自动转换） |

---

## 多媒体消息段

都继承 `DownloadableSegment`，共享 `file` / `url` / `file_id` / `file_size` / `file_name` 字段。

`file` 支持三种格式：URL / 本地路径 / `base64://...`

| 类型 | 构造示例 | 额外字段 |
|------|---------|---------|
| `Image` | `Image(file="https://...")` | `sub_type`（1=动画表情）, `type`（1=闪照） |
| `Record` | `Record(file="audio.silk")` | `magic`（1=变声） |
| `Video` | `Video(file="video.mp4")` | — |
| `File` | `File(file="doc.pdf", file_name="手册.pdf")` | — |

---

## 富文本消息段

| 类型 | 关键字段 | 说明 |
|------|---------|------|
| `Share` | `url`, `title`, `content?`, `image?` | 链接分享卡片 |
| `Location` | `lat`, `lon`, `title?`, `content?` | 定位消息 |
| `Music` | `type`("qq"/"163"/"custom"), `id?`, `url?`, `audio?` | 音乐卡片 |
| `Json` | `data: str` | JSON 消息 |
| `Markdown` | `content: str` | Markdown 消息 |

---

## 延伸阅读

- [MessageArray 消息数组](2_array.md) — 消息段的容器与链式构造
- [通用消息段](../../../reference/types/1_common_segments.md) — 通用段完整字段表
- [QQ 消息段](../../../reference/types/3_qq_segments.md) — QQ 专属段完整字段表

```python
seg = Music(type="qq", id="12345")        # QQ 音乐
seg = Music(type="163", id="67890")       # 网易云
seg = Music(                              # 自定义
    type="custom",
    url="https://music.example.com",
    audio="https://music.example.com/song.mp3",
    title="自定义歌曲",
)
```

### Json — JSON 消息

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `data` | `str` | ✅ | JSON 字符串内容 |

```python
from ncatbot.types import Json

seg = Json(data='{"app":"com.example","desc":"卡片消息"}')
```

### Markdown — Markdown 消息

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `content` | `str` | ✅ | Markdown 内容 |

```python
from ncatbot.types import Markdown

seg = Markdown(content="# 标题\n**粗体**\n- 列表项")
```

---

[← 上一篇：快速上手](README.md) | [返回目录](README.md) | [下一篇：MessageArray →](2_array.md)
