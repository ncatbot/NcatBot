# 使用指南

> NcatBot 从入门到进阶的完整指南 — 面向 Bot 开发者的任务导向文档。

---

## Quick Reference

### 两种使用模式

| 模式 | 入口 | 特点 | Mixin / 热重载 |
|------|------|------|---------------|
| 非插件模式 | `main.py` + `registrar` 装饰器 | 快速原型，无需插件目录 | ❌ |
| 插件模式（推荐） | `NcatBotPlugin` 子类 + `manifest.toml` | 配置持久化、RBAC、定时任务等 | ✅ |

从零开始的完整流程见 [quick_start/](quick_start/)。

### 核心导入路径

| 导入 | 说明 |
|------|------|
| `from ncatbot.app import BotClient` | 应用入口 |
| `from ncatbot.core import registrar` | 全局事件注册器 |
| `from ncatbot.plugin import NcatBotPlugin` | 插件基类 |
| `from ncatbot.event.qq import GroupMessageEvent` | QQ 群消息事件 |
| `from ncatbot.event.qq import PrivateMessageEvent` | QQ 私聊事件 |
| `from ncatbot.types import MessageArray` | 消息数组 |
| `from ncatbot.utils import get_log` | 日志工具 |

### 最常用操作速查

| 操作 | 调用方式 | 需要插件模式 |
|------|---------|-------------|
| 注册群命令 | `@registrar.on_group_command("cmd")` | ❌ |
| 注册私聊命令 | `@registrar.on_private_command("cmd")` | ❌ |
| 回复消息 | `await event.reply(text="内容")` | ❌ |
| 发送群消息 | `await self.api.qq.post_group_msg(gid, text="内容")` | ❌ |
| 发送图片 | `await self.api.qq.send_group_image(gid, "url")` | ❌ |
| 读取配置 | `self.get_config("key")` | ✅ ConfigMixin |
| 写入配置 | `self.set_config("key", value)` | ✅ ConfigMixin |
| 持久化数据 | `self.data["key"] = value` | ✅ DataMixin |
| 权限检查 | `self.check_permission(uid, "perm")` | ✅ RBACMixin |
| 定时任务 | `self.add_scheduled_task("名称", "60s")` | ✅ TimeTaskMixin |
| 等待事件 | `await self.wait_event(predicate, timeout=30)` | ✅ EventMixin |
| 群管理 | `await self.api.qq.manage.set_group_ban(gid, uid)` | ❌ |
| 信息查询 | `await self.api.qq.query.get_group_info(gid)` | ❌ |

### 按需求找文档

| 我想… | 去这里 |
|-------|--------|
| 从零跑通第一个 Bot | [quick_start/](quick_start/) |
| 开发插件 | [plugin/](plugin/) |
| 发消息、构造复杂消息 | [send_message/](send_message/) |
| 调用群管理/查询/文件 API | [api_usage/](api_usage/) |
| 管理 config.yaml | [configuration/](configuration/) |
| 用 CLI 管理项目 | [cli/](cli/) |
| 添加权限控制 | [rbac/](rbac/) |
| 写插件测试 | [testing/](testing/) |
| 接入多平台 | [multi_platform/](multi_platform/) |

---

## 本目录索引

| 目录 | 说明 | 难度 |
|------|------|------|
| [quick_start/](quick_start/) | 从零启动 — 安装、配置、两种模式启动 | ⭐ |
| [plugin/](plugin/) | 插件开发完整指南（11 篇） | ⭐ - ⭐⭐⭐ |
| [send_message/](send_message/) | 消息发送 — 消息段、MessageArray、转发、语法糖 | ⭐ |
| [api_usage/](api_usage/) | Bot API 使用 — 消息、群管理、查询 | ⭐⭐ |
| [configuration/](configuration/) | 配置管理 — config.yaml 结构与安全校验 | ⭐⭐ |
| [cli/](cli/) | CLI 工具 — init / run / dev / config / plugin | ⭐ |
| [rbac/](rbac/) | RBAC 权限管理 — 权限模型与插件集成 | ⭐⭐⭐ |
| [testing/](testing/) | 插件测试 — Harness、工厂函数、Scenario | ⭐⭐ |
| [multi_platform/](multi_platform/) | 多平台开发 — Trait 协议与跨平台插件 | ⭐⭐ |

---

## 交叉引用

- API 完整签名 → [reference/](../reference/)
- 核心概念速查 → [concepts.md](../concepts.md)
- 架构全景 → [architecture.md](../architecture.md)
