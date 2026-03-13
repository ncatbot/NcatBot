# SPEC-02: Service 规范

> 定义服务的概念边界、准入标准、基类接口和服务管理机制。

## 1. 定位

> **Service = 与平台无关的、可选的、有状态的内部能力提供者**

Service 层为 Core 层和 Plugin 层提供可复用的通用能力。Service 不关心消息来自哪个平台，不持有 Adapter 引用，不参与事件的分发路径。

## 2. 准入标准

一个模块要成为 Service，必须**同时**满足以下四项标准：

| 编号 | 标准 | 说明 | 反例 |
|------|------|------|------|
| S-1 | **平台无关** | 不依赖特定平台的协议、连接或数据格式 | MessageRouter 依赖 WebSocket，违反 S-1 |
| S-2 | **可选性** | 移除该服务后框架核心消息收发功能不受影响 | RegistryEngine 是消息分发的关键路径，违反 S-2 |
| S-3 | **能力提供** | 为上层（插件/Core）提供某种可复用的能力 | 纯工具函数不需要成为 Service |
| S-4 | **有状态/有生命周期** | 需要初始化和清理资源 | 无状态的纯函数/工具类用模块即可 |

## 3. 内置 Service 准入审查

| Service | S-1 | S-2 | S-3 | S-4 | 结论 |
|---------|-----|-----|-----|-----|------|
| RBACService | ✅ 纯逻辑 | ✅ 不影响收发 | ✅ 权限能力 | ✅ 加载权限表 | ✅ 保留 |
| PluginConfigService | ✅ 纯IO | ✅ 不影响收发 | ✅ 配置管理 | ✅ 监听文件 | ✅ 保留 |
| PluginDataService | ✅ 纯IO | ✅ 不影响收发 | ✅ 数据持久化 | ✅ 管理目录 | ✅ 保留 |
| FileWatcherService | ✅ 纯IO | ✅ 不影响收发 | ✅ 文件监控 | ✅ 维护watcher | ✅ 保留 |
| TimeTaskService | ✅ 纯逻辑 | ✅ 不影响收发 | ✅ 定时调度 | ✅ 管理调度器 | ✅ 保留 |
| MessageRouter | ❌ WebSocket | — | — | — | ❌ → Adapter |
| PreUploadService | ❌ 平台协议 | — | — | — | ❌ → Adapter |
| UnifiedRegistryService | — | ❌ 核心路径 | — | — | ❌ → Core/RegistryEngine |

## 4. BaseService 接口

> 源码位置：`ncatbot/core/service/base.py`

```python
from abc import ABC, abstractmethod
from typing import Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .manager import ServiceManager

class BaseService(ABC):
    """服务基类

    所有内部服务必须继承此类并实现生命周期钩子。

    属性：
        name: 服务唯一标识（子类必须定义）
        description: 人类可读描述
        dependencies: 依赖的其他 Service 名称列表
    """

    # ---- 元数据（子类必须定义 name） ----

    name: str = None
    description: str = "未提供描述"
    dependencies: List[str] = []

    def __init__(self, **config: Any):
        if not self.name:
            raise ValueError(f"{self.__class__.__name__} 必须定义 name 属性")
        self.config = config
        self._loaded = False
        self.service_manager: Optional["ServiceManager"] = None

    # ---- 生命周期钩子（子类必须实现） ----

    @abstractmethod
    async def on_load(self) -> None:
        """服务加载时初始化资源

        此方法在 ServiceManager.load_all() 时按依赖顺序调用。
        可以通过 self.service_manager 访问其他已加载的服务。
        """

    @abstractmethod
    async def on_close(self) -> None:
        """服务关闭时释放资源

        此方法在 ServiceManager.close_all() 时调用。
        必须幂等（多次调用不报错）。
        """

    # ---- 内部加载管理 ----

    async def _load(self) -> None:
        if self._loaded:
            return
        await self.on_load()
        self._loaded = True

    async def _close(self) -> None:
        if not self._loaded:
            return
        await self.on_close()
        self._loaded = False

    # ---- 状态查询 ----

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def event_bus(self):
        """通过 ServiceManager 获取 EventBus（可选）"""
        if self.service_manager:
            return self.service_manager.event_bus
        return None
```

