# Bot API 完整参考

> 参考文档：[guide/5. API 使用/](docs/guide/5. API 使用/), [reference/1. Bot API/](docs/reference/1. Bot API/), [reference/3. 数据类型/4. QQ 响应.md](docs/reference/3. 数据类型/4. QQ 响应.md)

## 响应类型与错误处理

所有 API 返回值使用 Pydantic 类型（定义在 `ncatbot.types.napcat`）：

```python
from ncatbot.types import SendMessageResult, LoginInfo, GroupInfo, GroupMemberInfo, MessageSender

# 发送消息返回 SendMessageResult
result = await self.api.qq.post_group_msg(group_id, text="hello")
print(result.message_id)  # str

# 查询返回对应类型
info = await self.api.qq.query.get_login_info()  # -> LoginInfo
groups = await self.api.qq.query.get_group_list()  # -> List[GroupInfo]
member = await self.api.qq.query.get_group_member_info(gid, uid)  # -> GroupMemberInfo
```

错误处理：adapter 层自动解析信封，retcode 非零时抛 `APIError`：

```python
from ncatbot.api import APIError, APINotFoundError, APIPermissionError

try:
    await self.api.qq.messaging.send_group_msg(group_id, msg)
except APINotFoundError:
    ...  # 目标不存在
except APIPermissionError:
    ...  # 权限不足
except APIError as e:
    print(e.retcode, e.message)
```

## 多平台 API 访问（5.2 新增）

```python
# 显式指定 QQ 平台
await self.api.qq.post_group_msg(group_id, text="Hello")

# 按名称获取平台
await self.api.platform("telegram").send_message(chat_id, text)

# 查看已注册平台
print(self.api.platforms)  # {"qq": <QQAPIClient>, ...}
```

## 消息发送 API

### 原子方法（通过 messaging 分组）

```python
await self.api.qq.messaging.send_group_msg(group_id, message=[{"type": "text", "data": {"text": "Hello"}}])
await self.api.qq.messaging.send_private_msg(user_id, message=[...])
await self.api.qq.messaging.delete_msg(message_id)
await self.api.qq.messaging.send_forward_msg(message_type, target_id, messages=[...])
await self.api.qq.send_poke(group_id, user_id)

# 高频消息扩展 API
history = await self.api.qq.messaging.get_group_msg_history(group_id, message_seq=None, count=20)
history = await self.api.qq.messaging.get_friend_msg_history(user_id, message_seq=None, count=20)
await self.api.qq.messaging.set_msg_emoji_like(message_id, emoji_id, set=True)
await self.api.qq.messaging.mark_group_msg_as_read(group_id)
await self.api.qq.messaging.mark_private_msg_as_read(user_id)
await self.api.qq.messaging.mark_all_as_read()
await self.api.qq.messaging.forward_friend_single_msg(user_id, message_id)
await self.api.qq.messaging.forward_group_single_msg(group_id, message_id)
await self.api.qq.friend_poke(user_id)
```

### Sugar — 群消息

```python
await self.api.qq.post_group_msg(group_id, text="Hello", at=user_id, image="pic.jpg", reply=msg_id)
await self.api.qq.send_group_text(group_id, "文本")
await self.api.qq.send_group_plain_text(group_id, "纯文本段")
await self.api.qq.send_group_image(group_id, "https://example.com/pic.jpg")
await self.api.qq.send_group_video(group_id, "https://example.com/video.mp4")
await self.api.qq.send_group_record(group_id, "https://example.com/audio.mp3")
await self.api.qq.send_group_file(group_id, "/path/to/file.pdf", name="文档.pdf")
await self.api.qq.send_group_sticker(group_id, Image(file="sticker.gif", sub_type=1))
await self.api.qq.post_group_array_msg(group_id, msg_array)
await self.api.qq.post_group_forward_msg(group_id, forward)
await self.api.qq.send_group_forward_msg_by_id(group_id, [msg_id1, msg_id2])
```

### Sugar — 私聊消息

```python
await self.api.qq.post_private_msg(user_id, text="Hello", image="pic.jpg")
await self.api.qq.send_private_text(user_id, "文本")
await self.api.qq.send_private_plain_text(user_id, "纯文本段")
await self.api.qq.send_private_image(user_id, "https://example.com/pic.jpg")
await self.api.qq.send_private_video(user_id, "https://example.com/video.mp4")
await self.api.qq.send_private_record(user_id, "https://example.com/audio.mp3")
await self.api.qq.send_private_file(user_id, "/path/to/file.pdf", name="文档.pdf")
await self.api.qq.send_private_sticker(user_id, Image(file="sticker.gif", sub_type=1))
await self.api.qq.send_private_dice(user_id, value=1)
await self.api.qq.send_private_rps(user_id, value=1)
await self.api.qq.post_private_array_msg(user_id, msg_array)
await self.api.qq.post_private_forward_msg(user_id, forward)
await self.api.qq.send_private_forward_msg_by_id(user_id, [msg_id1, msg_id2])
```

