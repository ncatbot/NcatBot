# 插件开发指南

> NcatBot 插件开发从入门到实战——覆盖插件结构、生命周期、事件处理、Mixin 能力、Hook 机制和高级主题。

---

## Quick Start

5 分钟跑通第一个插件。

### 1. 安装

```bash
uv add ncatbot5    # 或 pip install ncatbot5
```

### 2. 创建插件目录

```
plugins/
└── hello_world/
    ├── manifest.toml
    └── main.py
```

### 3. manifest.toml

```toml
name = "hello_world"
version = "1.0.0"
main = "main.py"
entry_class = "HelloWorldPlugin"
```

### 4. main.py

```python
from ncatbot.core.registry import registrar
from ncatbot.event import GroupMessageEvent, PrivateMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("HelloWorld")


class HelloWorldPlugin(NcatBotPlugin):
    name = "hello_world"
    version = "1.0.0"

    async def on_load(self):
        LOG.info("HelloWorld 插件已加载！")

    @registrar.on_group_command("hello", ignore_case=True)
    async def on_hello(self, event: GroupMessageEvent):
        await self.api.post_group_msg(event.group_id, text="Hello, World! 👋")

    @registrar.on_group_command("hi", ignore_case=True)
    async def on_hi(self, event: GroupMessageEvent):
        await event.reply(text="你好呀！🎉")

    @registrar.on_private_command("hello", ignore_case=True)
    async def on_private_hello(self, event: PrivateMessageEvent):
        await event.reply(text="你好！👋")
```

### 5. 入口与运行

```python
# main.py（项目根目录）
from ncatbot.app import BotClient
bot = BotClient()
if __name__ == "__main__":
    bot.run()
```

```bash
python main.py   # 启动 Bot，自动扫描 plugins/
```

> 完整入门教程 → [1. 快速入门](1.quick-start.md)

---

## 速查参考

### 插件结构

#### manifest.toml 关键字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | ✅ | 插件唯一标识 |
| `version` | ✅ | 语义化版本号 |
| `main` | ✅ | 入口文件名 |
| `entry_class` | ❌ | 插件类名（省略则自动发现） |
| `[dependencies]` | ❌ | 依赖的其他插件 + 版本约束 |
| `[pip_dependencies]` | ❌ | pip 依赖 |

#### 基类选择

| 特性 | `BasePlugin` | `NcatBotPlugin`（推荐） |
|------|-------------|-----------------|
| 生命周期 + 事件注册 + API | ✅ | ✅ |
| ConfigMixin（配置持久化） | ❌ | ✅ |
| DataMixin（数据持久化） | ❌ | ✅ |
| RBACMixin（权限管理） | ❌ | ✅ |
| TimeTaskMixin（定时任务） | ❌ | ✅ |
| EventMixin（事件流） | ❌ | ✅ |

---

### 事件处理

#### 装饰器一览

| 装饰器 | 事件类型 | 自动添加的 Hook |
|--------|---------|----------------|
| `on_group_command(*names)` | `message` | `MessageTypeFilter("group")` + `CommandHook` |
| `on_private_command(*names)` | `message` | `MessageTypeFilter("private")` + `CommandHook` |
| `on_command(*names)` | `message` | `CommandHook` |
| `on_group_message()` | `message` | `MessageTypeFilter("group")` |
| `on_private_message()` | `message` | `MessageTypeFilter("private")` |
| `on_message()` | `message` | — |
| `on_notice()` | `notice` | — |
| `on_request()` | `request` | — |
| `on_group_increase()` | `notice` | `NoticeTypeFilter("group_increase")` |
| `on_group_decrease()` | `notice` | `NoticeTypeFilter("group_decrease")` |
| `on_poke()` | `notice` | `NoticeTypeFilter("notify")` + `SubTypeFilter("poke")` |
| `on_friend_request()` | `request` | `RequestTypeFilter("friend")` |
| `on_group_request()` | `request` | `RequestTypeFilter("group")` |
| `on(event_type)` | 自定义 | 精确/前缀匹配 |

#### 三种模式对比

| 维度 | A: 装饰器（推荐） | B: 事件流 | C: wait_event |
|------|-----------------|----------|---------------|
| 场景 | 命令响应、通知处理 | 后台监控 | 交互确认、多步对话 |
| 风格 | 声明式 | 响应式（async for） | 命令式（await） |
| 并发 | 框架自动路由 | 手动 create_task | Handler 内顺序 |
| 优先级 | ✅ | ❌ | ❌ |
| 参数绑定 | ✅ CommandHook | ❌ | ❌ |

---

### Mixin API 速查表

#### ConfigMixin

| 方法 | 签名 |
|------|------|
| `get_config` | `(key, default=None) -> Any` |
| `set_config` | `(key, value) -> None` — 立即保存 |
| `update_config` | `(updates: dict) -> None` |
| `remove_config` | `(key) -> bool` |

