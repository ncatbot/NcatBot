# 群管理与账号操作 API 详解

> QQManage 群管理、好友管理、个人资料与组合 Sugar 的完整参数表、返回值和示例。

通过 `api.qq.manage.xxx()` 调用。源码：`ncatbot/api/qq/manage.py`。

## 群管理

### set_group_kick()

```python
async def set_group_kick(
    self, group_id: Union[str, int], user_id: Union[str, int],
    reject_add_request: bool = False,
) -> None:
```

踢出群成员。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 群号 |
| user_id | str \| int | 是 | 要踢出的用户 QQ 号 |
| reject_add_request | bool | 否 | 是否拒绝再次加群，默认 `False` |



```python
await api.qq.manage.set_group_kick(123456, 654321)
```

### set_group_ban()

```python
async def set_group_ban(
    self, group_id: Union[str, int], user_id: Union[str, int],
    duration: int = 1800,
) -> None:
```

禁言群成员。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 群号 |
| user_id | str \| int | 是 | 要禁言的用户 QQ 号 |
| duration | int | 否 | 禁言时长（秒），默认 `1800`；`0` 表示解除禁言 |



```python
# 禁言 10 分钟
await api.qq.manage.set_group_ban(123456, 654321, duration=600)

# 解除禁言
await api.qq.manage.set_group_ban(123456, 654321, duration=0)
```

### set_group_whole_ban()

```python
async def set_group_whole_ban(
    self, group_id: Union[str, int], enable: bool = True,
) -> None:
```

全员禁言开关。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 群号 |
| enable | bool | 否 | `True` 开启全员禁言，`False` 关闭，默认 `True` |



```python
await api.qq.manage.set_group_whole_ban(123456)          # 开启全员禁言
await api.qq.manage.set_group_whole_ban(123456, False)   # 关闭全员禁言
```

### set_group_admin()

```python
async def set_group_admin(
    self, group_id: Union[str, int], user_id: Union[str, int],
    enable: bool = True,
) -> None:
```

设置或取消管理员。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 群号 |
| user_id | str \| int | 是 | 目标用户 QQ 号 |
| enable | bool | 否 | `True` 设置管理员，`False` 取消，默认 `True` |



### set_group_card()

```python
async def set_group_card(
    self, group_id: Union[str, int], user_id: Union[str, int],
    card: str = "",
) -> None:
```

设置群名片。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 群号 |
| user_id | str \| int | 是 | 目标用户 QQ 号 |
| card | str | 否 | 群名片内容，空字符串表示删除群名片 |



```python
await api.qq.manage.set_group_card(123456, 654321, card="新名片")
```

### set_group_name()

```python
async def set_group_name(
    self, group_id: Union[str, int], name: str,
) -> None:
```

修改群名。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 群号 |
| name | str | 是 | 新群名 |



### set_group_leave()

```python
async def set_group_leave(
    self, group_id: Union[str, int], is_dismiss: bool = False,
) -> None:
```

退出群聊。群主可选择解散。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 群号 |
| is_dismiss | bool | 否 | 是否解散群（仅群主有效），默认 `False` |



### set_group_special_title()

```python
async def set_group_special_title(
    self, group_id: Union[str, int], user_id: Union[str, int],
    special_title: str = "",
) -> None:
```

设置群成员专属头衔。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 群号 |
| user_id | str \| int | 是 | 目标用户 QQ 号 |
| special_title | str | 否 | 专属头衔，空字符串表示删除 |



### send_group_notice()

```python
async def send_group_notice(
    self, group_id: Union[str, int], content: str, image: str = "",
) -> None:
```

发布群公告。`image` 可选，为图片路径或 URL。

### delete_group_notice()

```python
async def delete_group_notice(
    self, group_id: Union[str, int], notice_id: str,
) -> None:
```

删除群公告。

### set_essence_msg()

```python
async def set_essence_msg(self, message_id: Union[str, int]) -> None:
```

设置精华消息。

### delete_essence_msg()

```python
async def delete_essence_msg(self, message_id: Union[str, int]) -> None:
```

移除精华消息。

### set_group_kick_members()

```python
async def set_group_kick_members(
    self, group_id: Union[str, int], user_ids: list,
    reject_add_request: bool = False,
) -> None:
```

批量踢出群成员。

### set_group_remark()

```python
async def set_group_remark(
    self, group_id: Union[str, int], remark: str,
) -> None:
```

设置群备注。

### set_group_sign()

```python
async def set_group_sign(self, group_id: Union[str, int]) -> None:
```

群签到。

### set_group_todo()

```python
async def set_group_todo(
    self, group_id: Union[str, int], message_id: Union[str, int],
) -> None:
```

设置群代办（Todo）。

### set_group_portrait()

```python
async def set_group_portrait(
    self, group_id: Union[str, int], file: str,
) -> None:
```

设置群头像。`file` 为图片路径或 URL。

## 账号与好友操作

### set_friend_add_request()

```python
async def set_friend_add_request(
    self, flag: str, approve: bool = True, remark: str = "",
) -> None:
```

处理加好友请求。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| flag | str | 是 | 加好友请求标识（从事件中获取） |
| approve | bool | 否 | 是否同意，默认 `True` |
| remark | str | 否 | 好友备注（仅同意时有效） |



```python
await api.qq.manage.set_friend_add_request(flag=event.flag, approve=True, remark="通过")
```

### set_group_add_request()

```python
async def set_group_add_request(
    self, flag: str, sub_type: str, approve: bool = True, reason: str = "",
) -> None:
```

处理加群请求。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| flag | str | 是 | 加群请求标识（从事件中获取） |
| sub_type | str | 是 | 请求子类型：`"add"` 或 `"invite"` |
| approve | bool | 否 | 是否同意，默认 `True` |
| reason | str | 否 | 拒绝理由（仅拒绝时有效） |



```python
await api.qq.manage.set_group_add_request(
    flag=event.flag, sub_type="add", approve=False, reason="不满足条件"
)
```

### set_friend_remark()

```python
async def set_friend_remark(
    self, user_id: Union[str, int], remark: str,
) -> None:
```

设置好友备注。

### delete_friend()

```python
async def delete_friend(self, user_id: Union[str, int]) -> None:
```

删除好友。

## 个人资料

### set_self_longnick()

```python
async def set_self_longnick(self, long_nick: str) -> None:
```

设置个性签名。

### set_qq_avatar()

```python
async def set_qq_avatar(self, file: str) -> None:
```

设置 QQ 头像。`file` 为图片路径或 URL。

### set_qq_profile()

```python
async def set_qq_profile(
    self, nickname: str = "", company: str = "", email: str = "",
    college: str = "", personal_note: str = "",
) -> None:
```

设置个人资料。

### set_online_status()

```python
async def set_online_status(
    self, status: int, ext_status: int = 0, custom_status: str = "",
) -> None:
```

设置在线状态。

## 组合 Sugar

### kick_and_block()

```python
async def kick_and_block(
    self,
    group_id: Union[str, int],
    user_id: Union[str, int],
    message_id: Optional[Union[str, int]] = None,
) -> None:
```

组合操作：撤回消息 → 踢出用户 → 拒绝再次加群。如果 `message_id` 不为 `None`，先撤回该消息。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 群号 |
| user_id | str \| int | 是 | 目标用户 QQ 号 |
| message_id | str \| int \| None | 否 | 要撤回的消息 ID |


```python
# 撤回违规消息并踢出用户
await api.qq.manage.kick_and_block(123456, 654321, message_id=msg_id)
```