## 群管理 API

> 参考文档：[reference/1. Bot API/2. QQ/2. 管理 API.md](docs/reference/1. Bot API/2. QQ/2. 管理 API.md)

通过 `self.api.qq.manage.*` 访问：

```python
await self.api.qq.manage.set_group_kick(group_id, user_id, reject_add_request=False)
await self.api.qq.manage.set_group_ban(group_id, user_id, duration=1800)
await self.api.qq.manage.set_group_whole_ban(group_id, enable=True)
await self.api.qq.manage.set_group_admin(group_id, user_id, enable=True)
await self.api.qq.manage.set_group_card(group_id, user_id, card="新名片")
await self.api.qq.manage.set_group_name(group_id, name="新群名")
await self.api.qq.manage.set_group_leave(group_id, is_dismiss=False)
await self.api.qq.manage.set_group_special_title(group_id, user_id, special_title="头衔")
await self.api.qq.manage.kick_and_block(group_id, user_id, message_id=None)
await self.api.qq.manage.set_friend_add_request(flag, approve=True, remark="")
await self.api.qq.manage.set_group_add_request(flag, sub_type, approve=True, reason="")

# 群公告 / 精华 / 扩展管理
await self.api.qq.manage.send_group_notice(group_id, content, image="")
await self.api.qq.manage.delete_group_notice(group_id, notice_id)
await self.api.qq.manage.set_essence_msg(message_id)
await self.api.qq.manage.delete_essence_msg(message_id)
await self.api.qq.manage.set_group_kick_members(group_id, user_ids, reject_add_request=False)
await self.api.qq.manage.set_group_remark(group_id, remark)
await self.api.qq.manage.set_group_sign(group_id)
await self.api.qq.manage.set_group_todo(group_id, message_id)
await self.api.qq.manage.set_group_portrait(group_id, file)

# 好友管理
await self.api.qq.manage.set_friend_remark(user_id, remark)
await self.api.qq.manage.delete_friend(user_id)

# 个人资料
await self.api.qq.manage.set_self_longnick(long_nick)
await self.api.qq.manage.set_qq_avatar(file)
await self.api.qq.manage.set_qq_profile(nickname, company, email, college, personal_note)
await self.api.qq.manage.set_online_status(status, ext_status=0, custom_status="")
```

## 信息查询 API

> 参考文档：[reference/1. Bot API/2. QQ/3. 信息支持 API.md](docs/reference/1. Bot API/2. QQ/3. 信息支持 API.md)

通过 `self.api.qq.query.*` 访问：

```python
info = await self.api.qq.query.get_login_info()
info = await self.api.qq.query.get_stranger_info(user_id)
friends = await self.api.qq.query.get_friend_list()
info = await self.api.qq.query.get_group_info(group_id)
groups = await self.api.qq.query.get_group_list()
member = await self.api.qq.query.get_group_member_info(group_id, user_id)
members = await self.api.qq.query.get_group_member_list(group_id)
msg = await self.api.qq.query.get_msg(message_id)
fwd = await self.api.qq.query.get_forward_msg(message_id)
files = await self.api.qq.query.get_group_root_files(group_id)
url = await self.api.qq.query.get_group_file_url(group_id, file_id)

# 群扩展查询
notices = await self.api.qq.query.get_group_notice(group_id)
essences = await self.api.qq.query.get_essence_msg_list(group_id)
honor = await self.api.qq.query.get_group_honor_info(group_id, type="all")
remain = await self.api.qq.query.get_group_at_all_remain(group_id)
shut_list = await self.api.qq.query.get_group_shut_list(group_id)
sys_msg = await self.api.qq.query.get_group_system_msg()
info_ex = await self.api.qq.query.get_group_info_ex(group_id)

# 文件扩展查询
fs_info = await self.api.qq.query.get_group_file_system_info(group_id)
files = await self.api.qq.query.get_group_files_by_folder(group_id, folder_id)
url = await self.api.qq.query.get_private_file_url(user_id, file_id)
file = await self.api.qq.query.get_file(file_id)

# 消息扩展查询
emoji = await self.api.qq.query.fetch_emoji_like(message_id, emoji_id, emoji_type="1", count=20, cookie="")  # -> EmojiLikeInfo
likes = await self.api.qq.query.get_emoji_likes(message_id, emoji_id="", count=0)  # -> EmojiLikesResult

# 系统信息
version = await self.api.qq.query.get_version_info()
status = await self.api.qq.query.get_status()
recent = await self.api.qq.query.get_recent_contact(count=10)

# OCR
result = await self.api.qq.query.ocr_image(image)
```

