# 通用 API

> 跨平台通用的事件方法和 API Trait 协议 — 适用于所有已接入平台。

---

## Quick Reference

NcatBot 通过 Trait 协议实现跨平台统一：

| 层级 | 说明 | 适用场景 |
|------|------|---------|
| 事件方法 | `event.reply()`, `event.delete()` 等 | 处理器内直接操作事件 |
| API Trait | `IMessaging`, `IGroupManage` 等 | 编写跨平台插件时按协议调用 |

### 事件方法 vs 平台 API

```python
# 通用 — 任何平台都能用
await event.reply(text="收到")

# 平台专属 — 仅 QQ
await self.api.qq.post_group_msg(group_id, text="Hello!")

# 平台专属 — 仅 Bilibili
await self.api.bilibili.send_danmu(room_id, "弹幕内容")
```

---

## 本目录索引

| 文档 | 内容 |
|------|------|
| [事件方法](1_event_methods.md) | `event.reply()`, `event.delete()`, `event.kick()` 等跨平台事件操作 |
| [API Trait 协议](2_traits.md) | `IMessaging`, `IGroupManage`, `IQuery`, `IFileTransfer` 协议说明 |
