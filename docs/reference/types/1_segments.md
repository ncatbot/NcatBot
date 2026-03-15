# 消息段类型详解

> 每个消息段的完整属性表、验证规则和构造示例。

---

## MessageSegment 基类

所有消息段的基类，位于 `ncatbot.types.segment.base`。

```python
class MessageSegment(BaseModel):
    model_config = ConfigDict(extra="allow")   # 允许额外字段
    _type: ClassVar[str]                        # OB11 type 标识
```

| 方法 | 说明 |
|---|---|
| `to_dict() -> Dict` | 序列化为 `{"type": "...", "data": {...}}` |
| `from_dict(data) -> MessageSegment` | 从 OB11 字典解析为具体子类 |

**注册机制：** 子类定义 `_type` 后自动注册到 `SEGMENT_MAP`，`parse_segment()` 据此路由。

---

## 文本类消息段

### PlainText

纯文本消息。

| 属性 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `text` | `str` | ✅ | 文本内容 |

```python
from ncatbot.types import PlainText

seg = PlainText(text="Hello World")
seg.to_dict()  # {"type": "text", "data": {"text": "Hello World"}}
```

### Face

QQ 表情。

| 属性 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `id` | `str` | ✅ | 表情 ID（自动从 int 转换） |

**验证规则：** `id` 通过 `field_validator` 自动转为 `str`。

```python
from ncatbot.types import Face

seg = Face(id=178)       # int 自动转 str
seg = Face(id="178")     # 也可以直接传 str
```

### At

@某人 或 @全体成员。

| 属性 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `qq` | `str` | ✅ | QQ 号或 `"all"`（@全体） |

**验证规则：** `qq` 必须为纯数字或 `"all"`，否则抛出 `ValueError`。

```python
from ncatbot.types import At

at_user = At(qq="123456")    # @某人
at_user = At(qq=123456)      # int 自动转 str
at_all  = At(qq="all")       # @全体
```

### Reply

引用回复。

| 属性 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `id` | `str` | ✅ | 被引用的消息 ID（自动从 int 转换） |

```python
from ncatbot.types import Reply

seg = Reply(id="12345")
seg = Reply(id=12345)     # int 自动转 str
```

---

## 媒体类消息段

### DownloadableSegment（基类）

所有可下载资源的公共字段：

| 属性 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `file` | `str` | ✅ | 文件路径或 URL |
| `url` | `str` | ❌ | 下载 URL |
| `file_id` | `str` | ❌ | 文件 ID |
| `file_size` | `int` | ❌ | 文件大小（字节） |
| `file_name` | `str` | ❌ | 文件名 |

### Image

图片消息。继承 `DownloadableSegment`。

| 属性 | 类型 | 必需 | 默认值 | 说明 |
|---|---|---|---|---|
| `file` | `str` | ✅ | — | 图片路径或 URL |
| `sub_type` | `int` | ❌ | `0` | 图片子类型 |
| `type` | `int` | ❌ | `None` | OB11 data.type：`0`=普通，`1`=闪照 |
| *继承* | — | — | — | `url`, `file_id`, `file_size`, `file_name` |

```python
from ncatbot.types import Image

# URL 图片
img = Image(file="https://example.com/photo.jpg")

# 本地文件
img = Image(file="file:///C:/imgs/photo.jpg")

# 闪照
img = Image(file="https://example.com/photo.jpg", type=1)
```

### Record

语音消息。继承 `DownloadableSegment`。

| 属性 | 类型 | 必需 | 默认值 | 说明 |
|---|---|---|---|---|
| `file` | `str` | ✅ | — | 语音文件路径或 URL |
| `magic` | `int` | ❌ | `None` | 是否变声（`1`=变声） |
| *继承* | — | — | — | `url`, `file_id`, `file_size`, `file_name` |

```python
from ncatbot.types import Record

seg = Record(file="https://example.com/voice.silk")
```

### Video

视频消息。继承 `DownloadableSegment`。

| 属性 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `file` | `str` | ✅ | 视频文件路径或 URL |
| *继承* | — | — | `url`, `file_id`, `file_size`, `file_name` |

```python
from ncatbot.types import Video

seg = Video(file="https://example.com/video.mp4")
```

### File

文件消息。继承 `DownloadableSegment`。

| 属性 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `file` | `str` | ✅ | 文件路径或 URL |
| *继承* | — | — | `url`, `file_id`, `file_size`, `file_name` |

```python
from ncatbot.types import File

seg = File(file="https://example.com/doc.pdf")
```