## 辅助操作 API

通过 `self.api.qq.file.*` 访问：

```python
await self.api.qq.file.upload_group_file(group_id, file="/path/to/file", name="name.txt")
await self.api.qq.file.delete_group_file(group_id, file_id)
await self.api.qq.messaging.send_like(user_id, times=1)

# 直接传 Attachment 对象（自动下载并上传）
await self.api.qq.file.upload_group_file(group_id, file=attachment)

# 一步上传 Attachment 到指定文件夹（QQFile sugar）
await self.api.qq.file.upload_attachment(group_id, attachment, folder="备份")

# 文件系统扩展
result = await self.api.qq.file.create_group_file_folder(group_id, name, parent_id="")  # -> CreateFolderResult
await self.api.qq.file.delete_group_folder(group_id, folder_id)
await self.api.qq.file.upload_private_file(user_id, file, name)
result = await self.api.qq.file.download_file(url="", file="", headers="")
```

## GitHub 平台 API

> 参考文档：[guide/5. API 使用/4. GitHub/](docs/guide/5. API 使用/4. GitHub/), [reference/1. Bot API/4. GitHub/1. API.md](docs/reference/1. Bot API/4. GitHub/1. API.md)

通过 `self.api.github.*` 访问：

### Issue 操作（IssueAPIMixin）

```python
await self.api.github.create_issue(repo, title, body="", labels=None, assignees=None)
await self.api.github.update_issue(repo, issue_number, *, title=None, body=None, state=None, labels=None, assignees=None)
await self.api.github.close_issue(repo, issue_number)
await self.api.github.reopen_issue(repo, issue_number)
await self.api.github.get_issue(repo, issue_number)
await self.api.github.add_labels(repo, issue_number, labels)
await self.api.github.remove_label(repo, issue_number, label)
await self.api.github.set_assignees(repo, issue_number, assignees)
```

### 评论操作（CommentAPIMixin）

```python
await self.api.github.create_issue_comment(repo, issue_number, body)
await self.api.github.update_comment(repo, comment_id, body)
await self.api.github.delete_comment(repo, comment_id)
await self.api.github.list_issue_comments(repo, issue_number, page=1, per_page=30)
```

### PR 操作（PRAPIMixin）

```python
await self.api.github.create_pr_comment(repo, pr_number, body)
await self.api.github.merge_pr(repo, pr_number, *, merge_method="merge", commit_title=None, commit_message=None)
await self.api.github.close_pr(repo, pr_number)
await self.api.github.request_review(repo, pr_number, reviewers)
await self.api.github.get_pr(repo, pr_number)
```

### 查询操作（QueryAPIMixin）

```python
await self.api.github.get_repo(repo)
await self.api.github.get_user(username)
await self.api.github.get_authenticated_user()
```

### GitHub 事件实体快捷方法

```python
# GitHubIssueEvent / GitHubPREvent
await event.reply("评论内容")       # 创建 Issue/PR 评论

# GitHubIssueCommentEvent / GitHubPRReviewCommentEvent
await event.reply("回复内容")       # 在同一 Issue/PR 下回复
await event.delete()                # 删除该评论
```

## 事件实体快捷方法

```python
# MessageEvent
await event.reply("文本")
await event.delete()

# GroupMessageEvent
await event.kick()
await event.ban(duration=600)

# RequestEvent
await event.approve()
await event.reject(reason="理由")
```

## API action 名称映射

测试中使用 `h.api_called("action_name")` 验证调用：

