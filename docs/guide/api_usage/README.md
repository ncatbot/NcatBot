# Bot API 使用指南

> 掌握 `BotAPIClient` 的全部能力 — 消息收发、群管理、信息查询、文件操作与请求处理。

---

## Quick Start

### 获取 API 客户端

插件中通过 `self.api` 访问，类型为 `BotAPIClient`：

```python
from ncatbot.plugin import NcatBotPlugin
from ncatbot.core.registry import registrar
from ncatbot.event import GroupMessageEvent


class MyPlugin(NcatBotPlugin):
    name = "my_plugin"
    version = "1.0.0"

    @registrar.on_group_command("ping")
    async def on_ping(self, event: GroupMessageEvent):
        await self.api.post_group_msg(event.group_id, text="pong!")
```

事件对象也提供 `event.api`（底层 `IBotAPI`），但推荐优先使用 `self.api`（含语法糖 + 自动日志）。

> **最便捷的回复方式**：`await event.reply(text="pong!")`，内部自动引用原消息并 @发送者。

### 发送消息

```python
# 语法糖 — 最常用
await self.api.post_group_msg(group_id, text="Hello!")
await self.api.post_group_msg(group_id, text="看图", image="/path/to/img.jpg")
await self.api.post_private_msg(user_id, text="私聊消息")

# 原子 API — 手动构造消息段
await self.api.send_group_msg(group_id, [{"type": "text", "data": {"text": "你好"}}])
```

### 群管理

```python
# 禁言 60 秒
await self.api.manage.set_group_ban(group_id, user_id, 60)

# 踢人
await self.api.manage.set_group_kick(group_id, user_id)

# 撤回 + 踢出 + 拉黑（一步到位）
await self.api.manage.kick_and_block(group_id, user_id, message_id)
```

### API 分层结构

| 层级 | 访问方式 | 说明 |
|------|---------|------|
| 高频原子 API | `self.api.send_group_msg(...)` | 直接平铺在顶层，最常用 |
| 语法糖 | `self.api.post_group_msg(...)` | `MessageSugarMixin` 提供，关键字自动组装消息 |
| 群管理 | `self.api.manage.set_group_ban(...)` | `ManageExtension` 提供 |
| 信息查询 | `self.api.info.get_group_list()` | `InfoExtension` 提供 |
| 辅助功能 | `self.api.support.upload_group_file(...)` | `SupportExtension` 提供 |

---

## API 速查表

### 顶层高频 API

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `send_group_msg` | `(group_id, message, **kwargs)` | `dict` | 发送群消息 |
| `send_private_msg` | `(user_id, message, **kwargs)` | `dict` | 发送私聊消息 |
| `send_forward_msg` | `(message_type, target_id, messages, **kwargs)` | `dict` | 发送合并转发 |
| `delete_msg` | `(message_id)` | `None` | 撤回消息 |
| `send_poke` | `(group_id, user_id)` | `None` | 戳一戳 |

### 语法糖方法（MessageSugarMixin）

#### post_group_msg / post_private_msg

```python
async def post_group_msg(
    self, group_id, text=None, at=None, reply=None, image=None, video=None, rtf=None,
) -> dict

async def post_private_msg(
    self, user_id, text=None, reply=None, image=None, video=None, rtf=None,
) -> dict
```

#### 单类型快捷方法

| 方法 | 参数 | 说明 |
|------|------|------|
| `send_group_text` | `(group_id, text)` | 发送群纯文本 |
| `send_group_image` | `(group_id, image)` | 发送群图片 |
| `send_group_record` | `(group_id, file)` | 发送群语音 |
| `send_group_file` | `(group_id, file, name=None)` | 发送群文件消息 |
| `send_group_video` | `(group_id, video)` | 发送群视频 |
| `send_group_sticker` | `(group_id, image)` | 发送群动画表情 |
| `send_private_text` | `(user_id, text)` | 发送私聊纯文本 |
| `send_private_image` | `(user_id, image)` | 发送私聊图片 |
| `send_private_record` | `(user_id, file)` | 发送私聊语音 |
| `send_private_file` | `(user_id, file, name=None)` | 发送私聊文件消息 |
| `send_private_video` | `(user_id, video)` | 发送私聊视频 |
| `send_private_sticker` | `(user_id, image)` | 发送私聊动画表情 |

#### 合并转发快捷方法

