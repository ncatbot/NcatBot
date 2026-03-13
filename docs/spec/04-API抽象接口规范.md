# SPEC-04: API 抽象接口规范

> 定义 IBotAPI 抽象基类的完整签名、API 层级关系、Adapter 实现要求和 Event 对象的 API 绑定机制。

## 1. 定位

> **IBotAPI = 与协议无关的、由 Adapter 实现的 Bot 操作接口**

IBotAPI 位于 Layer 2（Abstract API），定义框架期望的所有 Bot 操作。Core 层和 Plugin 层通过此接口调用 API，不直接接触 Adapter 的具体实现。

## 2. 层级关系

```
IBotAPI (抽象接口, core/api/interface.py)
    ↑ 实现
NapCatBotAPI (具体实现, adapter/napcat/api_impl.py)
    内部使用 NapCatProtocol.send(action, params) 进行通信
```

Core 层引用 `IBotAPI`，不引用 `NapCatBotAPI`（规则 D-2）。

## 3. IBotAPI 抽象基类

> 源码位置：`ncatbot/core/api/interface.py`

### 3.1 设计原则

1. **方法签名按语义分类**：消息、群管理、账号、信息查询、文件、支持
2. **参数以 Python 原生类型为主**：`int`, `str`, `list`, `dict`, `bool`
3. **返回值统一**：一般返回 `dict`（API 原始响应）或具体数据模型
4. **可选参数用 `**kwargs` 预留扩展空间**
5. **从现有 BotAPI 提取核心方法**，便捷方法（如 `send_group_text`）由子类或 Mixin 提供

### 3.2 核心方法签名

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union


