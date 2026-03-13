# SPEC-03: Registry（命令/事件注册引擎）规范

> 定义 RegistryEngine 的定位、接口、与 EventBus 的集成方式，以及命令/过滤器/事件处理器的注册与执行机制。

## 1. 定位

> **RegistryEngine = 框架核心的事件处理管道组件，不是 Service**

RegistryEngine 是消息从 EventBus 到达用户处理函数的关键路径，与 EventBus、EventDispatcher 同为 Core 层核心组件。它不满足 Service 准入标准（S-2 可选性），因此不继承 `BaseService`，由 `BotClient` 直接持有和管理。

### 为什么不是 Service？

| 检查项 | 结论 |
|--------|------|
| S-1 平台无关 | ✅ 通过 |
| S-2 可选性 | ❌ **不通过** — 移除后命令和过滤器完全失效 |
| S-3 能力提供 | ✅ 通过 |
| S-4 有状态 | ✅ 通过 |

RegistryEngine 管理着命令注册表、过滤器注册表、事件处理器注册表的生命周期，是消息分发的核心枢纽，不可移除。

## 2. RegistryEngine 接口

> 源码位置：`ncatbot/core/registry/engine.py`

```python
from typing import Callable, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ncatbot.core.event import MessageEvent, BaseEvent
    from ncatbot.core.client.event_bus import EventBus
    from ncatbot.plugin_system import BasePlugin

class RegistryEngine:
    """统一的命令/过滤器/事件处理器注册与执行引擎

    不继承 BaseService。由 BotClient 直接持有和管理。

    组合关系：
    - 持有 CommandRunner（命令匹配与执行）
    - 持有 FunctionExecutor（函数调用与参数注入）
    - 引用全局注册表（command_registry, filter_registry, event_registry）
    """

    def __init__(self):
        self._initialized = False
        self._executor: FunctionExecutor = None
        self._command_runner: CommandRunner = None
        self.prefixes: List[str] = []

    # ==================================================================
    # 生命周期（非 Service，但有初始化/清理需求）
    # ==================================================================

    def initialize(self) -> None:
        """初始化引擎

        构建命令分发表，检查前缀冲突，创建 CommandRunner。
        采用惰性初始化策略：首次处理事件时自动调用。
        也可由 BotClient 显式调用。
        """

    def clear(self) -> None:
        """清理所有状态

        重置初始化标志，释放 CommandRunner。
        在 BotClient shutdown 时调用。
        """

    # ==================================================================
    # 事件处理（由 EventBus 回调调用）
    # ==================================================================

    async def handle_message_event(self, event: "MessageEvent") -> None:
        """处理消息事件

        执行流程：
        1. 惰性初始化（initialize_if_needed）
        2. CommandRunner.run() — 命令匹配与执行
        3. run_pure_filters() — 非命令过滤器执行

        此方法直接订阅 EventBus，不经过 SystemManager 桥接。
        """

    async def handle_notice_event(self, event: "BaseEvent") -> None:
        """处理通知事件

        遍历 event_registry.notice_handlers，逐个执行。
        """

    async def handle_request_event(self, event: "BaseEvent") -> None:
        """处理请求事件

        遍历 event_registry.request_handlers，逐个执行。
        """

    async def handle_meta_event(self, event: "BaseEvent") -> None:
        """处理元事件

        遍历 event_registry.meta_handlers，逐个执行。
        """

    async def handle_legacy_event(self, event: "BaseEvent") -> None:
        """统一入口：根据 post_type 分发到具体处理方法

        用于 EventBus 统一订阅非消息事件。
        """

    # ==================================================================
    # 插件联动
    # ==================================================================

    def handle_plugin_load(self) -> None:
        """插件加载后重新初始化

        清除当前状态并标记需要重新初始化。
        下次事件到来时自动重建命令分发表。
        """

    def handle_plugin_unload(self, plugin_name: str) -> None:
        """插件卸载，清理该插件注册的所有处理器

        从 command_registry、filter_registry、event_registry
        中移除该插件名下的所有注册项。
        """

    # ==================================================================
    # 注册 API（供装饰器使用，委托给全局注册表）
    # ==================================================================

    @staticmethod
    def set_current_plugin_name(plugin_name: str) -> None:
        """设置当前注册的插件名

        在插件加载期间调用，使后续装饰器注册的处理器
        自动关联到该插件。
        """
```

## 3. 与 EventBus 的集成

### 3.1 现有方式（SystemManager 桥接 — 将废弃）

```
EventBus.publish("ncatbot.message_event", event)
    ↓
SystemManager 插件订阅 → handle_group_message(event)
    ↓
unified_registry.handle_message_event(event)
```

