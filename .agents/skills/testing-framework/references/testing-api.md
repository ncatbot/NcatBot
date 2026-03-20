# 测试 API 速查

## TestHarness

| 属性/方法 | 签名 | 说明 |
|-----------|------|------|
| `bot` | `BotClient` | BotClient 实例 |
| `adapter` | `MockAdapter` | MockAdapter 实例 |
| `mock_api` | `MockBotAPI` | API mock，用于断言 |
| `dispatcher` | `AsyncEventDispatcher` | 事件分发器 |
| `start()` | `async` | 启动 BotClient |
| `stop()` | `async` | 停止 BotClient |
| `inject(event_data)` | `async` | 注入单个事件 |
| `inject_many(events)` | `async` | 注入多个事件 |
| `settle(delay=0.05)` | `async` | 等待 handler 执行完 |
| `wait_event(predicate, timeout=2.0)` | `async` | 等待满足条件的事件 |
| `api_calls` | `list[APICall]` | 所有 API 调用记录 |
| `api_called(action)` | `bool` | 是否调用过某 action |
| `api_call_count(action)` | `int` | 某 action 的调用次数 |
| `get_api_calls(action)` | `list[APICall]` | 某 action 的所有调用 |
| `last_api_call(action)` | `APICall` | 某 action 最近一次调用 |
| `reset_api()` | `void` | 清空调用记录 |

## PluginTestHarness（继承 TestHarness）

| 参数/方法 | 签名 | 说明 |
|-----------|------|------|
| `plugin_names` | `list[str]` | 构造参数：要加载的插件名 |
| `plugin_dir` | `Path` | 构造参数：插件目录 |
| `skip_builtin` | `bool = True` | 构造参数：是否跳过内置插件 |
| `skip_pip` | `bool = True` | 构造参数：是否跳过 pip 依赖安装 |
| `loaded_plugins` | `list[str]` | 已加载插件名列表 |
| `get_plugin(name)` | `NcatBotPlugin` | 获取插件实例 |
| `plugin_config(name)` | `dict` | 获取插件配置 |
| `plugin_data(name)` | `dict` | 获取插件数据 |
| `reload_plugin(name)` | `async` | 热重载插件 |

## 事件工厂函数

| 函数 | 返回类型 | 关键参数（均有默认值） |
|------|---------|----------------------|
| `group_message(text)` | `GroupMessageEventData` | `group_id`, `user_id`, `self_id` |
| `private_message(text)` | `PrivateMessageEventData` | `user_id`, `self_id` |
| `friend_request()` | `FriendRequestEventData` | `user_id`, `comment` |
| `group_request()` | `GroupRequestEventData` | `user_id`, `group_id`, `comment` |
| `group_increase()` | `GroupIncreaseNoticeEventData` | `user_id`, `group_id`, `operator_id` |
| `group_decrease()` | `GroupDecreaseNoticeEventData` | `user_id`, `group_id`, `operator_id` |
| `group_ban()` | `GroupBanNoticeEventData` | `user_id`, `group_id`, `duration` |
| `poke()` | `PokeNotifyEventData` | `user_id`, `target_id`, `group_id` |

默认值：`user_id="99999"`, `group_id="100200"`, `self_id="10001"`

## MockAdapter 平台参数

TestHarness 和 PluginTestHarness 默认使用 `MockAdapter(platform="qq")`，事件数据工厂函数（`group_message` 等）也默认生成 `platform="qq"` 的数据。这确保 QQ 事件正确路由到 QQ 工厂并创建带有 `reply()` 等方法的实体。

如需测试非 QQ 平台，显式指定 platform：

```python
adapter = MockAdapter(platform="telegram")
bot = BotClient(adapter=adapter)
```

多适配器测试：

```python
bot = BotClient(adapters=[
    MockAdapter(platform="qq"),
    MockAdapter(platform="telegram"),
])
```

## MockBotAPI

| 方法 | 说明 |
|------|------|
| `set_response(action, response)` | 预设某 action 的返回值 |
| `calls` | 所有 `APICall` 记录 |
| `called(action)` | `bool` |
| `call_count(action)` | `int` |
| `get_calls(action)` | `list[APICall]` |
| `last_call(action)` | `APICall` |
| `reset()` | 清空记录 |

