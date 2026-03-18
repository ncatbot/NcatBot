# 评论操作

> Bilibili 评论 API — 发送、回复、删除、点赞评论与获取评论列表。
>
> 所有方法通过 `self.api.bilibili` 访问，均为 `async`。

---

## 发送评论

```python
await self.api.bilibili.send_comment(
    resource_id="BV1xx411c7mD",
    resource_type="video",
    text="好视频！",
)
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `resource_id` | `str` | — | 资源 ID（BV 号、动态 ID 等） |
| `resource_type` | `str` | — | 资源类型：`"video"`, `"dynamic"` 等 |
| `text` | `str` | — | 评论内容 |

---

## 回复评论

```python
await self.api.bilibili.reply_comment(
    resource_id="BV1xx411c7mD",
    resource_type="video",
    root_id=123456,      # 根评论 ID
    parent_id=789012,    # 被回复的评论 ID
    text="谢谢！",
)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `resource_id` | `str` | 资源 ID |
| `resource_type` | `str` | 资源类型 |
| `root_id` | `int` | 根评论 ID（楼主评论） |
| `parent_id` | `int` | 被回复的评论 ID |
| `text` | `str` | 回复内容 |

---

## 删除评论

```python
await self.api.bilibili.delete_comment(
    resource_id="BV1xx411c7mD",
    resource_type="video",
    comment_id=123456,
)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `resource_id` | `str` | 资源 ID |
| `resource_type` | `str` | 资源类型 |
| `comment_id` | `int` | 要删除的评论 ID |

---

## 点赞评论

```python
await self.api.bilibili.like_comment(
    resource_id="BV1xx411c7mD",
    resource_type="video",
    comment_id=123456,
)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `resource_id` | `str` | 资源 ID |
| `resource_type` | `str` | 资源类型 |
| `comment_id` | `int` | 要点赞的评论 ID |

---

## 获取评论列表

```python
comments = await self.api.bilibili.get_comments(
    resource_id="BV1xx411c7mD",
    resource_type="video",
    page=1,
)
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `resource_id` | `str` | — | 资源 ID |
| `resource_type` | `str` | — | 资源类型 |
| `page` | `int` | `1` | 页码 |

**返回值**：`list` — 评论列表

---

## 实战示例

```python
class CommentBot(NcatBotPlugin):
    name = "comment_bot"
    version = "1.0.0"

    async def on_enable(self):
        # 监听视频评论
        await self.api.bilibili.add_comment_watch("BV1xx411c7mD", "video")

    @registrar.on_notice(platform="bilibili")
    async def on_new_comment(self, event):
        # 自动回复新评论
        if hasattr(event, "comment_id"):
            await self.api.bilibili.reply_comment(
                resource_id=event.resource_id,
                resource_type=event.resource_type,
                root_id=event.comment_id,
                parent_id=event.comment_id,
                text="感谢评论！",
            )
```

---

> **返回**：[Bilibili API 指南](README.md) · **上一篇**：[私信操作](2_private_msg.md) · **下一篇**：[数据源与查询](4_source_query.md)
