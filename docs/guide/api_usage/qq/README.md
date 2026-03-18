# QQ 平台 API 使用指南

> QQ 平台（NapCat 适配器）的完整 API 使用教程 — 消息收发、群管理、信息查询与文件操作。

---

## Quick Start

### 获取 API 客户端

插件中通过 `self.api.qq` 访问，类型为 `QQAPIClient`：

```python
from ncatbot.plugin import NcatBotPlugin
from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent


class MyPlugin(NcatBotPlugin):
    name = "my_plugin"
    version = "1.0.0"

    @registrar.on_group_command("ping")
    async def on_ping(self, event: GroupMessageEvent):
        await self.api.qq.post_group_msg(event.group_id, text="pong!")
```

> 最便捷的回复方式：`await event.reply(text="pong!")`，内部自动引用原消息并 @发送者。

### 发送消息

```python
# 语法糖 — 最常用
await self.api.qq.post_group_msg(group_id, text="Hello!")
await self.api.qq.post_group_msg(group_id, text="看图", image="/path/to/img.jpg")
await self.api.qq.post_private_msg(user_id, text="私聊消息")

# 原子 API — 手动构造消息段
await self.api.qq.messaging.send_group_msg(group_id, [{"type": "text", "data": {"text": "你好"}}])
```

### 群管理

```python
# 禁言 60 秒
await self.api.qq.manage.set_group_ban(group_id, user_id, 60)

# 踢人
await self.api.qq.manage.set_group_kick(group_id, user_id)

# 撤回 + 踢出 + 拉黑（一步到位）
await self.api.qq.manage.kick_and_block(group_id, user_id, message_id)
```

### 信息查询

```python
# 获取群成员列表
members = await self.api.qq.query.get_group_member_list(group_id)

# 获取消息详情
msg = await self.api.qq.query.get_msg(message_id)
```

---

## Quick Reference

### 访问方式

| 方式 | 类型 | 场景 |
|------|------|------|
| `self.api.qq` | `QQAPIClient` | 插件中（推荐，含语法糖） |
| `bot.api.qq` | `QQAPIClient` | 非插件模式 |
| `event.reply()` | — | 最便捷的回复方式 |

### API 分层结构

| 层级 | 访问方式 | 说明 |
|------|---------|------|
| 事件回复 | `event.reply(text=, at=, image=, video=, rtf=)` | 最便捷，自动引用 + @发送者 |
| 语法糖 | `self.api.qq.post_group_msg(...)` | 关键字自动组装 MessageArray |
| 消息 API | `self.api.qq.messaging.*` | QQMessaging — 底层 OB11 消息操作 |
| 群管理 | `self.api.qq.manage.*` | QQManage — 踢人/禁言/设置等 |
| 信息查询 | `self.api.qq.query.*` | QQQuery — 群/好友/消息查询 |
| 文件操作 | `self.api.qq.file.*` | QQFile — 上传/下载/文件夹管理 |

### sugar — 便捷消息发送

| 方法 | 关键参数 | 说明 |
|------|---------|------|
| `post_group_msg(group_id, ...)` | `text=, at=, reply=, image=, video=, rtf=` | 群消息（关键字自动组装） |
| `post_private_msg(user_id, ...)` | `text=, reply=, image=, video=, rtf=` | 私聊消息 |
| `post_group_array_msg(group_id, msg)` | `msg: MessageArray` | 直接发送 MessageArray |
| `post_private_array_msg(user_id, msg)` | `msg: MessageArray` | 直接发送 MessageArray |
| `send_group_text(group_id, text)` | | 纯文本 |
| `send_group_image(group_id, image)` | | 图片 |
| `send_group_sticker(group_id, image)` | | 动画表情 |
| `send_group_record(group_id, file)` | | 语音 |
| `send_group_video(group_id, video)` | | 视频 |
| `send_group_file(group_id, file, name=)` | | 文件 |
| `send_private_text(user_id, text)` | | 私聊纯文本 |
| `send_private_image(user_id, image)` | | 私聊图片 |
| `post_group_forward_msg(group_id, forward)` | `forward: Forward` | 群合并转发 |
| `post_private_forward_msg(user_id, forward)` | `forward: Forward` | 私聊合并转发 |

> 私聊还有 `send_private_record`, `send_private_file`, `send_private_video` 等方法，签名与群聊版对称。

### messaging — 消息操作

