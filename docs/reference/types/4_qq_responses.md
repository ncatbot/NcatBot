# QQ 响应类型

> QQ 平台（NapCat 协议）Bot API 返回值的 Pydantic 类型定义。

**导入路径：** `from ncatbot.types.napcat import SendMessageResult, GroupInfo, ...`

**源码：** `ncatbot/types/napcat/`

---

## NapCatModel 基类

所有响应类型的基类。

```python
from ncatbot.types.napcat import NapCatModel
```

| 特性 | 说明 |
|------|------|
| `extra="allow"` | 未知字段不报错，兼容协议变动 |
| `_coerce_ids` | 所有 `*_id` 字段自动从 int/float 转为 str |
| dict 兼容 | 支持 `result["key"]`、`result.get("key")`、`"key" in result` |

---

## 消息类型

**源码：** `ncatbot/types/napcat/message.py`

### SendMessageResult

发送消息的返回结果。对应 `send_group_msg`, `send_private_msg`, `send_forward_msg` 等。

| 字段 | 类型 | 说明 |
|------|------|------|
| `message_id` | `str` | 消息 ID |

### MessageSender

消息发送者信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| `user_id` | `str` | 用户 ID |
| `nickname` | `str?` | 昵称 |
| `card` | `str?` | 群名片 |
| `role` | `str?` | 群角色（仅群消息） |

### MessageData

单条消息详情。对应 `get_msg`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `message_id` | `str` | 消息 ID |
| `real_id` | `int?` | 真实 ID |
| `time` | `int?` | 时间戳 |
| `message_type` | `str?` | 消息类型 |
| `sender` | `MessageSender?` | 发送者 |
| `message` | `List[dict]?` | 消息段列表 |
| `raw_message` | `str?` | 原始消息 |

### MessageHistory

消息历史记录。对应 `get_group_msg_history`, `get_friend_msg_history`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `messages` | `List[MessageData]` | 消息列表 |

### ForwardMessageData

转发消息内容。对应 `get_forward_msg`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `messages` | `List[MessageData]` | 消息列表 |

---

## 群组类型

**源码：** `ncatbot/types/napcat/group.py`

### GroupInfo

群基本信息。对应 `get_group_info`, `get_group_list`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `group_id` | `str` | 群号 |
| `group_name` | `str?` | 群名 |
| `member_count` | `int?` | 成员数 |
| `max_member_count` | `int?` | 最大成员数 |

### GroupMemberInfo

群成员信息。对应 `get_group_member_info`, `get_group_member_list`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `group_id` | `str` | 群号 |
| `user_id` | `str` | 用户 ID |
| `nickname` | `str?` | 昵称 |
| `card` | `str?` | 群名片 |
| `sex` | `str?` | 性别 |
| `age` | `int?` | 年龄 |
| `area` | `str?` | 地区 |
| `join_time` | `int?` | 入群时间 |
| `last_sent_time` | `int?` | 最后发言时间 |
| `level` | `str?` | 等级 |
| `role` | `str?` | 角色（`owner`/`admin`/`member`） |
| `title` | `str?` | 专属头衔 |
| `title_expire_time` | `int?` | 头衔过期时间 |
| `shut_up_timestamp` | `int?` | 禁言截止时间 |

### GroupNotice

群公告。对应 `get_group_notice`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `notice_id` | `str` | 公告 ID |
| `sender_id` | `str` | 发送者 ID |
| `publish_time` | `int?` | 发布时间 |
| `message` | `GroupNoticeMessage?` | 公告内容 |
| `settings` | `GroupNoticeSettings?` | 公告设置 |
| `read_num` | `int?` | 已读数 |

### EssenceMessage

群精华消息。对应 `get_essence_msg_list`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `sender_id` | `str` | 发送者 ID |
| `sender_nick` | `str?` | 发送者昵称 |
| `operator_id` | `str` | 操作者 ID |
| `operator_nick` | `str?` | 操作者昵称 |
| `operator_time` | `int?` | 操作时间 |
| `message_id` | `str` | 消息 ID |

### HonorUser / GroupHonorInfo

群荣誉。对应 `get_group_honor_info`。

**HonorUser：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `user_id` | `str` | 用户 ID |
| `nickname` | `str?` | 昵称 |
| `avatar` | `str?` | 头像 URL |
| `description` | `str?` | 描述 |

**GroupHonorInfo：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `group_id` | `str` | 群号 |
| `current_talkative` | `HonorUser?` | 当前龙王 |
| `talkative_list` | `List[HonorUser]?` | 龙王榜 |
| `performer_list` | `List[HonorUser]?` | 群聊之火 |
| `legend_list` | `List[HonorUser]?` | 群聊炽焰 |
| `strong_newbie_list` | `List[HonorUser]?` | 冒尖小春笋 |
| `emotion_list` | `List[HonorUser]?` | 快乐之源 |

### GroupAtAllRemain

群 @全体 剩余次数。对应 `get_group_at_all_remain`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `can_at_all` | `bool` | 是否可以 @全体 |
| `remain_at_all_count_for_group` | `int` | 群剩余次数 |
| `remain_at_all_count_for_uin` | `int` | 个人剩余次数 |

### GroupShutInfo

群禁言信息。对应 `get_group_shut_list`。NapCat 返回格式使用 `uin` / `shutUpTime`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `uid` | `str?` | 成员 UID |
| `uin` | `str` | 成员 UIN (QQ 号) |
| `nick` | `str?` | 昵称 |
| `shutUpTime` | `int?` | 禁言截止时间 |
| `role` | `int?` | 角色 |
| `cardName` | `str?` | 群名片 |