| action | 方法 |
|--------|------|
| `"send_group_msg"` | `send_group_msg()` / `post_group_msg()` / `send_group_text()` 等 |
| `"send_private_msg"` | `send_private_msg()` / `post_private_msg()` 等 |
| `"delete_msg"` | `delete_msg()` |
| `"send_forward_msg"` | `send_forward_msg()` / `post_group_forward_msg()` 等 |
| `"send_poke"` | `send_poke()` |
| `"set_group_kick"` | `manage.set_group_kick()` |
| `"set_group_ban"` | `manage.set_group_ban()` |
| `"set_group_whole_ban"` | `manage.set_group_whole_ban()` |
| `"set_group_admin"` | `manage.set_group_admin()` |
| `"set_group_card"` | `manage.set_group_card()` |
| `"set_group_name"` | `manage.set_group_name()` |
| `"set_group_leave"` | `manage.set_group_leave()` |
| `"set_friend_add_request"` | `manage.set_friend_add_request()` |
| `"set_group_add_request"` | `manage.set_group_add_request()` |
| `"get_login_info"` | `query.get_login_info()` |
| `"get_stranger_info"` | `query.get_stranger_info()` |
| `"get_friend_list"` | `query.get_friend_list()` |
| `"get_group_info"` | `query.get_group_info()` |
| `"get_group_list"` | `query.get_group_list()` |
| `"get_group_member_info"` | `query.get_group_member_info()` |
| `"get_group_member_list"` | `query.get_group_member_list()` |
| `"get_msg"` | `query.get_msg()` |
| `"get_forward_msg"` | `query.get_forward_msg()` |
| `"upload_group_file"` | `file.upload_group_file()` |
| `"get_group_root_files"` | `query.get_group_root_files()` |
| `"get_group_file_url"` | `query.get_group_file_url()` |
| `"delete_group_file"` | `file.delete_group_file()` |
| `"send_like"` | `file.send_like()` |
| `"send_group_notice"` | `manage.send_group_notice()` |
| `"delete_group_notice"` | `manage.delete_group_notice()` |
| `"set_essence_msg"` | `manage.set_essence_msg()` |
| `"delete_essence_msg"` | `manage.delete_essence_msg()` |
| `"set_group_kick_members"` | `manage.set_group_kick_members()` |
| `"set_group_remark"` | `manage.set_group_remark()` |
| `"set_group_sign"` | `manage.set_group_sign()` |
| `"set_group_todo"` | `manage.set_group_todo()` |
| `"set_group_portrait"` | `manage.set_group_portrait()` |
| `"set_friend_remark"` | `manage.set_friend_remark()` |
| `"delete_friend"` | `manage.delete_friend()` |
| `"set_self_longnick"` | `manage.set_self_longnick()` |
| `"set_qq_avatar"` | `manage.set_qq_avatar()` |
| `"set_qq_profile"` | `manage.set_qq_profile()` |
| `"set_online_status"` | `manage.set_online_status()` |
| `"get_group_notice"` | `query.get_group_notice()` |
| `"get_essence_msg_list"` | `query.get_essence_msg_list()` |
| `"get_group_honor_info"` | `query.get_group_honor_info()` |
| `"get_group_at_all_remain"` | `query.get_group_at_all_remain()` |
| `"get_group_shut_list"` | `query.get_group_shut_list()` |
| `"get_group_system_msg"` | `query.get_group_system_msg()` |
| `"get_group_info_ex"` | `query.get_group_info_ex()` |
| `"get_group_file_system_info"` | `query.get_group_file_system_info()` |
| `"get_group_files_by_folder"` | `query.get_group_files_by_folder()` |
| `"get_private_file_url"` | `query.get_private_file_url()` |
| `"get_file"` | `query.get_file()` |
| `"fetch_emoji_like"` | `query.fetch_emoji_like()` |
| `"get_emoji_likes"` | `query.get_emoji_likes()` |
| `"get_version_info"` | `query.get_version_info()` |
| `"get_status"` | `query.get_status()` |
| `"get_recent_contact"` | `query.get_recent_contact()` |
| `"ocr_image"` | `query.ocr_image()` |
| `"create_group_file_folder"` | `file.create_group_file_folder()` |
| `"delete_group_folder"` | `file.delete_group_folder()` |
| `"upload_private_file"` | `file.upload_private_file()` |
| `"download_file"` | `file.download_file()` |
| `"get_group_msg_history"` | `get_group_msg_history()` (messaging) |
| `"get_friend_msg_history"` | `get_friend_msg_history()` (messaging) |
| `"set_msg_emoji_like"` | `set_msg_emoji_like()` (messaging) |
| `"mark_group_msg_as_read"` | `mark_group_msg_as_read()` (messaging) |
| `"mark_private_msg_as_read"` | `mark_private_msg_as_read()` (messaging) |
| `"mark_all_as_read"` | `mark_all_as_read()` (messaging) |
| `"forward_friend_single_msg"` | `forward_friend_single_msg()` (messaging) |
| `"forward_group_single_msg"` | `forward_group_single_msg()` (messaging) |
| `"friend_poke"` | `friend_poke()` (messaging) |
