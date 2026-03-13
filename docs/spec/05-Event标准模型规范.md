# SPEC-05: Event 标准模型规范

> 定义框架标准事件模型的继承体系、字段规范、Adapter 转换契约和 API 绑定机制。

## 1. 定位

> **当前 Event 模型作为框架标准模型保留，Adapter 负责将平台原始数据转换为此标准模型。**

Event 模型位于 Layer 2（Abstract API），属于框架与外部的交互契约的一部分。所有 Adapter 的 `convert_event()` 方法必须输出符合此规范的 Event 对象。

## 2. 标准 Event 继承体系

```
BaseEvent (ContextMixin, BaseModel)
├── MessageEvent
│   ├── PrivateMessageEvent
│   └── GroupMessageEvent
├── NoticeEvent
│   ├── GroupUploadNoticeEvent
│   ├── GroupAdminNoticeEvent
│   ├── GroupDecreaseNoticeEvent
│   ├── GroupIncreaseNoticeEvent
│   ├── GroupBanNoticeEvent
│   ├── FriendAddNoticeEvent
│   ├── GroupRecallNoticeEvent
│   ├── FriendRecallNoticeEvent
│   └── NotifyEvent
│       ├── PokeNotifyEvent
│       ├── LuckyKingNotifyEvent
│       └── HonorNotifyEvent
├── RequestEvent
│   ├── FriendRequestEvent
│   └── GroupRequestEvent
└── MetaEvent
    ├── LifecycleMetaEvent
    └── HeartbeatMetaEvent
```

## 3. 核心基类

### 3.1 ContextMixin（API 绑定）

> 源码位置：`ncatbot/core/event/context.py`

```python
from ncatbot.core.api.interface import IBotAPI

class ContextMixin(BaseModel):
    """依赖注入混入类

    为 Event 对象注入 IBotAPI 引用，
    使事件处理器可以通过 event.api 调用 Bot API。
    """

    _api: Optional[IBotAPI] = PrivateAttr(default=None)

    def bind_api(self, api: IBotAPI) -> None:
        """绑定 API 实例（由 Adapter.convert_event() 调用）"""
        self._api = api

    @property
    def api(self) -> IBotAPI:
        """获取已绑定的 API 实例"""
        if self._api is None:
            raise RuntimeError("API context not initialized.")
        return self._api
```

**变更点**：`IBotAPI` 类型从 `Protocol` 改为 `ABC`（SPEC-04 定义）。

### 3.2 BaseEvent

```python
class BaseEvent(ContextMixin):
    """所有事件的基类

    公共字段：
        time: 事件发生时间戳
        self_id: 收到事件的机器人 QQ 号
        post_type: 事件类型（message/notice/request/meta_event）
    """

    time: int
    self_id: int
    post_type: str
```

## 4. 消息事件（MessageEvent）

### 4.1 MessageEvent

```python
class MessageEvent(MessageActionMixin, BaseEvent):
    """消息事件基类

    字段：
        message_type: 消息类型（private/group）
        sub_type: 子类型
        message_id: 消息 ID
        user_id: 发送者 QQ 号
        message: 消息内容（MessageArray）
        raw_message: 原始消息文本
        font: 字体
        sender: 发送者信息
    """

    post_type: str = "message"
    message_type: str
    sub_type: str
    message_id: int
    user_id: int
    message: MessageArray
    raw_message: str
    font: int = 0
    sender: Sender
```

### 4.2 GroupMessageEvent / PrivateMessageEvent

```python
class GroupMessageEvent(GroupAdminMixin, MessageEvent):
    """群消息事件"""
    message_type: str = "group"
    group_id: int

class PrivateMessageEvent(MessageEvent):
    """私聊消息事件"""
    message_type: str = "private"
```

## 5. Action Mixin（便捷操作）

### 5.1 MessageActionMixin

```python
class MessageActionMixin:
    async def reply(self, text: str, **kwargs) -> None:
        """回复当前消息"""

    async def delete(self) -> None:
        """撤回当前消息"""
```

### 5.2 GroupAdminMixin

```python
class GroupAdminMixin:
    async def kick(self, reject_add_request: bool = False) -> None:
        """踢出发送者"""

    async def ban(self, duration: int = 30 * 60) -> None:
        """禁言发送者"""
```

