# Bilibili API 参考

> `IBiliAPIClient` 完整方法签名 — Bilibili 平台所有可用 API。
>
> 源码：`ncatbot/api/bilibili/interface.py`
>
> 通过 `api.bilibili.xxx()` 调用。

---

## 数据源管理

### add_live_room()

```python
async def add_live_room(self, room_id: int) -> None
```

添加直播间监听。

### remove_live_room()

```python
async def remove_live_room(self, room_id: int) -> None
```

移除直播间监听。

### add_comment_watch()

```python
async def add_comment_watch(
    self, resource_id: str, resource_type: str = "video",
) -> None
```

添加评论监听。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| resource_id | str | — | 资源 ID（BV 号、动态 ID 等） |
| resource_type | str | `"video"` | 资源类型 |

### remove_comment_watch()

```python
async def remove_comment_watch(self, resource_id: str) -> None
```

移除评论监听。

### list_sources()

```python
async def list_sources(self) -> List[Dict[str, Any]]
```

列出所有已注册的数据源。

---

## 直播间操作

### send_danmu()

```python
async def send_danmu(self, room_id: int, text: str) -> Any
```

发送弹幕。

| 参数 | 类型 | 说明 |
|------|------|------|
| room_id | int | 直播间 ID |
| text | str | 弹幕内容 |

### ban_user()

```python
async def ban_user(self, room_id: int, user_id: int, hour: int = 1) -> Any
```

禁言用户。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| room_id | int | — | 直播间 ID |
| user_id | int | — | 被禁言的用户 ID |
| hour | int | `1` | 禁言时长（小时） |

### unban_user()

```python
async def unban_user(self, room_id: int, user_id: int) -> Any
```

解除禁言。

### set_room_silent()

```python
async def set_room_silent(self, room_id: int, enable: bool, **kwargs: Any) -> Any
```

全员禁言开关。

### get_room_info()

```python
async def get_room_info(self, room_id: int) -> dict
```

获取直播间信息。

---

## 私信

### send_private_msg()

```python
async def send_private_msg(self, user_id: int, content: str) -> Any
```

发送私信。

### send_private_image()

```python
async def send_private_image(self, user_id: int, image_url: str) -> Any
```

发送私信图片。

### get_session_history()

```python
async def get_session_history(self, user_id: int, count: int = 20) -> list
```

获取私信历史。

---

## 评论

### send_comment()

```python
async def send_comment(
    self, resource_id: str, resource_type: str, text: str,
) -> Any
```

发送评论。

### reply_comment()

```python
async def reply_comment(
    self,
    resource_id: str,
    resource_type: str,
    root_id: int,
    parent_id: int,
    text: str,
) -> Any
```

回复评论。

| 参数 | 类型 | 说明 |
|------|------|------|
| resource_id | str | 资源 ID |
| resource_type | str | 资源类型 |
| root_id | int | 根评论 ID |
| parent_id | int | 被回复的评论 ID |
| text | str | 回复内容 |

### delete_comment()

```python
async def delete_comment(
    self, resource_id: str, resource_type: str, comment_id: int,
) -> Any
```

删除评论。

### like_comment()

```python
async def like_comment(
    self, resource_id: str, resource_type: str, comment_id: int,
) -> Any
```

点赞评论。

### get_comments()

```python
async def get_comments(
    self, resource_id: str, resource_type: str, page: int = 1,
) -> list
```

获取评论列表。

---

## 用户查询

### get_user_info()

```python
async def get_user_info(self, user_id: int) -> dict
```

获取用户信息。