### GroupSystemMsg

群系统消息。对应 `get_group_system_msg`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `invited_requests` | `List[GroupSystemRequest]?` | 邀请请求列表 |
| `join_requests` | `List[GroupSystemRequest]?` | 加群请求列表 |

**GroupSystemRequest：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `request_id` | `str` | 请求 ID |
| `invitor_uin` | `str` | 邀请者 QQ |
| `group_id` | `str` | 群号 |
| `group_name` | `str?` | 群名 |
| `checked` | `bool?` | 是否已处理 |
| `actor` | `str` | 处理者 |

### GroupInfoEx

群扩展信息。对应 `get_group_info_ex`（NapCat 扩展 API）。

| 字段 | 类型 | 说明 |
|------|------|------|
| `groupCode` | `str?` | 群号 |
| `resultCode` | `int?` | 结果码 |
| `extInfo` | `GroupExtInfo?` | 扩展详情 |

---

## 用户类型

**源码：** `ncatbot/types/napcat/user.py`

### LoginInfo

登录账号信息。对应 `get_login_info`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `user_id` | `str` | Bot QQ 号 |
| `nickname` | `str?` | Bot 昵称 |

### StrangerInfo

陌生人信息。对应 `get_stranger_info`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `user_id` | `str` | 用户 ID |
| `nickname` | `str?` | 昵称 |
| `sex` | `str?` | 性别 |
| `age` | `int?` | 年龄 |

### FriendInfo

好友信息。对应 `get_friend_list`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `user_id` | `str` | 用户 ID |
| `nickname` | `str?` | 昵称 |
| `remark` | `str?` | 备注 |

---

## 文件类型

**源码：** `ncatbot/types/napcat/file.py`

### GroupFileSystemInfo

群文件系统信息。对应 `get_group_file_system_info`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `file_count` | `int` | 文件数 |
| `limit_count` | `int` | 上限 |
| `used_space` | `int` | 已用空间 |
| `total_space` | `int` | 总空间 |

### GroupFileInfo

群文件信息。对应 `get_group_root_files`, `get_group_files_by_folder`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `group_id` | `str` | 群号 |
| `file_id` | `str` | 文件 ID |
| `file_name` | `str?` | 文件名 |
| `busid` | `int?` | 业务 ID |
| `size` | `int?` | 文件大小 |
| `file_size` | `int?` | 文件大小（备选） |
| `upload_time` | `int?` | 上传时间 |
| `dead_time` | `int?` | 过期时间 |
| `modify_time` | `int?` | 修改时间 |
| `download_times` | `int?` | 下载次数 |
| `uploader` | `str` | 上传者 ID |
| `uploader_name` | `str?` | 上传者名称 |

### GroupFolderInfo

群文件夹信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| `group_id` | `str` | 群号 |
| `folder_id` | `str` | 文件夹 ID |
| `folder_name` | `str?` | 文件夹名 |
| `create_time` | `int?` | 创建时间 |
| `creator` | `str` | 创建者 ID |
| `creator_name` | `str?` | 创建者名称 |
| `total_file_count` | `int?` | 文件总数 |

### GroupFileList

群文件/文件夹列表。对应 `get_group_root_files`, `get_group_files_by_folder`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `files` | `List[GroupFileInfo]?` | 文件列表 |
| `folders` | `List[GroupFolderInfo]?` | 文件夹列表 |

### CreateFolderResult

创建群文件夹的返回结果。对应 `create_group_file_folder`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `groupItem` | `CreateFolderResultGroupItem?` | 容器 |

访问方式：`result.groupItem.folderInfo.folderId`

### FileData

通用文件数据。对应 `get_file`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `file` | `str?` | 文件路径 |
| `file_name` | `str?` | 文件名 |
| `file_size` | `int?` | 大小 |
| `url` | `str?` | 下载 URL |

### DownloadResult

文件下载结果。对应 `download_file`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `file` | `str` | 本地文件路径 |

---

## 系统类型

**源码：** `ncatbot/types/napcat/system.py`

### VersionInfo

版本信息。对应 `get_version_info`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `app_name` | `str?` | 应用名 |
| `protocol_version` | `str?` | 协议版本 |
| `app_version` | `str?` | 应用版本 |

### BotStatus

运行状态。对应 `get_status`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `online` | `bool` | 是否在线 |
| `good` | `bool` | 是否可用 |

### EmojiLikeInfo

表情回应详情。对应 `fetch_emoji_like`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `emojiLikesList` | `List[EmojiLikeUser]?` | 回应用户列表 |
| `cookie` | `str?` | 分页标记 |
| `isLastPage` | `bool?` | 是否最后一页 |

### EmojiLikesResult

消息表情点赞列表。对应 `get_emoji_likes`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `emoji_like_list` | `List[EmojiLikesUser]?` | 点赞用户列表 |

### OcrResult

图片 OCR 结果。对应 `ocr_image`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `texts` | `List[OcrText]?` | 识别文本列表 |

**OcrText：** `text: str?`, `confidence: float?`, `coordinates: list?`

### RecentContact

最近联系人。对应 `get_recent_contact`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `peerUin` | `str?` | 对方 QQ |
| `remark` | `str?` | 备注 |
| `msgTime` | `str?` | 最后消息时间 |
| `chatType` | `int?` | 聊天类型 |
| `peerName` | `str?` | 对方昵称 |
| `lastestMsg` | `RecentContactMessage?` | 最新消息 |

---

## 交叉引用

- [QQ Bot API 方法](../api/) — 使用这些响应类型的 API 方法
- [QQ 事件类型](../events/2_qq_events.md) — QQ 事件实体参考
