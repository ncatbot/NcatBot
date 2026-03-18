# 事件方法

> 跨平台事件行为 Mixin — 通过 `isinstance` 检查事件能力，安全调用通用方法。

---

## 概览

事件实体通过多继承组合行为 Mixin，插件代码可用 `isinstance` 检查事件是否支持某操作：

```python
from ncatbot.event import Replyable, Deletable, Kickable

@registrar.on_message()
async def on_msg(self, event):
    if isinstance(event, Replyable):
        await event.reply(text="收到")
```

所有 Mixin 定义在 `ncatbot/event/common/mixins.py`，通过 `ncatbot.event` 导入。

---

## Replyable — 回复

支持回复的事件（消息事件、评论事件等）。

```python
async def reply(self, **kwargs) -> Any
```

| 平台 | 支持的关键字参数 |
|------|----------------|
| QQ | `text=, at=, image=, video=, rtf=`（自动引用 + @发送者） |
| Bilibili | `text=`（弹幕回复 / 评论回复，取决于事件类型） |

```python
# 最常用的回复方式
await event.reply(text="pong!")

# QQ 平台支持富文本回复
await event.reply(text="看图", image="photo.jpg")
```

---

## Deletable — 撤回/删除

支持撤回或删除的事件。

```python
async def delete(self) -> Any
```

```python
# 撤回触发事件的消息
await event.delete()
```

| 平台 | 行为 |
|------|------|
| QQ | 撤回消息（需要权限） |
| Bilibili | 删除评论（需要权限） |

---

## HasSender — 发送者信息

包含发送者信息的事件。

```python
@property
def user_id(self) -> str

@property
def sender(self) -> Any
```

```python
print(f"消息来自: {event.user_id}")
print(f"发送者昵称: {event.sender.nickname}")
```

---

## GroupScoped — 群/频道作用域

属于群或频道的事件。

```python
@property
def group_id(self) -> str
```

```python
if isinstance(event, GroupScoped):
    print(f"来自群 {event.group_id}")
```

---

## Kickable — 踢出成员

支持踢出成员的事件（群消息事件等）。

```python
async def kick(self, **kwargs) -> Any
```

```python
# 踢出发送违规消息的用户
await event.kick()
```

---

## Bannable — 禁言

支持禁言的事件。

```python
async def ban(self, duration: int = 1800, **kwargs) -> Any
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| duration | int | 1800 | 禁言时长（秒），0 = 解除 |

```python
await event.ban(duration=600)   # 禁言 10 分钟
await event.ban(duration=0)     # 解除禁言
```

---

## Approvable — 同意/拒绝

支持审批的事件（好友请求、加群请求等）。

```python
async def approve(self, **kwargs) -> Any
async def reject(self, **kwargs) -> Any
```

```python
from ncatbot.event import Approvable

@registrar.on_friend_request()
async def on_request(self, event):
    if isinstance(event, Approvable):
        await event.approve()
```

---

## 跨平台插件示例

```python
from ncatbot.event import Replyable, GroupScoped, Bannable

@registrar.on_message()
async def cross_platform_handler(self, event):
    """处理所有平台的消息"""
    if isinstance(event, Replyable):
        await event.reply(text=f"来自 {event.platform} 的消息已收到")

    if isinstance(event, GroupScoped):
        print(f"群/频道: {event.group_id}")

    if isinstance(event, Bannable):
        # 可以禁言的事件
        pass
```

---

> **返回**：[通用 API](README.md) · **相关**：[API Trait 协议](2_traits.md)
