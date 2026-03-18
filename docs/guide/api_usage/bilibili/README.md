# Bilibili 平台 API 使用指南

> Bilibili 平台（B 站适配器）的完整 API 使用教程 — 直播间操作、私信、评论与数据源管理。

---

## Quick Reference

### 访问方式

| 方式 | 类型 | 场景 |
|------|------|------|
| `self.api.bilibili` | `IBiliAPIClient` | 插件中 |
| `bot.api.bilibili` | `IBiliAPIClient` | 非插件模式 |
| `event.reply()` | — | 通用回复（弹幕/评论回复） |

### API 功能分类

| 类别 | 典型方法 | 说明 |
|------|---------|------|
| 直播间操作 | `send_danmu`, `ban_user`, `set_room_silent` | 弹幕、禁言、房间管理 |
| 私信 | `send_private_msg`, `send_private_image` | 私信文字与图片 |
| 评论 | `send_comment`, `reply_comment`, `delete_comment` | 视频/动态评论操作 |
| 数据源管理 | `add_live_room`, `add_comment_watch` | 监听直播间/评论 |
| 用户查询 | `get_user_info` | 获取用户信息 |

### 快速示例

```python
from ncatbot.plugin import NcatBotPlugin
from ncatbot.core import registrar

class BiliPlugin(NcatBotPlugin):
    name = "bili_demo"
    version = "1.0.0"

    async def on_enable(self):
        # 添加直播间监听
        await self.api.bilibili.add_live_room(12345)

    @registrar.on_message(platform="bilibili")
    async def on_msg(self, event):
        await event.reply(text="收到弹幕！")
```

---

## 本目录索引

| 文档 | 内容 |
|------|------|
| [直播间操作](1_live_room.md) | 弹幕发送、用户禁言、全员禁言、房间信息 |
| [私信操作](2_private_msg.md) | 发送私信文字/图片、获取私信历史 |
| [评论操作](3_comment.md) | 发送/回复/删除/点赞评论 |
| [数据源与查询](4_source_query.md) | 直播间/评论监听管理、用户信息查询 |

---

> **返回**：[Bot API 使用指南](../README.md) · **相关**：[Bilibili 消息发送](../../send_message/bilibili/README.md) · [Bilibili API 参考](../../../reference/api/bilibili/1_api.md)
