# 消息 API — 核心方法与便捷方法

> 核心消息方法与 MessageSugarMixin 便捷方法（post_group_msg / post_private_msg）的完整参数表、返回值和示例。

---

## 核心消息方法

直接通过 `api.xxx()` 调用。底层对应 `IBotAPI` 抽象接口（源码：`ncatbot/api/interface.py`），由 `BotAPIClient`（源码：`ncatbot/api/client.py`）透传。

### send_group_msg()

```python
async def send_group_msg(
    self, group_id: Union[str, int], message: list, **kwargs
) -> dict:
```

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 目标群号 |
| message | list | 是 | 消息段列表（OneBot v11 格式） |
| **kwargs | Any | 否 | 扩展参数 |

**返回值**：`dict` — 包含 `message_id` 的响应字典

**OneBot v11 Action**：`send_group_msg`

```python
result = await api.send_group_msg(123456, [{"type": "text", "data": {"text": "hello"}}])
```

---

### send_private_msg()

```python
async def send_private_msg(
    self, user_id: Union[str, int], message: list, **kwargs
) -> dict:
```

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_id | str \| int | 是 | 目标用户 QQ 号 |
| message | list | 是 | 消息段列表（OneBot v11 格式） |
| **kwargs | Any | 否 | 扩展参数 |

**返回值**：`dict` — 包含 `message_id` 的响应字典

**OneBot v11 Action**：`send_private_msg`

---

### delete_msg()

```python
async def delete_msg(self, message_id: Union[str, int]) -> None:
```

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| message_id | str \| int | 是 | 要撤回的消息 ID |

**返回值**：无

**OneBot v11 Action**：`delete_msg`

```python
await api.delete_msg(msg_id)
```

---

### send_forward_msg()

```python
async def send_forward_msg(
    self, message_type: str, target_id: Union[str, int],
    messages: list, **kwargs,
) -> dict:
```

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| message_type | str | 是 | `"group"` 或 `"private"` |
| target_id | str \| int | 是 | 目标群号或用户 QQ 号 |
| messages | list | 是 | 合并转发消息节点列表 |
| **kwargs | Any | 否 | 扩展参数 |

**返回值**：`dict` — 响应字典

**OneBot v11 Action**：`send_forward_msg`

---

### send_poke()

```python
async def send_poke(
    self, group_id: Union[str, int], user_id: Union[str, int],
) -> None:
```

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 群号 |
| user_id | str \| int | 是 | 目标用户 QQ 号 |

**返回值**：无

**OneBot v11 Action**：`send_poke`（NapCat 扩展）

```python
await api.send_poke(group_id=123456, user_id=654321)
```

---

## MessageSugarMixin 便捷方法

> 源码：`ncatbot/api/_sugar.py`

`MessageSugarMixin` 以 Mixin 形式注入 `BotAPIClient`，提供关键字参数自动组装 `MessageArray` 的便捷方法。直接通过 `api.xxx()` 调用。

### post_group_msg()

```python
async def post_group_msg(
    self, group_id: Union[str, int],
    text: Optional[str] = None, at: Optional[Union[str, int]] = None,
    reply: Optional[Union[str, int]] = None,
    image: Optional[Union[str, Image]] = None,
    video: Optional[Union[str, Video]] = None,
    rtf: Optional[MessageArray] = None,
) -> dict:
```

**便捷群消息** — 组装顺序：reply → at → text → image → video → rtf。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 群号 |
| text | str \| None | 否 | 文本内容 |
| at | str \| int \| None | 否 | 要 @ 的用户 QQ 号 |
| reply | str \| int \| None | 否 | 要回复的消息 ID |
| image | str \| Image \| None | 否 | 图片路径/URL 或 `Image` 对象 |
| video | str \| Video \| None | 否 | 视频路径/URL 或 `Video` 对象 |
| rtf | MessageArray \| None | 否 | 自定义富文本消息数组（追加到末尾） |

**返回值**：`dict` — 包含 `message_id`

```python
# 发送文本
await api.post_group_msg(123456, text="Hello!")

# @某人并发送文本
await api.post_group_msg(123456, text="你好", at=654321)

# 回复消息并附图
await api.post_group_msg(123456, text="看这个", reply=msg_id, image="https://example.com/img.png")
```

---

### post_private_msg()

```python
async def post_private_msg(
    self, user_id: Union[str, int],
    text: Optional[str] = None,
    reply: Optional[Union[str, int]] = None,
    image: Optional[Union[str, Image]] = None,
    video: Optional[Union[str, Video]] = None,
    rtf: Optional[MessageArray] = None,
) -> dict:
```

**便捷私聊消息** — 用法与 `post_group_msg` 类似，但无 `at` 参数。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_id | str \| int | 是 | 目标用户 QQ 号 |
| text | str \| None | 否 | 文本内容 |
| reply | str \| int \| None | 否 | 要回复的消息 ID |
| image | str \| Image \| None | 否 | 图片路径/URL 或 `Image` 对象 |
| video | str \| Video \| None | 否 | 视频路径/URL 或 `Video` 对象 |
| rtf | MessageArray \| None | 否 | 自定义富文本消息数组 |

**返回值**：`dict` — 包含 `message_id`

---

### post_group_array_msg() / post_private_array_msg()

```python
async def post_group_array_msg(self, group_id: Union[str, int], msg: MessageArray) -> dict:
async def post_private_array_msg(self, user_id: Union[str, int], msg: MessageArray) -> dict:
```

直接发送 `MessageArray` 到群或私聊。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id / user_id | str \| int | 是 | 群号 / 用户 QQ 号 |
| msg | MessageArray | 是 | 消息数组 |

**返回值**：`dict` — 包含 `message_id`