#### DataMixin

| 属性 | 说明 |
|------|------|
| `self.data` | `Dict[str, Any]` — 直接读写，卸载时自动保存 |

#### RBACMixin

| 方法 | 签名 |
|------|------|
| `check_permission` | `(user, permission) -> bool` |
| `add_permission` | `(path) -> None` |
| `add_role` | `(role, exist_ok=True) -> None` |
| `user_has_role` | `(user, role) -> bool` |

#### TimeTaskMixin

| 方法 | 签名 |
|------|------|
| `add_scheduled_task` | `(name, interval, conditions=None, max_runs=None) -> bool` |
| `remove_scheduled_task` | `(name) -> bool` |
| `list_scheduled_tasks` | `() -> List[str]` |
| `get_task_status` | `(name) -> Optional[Dict]` |

#### EventMixin

| 方法 | 签名 |
|------|------|
| `events` | `(event_type=None) -> EventStream` — `async with` + `async for` |
| `wait_event` | `(predicate=None, timeout=None) -> Event` |

---

### Hook 速查

#### 内置 Hook

| Hook | 类型 | 说明 |
|------|------|------|
| `MessageTypeFilter` | 过滤 | 按 `"group"` / `"private"` 过滤 |
| `PostTypeFilter` | 过滤 | 按 post_type 过滤 |
| `SubTypeFilter` | 过滤 | 按 sub_type 过滤 |
| `NoticeTypeFilter` | 过滤 | 按通知类型过滤 |
| `RequestTypeFilter` | 过滤 | 按请求类型过滤 |
| `SelfFilter` | 过滤 | 过滤 Bot 自身消息 |
| `StartsWithHook` | 匹配 | 消息以指定前缀开头 |
| `KeywordHook` | 匹配 | 消息包含任一关键词 |
| `RegexHook` | 匹配 | 正则匹配 |
| `CommandHook` | 命令 | 命令匹配 + 参数绑定 |

#### 自定义 Hook 骨架

```python
from ncatbot.core.registry.hook import Hook, HookAction, HookContext, HookStage

class MyHook(Hook):
    stage = HookStage.BEFORE_CALL
    priority = 50

    async def execute(self, ctx: HookContext) -> HookAction:
        # 你的逻辑
        return HookAction.CONTINUE  # 或 SKIP
```

---

## 深入阅读

| 章节 | 说明 | 难度 |
|------|------|------|
| [1. 快速入门](1.quick-start.md) | 环境准备、安装、5 分钟跑通第一个插件 | ⭐ |
| [2. 插件结构](2.structure.md) | manifest.toml 详解、基类选择、多文件组织 | ⭐ |
| [3a. 加载流程](3a.loading.md) | 扫描、依赖排序、模块导入、Mixin 钩子链 | ⭐ |
| [3b. 卸载与开发者钩子](3b.unloading.md) | 卸载流程、4 个生命周期钩子、常见模式 | ⭐ |
| [4a. 事件注册与装饰器](4a.event-registration.md) | 事件类型体系、装饰器路由、优先级、通知/请求 | ⭐⭐ |
| [4b. 事件高级用法](4b.event-advanced.md) | 事件流、wait_event、事件实体、实战组合 | ⭐⭐ |
| [5a. 配置与数据 Mixin](5a.config-data.md) | ConfigMixin + DataMixin 用法与对比 | ⭐⭐ |
| [5b. 权限、定时任务与事件 Mixin](5b.rbac-schedule-event.md) | RBACMixin + TimeTaskMixin + EventMixin | ⭐⭐ |
| [6a. Hook 基础](6a.hook-basics.md) | 三阶段模型、HookContext、自定义编写 | ⭐⭐ |
| [6b. 内置 Hook 与参数绑定](6b.hook-builtins.md) | 内置 Hook 清单、CommandHook、优先级 | ⭐⭐ |
| [7a. 高级模式](7a.patterns.md) | 热重载、依赖管理、跨插件交互、多步对话 | ⭐⭐⭐ |
| [7b. 实战案例与调试](7b.case-studies.md) | 群管理/定时报告/外部 API 案例、调试排查 | ⭐⭐⭐ |

### 阅读路线图

| 角色 | 推荐阅读 |
|------|---------|
| **新手** | 1.快速入门 → 2.插件结构 → 4a.事件注册 |
| **进阶** | 5a/5b.Mixin → 6a/6b.Hook |
| **高级** | 7a.高级模式 → 7b.实战案例 |

### 相关资源

- [架构总览](../../architecture.md) — NcatBot 整体分层架构
- [消息类型详解](../send_message/) — 消息段构造、MessageArray、合并转发
- [示例插件集合](../../../examples/README.md) — 15 个渐进式示例插件
