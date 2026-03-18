# 便捷接口参考

> `event.reply()`、`MessageSugarMixin` 全部方法、`send_poke` 的完整清单。

---

## 目录

- [event.reply() — 快速回复](#eventreply--快速回复)
- [便捷发送 — 关键字组装](#便捷发送--关键字组装)
- [直接发送 MessageArray](#直接发送-messagearray)
- [类型专用发送 — 群消息](#类型专用发送--群消息)
- [类型专用发送 — 私聊消息](#类型专用发送--私聊消息)
- [合并转发发送](#合并转发发送)
- [其他 — 戳一戳](#其他--戳一戳)

---

## event.reply() — 快速回复

在事件处理器中最便捷的回复方式，自动引用原消息。

```python
async def reply(
    self,
    text: str | None = None,
    *,
    at: str | int | None = None,
    image: str | Image | None = None,
    video: str | Video | None = None,
    rtf: MessageArray | None = None,
    at_sender: bool = True,
) -> Any
```

**行为：**
- 自动添加 `Reply`（引用原消息 ID）
- 群聊时默认 `@发送者`（`at_sender=True`）
- 私聊时只引用不 @
- 组装顺序：`reply → @sender → text → at → image → video → rtf`

```python
await event.reply(text="收到！")
await event.reply(text="看图", image="https://example.com/img.png")
await event.reply(text="不 @你", at_sender=False)
```

---

## 便捷发送 — 关键字组装

`post_group_msg` / `post_private_msg` 接受关键字参数，自动组装 `MessageArray`。

### post_group_msg

```python
async def post_group_msg(
    self,
    group_id: str | int,
    text: str | None = None,
    at: str | int | None = None,
    reply: str | int | None = None,
    image: str | Image | None = None,
    video: str | Video | None = None,
    rtf: MessageArray | None = None,
) -> dict
```

### post_private_msg

```python
async def post_private_msg(
    self,
    user_id: str | int,
    text: str | None = None,
    reply: str | int | None = None,
    image: str | Image | None = None,
    video: str | Video | None = None,
    rtf: MessageArray | None = None,
) -> dict
```

**组装顺序：** `reply → at → text → image → video → rtf`

```python
await self.api.qq.post_group_msg(gid, text="你好！", at=uid, reply=mid)
await self.api.qq.post_private_msg(uid, text="Hi", image="a.png")
```

> 如果需要更复杂的组合，使用 `rtf` 参数传入完整的 `MessageArray`。

---

## 直接发送 MessageArray

| 方法 | 说明 |
|---|---|
| `post_group_array_msg(group_id, msg)` | 发送群 MessageArray |
| `post_private_array_msg(user_id, msg)` | 发送私聊 MessageArray |

```python
msg = MessageArray().add_text("Hello").add_image("a.png")
await self.api.qq.post_group_array_msg(group_id, msg)
await self.api.qq.post_private_array_msg(user_id, msg)
```

---

## 类型专用发送 — 群消息

| 方法 | 参数 | 说明 |
|---|---|---|
| `send_group_text(group_id, text)` | `text: str` | 发送文本（CQ 码会被解析） |
| `send_group_plain_text(group_id, text)` | `text: str` | 发送纯文本（原样发送，不解析 CQ 码） |
| `send_group_image(group_id, image)` | `image: str \| Image` | 发送图片 |
| `send_group_record(group_id, file)` | `file: str` | 发送语音 |
| `send_group_video(group_id, video)` | `video: str \| Video` | 发送视频 |
| `send_group_file(group_id, file, name?)` | `file: str`, `name: str?` | 发送文件 |
| `send_group_sticker(group_id, image)` | `image: str \| Image` | 发送动画表情（sub_type=1） |

```python
await self.api.qq.send_group_text(gid, "Hello!")
await self.api.qq.send_group_plain_text(gid, "[CQ:at,qq=all] 这不会被解析")
await self.api.qq.send_group_image(gid, "https://example.com/img.png")
await self.api.qq.send_group_record(gid, "https://example.com/voice.silk")
await self.api.qq.send_group_video(gid, str(video_path))
await self.api.qq.send_group_file(gid, "https://example.com/doc.pdf", name="文档.pdf")
await self.api.qq.send_group_sticker(gid, str(image_path))
```

---

## 类型专用发送 — 私聊消息

| 方法 | 参数 | 说明 |
|---|---|---|
| `send_private_text(user_id, text)` | `text: str` | 发送文本 |
| `send_private_plain_text(user_id, text)` | `text: str` | 发送纯文本 |
| `send_private_image(user_id, image)` | `image: str \| Image` | 发送图片 |
| `send_private_record(user_id, file)` | `file: str` | 发送语音 |
| `send_private_video(user_id, video)` | `video: str \| Video` | 发送视频 |
| `send_private_file(user_id, file, name?)` | `file: str`, `name: str?` | 发送文件 |
| `send_private_sticker(user_id, image)` | `image: str \| Image` | 发送动画表情 |
| `send_private_dice(user_id, value?)` | `value: int = 1` | 发送骰子 |
| `send_private_rps(user_id, value?)` | `value: int = 1` | 发送猜拳 |

```python
await self.api.qq.send_private_text(uid, "你好")
await self.api.qq.send_private_image(uid, "a.png")
await self.api.qq.send_private_video(uid, "video.mp4")
await self.api.qq.send_private_file(uid, "doc.pdf", name="文档.pdf")
await self.api.qq.send_private_sticker(uid, "sticker.gif")
await self.api.qq.send_private_dice(uid, value=3)
await self.api.qq.send_private_rps(uid, value=2)
```

---

## 合并转发发送

| 方法 | 参数 | 说明 |
|---|---|---|
| `post_group_forward_msg(group_id, forward)` | `forward: Forward` | 发送群合并转发 |
| `post_private_forward_msg(user_id, forward)` | `forward: Forward` | 发送私聊合并转发 |
| `send_group_forward_msg_by_id(group_id, message_ids)` | `message_ids: List[str \| int]` | 通过消息 ID 逐条转发到群 |
| `send_private_forward_msg_by_id(user_id, message_ids)` | `message_ids: List[str \| int]` | 通过消息 ID 逐条转发到私聊 |

> 详见 [2_forward.md](2_forward.md)

---

## 其他 — 戳一戳

```python
async def send_poke(self, group_id: str | int, user_id: str | int) -> None
```

在群内戳指定用户：

```python
await self.api.qq.send_poke(event.group_id, event.user_id)
```

---

[← 上一篇：合并转发](2_forward.md) | [返回目录](../README.md) | [下一篇：实战示例 →](3_examples.md)
