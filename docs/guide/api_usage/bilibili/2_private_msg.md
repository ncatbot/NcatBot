# 私信操作

> Bilibili 私信 API — 发送文字/图片私信与获取私信历史。
>
> 所有方法通过 `self.api.bilibili` 访问，均为 `async`。

---

## 发送私信

```python
await self.api.bilibili.send_private_msg(user_id=67890, content="你好！")
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `user_id` | `int` | 目标用户 ID |
| `content` | `str` | 私信文字内容 |

---

## 发送私信图片

```python
await self.api.bilibili.send_private_image(user_id=67890, image_url="https://example.com/img.png")
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `user_id` | `int` | 目标用户 ID |
| `image_url` | `str` | 图片 URL |

---

## 获取私信历史

```python
history = await self.api.bilibili.get_session_history(user_id=67890, count=20)
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `user_id` | `int` | — | 目标用户 ID |
| `count` | `int` | `20` | 拉取条数 |

**返回值**：`list` — 私信历史记录列表

---

## 实战示例

```python
@registrar.on_private_message(platform="bilibili")
async def on_bili_pm(self, event):
    # 自动回复私信
    await self.api.bilibili.send_private_msg(event.user_id, "收到你的消息！")

    # 查看历史记录
    history = await self.api.bilibili.get_session_history(event.user_id, count=5)
    print(f"最近 {len(history)} 条私信")
```

---

> **返回**：[Bilibili API 指南](README.md) · **上一篇**：[直播间操作](1_live_room.md) · **下一篇**：[评论操作](3_comment.md)
