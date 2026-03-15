# 查询与支持操作

> `.info`（`InfoExtension`）+ `.support`（`SupportExtension`）命名空间的完整方法详解，以及请求处理与错误处理最佳实践。

---

## 信息查询（.info 命名空间）

通过 `self.api.info` 访问 `InfoExtension` 提供的只读查询操作。

### get_login_info — 获取登录信息

```python
async def get_login_info(self) -> dict
```

**返回值**：`{"user_id": 10001, "nickname": "MyBot"}`

```python
@registrar.on_group_command("查登录信息")
async def on_login_info(self, event: GroupMessageEvent):
    info = await self.api.info.get_login_info()
    await event.reply(
        f"QQ: {info.get('user_id')}\n昵称: {info.get('nickname')}"
    )
```

---

### get_friend_list — 好友列表

```python
async def get_friend_list(self) -> List[dict]
```

**返回值**：好友信息列表，每个元素包含 `user_id`、`nickname`、`remark` 等字段。

```python
friends = await self.api.info.get_friend_list()
for f in friends:
    print(f"{f['nickname']} ({f['user_id']})")
```

---

### get_group_list — 群列表

```python
async def get_group_list(self) -> list
```

**返回值**：群信息列表，每个元素包含 `group_id`、`group_name`、`member_count` 等字段。

```python
@registrar.on_group_command("查群列表")
async def on_group_list(self, event: GroupMessageEvent):
    groups = await self.api.info.get_group_list()
    lines = [f"共加入 {len(groups)} 个群:"]
    for g in groups[:10]:
        lines.append(f"  {g.get('group_name', '未知')} ({g.get('group_id')})")
    if len(groups) > 10:
        lines.append(f"  ...还有 {len(groups) - 10} 个群")
    await event.reply("\n".join(lines))
```

---

### get_group_member_info — 群成员信息

```python
async def get_group_member_info(
    self,
    group_id: Union[str, int],
    user_id: Union[str, int],
) -> dict
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `group_id` | `str \| int` | 群号 |
| `user_id` | `str \| int` | 群成员 QQ |

**返回值**：包含 `nickname`、`card`（群名片）、`role`（`owner`/`admin`/`member`）、`join_time` 等字段。

```python
@registrar.on_group_command("查成员")
async def on_member_info(self, event: GroupMessageEvent, target: At = None):
    if target is None:
        await event.reply("请 @一个用户")
        return
    info = await self.api.info.get_group_member_info(event.group_id, target.qq)
    await event.reply(
        f"昵称: {info.get('nickname')}\n"
        f"群名片: {info.get('card', '无')}\n"
        f"角色: {info.get('role')}"
    )
```

---

### get_group_member_list — 群成员列表

```python
async def get_group_member_list(self, group_id: Union[str, int]) -> list
```

**返回值**：群成员信息列表（结构同 `get_group_member_info` 的返回值）。

```python
members = await self.api.info.get_group_member_list(group_id)
admin_count = sum(1 for m in members if m.get("role") in ("owner", "admin"))
await event.reply(f"群成员 {len(members)} 人，其中管理员 {admin_count} 人")
```

---

### get_msg — 查询消息详情

```python
async def get_msg(self, message_id: Union[str, int]) -> dict
```

**返回值**：消息详情，包含 `message_id`、`message`（消息段列表）、`raw_message`、`sender` 等字段。

```python
from ncatbot.types import Reply

@registrar.on_group_command("转发")
async def on_forward(self, event: GroupMessageEvent):
    replies = event.message.filter(Reply)
    if not replies:
        await event.reply("请先回复一条消息")
        return

    msg_data = await self.api.info.get_msg(replies[0].id)
    raw = msg_data.get("raw_message", "（无内容）")
    await event.reply(text=f"原消息内容:\n{raw}")
```

---

### 其他查询方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `get_stranger_info` | `(user_id: str\|int) -> dict` | 获取陌生人信息 |
| `get_group_info` | `(group_id: str\|int) -> dict` | 获取群信息 |
| `get_forward_msg` | `(message_id: str\|int) -> dict` | 获取合并转发消息内容 |
| `get_group_root_files` | `(group_id: str\|int) -> dict` | 获取群根目录文件列表 |
| `get_group_file_url` | `(group_id: str\|int, file_id: str) -> str` | 获取群文件下载链接 |

---

## 文件操作（.support 命名空间）

通过 `self.api.support` 访问 `SupportExtension` 提供的辅助功能。

### upload_group_file — 上传群文件

```python
async def upload_group_file(
    self,
    group_id: Union[str, int],
    file: str,
    name: str,
    folder_id: str = "",
) -> None
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `group_id` | `str \| int` | — | 群号 |
| `file` | `str` | — | 本地文件路径或 URL |
| `name` | `str` | — | 文件显示名称 |
| `folder_id` | `str` | `""` | 上传到的文件夹 ID，空为根目录 |

