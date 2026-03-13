# SPEC-01: Adapter 规范

> 定义平台适配器的抽象接口、职责边界、注册机制和具体实现要求。

## 1. 定位

> **Adapter = 封装与外部平台全部交互的完整适配层**

Adapter 是框架与外部平台（如 NapCat/OneBot v11）之间的唯一通道。Core 层不直接进行任何网络 I/O 或协议操作，所有平台相关的逻辑都封装在 Adapter 中。

## 2. BaseAdapter 抽象基类

> 源码位置：`ncatbot/adapter/base.py`

```python
from abc import ABC, abstractmethod
from typing import Optional, Callable, Awaitable, List

from ncatbot.core.api import IBotAPI
from ncatbot.core.event import BaseEvent


class BaseAdapter(ABC):
    """平台适配器抽象基类

    每个平台适配器必须继承此类并实现所有抽象方法。
    一个 Adapter 实例封装与一个平台的完整交互。

    职责：
    1. 平台环境的准备和部署
    2. 与平台的连接建立和维护
    3. 原始协议数据到标准 Event 的转换
    4. IBotAPI 的具体实现
    5. 平台特定能力（如文件预上传）
    """

    # ---- 元数据（子类必须定义） ----

    name: str                       # 适配器唯一标识，如 "napcat"
    description: str                # 人类可读的描述
    supported_protocols: List[str]  # 支持的协议，如 ["onebot_v11"]

    # ---- 内部状态 ----

    _event_callback: Optional[Callable[[BaseEvent], Awaitable[None]]] = None

    # ==================================================================
    # 生命周期方法
    # ==================================================================

    @abstractmethod
    async def setup(self) -> None:
        """准备平台环境

        职责：
        - 检查平台依赖是否满足
        - 安装/部署平台服务（如 NapCat）
        - 生成/加载平台配置

        此方法在 connect() 之前调用。
        如果平台已就绪，此方法应快速返回。

        Raises:
            AdapterSetupError: 环境准备失败
        """

    @abstractmethod
    async def connect(self) -> None:
        """建立与平台的连接

        职责：
        - 建立通信通道（WebSocket/HTTP/...）
        - 完成认证/握手
        - 确认连接可用

        此方法在 setup() 之后、listen() 之前调用。

        Raises:
            AdapterConnectionError: 连接建立失败
        """

    @abstractmethod
    async def disconnect(self) -> None:
        """断开与平台的连接

        职责：
        - 清理所有挂起的请求
        - 关闭通信通道
        - 释放连接相关资源

        此方法在 shutdown 阶段调用，必须幂等。
        """

    @abstractmethod
    async def listen(self) -> None:
        """开始监听平台消息

        此方法阻塞运行，持续接收消息直到连接断开或被取消。
        收到消息后：
        1. 调用 convert_event() 转换为标准 Event
        2. 调用 _event_callback() 传递给 Core 层

        Raises:
            asyncio.CancelledError: 正常取消
            AdapterConnectionError: 连接中断
        """

    # ==================================================================
    # 事件转换
    # ==================================================================

    @abstractmethod
    def convert_event(self, raw_data: dict) -> Optional[BaseEvent]:
        """将平台原始数据转换为标准 Event 对象

        契约：
        1. 必须返回 BaseEvent 子类实例，或 None（无法解析时）
        2. 必须在返回前调用 event.bind_api(self.get_api()) 绑定 API
        3. 不得返回平台特定的 Event 子类（必须是标准模型中定义的类）
        4. 转换失败时返回 None 并记录日志，不得抛出异常

        Args:
            raw_data: 平台原始数据（通常是 JSON dict）

        Returns:
            标准 Event 对象，或 None
        """

    # ==================================================================
    # API 实现
    # ==================================================================

    @abstractmethod
    def get_api(self) -> IBotAPI:
        """返回此适配器的 IBotAPI 实现

        返回的 API 实例：
        - 必须实现 IBotAPI 中定义的所有方法
        - 生命周期与 Adapter 绑定（Adapter 断开后 API 不可用）
        - 应是单例（同一 Adapter 多次调用返回同一实例）

        Returns:
            IBotAPI 实现实例
        """

    # ==================================================================
    # 回调设置
    # ==================================================================

    def set_event_callback(
        self, callback: Callable[[BaseEvent], Awaitable[None]]
    ) -> None:
        """设置事件回调

        由 BotClient 在启动阶段调用，将转换后的标准 Event
        传递给 Core 层的 EventDispatcher。

        Args:
            callback: 接收标准 Event 的异步回调函数
        """
        self._event_callback = callback

    # ==================================================================
    # 状态查询
    # ==================================================================

    @property
    @abstractmethod
    def connected(self) -> bool:
        """是否已连接到平台"""

    # ==================================================================
    # 可选能力（子类按需实现）
    # ==================================================================

    async def preupload_file(self, file_path: str, file_type: str = "file") -> str:
        """预上传文件（可选能力）

        平台支持文件预上传时实现此方法。
        不支持时返回原始路径。

        Args:
            file_path: 本地文件路径、URL 或 base64
            file_type: 文件类型（image/video/record/file）

        Returns:
            处理后的文件引用（URL 或平台特定标识）
        """
        return file_path

    async def preupload_message(self, message: list) -> list:
        """预上传消息中的文件（可选能力）

        遍历消息段，对其中的文件类型进行预上传处理。
        不支持时原样返回。

        Args:
            message: 消息段列表

        Returns:
            处理后的消息段列表
        """
        return message
```

