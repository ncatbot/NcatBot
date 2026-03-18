# QQ 平台消息段

> QQ 平台专属的消息段类型，在通用段基础上扩展。

**导入路径：** `from ncatbot.types.qq import Face, Share, Location, Music, Json, Markdown, Forward, ForwardNode, QQImage, QQRecord, ForwardConstructor`

**源码：** `ncatbot/types/qq/segment/`, `ncatbot/types/qq/helper/`

---

## 文本类

### Face

QQ 表情。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `str` | QQ 表情 ID（自动转 str） |

```python
Face(id="123")
Face(id=123)  # 自动转为 "123"
```

---

## 媒体类

### QQImage

QQ 图片，扩展自通用 `Image`，增加 QQ 专属字段。

| 字段 | 类型 | 说明 |
|------|------|------|
| *(继承 Image)* | | `file`, `url`, `file_id`, `file_size`, `file_name` |
| `sub_type` | `int` | 子类型，默认 `0` |
| `type` | `int?` | 图片类型 |

### QQRecord

QQ 语音，扩展自通用 `Record`。

| 字段 | 类型 | 说明 |
|------|------|------|
| *(继承 Record)* | | `file`, `url`, `file_id`, `file_size`, `file_name` |
| `magic` | `int?` | 变声效果 |

---

## 富文本类

### Share

链接分享。

| 字段 | 类型 | 说明 |
|------|------|------|
| `url` | `str` | 链接地址 |
| `title` | `str` | 标题 |
| `content` | `str?` | 简介 |
| `image` | `str?` | 缩略图 URL |

```python
Share(url="https://example.com", title="示例网站")
```

### Location

位置消息。

| 字段 | 类型 | 说明 |
|------|------|------|
| `lat` | `float` | 纬度 |
| `lon` | `float` | 经度 |
| `title` | `str?` | 地点名称 |
| `content` | `str?` | 地址描述 |

```python
Location(lat=39.9, lon=116.3, title="北京")
```

### Music

音乐消息。`_type` ClassVar = `"music"`，`type` 字段为 OB11 协议的 `data.type`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | `"qq" \| "163" \| "custom"` | 音乐平台 |
| `id` | `str?` | 歌曲 ID（`"qq"` / `"163"` 时使用） |
| `url` | `str?` | 自定义链接 |
| `audio` | `str?` | 自定义音频 URL |
| `title` | `str?` | 自定义标题 |

```python
Music(type="qq", id="123456")
Music(type="custom", url="https://...", audio="https://...", title="My Song")
```

### Json

JSON 卡片消息。

| 字段 | 类型 | 说明 |
|------|------|------|
| `data` | `str` | JSON 字符串 |

```python
Json(data='{"app":"com.example","desc":"..."}')
```

### Markdown

Markdown 消息。

| 字段 | 类型 | 说明 |
|------|------|------|
| `content` | `str` | Markdown 内容 |

```python
Markdown(content="**加粗** *斜体*")
```

---

## 转发消息

### ForwardNode

转发消息的单个节点。

| 字段 | 类型 | 说明 |
|------|------|------|
| `user_id` | `str` | 发送者 QQ 号 |
| `nickname` | `str` | 发送者昵称 |
| `content` | `List[MessageSegment]` | 消息内容（段列表） |

| 方法 | 说明 |
|------|------|
| `to_node_dict()` | 序列化为 OB11 node 格式 |

### Forward

合并转发消息段。二选一：通过 `id` 引用已有转发，或通过 `content` 构建新转发。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `str?` | 引用已有转发的 ID |
| `content` | `List[ForwardNode]?` | 自定义转发节点列表 |

| 方法 | 说明 |
|------|------|
| `to_dict()` | 序列化为 OB11 forward 格式 |
| `to_forward_dict()` | 序列化为 `{"messages": [...]}` 格式 |
| `from_dict(data)` | 从 OB11 格式解析（classmethod） |

```python
# 引用已有转发
Forward(id="abc123")

# 构建新转发
Forward(content=[
    ForwardNode(user_id="123", nickname="Alice", content=[PlainText(text="hi")]),
    ForwardNode(user_id="456", nickname="Bob", content=[PlainText(text="hello")]),
])
```

### ForwardConstructor

便捷转发消息构造器，提供链式 API。

**导入：** `from ncatbot.types.qq import ForwardConstructor`

```python
fc = ForwardConstructor(user_id="123456", nickname="Bot")
fc.attach_text("第一条消息")
fc.attach_image("https://example.com/img.png")
fc.set_author("789", "另一个用户")
fc.attach_text("来自另一个用户的消息")
forward = fc.build()  # → Forward 对象
```

| 方法 | 说明 |
|------|------|
| `set_author(user_id, nickname)` | 更换后续消息的作者 |
| `attach(content, user_id?, nickname?)` | 添加 MessageArray 节点 |
| `attach_text(text, ...)` | 添加纯文本节点 |
| `attach_image(image, ...)` | 添加图片节点 |
| `attach_file(file, ...)` | 添加文件节点 |
| `attach_video(video, ...)` | 添加视频节点 |
| `attach_forward(forward, ...)` | 添加嵌套转发节点 |
| `build()` / `to_forward()` | 构建 `Forward` 对象 |

---

## CQ 码解析

```python
from ncatbot.types.qq import parse_cq_code_to_onebot11
```

| 函数 | 说明 |
|------|------|
| `parse_cq_code_to_onebot11(cq_str)` | CQ 码字符串 → OB11 格式 `List[dict]`，支持 HTML 反转义 |

---

## 继承关系

```
MessageSegment (common)
├── Face              _type="face"
├── Share             _type="share"
├── Location          _type="location"
├── Music             _type="music"
├── Json              _type="json"
├── Markdown          _type="markdown"
├── Forward           _type="forward"
├── Image (common)
│   └── QQImage       _type="image"  (覆盖注册)
└── Record (common)
    └── QQRecord      _type="record" (覆盖注册)
```

---

## 交叉引用

- [通用消息段](1_common_segments.md) — 跨平台基础段类型
- [MessageArray](2_message_array.md) — 消息段容器
- [消息发送指南](../../guide/send_message/) — 发送消息教程