问题：SystemManager 作为插件桥接 EventBus 与 UnifiedRegistryService，增加了不必要的间接层。

### 3.2 新方式（RegistryEngine 直接订阅）

```
EventBus.publish("ncatbot.message_event", event)
    ↓
RegistryEngine.handle_message_event(event)  ← 直接订阅
```

实现：

```python
class BotClient:
    def __init__(self):
        self.event_bus = EventBus()
        self.registry = RegistryEngine()

        # 直接订阅，无需 SystemManager 桥接
        self.event_bus.subscribe(
            "re:ncatbot\\.group_message_event|ncatbot\\.private_message_event"
            "|ncatbot\\.message_sent_event",
            self.registry.handle_message_event,
            priority=0,  # 高优先级
        )
        self.event_bus.subscribe(
            "re:ncatbot\\.notice_event|ncatbot\\.request_event|ncatbot\\.meta_event",
            self.registry.handle_legacy_event,
            priority=0,
        )
```

### 3.3 SystemManager 的变化

SystemManager 插件将精简或移除其「桥接」角色。SystemManager 仍可保留为内置插件，但仅处理管理类命令（如热重载、状态查看），不再负责事件分发桥接。

## 4. 全局注册表

### 4.1 注册表单例

命令/过滤器/事件处理器的注册表保持为模块级单例，因为装饰器在导入期间运行：

```python
# ncatbot/core/registry/command_system/registry/registry.py
command_registry = CommandRegistry()  # 模块级单例

# ncatbot/core/registry/filter_system/__init__.py
filter_registry = FilterRegistry()   # 模块级单例

# ncatbot/core/registry/filter_system/event_registry.py
event_registry = EventRegistry()     # 模块级单例
```

### 4.2 生命周期由 RegistryEngine 管理

```python
class RegistryEngine:
    def __init__(self):
        # 引用全局注册表
        self.command_registry = command_registry
        self.filter_registry = filter_registry
        self.event_registry = event_registry

    def handle_plugin_unload(self, plugin_name: str):
        """清理插件注册项"""
        self.command_registry.root_group.revoke_plugin(plugin_name)
        self.filter_registry.revoke_plugin(plugin_name)
        self.event_registry.revoke_plugin(plugin_name)
        self.clear()
```

## 5. 目录结构

```
ncatbot/core/registry/
├── __init__.py
├── engine.py                    # RegistryEngine 主类
├── command_runner.py            # 命令匹配与执行
├── executor.py                  # FunctionExecutor（参数注入、异常处理）
├── command_system/              # 命令系统
│   ├── lexer/                   # 词法分析
│   ├── registry/                # 命令注册表
│   │   └── registry.py          # CommandRegistry (全局单例)
│   └── utils.py                 # CommandSpec 等工具
├── filter_system/               # 过滤器系统
│   ├── __init__.py              # FilterRegistry (全局单例)
│   ├── event_registry.py        # EventRegistry (全局单例)
│   └── ...
└── trigger/                     # 触发器/参数绑定
    └── ...
```

## 6. 从 UnifiedRegistryService 迁移

### 6.1 变更映射

| 现有 | 新 | 变更 |
|------|-----|------|
| `UnifiedRegistryService` | `RegistryEngine` | 不继承 BaseService |
| `service.on_load()` | `engine.initialize()` | 非异步，惰性调用 |
| `service.on_close()` | `engine.clear()` | 非异步 |
| `service.service_manager.bot_client` | 由 BotClient 直接持有 | 断开 ServiceManager 依赖 |
| 通过 SystemManager 桥接 | 直接订阅 EventBus | 消除中间层 |

### 6.2 插件实例获取

现有代码中 `get_plugin_instance_if_needed()` 通过 `service_manager.bot_client` 获取插件实例。新设计中 RegistryEngine 需要通过 BotClient 注入的回调或引用来获取插件实例：

```python
class RegistryEngine:
    def __init__(self):
        self._get_plugin: Optional[Callable[[str], BasePlugin]] = None

    def set_plugin_resolver(self, resolver: Callable[[str], Optional["BasePlugin"]]):
        """注入插件实例解析器（由 BotClient 调用）"""
        self._get_plugin = resolver
```

## 7. RegistryEngine 合规检查清单

- [ ] 不继承 `BaseService`
- [ ] 由 `BotClient` 直接创建和持有
- [ ] 直接订阅 `EventBus`，不通过 SystemManager 桥接
- [ ] 不导入 `ncatbot.adapter` 中的任何模块
- [ ] 不直接依赖 `ServiceManager`
- [ ] 引用全局注册表单例（command_registry, filter_registry, event_registry）
- [ ] `clear()` 调用后可安全重新 `initialize()`
- [ ] 正确处理插件的加载/卸载事件
