# 群管理详解

> `.manage` 命名空间提供的群管理操作使用指南。完整参数表见 [reference/api/qq/2_manage_api.md](../../../reference/api/qq/2_manage_api.md)。
>
> 所有方法通过 `self.api.qq.manage` 访问，均为 `async`。执行需要 Bot 拥有对应群权限。

---

## 核心操作

### 踢人

```python
@registrar.on_group_command("踢")
async def on_kick(self, event: GroupMessageEvent, target: At = None):
    if target is None:
        await event.reply("请 @一个用户")
        return
    await self.api.qq.manage.set_group_kick(event.group_id, target.user_id)
    await event.reply(f"已踢出用户 {target.user_id}")
```

### 禁言 / 解除禁言

```python
await self.api.qq.manage.set_group_ban(event.group_id, target.user_id, 60)   # 禁言 60 秒
await self.api.qq.manage.set_group_ban(event.group_id, target.user_id, 0)    # 解除禁言
```

### 全员禁言

```python
await self.api.qq.manage.set_group_whole_ban(group_id, True)   # 开启
await self.api.qq.manage.set_group_whole_ban(group_id, False)  # 关闭
```

---

## 方法速查

| 方法 | 说明 |
|------|------|
| `set_group_kick(gid, uid, reject_add_request=False)` | 踢人 |
| `set_group_ban(gid, uid, duration=1800)` | 禁言（0=解除） |
| `set_group_whole_ban(gid, enable=True)` | 全员禁言 |
| `set_group_admin(gid, uid, enable=True)` | 设置/取消管理员 |
| `set_group_card(gid, uid, card="")` | 设置群名片 |
| `set_group_name(gid, name)` | 设置群名 |
| `set_group_leave(gid, is_dismiss=False)` | 退群 |
| `set_group_special_title(gid, uid, special_title="")` | 设置专属头衔 |
| `send_group_notice(gid, content, image="")` | 发布群公告 |
| `delete_group_notice(gid, notice_id)` | 删除群公告 |
| `set_essence_msg(message_id)` | 设为精华消息 |
| `delete_essence_msg(message_id)` | 取消精华消息 |
| `set_group_kick_members(gid, user_ids, reject=False)` | 批量踢人 |
| `set_group_remark(gid, remark)` | 设置群备注 |
| `set_friend_add_request(flag, approve=True, remark="")` | 处理好友请求 |
| `set_group_add_request(flag, sub_type, approve=True, reason="")` | 处理群请求 |
| `set_friend_remark(uid, remark)` | 设置好友备注 |
| `delete_friend(uid)` | 删除好友 |

---

## 延伸阅读

- [群管理 API 参考](../../../reference/api/qq/2_manage_api.md) — 完整参数表与返回值
- [RBAC 权限控制](../../rbac/) — 限制谁可以执行管理操作
- [示例：群管理机器人](../../../../examples/11_group_manager/) — 完整实现

```python
# 需要群主权限
await self.api.qq.manage.set_group_special_title(group_id, user_id, "🏆 最强王者")
```

---

## kick_and_block — 组合操作

`ManageExtension` 提供的组合操作方法：

```python
async def kick_and_block(
    self,
    group_id: Union[str, int],
    user_id: Union[str, int],
    message_id: Optional[Union[str, int]] = None,
) -> None
```

**功能**：撤回消息 → 踢出用户 → 拒绝再加群（一步到位）。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `group_id` | `str \| int` | — | 群号 |
| `user_id` | `str \| int` | — | 被踢用户 QQ |
| `message_id` | `str \| int \| None` | `None` | 可选，传入则先撤回该消息 |

```python
# 撤回违规消息 + 踢出 + 拉黑
await self.api.qq.manage.kick_and_block(
    group_id=event.group_id,
    user_id=event.user_id,
    message_id=event.message_id,  # 可选，传入则先撤回
)
```

---

> **返回**：[Bot API 使用指南](../README.md) · **相关**：[查询与支持操作](3_query_support.md)