## 3. Adapter 职责边界

### 3.1 属于 Adapter 的职责

| 职责 | 说明 | 对应组件 |
|------|------|---------|
| 平台环境管理 | 安装、部署、启动外部服务 | `environment.py` |
| 连接管理 | WebSocket/HTTP 连接建立和维护 | `connection.py` |
| 认证登录 | 平台账号认证、Token 管理 | `auth.py` |
| 协议封装 | 请求-响应匹配（echo/Future）、序列化 | `protocol.py` |
| 事件转换 | 原始协议数据 → 标准 Event 对象 | `event_converter.py` |
| API 实现 | IBotAPI 接口的协议映射 | `api_impl.py` |
| 文件预上传 | 平台特定的文件上传协议 | `preupload.py` |
| 平台配置 | 平台特定的配置项管理 | `config.py` |

### 3.2 不属于 Adapter 的职责

| 职责 | 应属于 | 说明 |
|------|--------|------|
| 事件分发到处理器 | Core (EventBus) | Adapter 将 Event 交给回调，不关心后续分发 |
| 命令/过滤器匹配 | Core (RegistryEngine) | 与平台无关的逻辑 |
| 插件管理 | Plugin System | 插件的加载、卸载与 Adapter 无关 |
| 权限判断 | Service (RBAC) | 权限模型与平台无关 |
| 配置/数据持久化 | Service | 插件配置和数据存储与平台无关 |
| 定时任务 | Service | 调度逻辑与平台无关 |

## 4. Adapter 注册与选择

### 4.1 注册

```python
# BotClient 启动时注册可用的适配器
from ncatbot.adapter.napcat import NapCatAdapter

class BotClient:
    # 内置适配器注册表
    _adapter_classes = {
        "napcat": NapCatAdapter,
    }
```

### 4.2 选择

```python
# 用户通过配置或参数选择适配器
bot = BotClient()
bot.run(adapter="napcat")  # 默认值
```

### 4.3 扩展

第三方适配器通过注册接入：

```python
from ncatbot.adapter.base import BaseAdapter

class MyPlatformAdapter(BaseAdapter):
    name = "my_platform"
    ...

# 注册
bot.register_adapter("my_platform", MyPlatformAdapter)
bot.run(adapter="my_platform")
```

## 5. NapCatAdapter 实现要求

### 5.1 组件迁移映射

| 现有组件 | 现位置 | 新位置 |
|---------|--------|--------|
| `MessageRouter` 核心逻辑 | `core/service/builtin/message_router.py` | `adapter/napcat/protocol.py` |
| `NapCatWebSocket` | `core/adapter/nc/websocket.py` | `adapter/napcat/connection.py` |
| `EventParser` + `register_builtin_events` | `core/event/parser.py` | `adapter/napcat/event_converter.py` |
| `BotAPI` (具体实现) | `core/api/api.py` + 子模块 | `adapter/napcat/api_impl.py` |
| `PreUploadService` | `core/service/builtin/preupload/` | `adapter/napcat/preupload.py` |
| `launch_napcat_service` | `core/adapter/nc/service.py` | `adapter/napcat/environment.py` |
| `AuthHandler` | `core/adapter/nc/auth.py` | `adapter/napcat/auth.py` |
| `NapCatConfigManager` | `core/adapter/nc/config_manager.py` | `adapter/napcat/config.py` |

