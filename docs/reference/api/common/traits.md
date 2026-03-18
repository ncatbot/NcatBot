# Trait 协议参考

> 跨平台 API Trait 协议的完整签名 — `IMessaging`, `IGroupManage`, `IQuery`, `IFileTransfer`。
>
> 源码：`ncatbot/api/traits/`

---

## IMessaging — 消息收发

```python
from ncatbot.api.traits import IMessaging
```

```python
@runtime_checkable
class IMessaging(Protocol):

    async def send_private_msg(
        self, user_id: Union[str, int], message: list, **kwargs: Any
    ) -> Any: ...

    async def send_group_msg(
        self, group_id: Union[str, int], message: list, **kwargs: Any
    ) -> Any: ...

    async def delete_msg(self, message_id: Union[str, int]) -> None: ...

    async def send_forward_msg(
        self,
        message_type: str,
        target_id: Union[str, int],
        messages: list,
        **kwargs: Any,
    ) -> Any: ...
```

---

## IGroupManage — 群管理

```python
from ncatbot.api.traits import IGroupManage
```

```python
@runtime_checkable
class IGroupManage(Protocol):

    async def set_group_kick(
        self, group_id: Union[str, int], user_id: Union[str, int],
        reject_add_request: bool = False,
    ) -> None: ...

    async def set_group_ban(
        self, group_id: Union[str, int], user_id: Union[str, int],
        duration: int = 1800,
    ) -> None: ...

    async def set_group_whole_ban(
        self, group_id: Union[str, int], enable: bool = True,
    ) -> None: ...

    async def set_group_admin(
        self, group_id: Union[str, int], user_id: Union[str, int],
        enable: bool = True,
    ) -> None: ...

    async def set_group_name(
        self, group_id: Union[str, int], name: str,
    ) -> None: ...

    async def set_group_leave(
        self, group_id: Union[str, int], is_dismiss: bool = False,
    ) -> None: ...
```

---

## IQuery — 信息查询

```python
from ncatbot.api.traits import IQuery
```

```python
@runtime_checkable
class IQuery(Protocol):

    async def get_login_info(self) -> Any: ...

    async def get_stranger_info(self, user_id: Union[str, int]) -> Any: ...

    async def get_friend_list(self) -> Any: ...

    async def get_group_info(self, group_id: Union[str, int]) -> Any: ...

    async def get_group_list(self) -> Any: ...

    async def get_group_member_info(
        self, group_id: Union[str, int], user_id: Union[str, int],
    ) -> Any: ...

    async def get_group_member_list(
        self, group_id: Union[str, int],
    ) -> Any: ...
```

---

## IFileTransfer — 文件传输

```python
from ncatbot.api.traits import IFileTransfer
```

```python
@runtime_checkable
class IFileTransfer(Protocol):

    async def upload_group_file(
        self, group_id: Union[str, int], file: str, name: str,
        folder_id: str = "",
    ) -> None: ...

    async def download_file(
        self, url: str = "", file: str = "", headers: str = "",
    ) -> Any: ...
```

---

## 平台实现情况

| Trait 方法 | QQ | Bilibili |
|-----------|:--:|:--------:|
| `send_private_msg` | ✅ | ✅（纯文本） |
| `send_group_msg` | ✅ | ✅（弹幕） |
| `delete_msg` | ✅ | ✅（删除评论） |
| `send_forward_msg` | ✅ | ❌ |
| `set_group_kick` | ✅ | ❌ |
| `set_group_ban` | ✅ | ✅（直播间禁言） |
| `set_group_whole_ban` | ✅ | ✅（直播间全员禁言） |
| `get_login_info` | ✅ | ❌ |
| `get_group_info` | ✅ | ✅（直播间信息） |
| `upload_group_file` | ✅ | ❌ |
| `download_file` | ✅ | ❌ |
