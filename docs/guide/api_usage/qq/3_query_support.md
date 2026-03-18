# 查询与文件操作

> `.query` 和 `.file` 命名空间的常用方法和使用场景。完整参数表见 [reference/api/qq/3_info_support_api.md](../../../reference/api/qq/3_info_support_api.md)。

---

## 信息查询（.query 命名空间）

### 常用查询示例

```python
# 获取登录信息
info = await self.api.qq.query.get_login_info()
# {"user_id": 10001, "nickname": "MyBot"}

# 群列表
groups = await self.api.qq.query.get_group_list()

# 群成员信息
member = await self.api.qq.query.get_group_member_info(event.group_id, target.user_id)
# 含 nickname, card, role("owner"/"admin"/"member"), join_time

# 查询消息详情（通过消息 ID）
msg_data = await self.api.qq.query.get_msg(message_id)
```

### 方法速查

| 方法 | 说明 |
|------|------|
| `get_login_info()` | 获取 Bot 登录信息 |
| `get_friend_list()` | 好友列表 |
| `get_group_list()` | 群列表 |
| `get_group_info(gid)` | 群信息 |
| `get_group_member_info(gid, uid)` | 群成员详情 |
| `get_group_member_list(gid)` | 群成员列表 |
| `get_stranger_info(uid)` | 陌生人信息 |
| `get_msg(message_id)` | 查询消息详情 |
| `get_forward_msg(msg_id)` | 合并转发内容 |
| `get_group_notice(gid)` | 群公告 |
| `get_essence_msg_list(gid)` | 精华消息列表 |
| `get_group_honor_info(gid, type="all")` | 群荣誉信息 |
| `get_group_at_all_remain(gid)` | @全体成员 剩余次数 |
| `get_group_shut_list(gid)` | 群禁言列表 |
| `get_group_system_msg()` | 群系统消息 |
| `get_recent_contact(count=10)` | 最近联系人 |
| `get_version_info()` | 版本信息 |
| `get_status()` | 运行状态 |
| `ocr_image(image)` | OCR 图片识别 |

---

## 文件操作（.file 命名空间）

```python
# 上传群文件
await self.api.qq.file.upload_group_file(group_id, "/path/to/report.pdf", "月报.pdf")

# 获取群文件下载链接
url = await self.api.qq.query.get_group_file_url(group_id, file_id)

# 删除群文件
await self.api.qq.file.delete_group_file(group_id, file_id)
```

> `upload_group_file` 通过群文件系统上传。以消息形式发送文件请用 `self.api.qq.send_group_file()`（sugar 方法）。

### 方法速查

| 方法 | 说明 |
|------|------|
| `upload_group_file(gid, file, name, folder_id="")` | 上传群文件 |
| `delete_group_file(gid, file_id)` | 删除群文件 |
| `create_group_file_folder(gid, name, parent_id="")` | 创建群文件夹 |
| `delete_group_folder(gid, folder_id)` | 删除群文件夹 |
| `upload_private_file(uid, file, name)` | 上传私聊文件 |
| `download_file(url="", file="", headers="")` | 下载文件到本地 |

### 群文件查询（通过 .query）

| 方法 | 说明 |
|------|------|
| `get_group_root_files(gid)` | 群根目录文件列表 |
| `get_group_files_by_folder(gid, folder_id)` | 指定文件夹内容 |
| `get_group_file_url(gid, file_id)` | 获取文件下载 URL |
| `get_group_file_system_info(gid)` | 群文件系统信息 |
| `get_private_file_url(uid, file_id)` | 私聊文件下载 URL |
| `get_file(file_id)` | 通用文件信息 |

---

## 请求处理

好友请求和加群请求通过 `.manage` 命名空间处理。通常在 `RequestEvent` 的处理器中调用。

```python
from ncatbot.event.qq import FriendRequestEvent, GroupRequestEvent

@registrar.on_friend_request()
async def on_friend_request(self, event: FriendRequestEvent):
    # 自动同意好友请求
    await event.approve()

@registrar.on_group_request()
async def on_group_request(self, event: GroupRequestEvent):
    if event.sub_type == "invite":
        await self.api.qq.manage.set_group_add_request(
            flag=event.flag, sub_type=event.sub_type, approve=True,
        )
```

---

## 延伸阅读

- [查询与支持 API 参考](../../../reference/api/qq/3_info_support_api.md) — 完整签名与返回值
- [消息发送指南](1_messaging.md) — 消息发送方式
```

---

## 错误处理与日志

### _LoggingAPIProxy 自动日志

`BotAPIClient` 内部通过 `_LoggingAPIProxy` 代理所有底层 `IAPIClient` 的异步方法调用，自动输出 `INFO` 级别日志，格式如下：

```text
INFO  BotAPIClient API调用 send_group_msg 123456 [{"type":"text","data":{"text":"hello"}}]
```

日志特点：
- **自动截断**：参数超过 2000 字符时自动截断并添加 `...`
- **零侵入**：无需手动记录日志，所有 API 调用都被自动追踪
- **dict/list 自动序列化**：JSON 格式，便于排查

### 异常处理最佳实践

```python
@registrar.on_group_command("踢人")
async def on_kick(self, event: GroupMessageEvent, target: At = None):
    if target is None:
        await event.reply("请 @一个用户")
        return

    try:
        await self.api.qq.manage.set_group_kick(event.group_id, target.user_id)
        await event.reply(f"已踢出 {target.user_id}")
    except Exception as e:
        LOG.error(f"踢人失败: {e}")
        await event.reply("操作失败，请检查 Bot 权限")
```

**建议**：

1. **权限检查在先**：调用群管理 API 前，先通过 RBAC 或 `get_group_member_info` 确认 Bot 和操作者的权限
2. **善用日志**：`_LoggingAPIProxy` 已自动记录所有调用，出错时查看 `logs/bot.log.*` 即可定位
3. **避免死循环**：在处理请求事件时，注意不要无条件触发新的请求

---

> **返回**：[Bot API 使用指南](../README.md) · **相关**：[群管理详解](2_manage.md)
