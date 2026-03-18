# 通用事件基础

> BaseEvent 基类、Mixin Trait 协议、事件工厂。所有平台的事件实体通用基础设施。

**导入路径：** `from ncatbot.event import BaseEvent, create_entity, Replyable, HasSender, ...`

**源码：** `ncatbot/event/common/`

---

## BaseEvent

所有事件实体的基类。包装 **数据模型**（`BaseEventData`）+ **API 客户端**。

```python
class BaseEvent:
    def __init__(self, data: BaseEventData, api: IAPIClient): ...
```

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `data` | `BaseEventData` | 底层数据模型 |
| `api` | `IAPIClient` | API 客户端实例 |
| `time` | `int` | 事件时间戳 |
| `self_id` | `str` | Bot 自身 ID |
| `post_type` | `str` | 事件顶层类型 |
| `platform` | `str` | 平台标识（`"qq"`, `"bilibili"` 等） |

---

## Mixin Traits

事件行为通过 Mixin 组合实现。平台事件实体多继承所需 Trait，插件代码可用 `isinstance` 检查能力。

```python
from ncatbot.event import Replyable, HasSender

if isinstance(event, Replyable):
    await event.reply(text="收到")

if isinstance(event, HasSender):
    print(f"来自 {event.user_id}")
```

### Replyable

支持回复的事件。

```python
async def reply(self, **kwargs) -> Any: ...
```

不同平台的 `reply()` 签名不同：
- **QQ MessageEvent**：`reply(text=, *, at=, image=, video=, rtf=, at_sender=True)`
- **Bilibili DanmuMsgEvent**：`reply(text, **kwargs)`
- **Bilibili BiliPrivateMessageEvent**：`reply(text, **kwargs)`
- **Bilibili BiliCommentEvent**：`reply(text, **kwargs)`

### Deletable

支持撤回/删除。

```python
async def delete(self) -> Any: ...
```

### HasSender

包含发送者信息。

```python
@property
def user_id(self) -> str: ...

@property
def sender(self) -> Any: ...
```

### GroupScoped

属于群/频道/直播间的事件。

```python
@property
def group_id(self) -> str: ...
```

> Bilibili 直播间事件的 `group_id` 返回 `room_id`。

### Kickable

支持踢出成员。

```python
async def kick(self, **kwargs) -> Any: ...
```

### Bannable

支持禁言。

```python
async def ban(self, duration: int = 1800, **kwargs) -> Any: ...
```

### Approvable

支持同意/拒绝请求。

```python
async def approve(self, **kwargs) -> Any: ...
async def reject(self, **kwargs) -> Any: ...
```

---

## 事件工厂

`create_entity()` 将数据模型转换为事件实体，自动路由到各平台工厂。

```python
from ncatbot.event import create_entity

entity = create_entity(data, api)
# data.platform == "qq"       → QQ 工厂
# data.platform == "bilibili" → Bilibili 工厂
# 未知平台                    → 返回 BaseEvent
```

### 路由策略

1. **精确映射**：根据数据模型类（如 `GroupMessageEventData`）找到对应实体类（如 `GroupMessageEvent`）
2. **降级匹配**：根据 `post_type` 找到该类别的基础实体类（如 `PostType.MESSAGE` → `MessageEvent`）
3. **兜底**：返回 `BaseEvent`

### 注册平台工厂

```python
from ncatbot.event import register_platform_factory

register_platform_factory("my_platform", my_factory_func)
```

工厂签名：`(data: BaseEventData, api: IAPIClient) -> Optional[BaseEvent]`

---

## 交叉引用

- [QQ 事件实体](2_qq_events.md) — QQ 平台事件完整参考
- [Bilibili 事件实体](3_bilibili_events.md) — Bilibili 平台事件完整参考
- [类型参考](../types/) — 数据模型与消息段
