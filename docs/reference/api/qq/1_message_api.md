# 消息 API — 核心方法与便捷方法

> QQMessaging 核心消息方法 + QQMessageSugarMixin 便捷方法的完整参数表、返回值和示例。
>
> 核心方法通过 `api.qq.messaging.xxx()` 调用，Sugar 方法通过 `api.qq.xxx()` 调用。

---

## 核心消息方法

> 命名空间：`api.qq.messaging`（`QQMessaging`）

### send_group_msg()

```python
async def send_group_msg(
    self, group_id: Union[str, int], message: list, **kwargs
) -> SendMessageResult:
```

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 目标群号 |
| message | list | 是 | 消息段列表（OneBot v11 格式） |

**返回值**：`SendMessageResult` — 包含 `message_id: str`

### send_private_msg()

```python
async def send_private_msg(
    self, user_id: Union[str, int], message: list, **kwargs
) -> SendMessageResult:
```

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_id | str \| int | 是 | 目标用户 QQ 号 |
| message | list | 是 | 消息段列表 |

### delete_msg()

```python
async def delete_msg(self, message_id: Union[str, int]) -> None:
```

撤回消息。**OneBot v11 Action**：`delete_msg`

### send_forward_msg()

```python
async def send_forward_msg(
    self, message_type: str, target_id: Union[str, int],
    messages: list, **kwargs,
) -> SendMessageResult:
```

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| message_type | str | 是 | `"group"` 或 `"private"` |
| target_id | str \| int | 是 | 目标群号或用户 QQ 号 |
| messages | list | 是 | 合并转发消息节点列表 |

### send_poke()

```python
async def send_poke(
    self, group_id: Union[str, int], user_id: Union[str, int],
) -> None:
```

戳一戳（NapCat 扩展）。

### friend_poke()

```python
async def friend_poke(self, user_id: Union[str, int]) -> None:
```

私聊戳一戳。

### send_like()

```python
async def send_like(self, user_id: Union[str, int], times: int = 1) -> None:
```

给用户点赞。`times` 为点赞次数，默认 `1`。

### set_msg_emoji_like()

```python
async def set_msg_emoji_like(
    self, message_id: Union[str, int], emoji_id: str, set: bool = True,
) -> None:
```

对消息设置/取消表情回应。`emoji_id` 为 QQ 表情 ID，`set=False` 取消。

### mark_group_msg_as_read() / mark_private_msg_as_read() / mark_all_as_read()

```python
async def mark_group_msg_as_read(self, group_id: Union[str, int]) -> None:
async def mark_private_msg_as_read(self, user_id: Union[str, int]) -> None:
async def mark_all_as_read(self) -> None:
```

标记群/私聊/全部消息为已读。

### forward_friend_single_msg() / forward_group_single_msg()

```python
async def forward_friend_single_msg(self, user_id: Union[str, int], message_id: Union[str, int]) -> None:
async def forward_group_single_msg(self, group_id: Union[str, int], message_id: Union[str, int]) -> None:
```

逐条转发单条消息到好友/群。

### get_group_msg_history() / get_friend_msg_history()

```python
async def get_group_msg_history(
    self, group_id: Union[str, int], message_seq: Optional[int] = None, count: int = 20,
) -> MessageHistory:
async def get_friend_msg_history(
    self, user_id: Union[str, int], message_seq: Optional[int] = None, count: int = 20,
) -> MessageHistory:
```

获取群/好友消息历史。`message_seq` 为起始消息序号，`count` 为拉取条数。

---

## QQMessageSugarMixin 便捷方法

> 通过 `api.qq.xxx()` 直接调用（QQAPIClient 继承了 QQMessageSugarMixin）。

### post_group_msg()

```python
async def post_group_msg(
    self, group_id, text=None, at=None, reply=None, image=None, video=None, rtf=None,
) -> SendMessageResult:
```

**便捷群消息** — 组装顺序：reply → at → text → image → video → rtf。

| 参数 | 类型 | 说明 |
|---|---|---|
| text | str \| None | 文本内容 |
| at | str \| int \| None | 要 @ 的用户 QQ 号 |
| reply | str \| int \| None | 要回复的消息 ID |
| image | str \| Image \| None | 图片路径/URL |
| video | str \| Video \| None | 视频路径/URL |
| rtf | MessageArray \| None | 自定义富文本消息数组 |

### post_private_msg()

用法与 `post_group_msg` 类似，但无 `at` 参数。

### post_group_array_msg() / post_private_array_msg()

```python
async def post_group_array_msg(self, group_id, msg: MessageArray) -> SendMessageResult:
async def post_private_array_msg(self, user_id, msg: MessageArray) -> SendMessageResult:
```

---

## 群消息 Sugar

| 方法 | 签名 | 说明 |
|------|------|------|
| `send_group_text` | `(group_id, text)` | 群纯文本 |
| `send_group_plain_text` | `(group_id, text)` | PlainText 段群文本 |
| `send_group_image` | `(group_id, image)` | 群图片 |
| `send_group_record` | `(group_id, file)` | 群语音 |
| `send_group_file` | `(group_id, file, name=None)` | 群文件 |
| `send_group_video` | `(group_id, video)` | 群视频 |
| `send_group_sticker` | `(group_id, image)` | 群动画表情 |

## 私聊消息 Sugar

| 方法 | 签名 | 说明 |
|------|------|------|
| `send_private_text` | `(user_id, text)` | 私聊纯文本 |
| `send_private_plain_text` | `(user_id, text)` | PlainText 段私聊文本 |
| `send_private_image` | `(user_id, image)` | 私聊图片 |
| `send_private_record` | `(user_id, file)` | 私聊语音 |
| `send_private_file` | `(user_id, file, name=None)` | 私聊文件 |
| `send_private_video` | `(user_id, video)` | 私聊视频 |
| `send_private_sticker` | `(user_id, image)` | 私聊动画表情 |
| `send_private_dice` | `(user_id, value=1)` | 骰子魔法表情 |
| `send_private_rps` | `(user_id, value=1)` | 猜拳魔法表情 |

## 合并转发 Sugar

| 方法 | 签名 | 说明 |
|------|------|------|
| `post_group_forward_msg` | `(group_id, forward: Forward)` | 群合并转发 |
| `post_private_forward_msg` | `(user_id, forward: Forward)` | 私聊合并转发 |
| `send_group_forward_msg_by_id` | `(group_id, message_ids: List)` | 通过消息 ID 逐条转发 |

所有方法返回 `SendMessageResult`（含 `message_id`）。