### 4.1 与现有 BaseService 的变更点

| 变更项 | 现有 | 新版 | 理由 |
|--------|------|------|------|
| `dependencies` 字段 | 无 | `List[str]` | 支持依赖顺序加载 |
| `event_bus` 属性 | 通过 `bot_client` 获取 | 通过 `service_manager` 直接获取 | 断开对 BotClient 的依赖 |

## 5. ServiceManager 精简

> 源码位置：`ncatbot/core/service/manager.py`

### 5.1 新接口

```python
class ServiceManager:
    """服务管理器

    管理纯内部服务的生命周期。
    不再管理 MessageRouter、PreUpload、UnifiedRegistry。
    """

    def __init__(self, event_bus: "EventBus"):
        self._services: Dict[str, BaseService] = {}
        self._service_classes: Dict[str, Type[BaseService]] = {}
        self._service_configs: Dict[str, Dict[str, Any]] = {}
        self._event_bus = event_bus

    @property
    def event_bus(self) -> "EventBus":
        return self._event_bus

    # ---- 服务管理（保留） ----

    def register(self, service_class: Type[BaseService], **config) -> None: ...
    async def load(self, service_name: str) -> BaseService: ...
    async def unload(self, service_name: str) -> None: ...
    async def load_all(self) -> None: ...
    async def close_all(self) -> None: ...
    def get(self, service_name: str) -> Optional[BaseService]: ...
    def has(self, service_name: str) -> bool: ...
    def list_services(self) -> List[str]: ...

    # ---- 内置服务属性（保留） ----

    @property
    def rbac(self) -> "RBACService": ...
    @property
    def plugin_config(self) -> "PluginConfigService": ...
    @property
    def plugin_data(self) -> "PluginDataService": ...
    @property
    def file_watcher(self) -> "FileWatcherService": ...
    @property
    def time_task(self) -> "TimeTaskService": ...
```

### 5.2 与现有 ServiceManager 的变更点

| 变更项 | 现有 | 新版 | 理由 |
|--------|------|------|------|
| 构造函数 | `__init__(self)` | `__init__(self, event_bus)` | 注入 EventBus，断开对 BotClient 的依赖 |
| `set_bot_client()` | 存在 | **移除** | 不再需要 BotClient 引用 |
| `bot_client` 属性 | 存在 | **移除** | 改为 `event_bus` 属性 |
| `message_router` 属性 | 存在 | **移除** | MessageRouter 迁至 Adapter |
| `preupload` 属性 | 存在 | **移除** | PreUpload 迁至 Adapter |
| `unified_registry` 属性 | 存在 | **移除** | 提升为 Core/RegistryEngine |
| 依赖顺序加载 | 无 | 按 `dependencies` 拓扑排序 | 保证服务间依赖正确初始化 |

### 5.3 依赖顺序加载

```python
async def load_all(self) -> None:
    """按依赖顺序加载所有已注册的服务

    使用拓扑排序确保被依赖的服务先加载。
    检测循环依赖并抛出异常。
    """
    order = self._topological_sort()
    for name in order:
        if name not in self._services:
            await self.load(name)
```

## 6. 第三方服务扩展

插件可以注册自定义 Service：

```python
class MyDatabaseService(BaseService):
    name = "my_database"
    description = "自定义数据库服务"
    dependencies = ["plugin_config"]  # 依赖配置服务

    async def on_load(self):
        config = self.service_manager.plugin_config
        ...

    async def on_close(self):
        ...

# 插件中注册
class MyPlugin(BasePlugin):
    async def on_load(self):
        self.service_manager.register(MyDatabaseService)
        await self.service_manager.load("my_database")
```

## 7. Service 合规检查清单

- [ ] 继承 `BaseService` 并实现 `on_load()` 和 `on_close()`
- [ ] 定义 `name` 属性（唯一标识）
- [ ] 满足准入标准 S-1 ~ S-4
- [ ] 不导入 `ncatbot.adapter` 中的任何模块（D-4 规则）
- [ ] 不直接持有 BotClient 引用
- [ ] `on_close()` 幂等
- [ ] 声明 `dependencies`（如果依赖其他 Service）
