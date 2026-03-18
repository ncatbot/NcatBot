# 数据源与查询

> Bilibili 数据源管理与用户查询 — 添加/移除直播间和评论监听，查询用户信息。
>
> 所有方法通过 `self.api.bilibili` 访问，均为 `async`。

---

## 数据源管理

Bilibili 适配器通过"数据源"概念管理监听目标。需要先添加数据源，才能接收对应的事件。

### 添加直播间监听

```python
await self.api.bilibili.add_live_room(room_id=12345)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `room_id` | `int` | 直播间 ID |

添加后，Bot 将接收该直播间的弹幕、礼物、进场等事件。

### 移除直播间监听

```python
await self.api.bilibili.remove_live_room(room_id=12345)
```

### 添加评论监听

```python
await self.api.bilibili.add_comment_watch(
    resource_id="BV1xx411c7mD",
    resource_type="video",
)
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `resource_id` | `str` | — | 资源 ID（BV 号、动态 ID 等） |
| `resource_type` | `str` | `"video"` | 资源类型 |

### 移除评论监听

```python
await self.api.bilibili.remove_comment_watch(resource_id="BV1xx411c7mD")
```

### 列出所有数据源

```python
sources = await self.api.bilibili.list_sources()
for src in sources:
    print(src)
```

**返回值**：`List[Dict[str, Any]]` — 所有已注册的数据源列表

---

## 用户查询

### 获取用户信息

```python
info = await self.api.bilibili.get_user_info(user_id=67890)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `user_id` | `int` | B 站用户 ID |

**返回值**：`dict` — 用户信息（昵称、头像、等级等）

---

## 实战示例

```python
class BiliMonitor(NcatBotPlugin):
    name = "bili_monitor"
    version = "1.0.0"

    async def on_enable(self):
        # 启动时添加监听
        await self.api.bilibili.add_live_room(12345)
        await self.api.bilibili.add_comment_watch("BV1xx411c7mD")

        # 查看当前数据源
        sources = await self.api.bilibili.list_sources()
        print(f"已监听 {len(sources)} 个数据源")

    async def on_disable(self):
        # 停用时清理
        await self.api.bilibili.remove_live_room(12345)
        await self.api.bilibili.remove_comment_watch("BV1xx411c7mD")
```

---

> **返回**：[Bilibili API 指南](README.md) · **上一篇**：[评论操作](3_comment.md)
