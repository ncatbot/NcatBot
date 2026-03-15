# API 参考

> Bot API 层完整参考 — NcatBot 5.0 所有对外 API 的签名、参数与用法索引。

---

## Quick Start

### 获取 BotAPI

在插件中通过 `ctx.api` 获取 `BotAPIClient` 实例：

```python
from ncatbot.plugin import on_group_message, EventContext

@on_group_message()
async def handle(ctx: EventContext):
    api = ctx.api  # BotAPIClient 实例
```

### 最常用方法示例

**1. 发送群消息（便捷方式）**

```python
# post_group_msg 自动组装 MessageArray，支持 text/at/reply/image/video 关键字
await api.post_group_msg(group_id, text="Hello!", at=user_id)

# 回复消息并附图
await api.post_group_msg(group_id, text="看这个", reply=msg_id, image="https://example.com/img.png")
```

**2. 发送群消息（原始方式）**

```python
# send_group_msg 需要手动构造消息段列表
result = await api.send_group_msg(group_id, [
    {"type": "text", "data": {"text": "hello"}}
])
print(result["message_id"])
```

**3. 撤回消息**

```python
await api.delete_msg(message_id)
```

### 架构总览

```
BotAPIClient
├── send_group_msg()        ← 高频 API（顶层直调）
├── send_private_msg()
├── delete_msg()
├── send_forward_msg()
├── send_poke()
├── post_group_msg()        ← MessageSugarMixin（便捷方法）
├── send_group_text()
├── ...
├── .manage                 ← ManageExtension（群管理 / 账号操作）
│   ├── set_group_ban()
│   └── ...
├── .info                   ← InfoExtension（信息查询）
│   ├── get_group_list()
│   └── ...
└── .support                ← SupportExtension（文件管理 / 杂项）
    ├── upload_group_file()
    └── ...
```

> **类型别名**：文档中 `Union[str, int]` 简写为 `str | int`。

---

## API 全方法速查

### 消息操作 — 核心方法

直接通过 `api.xxx()` 调用。

| 方法签名 | 返回值 | 说明 |
|---|---|---|
| `send_group_msg(group_id, message, **kwargs)` | `dict` | 发送群消息（消息段列表） |
| `send_private_msg(user_id, message, **kwargs)` | `dict` | 发送私聊消息（消息段列表） |
| `delete_msg(message_id)` | `None` | 撤回消息 |
| `send_forward_msg(message_type, target_id, messages, **kwargs)` | `dict` | 发送合并转发消息 |
| `send_poke(group_id, user_id)` | `None` | 发送群戳一戳 |

### 消息操作 — 便捷发送

直接通过 `api.xxx()` 调用（`MessageSugarMixin`）。

| 方法签名 | 返回值 | 说明 |
|---|---|---|
| `post_group_msg(group_id, text=, at=, reply=, image=, video=, rtf=)` | `dict` | 便捷群消息（关键字自动组装） |
| `post_private_msg(user_id, text=, reply=, image=, video=, rtf=)` | `dict` | 便捷私聊消息 |
| `post_group_array_msg(group_id, msg)` | `dict` | 直接发送 MessageArray 到群 |
| `post_private_array_msg(user_id, msg)` | `dict` | 直接发送 MessageArray 到私聊 |

### 消息操作 — 群消息 Sugar

直接通过 `api.xxx()` 调用。

| 方法签名 | 返回值 | 说明 |
|---|---|---|
| `send_group_text(group_id, text)` | `dict` | 发送群纯文本 |
| `send_group_plain_text(group_id, text)` | `dict` | 使用 PlainText 段发送群文本 |
| `send_group_image(group_id, image)` | `dict` | 发送群图片 |
| `send_group_record(group_id, file)` | `dict` | 发送群语音 |
| `send_group_file(group_id, file, name=)` | `dict` | 以消息形式发送群文件 |
| `send_group_video(group_id, video)` | `dict` | 发送群视频 |
| `send_group_sticker(group_id, image)` | `dict` | 发送群动画表情 |

### 消息操作 — 私聊消息 Sugar

直接通过 `api.xxx()` 调用。

| 方法签名 | 返回值 | 说明 |
|---|---|---|
| `send_private_text(user_id, text)` | `dict` | 发送私聊纯文本 |
| `send_private_plain_text(user_id, text)` | `dict` | 使用 PlainText 段发送私聊文本 |
| `send_private_image(user_id, image)` | `dict` | 发送私聊图片 |
| `send_private_record(user_id, file)` | `dict` | 发送私聊语音 |
| `send_private_file(user_id, file, name=)` | `dict` | 以消息形式发送私聊文件 |
| `send_private_video(user_id, video)` | `dict` | 发送私聊视频 |
| `send_private_sticker(user_id, image)` | `dict` | 发送私聊动画表情 |
| `send_private_dice(user_id, value=)` | `dict` | 发送骰子魔法表情 |
| `send_private_rps(user_id, value=)` | `dict` | 发送猜拳魔法表情 |

