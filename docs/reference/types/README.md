# 类型参考

> 消息段、消息数组等数据类型完整参考。

---

## Quick Start

3 行代码构造一条包含文本、@、图片的消息：

```python
from ncatbot.types import MessageArray, PlainText, At, Image

# 链式构造
msg = MessageArray().add_text("你好 ").add_at(123456).add_image("https://example.com/img.png")

# 等价写法：直接组合消息段
msg = MessageArray([PlainText(text="你好 "), At(qq="123456"), Image(file="https://example.com/img.png")])
```

在事件处理器中使用：

```python
@bot.on_message()
async def handler(event):
    # 提取纯文本
    text = event.message.text

    # 过滤出所有图片
    images = event.message.filter_image()

    # 检查是否 @了 bot
    if event.message.is_at(bot.self_id):
        reply = MessageArray().add_text("收到！")
        await bot.api.send_group_msg(group_id=event.group_id, message=reply)
```

---

## 消息段类型速查表

所有消息段继承自 `MessageSegment`（位于 `ncatbot.types`），通过 `_type` 注册到 `SEGMENT_MAP`。

### 文本类

| 类名 | `_type` | 构造签名 | 说明 |
|---|---|---|---|
| `PlainText` | `"text"` | `PlainText(text="...")` | 纯文本 |
| `Face` | `"face"` | `Face(id="123")` | QQ 表情 |
| `At` | `"at"` | `At(qq="123456")` / `At(qq="all")` | @某人 / @全体 |
| `Reply` | `"reply"` | `Reply(id="msg_id")` | 引用回复 |

### 媒体类

基类 `DownloadableSegment` 提供通用字段：`file`（必需）、`url`、`file_id`、`file_size`、`file_name`（均可选）。

| 类名 | `_type` | 构造签名 | 说明 |
|---|---|---|---|
| `Image` | `"image"` | `Image(file="url_or_path")` | 图片 |
| `Record` | `"record"` | `Record(file="url_or_path")` | 语音 |
| `Video` | `"video"` | `Video(file="url_or_path")` | 视频 |
| `File` | `"file"` | `File(file="url_or_path")` | 文件 |

### 富文本类

| 类名 | `_type` | 构造签名 | 说明 |
|---|---|---|---|
| `Share` | `"share"` | `Share(url="...", title="...")` | 链接分享 |
| `Location` | `"location"` | `Location(lat=39.9, lon=116.3)` | 位置 |
| `Music` | `"music"` | `Music(type="qq", id="123")` | 音乐 |
| `Json` | `"json"` | `Json(data='{"key":"val"}')` | JSON 消息 |
| `Markdown` | `"markdown"` | `Markdown(content="# 标题")` | Markdown 消息 |

### 转发类

| 类名 | `_type` | 构造签名 | 说明 |
|---|---|---|---|
| `Forward` | `"forward"` | `Forward(id="...")` / `Forward(content=[...])` | 合并转发 |
| `ForwardNode` | — | `ForwardNode(user_id="...", nickname="...", content=[...])` | 转发节点 |
| `ForwardConstructor` | — | `ForwardConstructor(user_id="...", nickname="...")` | 转发构造器 |

> 完整属性表与构造示例见 [1_segments.md](1_segments.md)。

---

## MessageArray 方法速查

`MessageArray` 是消息段数组的容器，支持链式构造、类型过滤和序列化。

### 创建

| 方法 | 签名 | 说明 |
|---|---|---|
| 构造函数 | `MessageArray(segments: List[MessageSegment] = None)` | 从消息段列表创建 |
| `from_list` | `MessageArray.from_list(data: List[Dict]) -> MessageArray` | 从 OB11 字典列表创建 |
| `from_any` | `MessageArray.from_any(data: Any) -> MessageArray` | 从任意输入创建（列表 / CQ 码 / 消息段） |

### 链式构造

| 方法 | 签名 | 说明 |
|---|---|---|
| `add_text` | `add_text(text: str) -> MessageArray` | 追加纯文本（支持 CQ 码自动解析） |
| `add_image` | `add_image(image: str \| Image) -> MessageArray` | 追加图片 |
| `add_video` | `add_video(video: str \| Video) -> MessageArray` | 追加视频 |
| `add_at` | `add_at(user_id: str \| int) -> MessageArray` | 追加 @某人 |
| `add_at_all` | `add_at_all() -> MessageArray` | 追加 @全体 |
| `add_reply` | `add_reply(message_id: str \| int) -> MessageArray` | 追加引用回复 |
| `add_segment` | `add_segment(segment: MessageSegment) -> MessageArray` | 追加任意消息段 |
| `add_segments` | `add_segments(data: Any) -> MessageArray` | 追加任意输入 |

### 查询与过滤

| 方法 / 属性 | 签名 | 说明 |
|---|---|---|
| `text` | `@property text -> str` | 所有纯文本拼接 |
| `filter` | `filter(cls: Type[T] = None) -> List[T]` | 按类型过滤消息段 |
| `filter_text` | `filter_text() -> List[PlainText]` | 过滤纯文本段 |
| `filter_at` | `filter_at() -> List[At]` | 过滤 @段 |
| `filter_image` | `filter_image() -> List[Image]` | 过滤图片段 |
| `filter_video` | `filter_video() -> List[Video]` | 过滤视频段 |
| `filter_face` | `filter_face() -> List[Face]` | 过滤表情段 |
| `is_at` | `is_at(user_id, all_except=False) -> bool` | 是否 @了指定用户 |
| `is_forward_msg` | `is_forward_msg() -> bool` | 是否包含转发消息 |

### 序列化与容器

| 方法 | 签名 | 说明 |
|---|---|---|
| `to_list` | `to_list() -> List[Dict]` | 序列化为 OB11 字典列表 |
| `__len__` | `len(msg)` | 消息段数量 |
| `__iter__` | `for seg in msg` | 迭代消息段 |
| `__add__` | `msg + other` | 拼接（返回新 MessageArray） |
| `__radd__` | `other + msg` | 反向拼接 |

> 完整方法详解与高级用法见 [2_message_array.md](2_message_array.md)。

---

## 深入阅读

| 文档 | 内容 |
|---|---|
| [消息段类型详解](1_segments.md) | 每个消息段的完整属性表、验证规则、构造示例 |
| [MessageArray 详解](2_message_array.md) | MessageArray 完整方法详解、高级用法、Pydantic 集成 |

**相关参考：**

- 原始类型参考（枚举、事件模型等）：[types.md](../types.md)
- 插件开发指南：[guide/plugin/](../../guide/plugin/README.md)