---

## 富文本类消息段

### Share

链接分享。

| 属性 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `url` | `str` | ✅ | 分享链接 |
| `title` | `str` | ✅ | 标题 |
| `content` | `str` | ❌ | 描述内容 |
| `image` | `str` | ❌ | 封面图 URL |

```python
from ncatbot.types import Share

seg = Share(url="https://ncatbot.dev", title="NcatBot", content="QQ Bot 框架")
```

### Location

位置消息。

| 属性 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `lat` | `float` | ✅ | 纬度 |
| `lon` | `float` | ✅ | 经度 |
| `title` | `str` | ❌ | 地点名称 |
| `content` | `str` | ❌ | 地址描述 |

```python
from ncatbot.types import Location

seg = Location(lat=39.9042, lon=116.4074, title="北京")
```

### Music

音乐消息。`_type` 为 OB11 外层 type，`type` 字段为 OB11 data.type（音乐平台）。

| 属性 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `type` | `Literal["qq", "163", "custom"]` | ✅ | 音乐平台 |
| `id` | `str` | ❌ | 歌曲 ID（QQ/网易云） |
| `url` | `str` | ❌ | 自定义跳转链接 |
| `audio` | `str` | ❌ | 自定义音频 URL |
| `title` | `str` | ❌ | 自定义标题 |

```python
from ncatbot.types import Music

# QQ 音乐
seg = Music(type="qq", id="12345")

# 自定义音乐
seg = Music(type="custom", url="https://...", audio="https://...", title="My Song")
```

### Json

JSON 消息（卡片消息等）。

| 属性 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `data` | `str` | ✅ | JSON 字符串 |

```python
from ncatbot.types import Json

seg = Json(data='{"app":"com.example","desc":"card"}')
```

### Markdown

Markdown 消息。

| 属性 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `content` | `str` | ✅ | Markdown 内容 |

```python
from ncatbot.types import Markdown

seg = Markdown(content="# 标题\n正文内容")
```

---

## 转发消息段

### ForwardNode

转发消息中的单个节点。

| 属性 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `user_id` | `str` | ✅ | 发送者 QQ 号（自动从 int 转换） |
| `nickname` | `str` | ✅ | 发送者昵称 |
| `content` | `List[MessageSegment]` | ✅ | 消息内容（自动从 dict 列表解析） |

### Forward

合并转发消息。

| 属性 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `id` | `str` | ❌ | 转发消息 ID（引用已有转发） |
| `content` | `List[ForwardNode]` | ❌ | 转发节点列表（构造新转发） |

> `id` 和 `content` 二选一：引用已有转发用 `id`，构造新转发用 `content`。

| 方法 | 说明 |
|---|---|
| `to_dict()` | 序列化为 OB11 格式 |
| `to_forward_dict()` | 序列化为 `{"messages": [...]}` 格式 |
| `from_dict(data)` | 从 OB11 字典解析（支持嵌套） |

```python
from ncatbot.types import Forward, ForwardNode, PlainText, Image

# 构造合并转发
fwd = Forward(content=[
    ForwardNode(user_id="123456", nickname="Alice", content=[PlainText(text="你好")]),
    ForwardNode(user_id="789012", nickname="Bob", content=[Image(file="https://img.url")]),
])
```

### ForwardConstructor

便捷的转发消息构造器，位于 `ncatbot.types.helper`。

| 方法 | 签名 | 说明 |
|---|---|---|
| `set_author` | `set_author(user_id, nickname)` | 设置默认作者 |
| `attach` | `attach(content: MessageArray, ...)` | 添加消息节点 |
| `attach_text` | `attach_text(text, ...)` | 添加纯文本节点 |
| `attach_image` | `attach_image(image, ...)` | 添加图片节点 |
| `attach_file` | `attach_file(file, ...)` | 添加文件节点 |
| `attach_video` | `attach_video(video, ...)` | 添加视频节点 |
| `attach_forward` | `attach_forward(forward, ...)` | 添加嵌套转发节点 |
| `build` | `build() -> Forward` | 构建 Forward 消息段 |

```python
from ncatbot.types.helper import ForwardConstructor
from ncatbot.types import MessageArray, PlainText

fc = ForwardConstructor(user_id="123456", nickname="Bot")
fc.attach_text("第一条消息")
fc.attach_text("第二条消息")
fc.set_author("789012", "Alice")
fc.attach_text("Alice 的消息")

fwd = fc.build()   # 返回 Forward 消息段
```
