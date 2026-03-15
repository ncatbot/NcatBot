# TestHarness + PluginTestHarness

> 测试编排器完整 API 参考

---

## TestHarness

```python
from ncatbot.testing import TestHarness
```

测试编排器，在后台启动 `BotClient`（使用 `MockAdapter`），提供事件注入和断言 API。

### 构造

```python
TestHarness() -> TestHarness
```

无参数。内部创建 `MockAdapter` + `BotClient`。

### Properties

| 属性 | 类型 | 说明 |
|------|------|------|
| `bot` | `BotClient` | Bot 客户端实例 |
| `adapter` | `MockAdapter` | Mock 适配器实例 |
| `mock_api` | `MockBotAPI` | Mock API 实例（用于 `set_response`） |
| `dispatcher` | `AsyncEventDispatcher` | 事件分发器 |
| `api_calls` | `List[APICall]` | 所有 API 调用记录 |

### 生命周期方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `start` | `async start() -> None` | 启动 BotClient（非阻塞） |
| `stop` | `async stop() -> None` | 停止 BotClient |
| `__aenter__` | `async __aenter__() -> TestHarness` | async with 入口 |
| `__aexit__` | `async __aexit__(...) -> None` | async with 出口 |

### 事件注入方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `inject` | `async inject(event_data: BaseEventData) -> None` | 注入单个事件 |
| `inject_many` | `async inject_many(events: List[BaseEventData]) -> None` | 依次注入多个事件 |
| `settle` | `async settle(delay: float = 0.05) -> None` | 等待 handler 执行 |
| `wait_event` | `async wait_event(predicate: Callable[[Event], bool] = None, timeout: float = 2.0) -> Event` | 等待特定事件 |

### API 断言方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `api_called` | `api_called(action: str) -> bool` | 检查 action 是否被调用 |
| `api_call_count` | `api_call_count(action: str) -> int` | 获取调用次数 |
| `get_api_calls` | `get_api_calls(action: str) -> List[APICall]` | 获取所有匹配调用 |
| `last_api_call` | `last_api_call(action: str = None) -> Optional[APICall]` | 获取最近一次调用 |
| `reset_api` | `reset_api() -> None` | 清空调用记录 |

### 使用示例

```python
async with TestHarness() as h:
    await h.inject(group_message("hello"))
    await h.settle()
    assert h.api_called("send_group_msg")

    call = h.last_api_call("send_group_msg")
    print(call.action, call.args, call.kwargs)
```

---

## PluginTestHarness

```python
from ncatbot.testing import PluginTestHarness
```

继承 `TestHarness`，增加插件选择性加载和查询能力。

### 构造

```python
PluginTestHarness(
    plugin_names: List[str],      # 要加载的插件名列表
    plugin_dir: Path,             # 插件根目录
    *,
    skip_builtin: bool = True,    # 是否跳过内置插件
    skip_pip: bool = True,        # 是否跳过 pip 依赖安装
) -> PluginTestHarness
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `plugin_names` | `List[str]` | 必填 | 要加载的插件名（manifest.toml 中的 name） |
| `plugin_dir` | `Path` | 必填 | 包含插件文件夹的**父目录** |
| `skip_builtin` | `bool` | `True` | 跳过内置插件加载 |
| `skip_pip` | `bool` | `True` | 跳过 pip 依赖安装 |

### 额外 Properties

| 属性 | 类型 | 说明 |
|------|------|------|
| `loaded_plugins` | `List[str]` | 已加载的插件名列表 |

> 继承自 TestHarness 的所有 properties 和方法同样可用。

### 插件操作方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `get_plugin` | `get_plugin(name: str) -> Optional[BasePlugin]` | 获取插件实例 |
| `plugin_config` | `plugin_config(name: str) -> dict` | 获取插件配置 |
| `plugin_data` | `plugin_data(name: str) -> dict` | 获取插件数据 |
| `reload_plugin` | `async reload_plugin(name: str) -> bool` | 热重载插件 |

> `plugin_config` 和 `plugin_data` 在插件未加载时抛出 `KeyError`。

### start 流程

`PluginTestHarness.start()` 执行以下步骤：

1. 启动核心基础设施（adapter / API / dispatcher / services）
2. 配置 PluginLoader 依赖注入
3. 如果 `skip_builtin=False`，加载内置插件
4. 通过 `loader.load_selected()` 加载指定插件及其传递依赖
5. 启动后台监听任务

### 使用示例

```python
async with PluginTestHarness(
    plugin_names=["hello_world"],
    plugin_dir=Path("examples/01_hello_world"),
) as h:
    # 验证加载
    assert "hello_world" in h.loaded_plugins

    # 注入事件
    await h.inject(group_message("hello", group_id="100", user_id="99"))
    await h.settle()

    # 断言
    assert h.api_called("send_group_msg")

    # 查询插件状态
    plugin = h.get_plugin("hello_world")
    config = h.plugin_config("hello_world")
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [Factory + Scenario + Mock](2_factory_scenario_mock.md) | 事件工厂、场景构建器、Mock API |
| [测试指南](../../guide/testing/) | 教程风格入门 |
| [Harness 使用详解](../../guide/testing/2.harness.md) | 实践指南 |
