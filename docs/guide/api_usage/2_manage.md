# 群管理详解

> `.manage` 命名空间（`ManageExtension`）提供的群管理操作完整参数表与示例。
>
> 所有方法通过 `self.api.manage` 访问，均为 `async`，返回 `None`。

---

> **注意**：执行群管理操作需要 Bot 拥有对应的群权限（如管理员 / 群主）。

## set_group_kick — 踢人

```python
async def set_group_kick(
    self,
    group_id: Union[str, int],
    user_id: Union[str, int],
    reject_add_request: bool = False,
) -> None
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `group_id` | `str \| int` | — | 群号 |
| `user_id` | `str \| int` | — | 被踢用户 QQ |
| `reject_add_request` | `bool` | `False` | 是否拒绝此人再次加群 |

```python
@registrar.on_group_command("踢")
async def on_kick(self, event: GroupMessageEvent, target: At = None):
    if target is None:
        await event.reply("请 @一个用户")
        return
    await self.api.manage.set_group_kick(event.group_id, target.qq)
    await event.reply(f"已踢出用户 {target.qq}")
```

---

## set_group_ban — 禁言

```python
async def set_group_ban(
    self,
    group_id: Union[str, int],
    user_id: Union[str, int],
    duration: int = 1800,
) -> None
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `group_id` | `str \| int` | — | 群号 |
| `user_id` | `str \| int` | — | 被禁言用户 QQ |
| `duration` | `int` | `1800` | 禁言时长（秒），`0` 为解除禁言 |

```python
# 禁言 60 秒
await self.api.manage.set_group_ban(event.group_id, target.qq, 60)

# 解除禁言
await self.api.manage.set_group_ban(event.group_id, target.qq, 0)
```

---

## set_group_whole_ban — 全员禁言

```python
async def set_group_whole_ban(
    self,
    group_id: Union[str, int],
    enable: bool = True,
) -> None
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `group_id` | `str \| int` | — | 群号 |
| `enable` | `bool` | `True` | `True` 开启全员禁言，`False` 关闭 |

```python
# 开启全员禁言
await self.api.manage.set_group_whole_ban(group_id, True)

# 关闭全员禁言
await self.api.manage.set_group_whole_ban(group_id, False)
```

---

## set_group_admin — 设置管理员

```python
async def set_group_admin(
    self,
    group_id: Union[str, int],
    user_id: Union[str, int],
    enable: bool = True,
) -> None
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `group_id` | `str \| int` | — | 群号 |
| `user_id` | `str \| int` | — | 目标用户 QQ |
| `enable` | `bool` | `True` | `True` 设置管理员，`False` 取消管理员 |

```python
# 设置为管理员（需要群主权限）
await self.api.manage.set_group_admin(group_id, user_id, True)

# 取消管理员
await self.api.manage.set_group_admin(group_id, user_id, False)
```

---

## set_group_card — 设置群名片

```python
async def set_group_card(
    self,
    group_id: Union[str, int],
    user_id: Union[str, int],
    card: str = "",
) -> None
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `group_id` | `str \| int` | — | 群号 |
| `user_id` | `str \| int` | — | 目标用户 QQ |
| `card` | `str` | `""` | 新群名片，空字符串表示删除群名片 |

```python
await self.api.manage.set_group_card(event.group_id, target.qq, "新名片")
```

---

## set_group_name — 设置群名

```python
async def set_group_name(
    self,
    group_id: Union[str, int],
    name: str,
) -> None
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `group_id` | `str \| int` | 群号 |
| `name` | `str` | 新群名 |

```python
await self.api.manage.set_group_name(group_id, "新群名称")
```

---

## set_group_leave — 退群

```python
async def set_group_leave(
    self,
    group_id: Union[str, int],
    is_dismiss: bool = False,
) -> None
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `group_id` | `str \| int` | — | 群号 |
| `is_dismiss` | `bool` | `False` | 如果 Bot 是群主，是否解散群 |

```python
await self.api.manage.set_group_leave(group_id)
```

---

## set_group_special_title — 设置专属头衔

```python
async def set_group_special_title(
    self,
    group_id: Union[str, int],
    user_id: Union[str, int],
    special_title: str = "",
) -> None
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `group_id` | `str \| int` | — | 群号 |
| `user_id` | `str \| int` | — | 目标用户 QQ |
| `special_title` | `str` | `""` | 专属头衔，空字符串表示删除头衔 |

```python
# 需要群主权限
await self.api.manage.set_group_special_title(group_id, user_id, "🏆 最强王者")
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
await self.api.manage.kick_and_block(
    group_id=event.group_id,
    user_id=event.user_id,
    message_id=event.message_id,  # 可选，传入则先撤回
)
```

---

> **返回**：[Bot API 使用指南](README.md) · **相关**：[查询与支持操作](3_query_support.md)