## APICall 数据类

```python
@dataclass
class APICall:
    action: str       # API action 名称
    args: tuple       # 位置参数
    kwargs: dict      # 关键字参数
    timestamp: float  # 调用时间
```

## Scenario 链式构建器

`Scenario` 是链式步骤构建器，调用 `await scenario.run(harness)` 执行全部步骤。

| 方法 | 返回 | 说明 |
|------|------|------|
| `Scenario(name="")` | `Scenario` | 构造，name 用于报错时定位步骤 |
| `.inject(event_data)` | `Scenario` | 注入单个事件 |
| `.inject_many(events)` | `Scenario` | 注入多个事件 |
| `.settle(delay=0.05)` | `Scenario` | 等待 handler 处理完成 |
| `.assert_api_called(action, **match)` | `Scenario` | 断言 API 被调用（可选 kwargs 参数匹配） |
| `.assert_api_not_called(action)` | `Scenario` | 断言 API 未被调用 |
| `.assert_api_count(action, count)` | `Scenario` | 断言 API 调用次数 |
| `.assert_that(predicate, desc="")` | `Scenario` | 自定义断言（predicate 接收 harness，可抛 AssertionError） |
| `.reset_api()` | `Scenario` | 清空 API 调用记录 |
| `await .run(harness)` | `None` | 执行全部步骤（async，必须传入 harness） |

```python
# 示例
scenario = (
    Scenario("login_flow")
    .inject(group_message("注册"))
    .settle()
    .assert_api_called("send_group_msg")
    .reset_api()
    .inject(group_message("张三"))
    .settle()
    .assert_api_called("send_group_msg")
)
await scenario.run(harness)  # 必须传入 harness 实例
```

## pytest Fixtures（conftest.py 提供）

| Fixture | 作用域 | 说明 |
|---------|--------|------|
| `mock_adapter` | function | 独立 MockAdapter |
| `harness` | function | TestHarness（async with 管理） |
| `mock_api` | function | MockBotAPI |
| `event_dispatcher` | function | AsyncEventDispatcher |
| `handler_dispatcher` | function | HandlerDispatcher（注入 mock_api） |
| `fresh_registrar` | function | 清理全局 pending 后的 Registrar |
| `tmp_plugin_workspace` | function | 临时插件工作目录（tmp_path） |

---

## 常见失败扩展

| 症状 | 可能原因 | 排查 / 修复 |
|------|---------|------------|
| handler 没被调用 | 事件类型字符串不匹配 / Hook 拦截 | 检查注册的事件类型；打印 `h.api_calls` 确认 |
| `api_called` 返回 False | handler 未执行 / `settle` 时间不足 | 改为 `await h.settle(0.1)`；加 `print` 确认 handler 执行 |
| `asyncio` 警告/报错 | 缺少 `asyncio_mode` 标记 | 文件顶部加 `pytestmark = pytest.mark.asyncio(mode="strict")` |
| `ImportError` | 测试依赖未安装 | `uv pip install -e ".[test]"` |
| 插件加载失败 | `plugin_dir` 路径错误 / 缺少 `__init__.py` | 用 `Path(__file__).resolve().parents[N] / "..."` 确保绝对路径 |
| flaky（偶发失败） | 异步竞态 / settle 时间不稳定 | 用 `wait_event(predicate, timeout=2.0)` 替代固定 delay |
| Mock 返回值不对 | 未预设 response | `harness.mock_api.set_response("action", {...})` |
| `platform` 过滤不生效 | 事件 data 与 adapter platform 不一致 | 工厂函数默认 `platform="qq"`；检查自定义事件数据 |
| `'BotAPIClient' has no attr 'post_group_msg'` | 插件直接调 `self.api.xxx` | QQ sugar 方法在 `self.api.qq` 上；`self.api` 是多平台路由器 |
| `'BaseEvent' has no attr 'reply'` | 事件数据缺少 `platform="qq"` | QQ 数据模型已内置 `platform: str = "qq"` 默认值；检查自定义数据 |