| 方法 | 关键参数 | 说明 |
|------|---------|------|
| `send_group_msg(group_id, message)` | `message: list` | 发送群消息（原始格式） |
| `send_private_msg(user_id, message)` | `message: list` | 发送私聊消息 |
| `delete_msg(message_id)` | | 撤回消息 |
| `send_forward_msg(message_type, target_id, messages)` | | 合并转发 |
| `send_poke(group_id, user_id)` | | 群内戳一戳 |
| `friend_poke(user_id)` | | 好友戳一戳 |
| `send_like(user_id, times=1)` | | 点赞 |
| `set_msg_emoji_like(message_id, emoji_id, set=True)` | | 消息表情回应 |
| `mark_group_msg_as_read(group_id)` | | 标记群消息已读 |
| `mark_private_msg_as_read(user_id)` | | 标记私聊已读 |
| `mark_all_as_read()` | | 全部已读 |
| `forward_friend_single_msg(user_id, message_id)` | | 转发到好友 |
| `forward_group_single_msg(group_id, message_id)` | | 转发到群 |
| `get_group_msg_history(group_id, message_seq=, count=20)` | | 群消息历史 |
| `get_friend_msg_history(user_id, message_seq=, count=20)` | | 好友消息历史 |

### manage — 群管理 / 账号操作

| 方法 | 关键参数 | 说明 |
|------|---------|------|
| `set_group_kick(group_id, user_id, reject_add_request=False)` | | 踢出群成员 |
| `set_group_ban(group_id, user_id, duration=1800)` | | 禁言 |
| `set_group_whole_ban(group_id, enable=True)` | | 全员禁言 |
| `set_group_admin(group_id, user_id, enable=True)` | | 设置/取消管理员 |
| `set_group_card(group_id, user_id, card="")` | | 设置群名片 |
| `set_group_name(group_id, name)` | | 修改群名 |
| `set_group_leave(group_id, is_dismiss=False)` | | 退群/解散群 |
| `set_group_special_title(group_id, user_id, special_title="")` | | 设置专属头衔 |
| `send_group_notice(group_id, content, image="")` | | 发布群公告 |
| `delete_group_notice(group_id, notice_id)` | | 删除群公告 |
| `set_essence_msg(message_id)` | | 设置精华消息 |
| `delete_essence_msg(message_id)` | | 移除精华消息 |
| `set_group_kick_members(group_id, user_ids, ...)` | | 批量踢人 |
| `set_friend_add_request(flag, approve=True, remark="")` | | 处理好友请求 |
| `set_group_add_request(flag, sub_type, approve=True, reason="")` | | 处理加群请求 |
| `kick_and_block(group_id, user_id, message_id=None)` | | 撤回+踢出+拉黑 |

### query — 信息查询

| 方法 | 返回类型 | 说明 |
|------|---------|------|
| `get_login_info()` | `LoginInfo` | 获取登录号信息 |
| `get_friend_list()` | `List[FriendInfo]` | 好友列表 |
| `get_group_info(group_id)` | `GroupInfo` | 群信息 |
| `get_group_list()` | `List[GroupInfo]` | 群列表 |
| `get_group_member_info(group_id, user_id)` | `GroupMemberInfo` | 群成员信息 |
| `get_group_member_list(group_id)` | `List[GroupMemberInfo]` | 群成员列表 |
| `get_stranger_info(user_id)` | `StrangerInfo` | 陌生人信息 |
| `get_msg(message_id)` | `MessageData` | 获取消息详情 |
| `get_forward_msg(message_id)` | `ForwardMessageData` | 获取合并转发内容 |
| `get_group_msg_history(group_id, ...)` | `MessageHistory` | 群消息历史 |
| `get_friend_msg_history(user_id, ...)` | `MessageHistory` | 好友消息历史 |
| `get_essence_msg_list(group_id)` | `List[EssenceMessage]` | 精华消息列表 |
| `get_group_honor_info(group_id, type="all")` | `GroupHonorInfo` | 群荣誉信息 |
| `get_group_notice(group_id)` | `List[GroupNotice]` | 群公告 |
| `get_status()` | `BotStatus` | 运行状态 |
| `get_version_info()` | `VersionInfo` | 版本信息 |

> 完整查询方法还包括 `get_group_at_all_remain`, `get_group_shut_list`, `get_group_system_msg` 等。

### file — 文件操作

| 方法 | 说明 |
|------|------|
| `upload_group_file(group_id, file, name, folder_id="")` | 上传群文件 |
| `upload_private_file(user_id, file, name)` | 上传私聊文件 |
| `download_file(url=, file=, headers=)` | 下载文件 |
| `get_group_root_files(group_id)` | 获取群根目录文件 |
| `get_group_file_url(group_id, file_id)` | 获取文件下载链接 |
| `delete_group_file(group_id, file_id)` | 删除群文件 |
| `create_group_file_folder(group_id, name, parent_id="")` | 创建文件夹 |
| `delete_group_folder(group_id, folder_id)` | 删除文件夹 |

---

## 本目录索引

| 文档 | 内容 |
|------|------|
| [消息发送详解](1_messaging.md) | sugar 方法、原子 messaging API、合并转发 |
| [群管理详解](2_manage.md) | .manage 每个方法的参数与示例 |
| [查询与文件操作](3_query_support.md) | .query + .file 方法详解 |

---

> **返回**：[Bot API 使用指南](../README.md) · **相关**：[QQ 消息发送指南](../../send_message/qq/README.md) · [QQ API 参考](../../../reference/api/qq/1_message_api.md)
