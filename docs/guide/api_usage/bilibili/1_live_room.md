# 直播间操作

> Bilibili 直播间相关 API — 弹幕发送、用户禁言、全员禁言与房间信息查询。
>
> 所有方法通过 `self.api.bilibili` 访问，均为 `async`。

---

## 发送弹幕

```python
await self.api.bilibili.send_danmu(room_id=12345, text="Hello!")
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `room_id` | `int` | 直播间 ID |
| `text` | `str` | 弹幕内容 |

---

## 禁言用户

```python
# 禁言 1 小时（默认）
await self.api.bilibili.ban_user(room_id=12345, user_id=67890)

# 禁言 24 小时
await self.api.bilibili.ban_user(room_id=12345, user_id=67890, hour=24)
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `room_id` | `int` | — | 直播间 ID |
| `user_id` | `int` | — | 被禁言的用户 ID |
| `hour` | `int` | `1` | 禁言时长（小时） |

---

## 解除禁言

```python
await self.api.bilibili.unban_user(room_id=12345, user_id=67890)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `room_id` | `int` | 直播间 ID |
| `user_id` | `int` | 被解除禁言的用户 ID |

---

## 全员禁言

```python
await self.api.bilibili.set_room_silent(room_id=12345, enable=True)   # 开启
await self.api.bilibili.set_room_silent(room_id=12345, enable=False)  # 关闭
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `room_id` | `int` | 直播间 ID |
| `enable` | `bool` | `True` 开启全员禁言，`False` 关闭 |

---

## 获取直播间信息

```python
info = await self.api.bilibili.get_room_info(room_id=12345)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `room_id` | `int` | 直播间 ID |

**返回值**：`dict` — 直播间信息（标题、状态、主播信息等）

---

## 实战示例

```python
from ncatbot.core import registrar

class LiveManager(NcatBotPlugin):
    name = "live_manager"
    version = "1.0.0"

    async def on_enable(self):
        await self.api.bilibili.add_live_room(12345)

    @registrar.on_message(platform="bilibili")
    async def on_danmu(self, event):
        # 自动回复弹幕
        if "你好" in event.content:
            await self.api.bilibili.send_danmu(event.room_id, "欢迎！")

        # 违规弹幕自动禁言
        if "广告" in event.content:
            await self.api.bilibili.ban_user(event.room_id, event.user_id, hour=1)
```

---

> **返回**：[Bilibili API 指南](README.md) · **下一篇**：[私信操作](2_private_msg.md)