class IBotAPI(ABC):
    """与协议无关的 Bot API 接口

    此接口定义框架期望的所有 Bot 操作。
    各 Adapter 提供具体实现。

    方法分类：
    1. 消息操作：发送、撤回、转发
    2. 群管理：踢人、禁言、设置管理员
    3. 账号操作：设置资料、好友管理
    4. 信息查询：获取群/好友/消息信息
    5. 文件操作：群文件管理
    6. 辅助功能：戳一戳、点赞等
    """

    # ==================================================================
    # 消息操作
    # ==================================================================

    @abstractmethod
    async def send_private_msg(
        self, user_id: Union[str, int], message: list, **kwargs
    ) -> dict:
        """发送私聊消息"""

    @abstractmethod
    async def send_group_msg(
        self, group_id: Union[str, int], message: list, **kwargs
    ) -> dict:
        """发送群聊消息"""

    @abstractmethod
    async def delete_msg(self, message_id: Union[str, int]) -> None:
        """撤回消息"""

    @abstractmethod
    async def send_forward_msg(
        self,
        message_type: str,
        target_id: Union[str, int],
        messages: list,
        **kwargs,
    ) -> dict:
        """发送合并转发消息"""

    # ==================================================================
    # 群管理
    # ==================================================================

    @abstractmethod
    async def set_group_kick(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        reject_add_request: bool = False,
    ) -> None:
        """踢出群成员"""

    @abstractmethod
    async def set_group_ban(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        duration: int = 30 * 60,
    ) -> None:
        """禁言群成员"""

    @abstractmethod
    async def set_group_whole_ban(
        self, group_id: Union[str, int], enable: bool = True
    ) -> None:
        """全群禁言"""

    @abstractmethod
    async def set_group_admin(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        enable: bool = True,
    ) -> None:
        """设置群管理员"""

    @abstractmethod
    async def set_group_card(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        card: str = "",
    ) -> None:
        """设置群名片"""

    @abstractmethod
    async def set_group_name(
        self, group_id: Union[str, int], name: str
    ) -> None:
        """设置群名称"""

    @abstractmethod
    async def set_group_leave(
        self, group_id: Union[str, int], is_dismiss: bool = False
    ) -> None:
        """退出群组"""

    @abstractmethod
    async def set_group_special_title(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        special_title: str = "",
    ) -> None:
        """设置群成员专属头衔"""

    # ==================================================================
    # 账号操作
    # ==================================================================

    @abstractmethod
    async def set_friend_add_request(
        self, flag: str, approve: bool = True, remark: str = ""
    ) -> None:
        """处理好友请求"""

    @abstractmethod
    async def set_group_add_request(
        self,
        flag: str,
        sub_type: str,
        approve: bool = True,
        reason: str = "",
    ) -> None:
        """处理群请求/邀请"""

    # ==================================================================
    # 信息查询
    # ==================================================================

    @abstractmethod
    async def get_login_info(self) -> dict:
        """获取登录号信息"""

    @abstractmethod
    async def get_stranger_info(
        self, user_id: Union[str, int]
    ) -> dict:
        """获取陌生人信息"""

    @abstractmethod
    async def get_friend_list(self) -> List[dict]:
        """获取好友列表"""

    @abstractmethod
    async def get_group_info(
        self, group_id: Union[str, int]
    ) -> dict:
        """获取群信息"""

    @abstractmethod
    async def get_group_list(self) -> list:
        """获取群列表"""

    @abstractmethod
    async def get_group_member_info(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
    ) -> dict:
        """获取群成员信息"""

    @abstractmethod
    async def get_group_member_list(
        self, group_id: Union[str, int]
    ) -> list:
        """获取群成员列表"""

    @abstractmethod
    async def get_msg(self, message_id: Union[str, int]) -> dict:
        """获取消息"""

    @abstractmethod
    async def get_forward_msg(self, message_id: Union[str, int]) -> dict:
        """获取合并转发消息"""

    # ==================================================================
    # 文件操作
    # ==================================================================

    @abstractmethod
    async def upload_group_file(
        self,
        group_id: Union[str, int],
        file: str,
        name: str,
        folder_id: str = "",
    ) -> None:
        """上传群文件"""

    @abstractmethod
    async def get_group_root_files(
        self, group_id: Union[str, int]
    ) -> dict:
        """获取群根目录文件列表"""

    @abstractmethod
    async def get_group_file_url(
        self, group_id: Union[str, int], file_id: str
    ) -> str:
        """获取群文件 URL"""

    @abstractmethod
    async def delete_group_file(
        self, group_id: Union[str, int], file_id: str
    ) -> None:
        """删除群文件"""

    # ==================================================================
    # 辅助功能
    # ==================================================================

    @abstractmethod
    async def send_like(
        self, user_id: Union[str, int], times: int = 1
    ) -> None:
        """发送好友赞"""

    @abstractmethod
    async def send_poke(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
    ) -> None:
        """发送戳一戳"""
```

## 4. 便捷方法层

IBotAPI 定义核心操作；便捷方法（如 `send_group_text`, `send_group_image`）通过 Mixin 或子类提供，不属于抽象接口：

```python
class BotAPIMixin:
    """便捷方法混入

    基于 IBotAPI 的核心方法提供便捷封装。
    此 Mixin 不定义任何 abstract 方法。
    """

    async def send_group_text(self, group_id, text: str) -> str:
        """便捷方法：发送纯文本群消息"""
        result = await self.send_group_msg(
            group_id, [{"type": "text", "data": {"text": text}}]
        )
        return str(result.get("message_id", ""))

    async def send_group_image(self, group_id, image: str) -> str:
        """便捷方法：发送图片群消息"""
        result = await self.send_group_msg(
            group_id, [{"type": "image", "data": {"file": image}}]
        )
        return str(result.get("message_id", ""))

    # ... 其他便捷方法