| 方法 | 参数 | 说明 |
|------|------|------|
| `post_group_forward_msg` | `(group_id, forward)` | 发送群合并转发（`Forward` 对象） |
| `post_private_forward_msg` | `(user_id, forward)` | 发送私聊合并转发 |
| `send_group_forward_msg_by_id` | `(group_id, message_ids)` | 通过消息 ID 列表转发群消息 |
| `send_private_forward_msg_by_id` | `(user_id, message_ids)` | 通过消息 ID 列表转发私聊消息 |

#### MessageArray 快捷方法

| 方法 | 参数 | 说明 |
|------|------|------|
| `post_group_array_msg` | `(group_id, msg)` | 发送 `MessageArray` 群消息 |
| `post_private_array_msg` | `(user_id, msg)` | 发送 `MessageArray` 私聊消息 |

### .manage 群管理

| 方法 | 参数 | 说明 |
|------|------|------|
| `set_group_kick` | `(group_id, user_id, reject_add_request=False)` | 踢出群成员 |
| `set_group_ban` | `(group_id, user_id, duration=1800)` | 禁言（`0` 解禁） |
| `set_group_whole_ban` | `(group_id, enable=True)` | 全员禁言 |
| `set_group_admin` | `(group_id, user_id, enable=True)` | 设置/取消管理员 |
| `set_group_card` | `(group_id, user_id, card="")` | 设置群名片 |
| `set_group_name` | `(group_id, name)` | 设置群名 |
| `set_group_leave` | `(group_id, is_dismiss=False)` | 退群 |
| `set_group_special_title` | `(group_id, user_id, special_title="")` | 设置专属头衔 |
| `set_friend_add_request` | `(flag, approve=True, remark="")` | 处理好友请求 |
| `set_group_add_request` | `(flag, sub_type, approve=True, reason="")` | 处理群请求 |
| `kick_and_block` | `(group_id, user_id, message_id=None)` | 撤回+踢出+拉黑 |

### .info 信息查询

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `get_login_info` | `()` | `dict` | Bot 登录信息 |
| `get_stranger_info` | `(user_id)` | `dict` | 陌生人信息 |
| `get_friend_list` | `()` | `List[dict]` | 好友列表 |
| `get_group_info` | `(group_id)` | `dict` | 群信息 |
| `get_group_list` | `()` | `list` | 群列表 |
| `get_group_member_info` | `(group_id, user_id)` | `dict` | 群成员信息 |
| `get_group_member_list` | `(group_id)` | `list` | 群成员列表 |
| `get_msg` | `(message_id)` | `dict` | 消息详情 |
| `get_forward_msg` | `(message_id)` | `dict` | 合并转发内容 |
| `get_group_root_files` | `(group_id)` | `dict` | 群根目录文件 |
| `get_group_file_url` | `(group_id, file_id)` | `str` | 群文件下载链接 |

### .support 辅助功能

| 方法 | 参数 | 说明 |
|------|------|------|
| `upload_group_file` | `(group_id, file, name, folder_id="")` | 上传群文件 |
| `delete_group_file` | `(group_id, file_id)` | 删除群文件 |
| `send_like` | `(user_id, times=1)` | 点赞 |

---

## 常见错误码

OneBot v11 协议的 API 调用可能返回以下错误：

| retcode | 含义 | 常见原因 |
|---------|------|----------|
| `0` | 成功 | — |
| `1` | 异步操作已提交 | 操作需要排队处理 |
| `100` | 参数缺失或无效 | 检查 `group_id`、`user_id` 等参数 |
| `102` | 操作失败 | Bot 权限不足 / 目标不存在 |
| `103` | 操作超时 | NapCat 与 QQ 通信超时 |
| `104` | 未找到资源 | 消息已撤回 / 群已退出 |
| `200` | Bot 未连接 | NapCat 未启动或连接已断开 |

---

## 深入阅读

| 文档 | 内容 |
|------|------|
| [消息发送详解](1_messaging.md) | `send_group_msg` / `send_private_msg` / `send_forward_msg` / `delete_msg` / `send_poke` 完整参数表与示例，语法糖方法完整示例 |
| [群管理详解](2_manage.md) | `.manage` 命名空间每个方法的完整参数表与示例 |
| [查询与支持操作](3_query_support.md) | `.info` + `.support` 方法详解、请求处理、错误处理最佳实践 |

> **相关文档**：[消息发送指南](../send_message/README.md) · [架构文档](../../architecture.md) · [插件开发入门](../plugin/README.md)