```python
await self.api.support.upload_group_file(
    group_id=123456,
    file="/path/to/report.pdf",
    name="月报.pdf",
)
```

> **注意**：`upload_group_file` 通过群文件系统上传。若需要以消息形式发送文件，请使用 `self.api.send_group_file(group_id, file, name)`（sugar 方法）。

---

### delete_group_file — 删除群文件

```python
async def delete_group_file(
    self,
    group_id: Union[str, int],
    file_id: str,
) -> None
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `group_id` | `str \| int` | 群号 |
| `file_id` | `str` | 文件 ID（通过 `info.get_group_root_files` 获取） |

```python
# 获取群文件列表 → 找到目标文件 → 删除
files = await self.api.info.get_group_root_files(group_id)
for f in files.get("files", []):
    if f.get("file_name") == "旧文件.pdf":
        await self.api.support.delete_group_file(group_id, f["file_id"])
        break
```

---

### send_like — 点赞

```python
async def send_like(
    self,
    user_id: Union[str, int],
    times: int = 1,
) -> None
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `user_id` | `str \| int` | — | 目标用户 QQ |
| `times` | `int` | `1` | 点赞次数 |

```python
await self.api.support.send_like(user_id, times=10)
```

---

## 请求处理

好友请求和加群请求通过 `manage` 命名空间进行处理。通常在 `RequestEvent` 的处理器中调用。

### set_friend_add_request — 处理好友请求

```python
async def set_friend_add_request(
    self,
    flag: str,
    approve: bool = True,
    remark: str = "",
) -> None
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `flag` | `str` | — | 请求标识（从 `RequestEvent` 中获取） |
| `approve` | `bool` | `True` | `True` 同意，`False` 拒绝 |
| `remark` | `str` | `""` | 同意后的备注名 |

```python
from ncatbot.event import FriendRequestEvent

@registrar.on_friend_request()
async def on_friend_request(self, event: FriendRequestEvent):
    # 自动同意好友请求
    await self.api.manage.set_friend_add_request(
        flag=event.flag,
        approve=True,
        remark="新朋友",
    )
```

---

### set_group_add_request — 处理群请求

```python
async def set_group_add_request(
    self,
    flag: str,
    sub_type: str,
    approve: bool = True,
    reason: str = "",
) -> None
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `flag` | `str` | — | 请求标识 |
| `sub_type` | `str` | — | 请求子类型：`"add"`（加群）或 `"invite"`（邀请） |
| `approve` | `bool` | `True` | `True` 同意，`False` 拒绝 |
| `reason` | `str` | `""` | 拒绝理由（仅拒绝时有效） |

```python
from ncatbot.event import GroupRequestEvent

@registrar.on_group_request()
async def on_group_request(self, event: GroupRequestEvent):
    if event.sub_type == "invite":
        # 自动同意邀请入群
        await self.api.manage.set_group_add_request(
            flag=event.flag,
            sub_type=event.sub_type,
            approve=True,
        )
    else:
        # 加群请求需要人工审核，先拒绝
        await self.api.manage.set_group_add_request(
            flag=event.flag,
            sub_type=event.sub_type,
            approve=False,
            reason="请联系管理员",
        )
```

---

## 错误处理与日志

### _LoggingAPIProxy 自动日志

`BotAPIClient` 内部通过 `_LoggingAPIProxy` 代理所有底层 `IBotAPI` 的异步方法调用，自动输出 `INFO` 级别日志，格式如下：

```
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
        await self.api.manage.set_group_kick(event.group_id, target.qq)
        await event.reply(f"已踢出 {target.qq}")
    except Exception as e:
        LOG.error(f"踢人失败: {e}")
        await event.reply("操作失败，请检查 Bot 权限")
```

**建议**：

1. **权限检查在先**：调用群管理 API 前，先通过 RBAC 或 `get_group_member_info` 确认 Bot 和操作者的权限
2. **善用日志**：`_LoggingAPIProxy` 已自动记录所有调用，出错时查看 `logs/bot.log.*` 即可定位
3. **避免死循环**：在处理请求事件时，注意不要无条件触发新的请求

---

> **返回**：[Bot API 使用指南](README.md) · **相关**：[群管理详解](2_manage.md)
