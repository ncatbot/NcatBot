# 查询与文件操作 API 详解

> QQQuery 信息查询（40+ 方法）+ QQFile 文件操作的完整参数表、返回值和示例。

---

## 信息查询（QQQuery）

通过 `api.qq.query.xxx()` 调用。源码：`ncatbot/api/qq/query.py`。

### 基础查询

### get_login_info()

```python
async def get_login_info(self) -> LoginInfo:
```

**返回值**：`LoginInfo` — 包含 `user_id: str` 和 `nickname: str`

```python
info = await api.qq.query.get_login_info()
print(f"Bot QQ: {info.user_id}")
```

---

### get_stranger_info()

```python
async def get_stranger_info(self, user_id: Union[str, int]) -> StrangerInfo:
```

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_id | str \| int | 是 | 目标用户 QQ 号 |

**返回值**：`StrangerInfo` — 用户信息（`user_id`, `nickname`, `sex`, `age` 等）

---

### get_friend_list()

```python
async def get_friend_list(self) -> List[FriendInfo]:
```

**返回值**：`List[FriendInfo]` — 好友列表，每项包含 `user_id`, `nickname`, `remark`

---

### get_group_info()

```python
async def get_group_info(self, group_id: Union[str, int]) -> GroupInfo:
```

**返回值**：`GroupInfo` — 群信息（`group_id`, `group_name`, `member_count` 等）

---

### get_group_list()

```python
async def get_group_list(self) -> List[GroupInfo]:
```

**返回值**：`List[GroupInfo]` — 群列表

```python
groups = await api.qq.query.get_group_list()
for g in groups:
    print(g.group_name)
```

---

### get_group_member_info()

```python
async def get_group_member_info(
    self, group_id: Union[str, int], user_id: Union[str, int],
) -> GroupMemberInfo:
```

**返回值**：`GroupMemberInfo` — 群成员信息（`group_id`, `user_id`, `nickname`, `card`, `role` 等）

---

### get_group_member_list()

```python
async def get_group_member_list(self, group_id: Union[str, int]) -> List[GroupMemberInfo]:
```

**返回值**：`List[GroupMemberInfo]` — 群成员列表

---

### get_msg()

```python
async def get_msg(self, message_id: Union[str, int]) -> MessageData:
```

**返回值**：`MessageData` — 消息详情（`message_id`, `real_id`, `sender`, `time`, `message` 等）

---

### get_forward_msg()

```python
async def get_forward_msg(self, message_id: Union[str, int]) -> ForwardMessageData:
```

**返回值**：`ForwardMessageData` — 合并转发消息内容

---

### 群扩展查询

### get_group_notice()

```python
async def get_group_notice(self, group_id: Union[str, int]) -> List[GroupNotice]:
```

获取群公告列表。

### get_essence_msg_list()

```python
async def get_essence_msg_list(self, group_id: Union[str, int]) -> List[EssenceMessage]:
```

获取群精华消息列表。

### get_group_honor_info()

```python
async def get_group_honor_info(
    self, group_id: Union[str, int], type: str = "all",
) -> GroupHonorInfo:
```

获取群荣誉信息。`type` 可选 `"talkative"`, `"performer"`, `"legend"`, `"strong_newbie"`, `"emotion"`, `"all"`。

### get_group_at_all_remain()

```python
async def get_group_at_all_remain(self, group_id: Union[str, int]) -> GroupAtAllRemain:
```

获取群 @全体成员 剩余次数。

### get_group_shut_list()

```python
async def get_group_shut_list(self, group_id: Union[str, int]) -> List[GroupShutInfo]:
```

获取群禁言列表。

### get_group_system_msg()

```python
async def get_group_system_msg(self) -> GroupSystemMsg:
```

获取群系统消息（加群请求/邀请等）。

### get_group_info_ex()

```python
async def get_group_info_ex(self, group_id: Union[str, int]) -> GroupInfoEx:
```

获取群扩展信息。

---

### 文件查询

### get_group_root_files()

```python
async def get_group_root_files(self, group_id: Union[str, int]) -> GroupFileList:
```

获取群根目录文件列表。

### get_group_file_url()

```python
async def get_group_file_url(
    self, group_id: Union[str, int], file_id: str,
) -> str:
```

获取群文件下载 URL。

```python
url = await api.qq.query.get_group_file_url(123456, "file_abc123")
```

### get_group_file_system_info()

```python
async def get_group_file_system_info(self, group_id: Union[str, int]) -> GroupFileSystemInfo:
```

获取群文件系统信息（文件数/容量等）。

### get_group_files_by_folder()

```python
async def get_group_files_by_folder(
    self, group_id: Union[str, int], folder_id: str,
) -> GroupFileList:
```

获取指定文件夹中的文件列表。

### get_private_file_url()

```python
async def get_private_file_url(self, user_id: Union[str, int], file_id: str) -> str:
```

获取私聊文件下载 URL。

### get_file()

```python
async def get_file(self, file_id: str) -> FileData:
```

获取文件信息。

---

### 表情回应查询

### fetch_emoji_like()

```python
async def fetch_emoji_like(
    self, message_id: Union[str, int], emoji_id: str,
    emoji_type: str = "1", count: int = 20, cookie: str = "",
) -> EmojiLikeInfo:
```

获取消息的表情回应详情。

### get_emoji_likes()

```python
async def get_emoji_likes(
    self, message_id: Union[str, int], emoji_id: str = "", count: int = 0,
) -> EmojiLikesResult:
```

获取消息的表情回应汇总。

---

### 系统信息

### get_version_info()

```python
async def get_version_info(self) -> VersionInfo:
```

获取 NapCat 版本信息。

### get_status()

```python
async def get_status(self) -> BotStatus:
```

获取 Bot 在线状态。

### get_recent_contact()

```python
async def get_recent_contact(self, count: int = 10) -> List[RecentContact]:
```

获取最近联系人列表。

### ocr_image()

```python
async def ocr_image(self, image: str) -> OcrResult:
```

OCR 图片识别。

---

## 文件操作（QQFile）

通过 `api.qq.file.xxx()` 调用。源码：`ncatbot/api/qq/file.py`。

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

```python
await api.qq.file.upload_group_file(123456, "/tmp/report.pdf", "月报.pdf")
```

---

### delete_group_file()

```python
async def delete_group_file(
    self, group_id: Union[str, int], file_id: str,
) -> None:
```

删除群文件。

---

### create_group_file_folder()

```python
async def create_group_file_folder(
    self, group_id: Union[str, int], name: str, parent_id: str = "",
) -> CreateFolderResult:
```

创建群文件夹。

---

### delete_group_folder()

```python
async def delete_group_folder(
    self, group_id: Union[str, int], folder_id: str,
) -> None:
```

删除群文件夹。

---

### upload_private_file()

```python
async def upload_private_file(
    self, user_id: Union[str, int], file: str, name: str,
) -> None:
```

上传私聊文件。

---

### download_file()

```python
async def download_file(
    self, url: str = "", file: str = "", headers: str = "",
) -> DownloadResult:
```

下载文件到本地。`url` 或 `file` 至少指定一个。
