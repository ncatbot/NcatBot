# 消息构造与发送参考

> 参考文档：`guide/4. 消息发送/`、`reference/3. 数据类型/`

## 三种发送方式

### 方式 1：event.reply()

```python
await event.reply("Hello!")
await event.reply("看图", image="https://example.com/pic.jpg")
await event.reply("通知", at_sender=False)

msg = MessageArray().add_text("Hello ").add_image("pic.jpg")
await event.reply(rtf=msg)
```

**签名**：
```python
async def reply(
    self,
    text: Optional[str] = None,
    *,
    at: Optional[Union[str, int]] = None,
    image: Optional[Union[str, Image]] = None,
    video: Optional[Union[str, Video]] = None,
    rtf: Optional[MessageArray] = None,
    at_sender: bool = True,
) -> Any
```

### 方式 2：Sugar 方法

```python
# 群消息
await self.api.qq.post_group_msg(group_id, text="Hello", at=user_id)
await self.api.qq.send_group_text(group_id, "纯文本")
await self.api.qq.send_group_image(group_id, "https://example.com/pic.jpg")
await self.api.qq.send_group_video(group_id, "https://example.com/video.mp4")
await self.api.qq.send_group_record(group_id, "https://example.com/audio.mp3")
await self.api.qq.send_group_file(group_id, "/path/to/file.pdf", name="文档.pdf")
await self.api.qq.send_group_sticker(group_id, Image(file="sticker.gif", sub_type=1))

# 私聊消息
await self.api.qq.post_private_msg(user_id, text="Hello", image="pic.jpg")
await self.api.qq.send_private_text(user_id, "纯文本")
await self.api.qq.send_private_image(user_id, "https://example.com/pic.jpg")
```

### 方式 3：MessageArray

```python
from ncatbot.types import MessageArray, PlainText, Image, At, Reply

# 链式构造
msg = (
    MessageArray()
    .add_reply(message_id)
    .add_at(user_id)
    .add_text("看这张图：")
    .add_image("pic.jpg")
)
await self.api.qq.messaging.send_group_msg(group_id, msg.to_list())

# 直接构造
msg = MessageArray([
    PlainText(text="Hello "),
    At(user_id="123456"),
    Image(file="https://example.com/pic.jpg"),
])
await self.api.qq.messaging.send_group_msg(group_id, msg.to_list())
```

## 消息段类型速查

> 参考文档：`reference/3. 数据类型/1. 通用消息段.md`
>
> 5.2 起消息段分为 **通用**（`types.common.segment`）和 **QQ 平台**（`types.qq.segment`）两层，
> 但 `from ncatbot.types import ...` 的导入方式保持不变。

### 文本类（通用）

| 类名 | 构造 | 说明 |
|------|------|------|
| `PlainText` | `PlainText(text="内容")` | 纯文本 |
| `At` | `At(user_id="123456")` | @某人（user_id 为字符串或 `"all"`） |
| `Reply` | `Reply(id="msg_id")` | 引用消息 |

### 媒体类（通用）

| 类名 | 构造 | 说明 |
|------|------|------|
| `Image` | `Image(file="url或路径")` | 图片，`sub_type=1` 为表情包 |
| `Video` | `Video(file="url或路径")` | 视频 |
| `Record` | `Record(file="url或路径")` | 语音 |
| `File` | `File(file="路径")` | 文件 |

### QQ 平台

| 类名 | 构造 | 说明 |
|------|------|------|
| `Face` | `Face(id="123")` | QQ 表情 |
| `Share` | `Share(url="...", title="标题")` | 链接分享 |
| `Location` | `Location(lat=39.9, lon=116.3)` | 位置 |
| `Music` | `Music(type="qq", id="123")` | 音乐 |
| `Json` | `Json(data='{"key":"value"}')` | JSON 卡片 |
| `Markdown` | `Markdown(content="**bold**")` | Markdown |

### 转发类（QQ 平台）

| 类名 | 构造 | 说明 |
|------|------|------|
| `ForwardNode` | `ForwardNode(user_id="123", nickname="昵称", content=[...])` | 转发节点 |
| `Forward` | `Forward(id="msg_id")` 或 `Forward(content=[...])` | 合并转发 |

