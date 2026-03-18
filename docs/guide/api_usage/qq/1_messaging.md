# 消息发送详解

> `BotAPIClient` 消息发送 API 的任务导向教程。完整参数表见 [reference/api/qq/1_message_api.md](../../../reference/api/qq/1_message_api.md)。

---

## 获取 API 客户端

| 方式 | 类型 | 场景 |
|------|------|------|
| `self.api.qq` | `QQAPIClient` | 插件中（推荐，含语法糖） |
| `event.reply()` | — | 最便捷的回复方式 |

---

## 常用发送方式

### 1. event.reply() — 一行回复

```python
await event.reply(text="pong!")  # 自动引用 + @发送者
```

### 2. post_group_msg — 关键字发送

```python
await self.api.qq.post_group_msg(event.group_id, text="Hello!", at=654321)
await self.api.qq.post_group_msg(event.group_id, text="看这个", reply=msg_id, image="img.png")
```

组装顺序：`reply → at → text → image → video → rtf`

### 3. MessageArray — 精细控制

```python
from ncatbot.types import MessageArray
msg = MessageArray().add_text("你好").add_image("img.png")
await self.api.qq.post_group_array_msg(event.group_id, msg)
```

### 4. 原子 API — OneBot v11 格式

```python
await self.api.qq.messaging.send_group_msg(123456, [{"type": "text", "data": {"text": "你好"}}])
```

---

## 合并转发

```python
from ncatbot.types import Forward
forward = Forward()
forward.add_message(user_id=10001, nickname="Bot", content="第一条")
await self.api.qq.post_group_forward_msg(group_id, forward)

# 或通过消息 ID 转发已有消息
await self.api.qq.send_group_forward_msg_by_id(group_id, [msg_id_1, msg_id_2])
```

---

## 撤回消息

```python
result = await self.api.qq.messaging.send_group_msg(group_id, message)
await self.api.qq.messaging.delete_msg(result["message_id"])

# 或直接撤回触发事件的消息
await event.delete()
```

---

## 延伸阅读

- [消息 API 完整参数表](../../../reference/api/qq/1_message_api.md) — 核心方法与 Sugar 方法签名
- [消息段参考](../../send_message/common/1_segments.md) — MessageSegment 类型
- [通用消息段](../../../reference/types/1_common_segments.md) — 通用段完整字段表
- [QQ 消息段](../../../reference/types/3_qq_segments.md) — QQ 专属段
- [群管理 API](2_manage.md) — 踢人、禁言等管理操作
| `group_id` | `str \| int` | 群号 |
| `user_id` | `str \| int` | 被戳的用户 QQ |

**示例**

```python
@registrar.on_group_command("戳我")
async def on_poke(self, event: GroupMessageEvent):
    await self.api.qq.messaging.send_poke(event.group_id, event.user_id)
```

---

## 语法糖方法

`QQAPIClient`（通过 `self.api.qq` 访问）继承了 `QQMessageSugarMixin`，提供 **关键字参数自动组装消息** 的便捷方法，无需手动构造 `message` 列表。

### post_group_msg — 便捷群消息

```python
async def post_group_msg(
    self,
    group_id: Union[str, int],
    text: Optional[str] = None,
    at: Optional[Union[str, int]] = None,
    reply: Optional[Union[str, int]] = None,
    image: Optional[Union[str, Image]] = None,
    video: Optional[Union[str, Video]] = None,
    rtf: Optional[MessageArray] = None,
) -> dict
```

所有关键字参数都是可选的，按需组合：

```python
# 发送纯文本
await self.api.qq.post_group_msg(group_id, text="Hello!")

# 发送文本 + @某人
await self.api.qq.post_group_msg(group_id, text="欢迎", at=user_id)

# 发送文本 + 图片
await self.api.qq.post_group_msg(group_id, text="看图", image="/path/to/img.jpg")

# 发送引用回复
await self.api.qq.post_group_msg(group_id, text="收到", reply=message_id)

# 发送自定义 MessageArray
msg = MessageArray()
msg.add_text("复杂消息")
msg.add_image("https://example.com/img.png")
await self.api.qq.post_group_msg(group_id, rtf=msg)
```

### post_private_msg — 便捷私聊消息

```python
async def post_private_msg(
    self,
    user_id: Union[str, int],
    text: Optional[str] = None,
    reply: Optional[Union[str, int]] = None,
    image: Optional[Union[str, Image]] = None,
    video: Optional[Union[str, Video]] = None,
    rtf: Optional[MessageArray] = None,
) -> dict
```

### 其他 sugar 方法速查

| 方法 | 说明 |
|------|------|
| `send_group_text(group_id, text)` | 发送群纯文本 |
| `send_group_image(group_id, image)` | 发送群图片 |
| `send_group_record(group_id, file)` | 发送群语音 |
| `send_group_file(group_id, file, name=None)` | 发送群文件消息 |
| `send_group_video(group_id, video)` | 发送群视频 |
| `send_group_sticker(group_id, image)` | 发送群动画表情 |
| `send_private_text(user_id, text)` | 发送私聊纯文本 |
| `send_private_image(user_id, image)` | 发送私聊图片 |
| `send_private_record(user_id, file)` | 发送私聊语音 |
| `send_private_file(user_id, file, name=None)` | 发送私聊文件消息 |
| `send_private_video(user_id, video)` | 发送私聊视频 |
| `send_private_sticker(user_id, image)` | 发送私聊动画表情 |
| `post_group_forward_msg(group_id, forward)` | 发送群合并转发（`Forward` 对象） |
| `post_private_forward_msg(user_id, forward)` | 发送私聊合并转发 |
| `send_group_forward_msg_by_id(group_id, message_ids)` | 通过消息 ID 列表转发群消息 |
| `send_private_forward_msg_by_id(user_id, message_ids)` | 通过消息 ID 列表转发私聊消息 |
| `post_group_array_msg(group_id, msg)` | 发送 `MessageArray` 群消息 |
| `post_private_array_msg(user_id, msg)` | 发送 `MessageArray` 私聊消息 |

---

> **返回**：[Bot API 使用指南](../README.md) · **相关**：[消息发送指南](../../send_message/README.md)