### 消息操作 — 合并转发 Sugar

直接通过 `api.xxx()` 调用。

| 方法签名 | 返回值 | 说明 |
|---|---|---|
| `post_group_forward_msg(group_id, forward)` | `dict` | 发送群合并转发 |
| `post_private_forward_msg(user_id, forward)` | `dict` | 发送私聊合并转发 |
| `send_group_forward_msg_by_id(group_id, message_ids)` | `dict` | 通过消息 ID 列表逐条转发群消息 |
| `send_private_forward_msg_by_id(user_id, message_ids)` | `dict` | 通过消息 ID 列表逐条转发私聊消息 |

### 群管理与账号操作

通过 `api.manage.xxx()` 调用（`ManageExtension`）。

| 方法签名 | 返回值 | 说明 |
|---|---|---|
| `set_group_kick(group_id, user_id, reject_add_request=)` | `None` | 踢出群成员 |
| `set_group_ban(group_id, user_id, duration=)` | `None` | 禁言群成员（duration=0 解禁） |
| `set_group_whole_ban(group_id, enable=)` | `None` | 全员禁言开关 |
| `set_group_admin(group_id, user_id, enable=)` | `None` | 设置/取消管理员 |
| `set_group_card(group_id, user_id, card=)` | `None` | 设置群名片 |
| `set_group_name(group_id, name)` | `None` | 修改群名 |
| `set_group_leave(group_id, is_dismiss=)` | `None` | 退群（群主可解散） |
| `set_group_special_title(group_id, user_id, special_title=)` | `None` | 设置专属头衔 |
| `set_friend_add_request(flag, approve=, remark=)` | `None` | 处理好友请求 |
| `set_group_add_request(flag, sub_type, approve=, reason=)` | `None` | 处理加群请求 |
| `kick_and_block(group_id, user_id, message_id=)` | `None` | 撤回 + 踢出 + 拒绝再加群 |

### 信息查询

通过 `api.info.xxx()` 调用（`InfoExtension`）。

| 方法签名 | 返回值 | 说明 |
|---|---|---|
| `get_login_info()` | `dict` | 获取登录号信息 |
| `get_stranger_info(user_id)` | `dict` | 获取陌生人信息 |
| `get_friend_list()` | `List[dict]` | 获取好友列表 |
| `get_group_info(group_id)` | `dict` | 获取群信息 |
| `get_group_list()` | `list` | 获取群列表 |
| `get_group_member_info(group_id, user_id)` | `dict` | 获取群成员信息 |
| `get_group_member_list(group_id)` | `list` | 获取群成员列表 |
| `get_msg(message_id)` | `dict` | 获取消息详情 |
| `get_forward_msg(message_id)` | `dict` | 获取合并转发消息内容 |
| `get_group_root_files(group_id)` | `dict` | 获取群文件根目录 |
| `get_group_file_url(group_id, file_id)` | `str` | 获取群文件下载 URL |

### 支持操作

通过 `api.support.xxx()` 调用（`SupportExtension`）。

| 方法签名 | 返回值 | 说明 |
|---|---|---|
| `upload_group_file(group_id, file, name, folder_id=)` | `None` | 上传群文件 |
| `delete_group_file(group_id, file_id)` | `None` | 删除群文件 |
| `send_like(user_id, times=)` | `None` | 给用户点赞 |

---

## 深入阅读

各模块的完整参数表、返回值说明与使用示例：

| 子文档 | 内容 |
|---|---|
| [消息 API — 核心方法与便捷方法](1a_message_api.md) | 核心消息方法 + MessageSugarMixin 便捷方法（post_group_msg / post_private_msg）的参数与示例 |
| [消息 API — Sugar 快捷方法](1b_message_api.md) | 群消息 / 私聊消息 / 合并转发的各类 Sugar 快捷方法参数一览 |
| [群管理 API 详解](2_manage_api.md) | ManageExtension 群管理 / 账号操作 / 组合 Sugar 的参数、返回值与示例 |
| [信息查询与支持操作 API 详解](3_info_support_api.md) | InfoExtension 信息查询 + SupportExtension 文件管理与辅助操作的参数、返回值与示例 |

### 相关文档

- [架构文档](../architecture.md) — 系统整体架构
- [插件开发指南](../guide/plugin/) — 插件开发入门