```

## 5. 与现有 BotAPI 的对照

### 5.1 现有结构

```
BotAPI(AccountAPI, GroupAPI, MessageAPI, PrivateAPI, SupportAPI)
    ├── AccountAPI(APIComponent) → api_account.py
    ├── GroupAPI(GroupAdminAPI, GroupFileAPI, GroupInfoAPI, GroupMemberAPI)
    │   ├── GroupAdminAPI(APIComponent) → api_group/admin.py
    │   ├── GroupFileAPI(APIComponent) → api_group/file.py
    │   ├── GroupInfoAPI(APIComponent) → api_group/info.py
    │   └── GroupMemberAPI(APIComponent) → api_group/member.py
    ├── MessageAPI(MessageCommonAPI, MessageForwardAPI, MessageRetrieveAPI, ...)
    ├── PrivateAPI(APIComponent) → api_private.py
    └── SupportAPI(APIComponent) → api_support.py
```

### 5.2 迁移策略

1. **IBotAPI** 从以上所有 API 中提取核心 abstract 方法签名
2. **NapCatBotAPI** 继承 IBotAPI + BotAPIMixin，内部使用 NapCatProtocol
3. 现有 Mixin 继承关系（AccountAPI, GroupAPI...）整体迁入 `adapter/napcat/api_impl.py`，作为 NapCatBotAPI 的实现细节
4. 现有 `APIComponent` 基类的 `_preupload_message()` / `_preupload_file()` 逻辑迁入 Adapter 的 PreUpload 模块

### 5.3 APIComponent 基类的变化

| 现有 | 新版 | 说明 |
|------|------|------|
| `APIComponent.__init__(send_callback, service_manager)` | NapCatBotAPI 组件持有 `NapCatProtocol` | 不再传入 service_manager |
| `APIComponent._preupload_message()` | 由 Adapter 的 `preupload_message()` 替代 | 预上传属于 Adapter |
| `APIComponent._preupload_file()` | 由 Adapter 的 `preupload_file()` 替代 | 预上传属于 Adapter |

## 6. Event 对象的 API 绑定

### 6.1 现有 IBotAPI Protocol（context.py）

```python
class IBotAPI(Protocol):
    async def post_group_msg(...): ...
    async def post_private_msg(...): ...
    async def delete_msg(...): ...
    async def set_group_kick(...): ...
    async def set_group_ban(...): ...
    async def set_friend_add_request(...): ...
    async def set_group_add_request(...): ...
```

### 6.2 新版：统一为 IBotAPI ABC

现有的 `IBotAPI Protocol` 将统一为 SPEC-04 中定义的 `IBotAPI ABC`：

```python
# core/event/context.py
from ncatbot.core.api.interface import IBotAPI

class ContextMixin(BaseModel):
    _api: Optional[IBotAPI] = PrivateAttr(default=None)

    def bind_api(self, api: IBotAPI):
        self._api = api

    @property
    def api(self) -> IBotAPI:
        if self._api is None:
            raise RuntimeError("API context not initialized.")
        return self._api
```

### 6.3 Mixin 方法调整

Event Mixin（MessageActionMixin, GroupAdminMixin, RequestActionMixin）的 `self.api` 类型从 Protocol 变为 IBotAPI ABC，方法签名不变：

```python
class MessageActionMixin:
    async def reply(self, text: str, **kwargs):
        # self.api 现在是 IBotAPI 类型
        await self.api.send_group_msg(...)  # 或 send_private_msg

    async def delete(self):
        await self.api.delete_msg(self.message_id)
```

## 7. IBotAPI 合规检查清单

- [ ] 位于 `ncatbot/core/api/interface.py`
- [ ] 所有核心 API 方法定义为 `@abstractmethod`
- [ ] 不导入任何 Adapter 模块
- [ ] 不包含协议特定逻辑（如 echo、action 名称）
- [ ] 参数使用 Python 原生类型
- [ ] Event 的 `ContextMixin._api` 类型为 `IBotAPI`
- [ ] NapCatBotAPI 实现 IBotAPI 全部抽象方法
- [ ] NapCatBotAPI 不被 Core 层直接引用
