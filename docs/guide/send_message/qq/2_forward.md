# 合并转发

> `ForwardNode` 转发节点、`Forward` 合并转发消息段，以及 `ForwardConstructor` 便捷构造器。

---

## 目录

- [ForwardNode — 转发节点](#forwardnode--转发节点)
- [Forward — 合并转发](#forward--合并转发)
- [ForwardConstructor — 便捷构造器](#forwardconstructor--便捷构造器)
- [嵌套合并转发](#嵌套合并转发)
- [发送合并转发](#发送合并转发)

---

## ForwardNode — 转发节点

`ForwardNode` 代表合并转发中的单条消息。它不是 `MessageSegment` 的子类，而是独立的 Pydantic `BaseModel`。

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | `str` | ✅ | 发送者 QQ（自动转为字符串） |
| `nickname` | `str` | ✅ | 发送者昵称（合并转发中的显示名） |
| `content` | `List[MessageSegment]` | ✅ | 消息内容（可包含多个消息段） |

`content` 字段支持传入 OB11 字典列表，会自动解析为 `MessageSegment` 对象。

```python
from ncatbot.types import ForwardNode, PlainText, Image

node = ForwardNode(
    user_id="123456",
    nickname="小明",
    content=[PlainText(text="这是转发的第一条消息")],
)

# 也可以传入字典列表
node = ForwardNode(
    user_id=123456,
    nickname="小明",
    content=[
        {"type": "text", "data": {"text": "Hello"}},
        {"type": "image", "data": {"file": "https://example.com/img.png"}},
    ],
)
```

---

## Forward — 合并转发

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | `str?` | ❌ | 转发消息 ID（引用已有的合并转发） |
| `content` | `List[ForwardNode]?` | ❌ | 转发节点列表（构造新的合并转发） |

### 方式一：引用已有的合并转发（通过 `id`）

```python
from ncatbot.types import Forward

fwd = Forward(id="abc123")
```

### 方式二：构造新的合并转发（通过 `content`）

```python
from ncatbot.types import Forward, ForwardNode, PlainText, Image

fwd = Forward(content=[
    ForwardNode(
        user_id="123456",
        nickname="小明",
        content=[PlainText(text="第一条消息")],
    ),
    ForwardNode(
        user_id="654321",
        nickname="小红",
        content=[
            PlainText(text="带图片的消息"),
            Image(file="https://example.com/img.png"),
        ],
    ),
])
```

---

## ForwardConstructor — 便捷构造器

手动创建 `ForwardNode` 列表比较繁琐，`ForwardConstructor` 提供快捷方式：

```python
from ncatbot.types import ForwardConstructor
```

### 构造方法

| 方法 | 参数 | 说明 |
|---|---|---|
| `__init__(user_id, nickname)` | 默认 `"123456"`, `"QQ用户"` | 初始化，设置默认作者信息 |
| `set_author(user_id, nickname)` | — | 修改后续消息的默认作者 |
| `attach(content, user_id?, nickname?)` | `content: MessageArray` | 添加一条消息节点 |
| `attach_message(message, ...)` | `message: MessageArray` | 同 `attach` |
| `attach_text(text, ...)` | `text: str` | 添加一条纯文本消息 |
| `attach_image(image, ...)` | `image: str` | 添加一条图片消息 |
| `attach_file(file, ...)` | `file: str` | 添加一条文件消息 |
| `attach_video(video, ...)` | `video: str` | 添加一条视频消息 |
| `attach_forward(forward, ...)` | `forward: Forward` | 添加一条嵌套转发 |
| `build()` | — | 构建并返回 `Forward` 对象 |

> 所有 `attach_*` 方法都接受可选的 `user_id` 和 `nickname` 参数覆盖默认作者。

### 基本用法

```python
from ncatbot.types import ForwardConstructor, MessageArray

fc = ForwardConstructor(user_id=str(event.self_id), nickname="Bot")

fc.attach_text("这是转发消息的第一条 📝")
fc.attach_text("这是转发消息的第二条 📝")

# 图文混合节点
msg = MessageArray()
msg.add_text("这条包含图片: ")
msg.add_image(str(EXAMPLE_IMAGE))
fc.attach_message(msg)

forward = fc.build()
await self.api.qq.post_group_forward_msg(event.group_id, forward)
```

### 切换作者

```python
fc = ForwardConstructor(user_id="111", nickname="Alice")
fc.attach_text("Alice 说的话")

fc.set_author("222", "Bob")
fc.attach_text("Bob 说的话")

# 或在 attach 时临时指定
fc.attach_text("Charlie 客串", user_id="333", nickname="Charlie")
```

---

## 嵌套合并转发

通过 `attach_forward` 可以实现转发套转发：

```python
bot_id = str(event.self_id)

# 构造内层转发
inner_fc = ForwardConstructor(user_id=bot_id, nickname="Bot 内层")
inner_fc.attach_text("🔹 内层第一条消息")
inner_fc.attach_text("🔹 内层第二条消息")
inner_forward = inner_fc.build()

# 构造外层转发，嵌套内层
outer_fc = ForwardConstructor(user_id=bot_id, nickname="Bot")
outer_fc.attach_text("🔸 外层第一条消息")
outer_fc.attach_forward(inner_forward)  # 嵌套内层转发
outer_fc.attach_text("🔸 外层第三条消息（在嵌套转发之后）")

forward = outer_fc.build()
await self.api.qq.post_group_forward_msg(event.group_id, forward)
```

---

## 发送合并转发

| 方法 | 说明 |
|---|---|
| `post_group_forward_msg(group_id, forward)` | 发送群合并转发 |
| `post_private_forward_msg(user_id, forward)` | 发送私聊合并转发 |
| `send_group_forward_msg_by_id(group_id, message_ids)` | 通过消息 ID 列表逐条转发到群 |
| `send_private_forward_msg_by_id(user_id, message_ids)` | 通过消息 ID 列表逐条转发到私聊 |

```python
# 发送构造的合并转发
await self.api.qq.post_group_forward_msg(group_id, forward)

# 通过消息 ID 转发已有消息
await self.api.qq.send_group_forward_msg_by_id(group_id, [msg_id_1, msg_id_2])
```

---

[← 上一篇：MessageArray](../common/2_array.md) | [返回目录](../README.md) | [下一篇：便捷接口 →](1_sugar.md)