## MessageArray 方法速查

> 参考文档：`reference/3. 数据类型/2. 消息数组.md`

### 链式添加

| 方法 | 说明 |
|------|------|
| `add_text(text)` | 添加文本（支持 CQ 码解析） |
| `add_image(image)` | 添加图片 |
| `add_video(video)` | 添加视频 |
| `add_at(user_id)` | 添加 @ |
| `add_at_all()` | 添加 @全体 |
| `add_reply(message_id)` | 添加引用 |
| `add_segment(segment)` | 添加任意消息段 |

### 查询过滤

| 方法 | 返回 | 说明 |
|------|------|------|
| `text` (property) | `str` | 拼接所有纯文本 |
| `filter(cls)` | `List[T]` | 按类型过滤 |
| `filter_text()` / `filter_at()` / `filter_image()` / `filter_video()` | `List[T]` | 类型快捷过滤 |
| `is_at(user_id)` | `bool` | 是否 @了某人 |
| `is_forward_msg()` | `bool` | 是否包含转发 |

### 序列化

| 方法 | 说明 |
|------|------|
| `to_list()` | 序列化为 OB11 格式（传给 API） |
| `from_list(data)` | 从 OB11 列表反序列化 |
| `from_any(data)` | 从任意格式反序列化 |

## 合并转发

```python
# 方式 1：ForwardConstructor（推荐）
from ncatbot.types.qq import ForwardConstructor
fc = ForwardConstructor()
fc.add_message(user_id="123", nickname="用户A", content="第一条")
fc.add_message(user_id="123", nickname="用户A", content="第二条")
await self.api.qq.post_group_forward_msg(group_id, fc.build())

# 方式 2：按消息 ID 转发
await self.api.qq.send_group_forward_msg_by_id(group_id, [msg_id1, msg_id2])
```

## 从接收消息提取信息

```python
text = event.message.text                    # 纯文本
images = event.message.filter_image()        # 所有图片
if event.message.is_at(event.self_id):       # 是否 @了我
    ...
```

## GitHub 平台消息发送

> 参考文档：`guide/4. 消息发送/4. GitHub/`

GitHub 平台不使用 MessageArray 或消息段，消息以纯文本 / Markdown 发送。

### 通过事件回复

```python
from ncatbot.event.github import GitHubIssueEvent, GitHubPREvent

@registrar.github.on_issue()
async def on_issue(self, event: GitHubIssueEvent):
    await event.reply("感谢反馈！")          # 纯文本或 Markdown

@registrar.github.on_pr()
async def on_pr(self, event: GitHubPREvent):
    await event.reply("LGTM! :rocket:")     # 支持 GitHub emoji
```

### 通过 API 主动发送

```python
# Issue 评论
await self.api.github.create_issue_comment("owner/repo", 42, "已处理")

# PR 评论
await self.api.github.create_pr_comment("owner/repo", 10, "CI 通过")

# 编辑/删除评论
await self.api.github.update_comment("owner/repo", comment_id, "更新内容")
await self.api.github.delete_comment("owner/repo", comment_id)
```

### 与 QQ/Bilibili 的差异

| 特性 | QQ | Bilibili | GitHub |
|------|-----|----------|--------|
| 消息格式 | 富文本（消息段） | 纯文本 | 纯文本 / Markdown |
| At / 图片 / 视频 | ✅ | 部分 | ❌ |
| MessageArray | ✅ | — | — |
| `event.reply()` | ✅ | ✅ | ✅ |
| `event.delete()` | ✅ | ✅ | ✅（仅评论事件） |

## 常见陷阱

1. **file 参数**：支持 URL（`http://`）、base64（`base64://`）、本地路径（`file:///`）
2. **to_list()**：调用 API 时必须用 `msg.to_list()` 序列化
3. **add_text() 与 CQ 码**：会尝试解析 CQ 码，纯文本用 `add_segment(PlainText(text="..."))`
4. **At 的 qq 参数**：必须是字符串
5. **Forward 发送**：用 `post_group_forward_msg()`，不能用普通 `send_group_msg()`