### 5.2 NapCatAdapter 主类结构

```python
class NapCatAdapter(BaseAdapter):
    name = "napcat"
    description = "NapCat OneBot v11 适配器"
    supported_protocols = ["onebot_v11"]

    def __init__(self):
        self._connection: NapCatConnection = None     # WebSocket
        self._protocol: NapCatProtocol = None         # echo/Future
        self._api: NapCatBotAPI = None                # IBotAPI 实现
        self._preupload: PreUploadManager = None      # 预上传
        self._converter: EventConverter = None        # 事件转换

    async def setup(self):
        """安装/启动 NapCat"""
        launch_napcat_service()

    async def connect(self):
        """建立 WebSocket 连接"""
        uri = ncatbot_config.get_uri_with_token()
        self._connection = NapCatConnection(uri)
        await self._connection.connect()

        self._protocol = NapCatProtocol(self._connection)
        self._api = NapCatBotAPI(self._protocol)
        self._converter = EventConverter(self._api)
        self._preupload = PreUploadManager(self._protocol)

    async def disconnect(self):
        """断开连接"""
        if self._protocol:
            self._protocol.cancel_all()
        if self._connection:
            await self._connection.disconnect()

    async def listen(self):
        """监听消息"""
        await self._connection.listen(self._on_raw_message)

    def convert_event(self, raw_data: dict) -> Optional[BaseEvent]:
        """JSON → 标准 Event"""
        return self._converter.convert(raw_data)

    def get_api(self) -> IBotAPI:
        return self._api

    @property
    def connected(self) -> bool:
        return self._connection and self._connection.connected

    async def _on_raw_message(self, data: dict):
        """内部消息处理"""
        echo = data.get("echo")
        if echo:
            # API 响应 → 设置 Future
            self._protocol.resolve(echo, data)
        else:
            # 事件 → 转换并回调
            event = self.convert_event(data)
            if event and self._event_callback:
                await self._event_callback(event)
```

### 5.3 NapCatProtocol（请求-响应匹配）

从 `MessageRouter` 核心逻辑迁移，职责纯化为协议层：

```python
class NapCatProtocol:
    """OneBot v11 请求-响应匹配

    核心机制：
    1. 生成 UUID echo 标识每个请求
    2. 使用 asyncio.Future 等待响应
    3. threading.Lock 保护跨线程访问
    """

    async def send(self, action: str, params: dict, timeout: float = 30.0) -> dict:
        """发送 API 请求并等待响应"""

    def resolve(self, echo: str, data: dict) -> None:
        """解析 API 响应（由消息接收回调调用）"""

    def cancel_all(self) -> None:
        """取消所有挂起的请求"""
```

### 5.4 EventConverter（事件转换）

从 `EventParser` 迁移，职责纯化为协议转换：

```python
class EventConverter:
    """OneBot v11 原始 JSON → 标准 Event 转换器

    使用注册表模式：(post_type, secondary_key) → EventClass
    """

    def convert(self, raw_data: dict) -> Optional[BaseEvent]:
        """转换原始数据为标准 Event"""

    def register(self, post_type: str, secondary_key: str, event_cls: type):
        """注册事件类映射"""
```

## 6. Adapter 错误体系

```python
class AdapterError(Exception):
    """适配器错误基类"""

class AdapterSetupError(AdapterError):
    """环境准备失败"""

class AdapterConnectionError(AdapterError):
    """连接错误"""

class AdapterProtocolError(AdapterError):
    """协议错误（请求超时、格式错误等）"""

class AdapterAuthError(AdapterError):
    """认证失败"""
```

## 7. Adapter 合规检查清单

实现新 Adapter 时须逐项确认：

- [ ] 继承 `BaseAdapter` 并实现所有抽象方法
- [ ] 定义 `name`、`description`、`supported_protocols`
- [ ] `convert_event()` 仅返回标准 Event 子类或 None
- [ ] `convert_event()` 在返回前调用 `event.bind_api()`
- [ ] `get_api()` 返回的对象实现 `IBotAPI` 全部方法
- [ ] `disconnect()` 幂等（多次调用不报错）
- [ ] 不导入 `ncatbot.core.client`、`ncatbot.core.registry`、`ncatbot.core.service` 中的任何模块
- [ ] 仅依赖 `ncatbot.core.api`（IBotAPI）和 `ncatbot.core.event`（标准 Event 模型）
- [ ] 所有平台特定异常包装为 `AdapterError` 子类