### 5.3 RequestActionMixin

```python
class RequestActionMixin:
    async def approve(self, remark: str = "", reason: str = "") -> None:
        """同意请求"""

    async def reject(self, reason: str = "") -> None:
        """拒绝请求"""
```

## 6. Adapter 事件转换契约

### 6.1 转换规则

| 规则编号 | 规则 | 说明 |
|---------|------|------|
| EV-1 | 必须返回标准 Event 子类实例或 None | 不得返回平台特定的 Event 子类 |
| EV-2 | 必须在返回前调用 `event.bind_api(api)` | 确保事件处理器可以调用 API |
| EV-3 | 字段名必须符合标准模型定义 | 平台特定字段名在转换时统一为标准名称 |
| EV-4 | 转换失败返回 None 并记录日志 | 不得抛出异常导致消息丢失 |
| EV-5 | MessageArray 格式统一为 OneBot v11 消息段格式 | `[{"type": "text", "data": {"text": "hello"}}]` |

### 6.2 转换示例（NapCat / OneBot v11）

OneBot v11 原始数据恰好与标准模型一致，NapCatAdapter 的转换几乎是直接映射：

```python
class EventConverter:
    def convert(self, raw_data: dict) -> Optional[BaseEvent]:
        post_type = raw_data.get("post_type")
        if not post_type:
            return None

        # 查找注册的 Event 类
        event_cls = self._find_event_class(post_type, raw_data)
        if not event_cls:
            return None

        # 使用 pydantic 构造（自动校验字段）
        event = event_cls.model_validate(raw_data)

        # 绑定 API
        event.bind_api(self._api)

        return event
```

### 6.3 其他平台适配示例

如果未来接入其他平台（如 Telegram），Adapter 需要将其字段映射到标准模型：

```python
# 假设 Telegram 适配器
class TelegramEventConverter:
    def convert(self, raw_data: dict) -> Optional[BaseEvent]:
        # Telegram 的 update 对象 → 标准 MessageEvent
        if "message" in raw_data:
            tg_msg = raw_data["message"]
            return PrivateMessageEvent(
                time=tg_msg["date"],
                self_id=self._bot_id,
                message_id=tg_msg["message_id"],
                user_id=tg_msg["from"]["id"],
                message=[{"type": "text", "data": {"text": tg_msg.get("text", "")}}],
                raw_message=tg_msg.get("text", ""),
                sender=Sender(user_id=tg_msg["from"]["id"], ...),
                ...
            )
```

## 7. 数据模型

### 7.1 MessageArray

消息内容采用 OneBot v11 消息段格式：

```python
MessageArray = List[MessageSegment]

class MessageSegment(TypedDict):
    type: str       # 消息类型：text, image, at, face, record, ...
    data: dict      # 消息数据，根据 type 不同而不同
```

### 7.2 Sender

```python
class Sender(BaseModel):
    user_id: Optional[int] = None
    nickname: Optional[str] = None
    sex: Optional[str] = None
    age: Optional[int] = None
    card: Optional[str] = None      # 群名片
    area: Optional[str] = None
    level: Optional[str] = None
    role: Optional[str] = None      # owner/admin/member
    title: Optional[str] = None     # 专属头衔
```

## 8. 目录结构

```
ncatbot/core/event/
├── __init__.py
├── context.py          # ContextMixin + IBotAPI 引用
├── mixins.py           # MessageActionMixin, GroupAdminMixin, RequestActionMixin
├── events.py           # 完整 Event 继承体系
├── models.py           # Sender, MessageArray, Forward 等数据模型
└── enums.py            # 事件枚举常量（可选）
```

## 9. Event 合规检查清单

- [ ] 所有 Event 类继承自 `BaseEvent(ContextMixin)`
- [ ] `ContextMixin._api` 类型为 `IBotAPI`（非 Protocol、非具体实现）
- [ ] MessageEvent 包含 `MessageActionMixin`
- [ ] GroupMessageEvent 包含 `GroupAdminMixin`
- [ ] RequestEvent 子类包含 `RequestActionMixin`
- [ ] Event 模型不导入任何 Adapter 特定模块
- [ ] Event 模型不包含协议特定字段（如 OneBot action 名称）
- [ ] Adapter 的 `convert_event()` 遵守 EV-1 ~ EV-5 规则
