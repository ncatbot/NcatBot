# 消息发送详解

> 本文档详细介绍 `BotAPIClient` 的消息发送 API — 参数说明、返回值与完整示例。
>
> 消息段的构造细节（`MessageArray`、`PlainText`、`Image` 等）请参阅 [消息发送指南](../send_message/README.md)。

---

## 获取 API 客户端

### 在插件中：self.api

继承 `NcatBotPlugin` 的插件实例会在加载时由框架自动注入 `self.api`，类型为 `BotAPIClient`。

```python
from ncatbot.plugin import NcatBotPlugin
from ncatbot.core.registry import registrar
from ncatbot.event import GroupMessageEvent


class MyPlugin(NcatBotPlugin):
    name = "my_plugin"
    version = "1.0.0"

    @registrar.on_group_command("ping")
    async def on_ping(self, event: GroupMessageEvent):
        # self.api 是 BotAPIClient 实例
        await self.api.post_group_msg(event.group_id, text="pong!")
```

### 在事件处理器中：event.api

每个事件对象都持有一个 `api` 属性（类型为 `IBotAPI`），可直接调用底层接口。但推荐优先使用 `self.api`，因为它提供语法糖和自动日志。

```python
@registrar.on_group_command("ping")
async def on_ping(self, event: GroupMessageEvent):
    # event.api 是 IBotAPI 实例（底层接口）
    await event.api.send_group_msg(event.group_id, [{"type": "text", "data": {"text": "pong!"}}])

    # 更推荐 — 使用 self.api 的语法糖
    await self.api.post_group_msg(event.group_id, text="pong!")
```

> **提示**：`event.reply()` 是最便捷的回复方式，内部自动引用原消息并 @发送者。

```python
await event.reply(text="pong!")
```

---

## send_group_msg — 发送群消息

```python
async def send_group_msg(
    self,
    group_id: Union[str, int],
    message: list,
    **kwargs,
) -> dict
```

**参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| `group_id` | `str \| int` | 群号 |
| `message` | `list` | 消息段列表（OneBot v11 格式） |

**返回值**：`dict`，包含 `message_id` 等字段。

**示例**

```python
from ncatbot.types import MessageArray, PlainText, Image

# 方式 1：原子 API — 手动构造消息段列表
result = await self.api.send_group_msg(
    group_id=123456,
    message=[{"type": "text", "data": {"text": "你好"}}],
)
print(f"消息 ID: {result.get('message_id')}")

# 方式 2：通过 MessageArray 构造
msg = MessageArray([PlainText(text="你好")])
result = await self.api.send_group_msg(123456, msg.to_list())
```

> **推荐**：对于简单消息，使用语法糖 `post_group_msg` 更方便，见 [语法糖方法](#语法糖方法)。

---

## send_private_msg — 发送私聊消息

```python
async def send_private_msg(
    self,
    user_id: Union[str, int],
    message: list,
    **kwargs,
) -> dict
```

**参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| `user_id` | `str \| int` | 对方 QQ 号 |
| `message` | `list` | 消息段列表 |

**示例**

```python
await self.api.send_private_msg(
    user_id=654321,
    message=[{"type": "text", "data": {"text": "私聊消息"}}],
)
```

---

## send_forward_msg — 发送合并转发

```python
async def send_forward_msg(
    self,
    message_type: str,       # "group" 或 "private"
    target_id: Union[str, int],  # 群号或用户 QQ
    messages: list,           # 转发节点列表
    **kwargs,
) -> dict
```

**参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| `message_type` | `str` | `"group"` 或 `"private"` |
| `target_id` | `str \| int` | 目标群号或 QQ 号 |
| `messages` | `list` | 转发消息节点列表 |

**示例**

```python
from ncatbot.types import Forward

# 使用 Forward 辅助类构造合并转发
forward = Forward()
forward.add_message(user_id=10001, nickname="Bot", content="第一条消息")
forward.add_message(user_id=10001, nickname="Bot", content="第二条消息")

# 语法糖方式
await self.api.post_group_forward_msg(group_id, forward)

# 或通过消息 ID 转发已有消息
await self.api.send_group_forward_msg_by_id(group_id, [msg_id_1, msg_id_2])
```

---

## delete_msg — 撤回消息

```python
async def delete_msg(self, message_id: Union[str, int]) -> None
```

**参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| `message_id` | `str \| int` | 要撤回的消息 ID |

**示例**

```python
# 发送后撤回
result = await self.api.send_group_msg(group_id, message)
await asyncio.sleep(5)
await self.api.delete_msg(result["message_id"])
```

> MessageEvent 还提供便捷的 `event.delete()` 方法，用于撤回触发事件的那条消息。

---

## send_poke — 戳一戳

```python
async def send_poke(
    self,
    group_id: Union[str, int],
    user_id: Union[str, int],
) -> None
```

**参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| `group_id` | `str \| int` | 群号 |
| `user_id` | `str \| int` | 被戳的用户 QQ |

**示例**

```python
@registrar.on_group_command("戳我")
async def on_poke(self, event: GroupMessageEvent):
    await self.api.send_poke(event.group_id, event.user_id)
```

---

## 语法糖方法

`BotAPIClient` 继承了 `MessageSugarMixin`，提供 **关键字参数自动组装消息** 的便捷方法，无需手动构造 `message` 列表。

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
await self.api.post_group_msg(group_id, text="Hello!")

# 发送文本 + @某人
await self.api.post_group_msg(group_id, text="欢迎", at=user_id)

# 发送文本 + 图片
await self.api.post_group_msg(group_id, text="看图", image="/path/to/img.jpg")

# 发送引用回复
await self.api.post_group_msg(group_id, text="收到", reply=message_id)

# 发送自定义 MessageArray
msg = MessageArray()
msg.add_text("复杂消息")
msg.add_image("https://example.com/img.png")
await self.api.post_group_msg(group_id, rtf=msg)
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

> **返回**：[Bot API 使用指南](README.md) · **相关**：[消息发送指南](../send_message/README.md)
