# 消息 API — Sugar 快捷方法

> 群消息 / 私聊消息 / 合并转发的各类 Sugar 快捷方法参数一览。

---

## 群消息 Sugar

以下方法均通过 `api.xxx()` 调用，内部委托 `post_group_msg` 或 `post_group_array_msg`。

### send_group_text()

```python
async def send_group_text(self, group_id: Union[str, int], text: str) -> dict:
```

发送群纯文本消息。

---

### send_group_plain_text()

```python
async def send_group_plain_text(self, group_id: Union[str, int], text: str) -> dict:
```

使用 `PlainText` 消息段发送群纯文本。

---

### send_group_image()

```python
async def send_group_image(self, group_id: Union[str, int], image: Union[str, Image]) -> dict:
```

发送群图片。`image` 可以是路径/URL 字符串或 `Image` 对象。

```python
await api.send_group_image(123456, "https://example.com/img.png")
```

---

### send_group_record()

```python
async def send_group_record(self, group_id: Union[str, int], file: str) -> dict:
```

发送群语音。`file` 为语音文件路径或 URL。

---

### send_group_file()

```python
async def send_group_file(
    self, group_id: Union[str, int], file: str, name: Optional[str] = None,
) -> dict:
```

以消息形式发送群文件。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 群号 |
| file | str | 是 | 文件路径或 URL |
| name | str \| None | 否 | 文件名 |

---

### send_group_video()

```python
async def send_group_video(self, group_id: Union[str, int], video: Union[str, Video]) -> dict:
```

发送群视频。`video` 可以是路径/URL 字符串或 `Video` 对象。

---

### send_group_sticker()

```python
async def send_group_sticker(self, group_id: Union[str, int], image: Union[str, Image]) -> dict:
```

发送群动画表情（`sub_type=1` 的图片）。

---

## 私聊消息 Sugar

以下方法均通过 `api.xxx()` 调用，用法与群消息 Sugar 对称。

### send_private_text() / send_private_plain_text()

```python
async def send_private_text(self, user_id: Union[str, int], text: str) -> dict:
async def send_private_plain_text(self, user_id: Union[str, int], text: str) -> dict:
```

发送私聊纯文本 / 使用 `PlainText` 段发送私聊文本。

---

### send_private_image()

```python
async def send_private_image(self, user_id: Union[str, int], image: Union[str, Image]) -> dict:
```

发送私聊图片。

---

### send_private_record()

```python
async def send_private_record(self, user_id: Union[str, int], file: str) -> dict:
```

发送私聊语音。

---

### send_private_file()

```python
async def send_private_file(
    self, user_id: Union[str, int], file: str, name: Optional[str] = None,
) -> dict:
```

以消息形式发送私聊文件。

---

### send_private_video()

```python
async def send_private_video(self, user_id: Union[str, int], video: Union[str, Video]) -> dict:
```

发送私聊视频。

---

### send_private_sticker()

```python
async def send_private_sticker(self, user_id: Union[str, int], image: Union[str, Image]) -> dict:
```

发送私聊动画表情（`sub_type=1` 的图片）。

---

### send_private_dice()

```python
async def send_private_dice(self, user_id: Union[str, int], value: int = 1) -> dict:
```

发送骰子魔法表情。`value` 为骰子点数，默认 `1`。

---

### send_private_rps()

```python
async def send_private_rps(self, user_id: Union[str, int], value: int = 1) -> dict:
```

发送猜拳魔法表情。`value` 为猜拳值，默认 `1`。

---

## 合并转发 Sugar

### post_group_forward_msg()

```python
async def post_group_forward_msg(
    self, group_id: Union[str, int], forward: Forward,
) -> dict:
```

发送群合并转发消息。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 群号 |
| forward | Forward | 是 | 合并转发消息对象 |

**返回值**：`dict`

```python
from ncatbot.types.segment import Forward

fwd = Forward()
fwd.add_node(uin=123, name="Alice", content=[{"type": "text", "data": {"text": "hi"}}])
await api.post_group_forward_msg(123456, fwd)
```

---

### post_private_forward_msg()

```python
async def post_private_forward_msg(
    self, user_id: Union[str, int], forward: Forward,
) -> dict:
```

发送私聊合并转发消息。参数与 `post_group_forward_msg` 对称（`user_id` 替代 `group_id`）。

---

### send_group_forward_msg_by_id()

```python
async def send_group_forward_msg_by_id(
    self, group_id: Union[str, int], message_ids: List[Union[str, int]],
) -> dict:
```

通过消息 ID 列表逐条转发群消息。内部逐条调用 `get_msg` 获取内容后通过 `send_group_msg` 发送。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 目标群号 |
| message_ids | List[str \| int] | 是 | 要转发的消息 ID 列表 |

**返回值**：`dict` — 最后一条发送的结果

```python
await api.send_group_forward_msg_by_id(123456, [msg_id_1, msg_id_2, msg_id_3])
```

---

### send_private_forward_msg_by_id()

```python
async def send_private_forward_msg_by_id(
    self, user_id: Union[str, int], message_ids: List[Union[str, int]],
) -> dict:
```

通过消息 ID 列表逐条转发私聊消息。参数与 `send_group_forward_msg_by_id` 对称。

**返回值**：`dict` — 最后一条发送的结果
