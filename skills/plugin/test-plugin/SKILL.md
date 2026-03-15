# test-plugin — 为 NcatBot 插件生成离线测试

## 触发条件

当用户请求为某个 NcatBot 插件编写测试、生成测试用例、或测试某个插件时，使用此技能。

## 上下文收集

1. **读取插件源码**: 读取 `main.py`（或 manifest.toml 中 `main` 字段指定的文件）
2. **读取 manifest.toml**: 获取插件名、版本、依赖
3. **识别 handler**: 找到所有 `@registrar.on_group_command()`, `@registrar.on_private_command()`, `@registrar.on_group_message()` 等装饰器注册的 handler
4. **识别 Hook**: 找到 `@add_hooks(...)` 或 `@hook_instance` 装饰的 handler
5. **识别生命周期**: 找到 `on_load()`, `on_close()` 方法
6. **识别 Mixin 使用**: 检查 ConfigMixin (`get_config`, `set_config`), DataMixin (`self.data`), RBACMixin (`check_permission`, `add_role`), TimeTaskMixin (`add_scheduled_task`), EventMixin (`self.events()`, `self.wait_event()`)

## 测试生成模板

> 参考文档：[guide/testing/1.quick-start.md](docs/guide/testing/1.quick-start.md), [reference/testing/1_harness.md](docs/reference/testing/1_harness.md)

```python
"""
{plugin_name} 插件离线测试
"""

import pytest
from pathlib import Path
from ncatbot.testing import PluginTestHarness, group_message, private_message

pytestmark = pytest.mark.asyncio

PLUGIN_NAME = "{manifest_name}"


@pytest.fixture
def plugin_dir():
    return Path(__file__).resolve().parents[3] / "examples"


# ---- 加载测试 ----

async def test_plugin_loads(plugin_dir):
    """插件加载成功"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugin_dir=plugin_dir
    ) as h:
        assert PLUGIN_NAME in h.loaded_plugins


# ---- 命令测试 ----
# 为每个 @registrar.on_group_command("xxx") 生成:

async def test_{command_name}(plugin_dir):
    """群里发 '{command}' → handler 执行 → API 调用"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugin_dir=plugin_dir
    ) as h:
        await h.inject(group_message("{command}", group_id="100", user_id="99"))
        await h.settle(0.1)
        assert h.api_called("send_group_msg")


# ---- 多步对话测试 ----
# 如果插件使用了 self.wait_event()，为对话流程生成:

async def test_dialog_flow(plugin_dir):
    """多步对话流程"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugin_dir=plugin_dir
    ) as h:
        # Step 1: 触发
        await h.inject(group_message("{trigger}", group_id="100", user_id="99"))
        await h.settle(0.1)
        assert h.api_called("send_group_msg")

        # Step 2: 回复
        h.reset_api()
        await h.inject(group_message("{reply}", group_id="100", user_id="99"))
        await h.settle(0.1)
        assert h.api_called("send_group_msg")


# ---- Hook 测试 ----
# 如果插件使用了 Hook:

async def test_hook_filter(plugin_dir):
    """BEFORE_CALL Hook 拦截"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugin_dir=plugin_dir
    ) as h:
        await h.inject(group_message("{blocked_input}", group_id="100", user_id="99"))
        await h.settle(0.1)
        assert not h.api_called("send_group_msg"), "应被 Hook 拦截"


# ---- Data/Config 测试 ----
# 如果插件使用了 DataMixin/ConfigMixin:

async def test_data_persistence(plugin_dir):
    """数据持久化验证"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugin_dir=plugin_dir
    ) as h:
        plugin = h.get_plugin(PLUGIN_NAME)
        # 验证 data 初始化结构
        assert isinstance(plugin.data, dict)
```

## Scenario 构建器用法

> 参考文档：[guide/testing/3.factory-scenario.md](docs/guide/testing/3.factory-scenario.md), [reference/testing/2_factory_scenario_mock.md](docs/reference/testing/2_factory_scenario_mock.md)

对于复杂场景，可使用 Scenario 构建器:

```python
from ncatbot.testing import Scenario, group_message

await (
    Scenario("签到流程")
    .inject(group_message("签到", group_id="100", user_id="99"))
    .settle()
    .assert_api_called("send_group_msg")
    .run(harness)
)
```

## 关键规则

> 参考文档：[guide/testing/2.harness.md](docs/guide/testing/2.harness.md), [reference/testing/2_factory_scenario_mock.md](docs/reference/testing/2_factory_scenario_mock.md)

### API action 名称

常用 action 名称（完整列表见 [MockBotAPI 参考](docs/reference/testing/2_factory_scenario_mock.md#mockbotapi)）：

| action | 说明 |
|--------|------|
| `"send_group_msg"` | 发送群消息 |
| `"send_private_msg"` | 发送私聊消息 |
| `"delete_msg"` | 撤回消息 |
| `"set_group_kick"` | 踢出群成员 |
| `"set_group_ban"` | 群禁言 |

### settle 时间

- 默认 `settle(0.05)` 对简单 handler 足够
- 复杂 handler 增大至 `settle(0.2)`
- 含 `wait_event` 的多步对话用 `settle(0.5)`

### 多步对话

每步之间用 `h.reset_api()` 清除调用记录，避免断言混淆。

### 插件依赖

如果插件有 `[dependencies]`，`PluginTestHarness` 会自动解析传递依赖。

### skip_builtin

默认 `skip_builtin=True`，不加载内置插件，减少测试副作用。

### 事件工厂

8 个工厂函数（详见 [guide/testing/3.factory-scenario.md](docs/guide/testing/3.factory-scenario.md#1-事件工厂)）：

- `group_message(text, group_id=, user_id=)` — 群消息
- `private_message(text, user_id=)` — 私聊消息
- `friend_request()`, `group_request()` — 请求事件
- `group_increase()`, `group_decrease()`, `group_ban()`, `poke()` — 通知事件

### Mock 响应配置

如果 handler 依赖 API 返回值（详见 [guide/testing/2.harness.md](docs/guide/testing/2.harness.md#4-mock-响应配置)）：

```python
h.mock_api.set_response("get_group_member_info", {"user_id": "99", "nickname": "test"})
```

## 参考文档

- 测试快速入门: [docs/guide/testing/1.quick-start.md](docs/guide/testing/1.quick-start.md)
- Harness 详解: [docs/guide/testing/2.harness.md](docs/guide/testing/2.harness.md)
- 事件工厂与场景: [docs/guide/testing/3.factory-scenario.md](docs/guide/testing/3.factory-scenario.md)
- 测试 API 参考: [docs/reference/testing/](docs/reference/testing/)
- 示例插件: [examples/](examples/)
