# API Trait 协议

> 跨平台 API 能力协议 — 各平台 APIClient 按功能实现的 Protocol 接口。

---

## 概览

NcatBot 将 API 能力拆分为 4 个 Trait 协议（`ncatbot/api/traits/`），各平台按需实现：

| Trait | 功能 | QQ | Bilibili |
|-------|------|:--:|:--------:|
| `IMessaging` | 消息发送与撤回 | ✅ | 部分 |
| `IGroupManage` | 群/频道管理 | ✅ | 部分 |
| `IQuery` | 信息查询 | ✅ | 部分 |
| `IFileTransfer` | 文件上传/下载 | ✅ | ❌ |

---

## IMessaging — 消息收发

```python
from ncatbot.api.traits import IMessaging
```

| 方法 | 说明 |
|------|------|
| `send_private_msg(user_id, message)` | 发送私聊消息 |
| `send_group_msg(group_id, message)` | 发送群消息 |
| `delete_msg(message_id)` | 撤回消息 |
| `send_forward_msg(message_type, target_id, messages)` | 合并转发 |

```python
# 跨平台消息发送
client = self.api.platform("qq")
if isinstance(client.messaging, IMessaging):
    await client.messaging.send_group_msg(group_id, message)
```

---

## IGroupManage — 群管理

```python
from ncatbot.api.traits import IGroupManage
```

| 方法 | 说明 |
|------|------|
| `set_group_kick(group_id, user_id, reject_add_request=False)` | 踢出成员 |
| `set_group_ban(group_id, user_id, duration=1800)` | 禁言 |
| `set_group_whole_ban(group_id, enable=True)` | 全员禁言 |
| `set_group_admin(group_id, user_id, enable=True)` | 设置管理员 |
| `set_group_name(group_id, name)` | 修改群名 |
| `set_group_leave(group_id, is_dismiss=False)` | 退群 |

---

## IQuery — 信息查询

```python
from ncatbot.api.traits import IQuery
```

| 方法 | 说明 |
|------|------|
| `get_login_info()` | 获取登录信息 |
| `get_stranger_info(user_id)` | 陌生人/用户信息 |
| `get_friend_list()` | 好友列表 |
| `get_group_info(group_id)` | 群信息 |
| `get_group_list()` | 群列表 |
| `get_group_member_info(group_id, user_id)` | 群成员信息 |
| `get_group_member_list(group_id)` | 群成员列表 |

---

## IFileTransfer — 文件传输

```python
from ncatbot.api.traits import IFileTransfer
```

| 方法 | 说明 |
|------|------|
| `upload_group_file(group_id, file, name, folder_id="")` | 上传群文件 |
| `download_file(url="", file="", headers="")` | 下载文件 |

---

## 在插件中使用 Trait

Trait 协议的主要用途是编写跨平台插件时进行能力检查：

```python
from ncatbot.api.traits import IMessaging, IGroupManage

class CrossPlatformPlugin(NcatBotPlugin):
    name = "cross_platform"

    @registrar.on_group_command("ban")
    async def on_ban(self, event, target=None):
        # 获取当前平台的 API
        client = self.api.platform(event.platform)

        # 检查平台是否支持群管理
        if isinstance(client.manage, IGroupManage):
            await client.manage.set_group_ban(event.group_id, target.user_id)
        else:
            await event.reply(text="当前平台不支持禁言操作")
```

---

> **返回**：[通用 API](README.md) · **相关**：[事件方法](1_event_methods.md)
