# 信息查询与支持操作 API 详解

> InfoExtension 信息查询 + SupportExtension 文件管理与辅助操作的完整参数表、返回值和示例。

---

## 信息查询（InfoExtension）

通过 `api.info.xxx()` 调用。源码：`ncatbot/api/extensions/info.py`。

底层接口定义见 `IBotAPI`（源码：`ncatbot/api/interface.py`）。

### get_login_info()

```python
async def get_login_info(self) -> dict:
```

**参数**：无

**返回值**：`dict` — 包含 `user_id` 和 `nickname` 的字典

**OneBot v11 Action**：`get_login_info`

```python
info = await api.info.get_login_info()
print(f"Bot QQ: {info['user_id']}")
```

---

### get_stranger_info()

```python
async def get_stranger_info(self, user_id: Union[str, int]) -> dict:
```

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_id | str \| int | 是 | 目标用户 QQ 号 |

**返回值**：`dict` — 用户信息（`user_id`, `nickname`, `sex`, `age` 等）

**OneBot v11 Action**：`get_stranger_info`

---

### get_friend_list()

```python
async def get_friend_list(self) -> List[dict]:
```

**参数**：无

**返回值**：`List[dict]` — 好友列表，每项包含 `user_id`, `nickname`, `remark`

**OneBot v11 Action**：`get_friend_list`

---

### get_group_info()

```python
async def get_group_info(self, group_id: Union[str, int]) -> dict:
```

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 群号 |

**返回值**：`dict` — 群信息（`group_id`, `group_name`, `member_count` 等）

**OneBot v11 Action**：`get_group_info`

---

### get_group_list()

```python
async def get_group_list(self) -> list:
```

**参数**：无

**返回值**：`list` — 群列表

**OneBot v11 Action**：`get_group_list`

```python
groups = await api.info.get_group_list()
for g in groups:
    print(g["group_name"])
```

---

### get_group_member_info()

```python
async def get_group_member_info(
    self, group_id: Union[str, int], user_id: Union[str, int],
) -> dict:
```

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 群号 |
| user_id | str \| int | 是 | 目标用户 QQ 号 |

**返回值**：`dict` — 群成员信息（`group_id`, `user_id`, `nickname`, `card`, `role` 等）

**OneBot v11 Action**：`get_group_member_info`

---

### get_group_member_list()

```python
async def get_group_member_list(self, group_id: Union[str, int]) -> list:
```

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 群号 |

**返回值**：`list` — 群成员列表

**OneBot v11 Action**：`get_group_member_list`

---

### get_msg()

```python
async def get_msg(self, message_id: Union[str, int]) -> dict:
```

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| message_id | str \| int | 是 | 消息 ID |

**返回值**：`dict` — 消息详情（`message_id`, `real_id`, `sender`, `time`, `message` 等）

**OneBot v11 Action**：`get_msg`

---

### get_forward_msg()

```python
async def get_forward_msg(self, message_id: Union[str, int]) -> dict:
```

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| message_id | str \| int | 是 | 合并转发消息 ID |

**返回值**：`dict` — 合并转发消息内容

**OneBot v11 Action**：`get_forward_msg`

---

### get_group_root_files()

```python
async def get_group_root_files(self, group_id: Union[str, int]) -> dict:
```

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 群号 |

**返回值**：`dict` — 群根目录文件列表

**OneBot v11 Action**：`get_group_root_files`

---

### get_group_file_url()

```python
async def get_group_file_url(
    self, group_id: Union[str, int], file_id: str,
) -> str:
```

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 群号 |
| file_id | str | 是 | 文件 ID |

**返回值**：`str` — 文件下载 URL

**OneBot v11 Action**：`get_group_file_url`

```python
url = await api.info.get_group_file_url(123456, "file_abc123")
```

---

## 支持操作（SupportExtension）

通过 `api.support.xxx()` 调用。源码：`ncatbot/api/extensions/support.py`。

封装文件管理与杂项辅助操作。

### upload_group_file()

```python
async def upload_group_file(
    self, group_id: Union[str, int], file: str, name: str, folder_id: str = "",
) -> None:
```

上传群文件。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 群号 |
| file | str | 是 | 本地文件路径或 URL |
| name | str | 是 | 上传后的文件名 |
| folder_id | str | 否 | 目标文件夹 ID，默认为根目录 |

**返回值**：无

**OneBot v11 Action**：`upload_group_file`

```python
await api.support.upload_group_file(123456, "/tmp/report.pdf", "月报.pdf")
```

---

### delete_group_file()

```python
async def delete_group_file(
    self, group_id: Union[str, int], file_id: str,
) -> None:
```

删除群文件。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 群号 |
| file_id | str | 是 | 文件 ID |

**返回值**：无

**OneBot v11 Action**：`delete_group_file`

---

### send_like()

```python
async def send_like(self, user_id: Union[str, int], times: int = 1) -> None:
```

给用户点赞。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_id | str \| int | 是 | 目标用户 QQ 号 |
| times | int | 否 | 点赞次数，默认 `1` |

**返回值**：无

**OneBot v11 Action**：`send_like`

```python
await api.support.send_like(654321, times=10)
```
