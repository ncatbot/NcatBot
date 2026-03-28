# 测试 API 速查

## TestHarness

`from ncatbot.testing import TestHarness`

| 属性/方法 | 签名 | 说明 |
|-----------|------|------|
| 构造 | `TestHarness(platforms=("qq",))` | 可传多平台 |
| `bot` | `BotClient` | BotClient 实例 |
| `dispatcher` | `AsyncEventDispatcher` | 事件分发器（原始事件流） |
| `bot.handler_dispatcher` | `HandlerDispatcher` | Handler 路由层（注册 handler 用此属性） |
| `mock_api` | `MockAPIBase` | 第一个平台的 MockAPI（单平台快捷） |
| `mock_api_for(platform)` | `MockAPIBase` | 指定平台的 MockAPI |
| `adapter_for(platform)` | `MockAdapter` | 指定平台的 MockAdapter |
| `start()` | `async` | 启动 BotClient |
| `stop()` | `async` | 停止 BotClient |
| `inject(event_data)` | `async` | 注入事件（按 `event_data.platform` 自动路由） |
| `inject_many(events)` | `async` | 依次注入多个事件 |
| `settle(delay=0.05)` | `async` | 等待 handler 执行完 |
| `wait_event(predicate, timeout=2.0)` | `async → Event` | 等待满足条件的事件 |
| `assert_api(action)` | `→ APICallAssertion` | 全平台范围 fluent 断言 |
| `on(platform)` | `→ PlatformScope` | 限定平台后再断言 |
| `reset_api(platform=None)` | `void` | 清空调用记录（指定平台或全部） |

## PluginTestHarness（继承 TestHarness）

`from ncatbot.testing import PluginTestHarness`

| 参数/方法 | 签名 | 说明 |
|-----------|------|------|
| 构造 | `PluginTestHarness(plugin_names, plugins_dir, *, platforms=("qq",), skip_builtin=True, skip_pip=True)` | |
| `loaded_plugins` | `list[str]` | 已加载插件名列表 |
| `get_plugin(name)` | `BasePlugin \| None` | 获取插件实例 |
| `plugin_config(name)` | `dict` | 获取插件配置 |
| `plugin_data(name)` | `dict` | 获取插件数据 |
| `reload_plugin(name)` | `async → bool` | 热重载插件 |

## APICall 数据类

`from ncatbot.adapter.mock.api_base import APICall`

```python
@dataclass
class APICall:
    action: str                          # API action 名称
    params: Dict[str, Any] = field(...)  # 所有参数按名存储
```

> 无 `args` / `kwargs` / `timestamp`。所有参数以关键字形式统一存入 `params` 字典。

## MockAPIBase

`from ncatbot.adapter.mock import MockAPIBase`

所有平台 Mock API 的共享基类。`MockBotAPI`、`MockBiliAPI`、`MockGitHubAPI` 均继承此类。

| 方法/属性 | 签名 | 说明 |
|-----------|------|------|
| 构造 | `MockAPIBase(platform="unknown")` | |
| `platform` | `str` | 平台标识 |
| `set_response(action, response)` | `void` | 预设某 action 的返回值 |
| `calls` | `list[APICall]` | 全部调用记录 |
| `called(action)` | `bool` | 某 action 是否被调用过 |
| `call_count(action)` | `int` | 某 action 调用次数 |
| `get_calls(action)` | `list[APICall]` | 某 action 的全部调用 |
| `last_call(action=None)` | `APICall \| None` | 最近一次（指定 action 或全部） |
| `reset()` | `void` | 清空全部记录 |

## MockBotAPI（QQ）

`from ncatbot.adapter.mock import MockBotAPI`

继承 `MockAPIBase` + `IQQAPIClient`。所有 QQ API 方法均以 `self._record("action", key=val, ...)` 形式录制。

代表方法签名示例：

| 方法 | 录制 action | 录制的 params keys |
|------|-----------|-------------------|
| `send_group_msg(group_id, message, **kw)` | `send_group_msg` | `group_id`, `message`, ... |
| `send_private_msg(user_id, message, **kw)` | `send_private_msg` | `user_id`, `message`, ... |
| `set_group_ban(group_id, user_id, duration)` | `set_group_ban` | `group_id`, `user_id`, `duration` |

## MockBiliAPI（Bilibili）

`from ncatbot.adapter.mock import MockBiliAPI`

继承 `MockAPIBase` + `IBiliAPIClient`。

| 方法 | 录制 action | 录制的 params keys |
|------|-----------|-------------------|
| `send_danmu(room_id, text)` | `send_danmu` | `room_id`, `text` |
| `send_private_msg(user_id, text)` | `send_private_msg` | `user_id`, `text` |
| `ban_user(room_id, user_id, duration)` | `ban_user` | `room_id`, `user_id`, `duration` |

## MockGitHubAPI（GitHub）

`from ncatbot.adapter.mock import MockGitHubAPI`

继承 `MockAPIBase` + `IGitHubAPIClient`。

| 方法 | 录制 action | 录制的 params keys |
|------|-----------|-------------------|
| `create_issue_comment(repo, issue_number, body)` | `create_issue_comment` | `repo`, `issue_number`, `body` |
| `create_issue(repo, title, body, labels)` | `create_issue` | `repo`, `title`, `body`, `labels` |
| `merge_pull_request(repo, pr_number, method)` | `merge_pull_request` | `repo`, `pr_number`, `method` |

## APICallAssertion（Fluent 断言）

`from ncatbot.testing import APICallAssertion`

通过 `h.assert_api(action)` 或 `h.on(platform).assert_api(action)` 获取。

| 方法 | 返回 | 说明 |
|------|------|------|
| `called()` | `self` | 断言至少被调用一次 |
| `not_called()` | `self` | 断言未被调用 |
| `times(n)` | `self` | 断言调用次数 |
| `with_params(**expected)` | `self` | 断言任一调用的 params 包含 expected 子集 |
| `with_text(*fragments)` | `self` | 断言任一调用的文本包含所有 fragment（跨平台感知） |
| `where(predicate)` | `self` | 断言任一调用满足自定义条件 |
| `last` | `APICall` | 最后一次匹配调用（property） |
| `calls` | `list[APICall]` | 所有匹配调用（property） |

链式用法：

```python
h.assert_api("send_group_msg").called().with_params(group_id="999").with_text("pong")
```

## PlatformScope

`from ncatbot.testing import PlatformScope`

通过 `h.on(platform)` 获取。

| 方法/属性 | 签名 | 说明 |
|-----------|------|------|
| `assert_api(action)` | `→ APICallAssertion` | 该平台范围内的断言 |
| `mock_api` | `MockAPIBase` | 该平台的 MockAPI |
| `reset()` | `void` | 清空该平台记录 |

## extract_text()

`from ncatbot.testing import extract_text`

```python
def extract_text(call: APICall) -> str
```

从 `APICall` 中提取文本内容（跨平台感知）：
- QQ `message` (list[segment]) → 拼接 `type=text` 的 `data.text`
- Bilibili `text`/`content` → 直接取字符串
- GitHub `body` → 直接取字符串
- 兜底 → `str(params)`

## 事件工厂函数

### QQ — `from ncatbot.testing.factories.qq import ...`

| 函数 | 返回类型 | 关键参数（均有默认值） |
|------|---------|----------------------|
| `group_message(text)` | `GroupMessageEventData` | `group_id`, `user_id`, `self_id`, `message`, `raw_message`, `sub_type` |
| `private_message(text)` | `PrivateMessageEventData` | `user_id`, `self_id`, `message`, `raw_message`, `sub_type` |
| `friend_request(user_id, comment)` | `FriendRequestEventData` | `flag`, `self_id` |
| `group_request(user_id, group_id, comment)` | `GroupRequestEventData` | `flag`, `sub_type`, `self_id` |
| `group_increase(user_id, group_id, operator_id)` | `GroupIncreaseNoticeEventData` | `sub_type`, `self_id` |
| `group_decrease(user_id, group_id, operator_id)` | `GroupDecreaseNoticeEventData` | `sub_type`, `self_id` |
| `group_ban(user_id, group_id, operator_id, duration)` | `GroupBanNoticeEventData` | `sub_type`, `self_id` |
| `poke(user_id, target_id, group_id)` | `PokeNotifyEventData` | `self_id` |

默认值：`user_id="99999"`, `group_id="100200"`, `self_id="10001"`

### Bilibili — `from ncatbot.testing.factories.bilibili import ...`

| 函数 | 返回类型 | 关键参数 |
|------|---------|---------|
| `danmu(text)` | `DanmuMsgEventData` | `room_id`, `user_id`, `user_name` |
| `super_chat(content, price)` | `SuperChatEventData` | `room_id`, `user_id`, `duration` |
| `gift(gift_name, num)` | `GiftEventData` | `room_id`, `gift_id`, `price`, `coin_type` |
| `private_message(text)` | `BiliPrivateMessageEventData` | `user_id`, `user_name` |
| `comment(content)` | `BiliCommentEventData` | `resource_id`, `resource_type`, `comment_id` |
| `dynamic(text)` | `BiliDynamicEventData` | `uid`, `dynamic_id`, `dynamic_type` |

默认值：`room_id="12345"`, `user_id="88888"`

### GitHub — `from ncatbot.testing.factories.github import ...`

| 函数 | 返回类型 | 关键参数 |
|------|---------|---------|
| `issue_opened(title, body)` | `GitHubIssueEventData` | `repo`, `issue_number`, `login`, `labels` |
| `issue_closed(title)` | `GitHubIssueEventData` | `repo`, `issue_number`, `login` |
| `issue_comment(body)` | `GitHubIssueCommentEventData` | `repo`, `issue_number`, `comment_id`, `login` |
| `pr_opened(title, body)` | `GitHubPREventData` | `repo`, `pr_number`, `head_ref`, `base_ref`, `login` |
| `push(ref)` | `GitHubPushEventData` | `repo`, `login`, `before`, `after` |
| `star()` | `GitHubStarEventData` | `repo`, `login`, `action` |
| `release_published(tag_name, name, body)` | `GitHubReleaseEventData` | `repo`, `login` |

默认值：`repo="owner/repo"`, `login="test-user"`

## Scenario 链式构建器

`from ncatbot.testing import Scenario`

| 方法 | 返回 | 说明 |
|------|------|------|
| `Scenario(name="")` | `Scenario` | 构造，name 用于报错时定位步骤 |
| `.on(platform)` | `Scenario` | 切换后续断言步骤的平台作用域 |
| `.inject(event_data)` | `Scenario` | 注入单个事件 |
| `.inject_many(events)` | `Scenario` | 注入多个事件 |
| `.settle(delay=0.05)` | `Scenario` | 等待 handler 处理完成 |
| `.assert_api_called(action, **match)` | `Scenario` | 断言 API 被调用（可选 params 子集匹配） |
| `.assert_api_not_called(action)` | `Scenario` | 断言 API 未被调用 |
| `.assert_api_count(action, count)` | `Scenario` | 断言 API 调用次数 |
| `.assert_api_params(action, **params)` | `Scenario` | 断言 API 被调用且 params 包含指定子集 |
| `.assert_api_text(action, *fragments)` | `Scenario` | 断言 API 文本内容包含所有 fragment |
| `.assert_api_where(action, predicate, desc="")` | `Scenario` | 断言 API 任一调用满足 predicate |
| `.assert_that(predicate, desc="")` | `Scenario` | 自定义断言（predicate 接收 harness） |
| `.reset_api()` | `Scenario` | 清空 API 调用记录 |
| `await .run(harness)` | `None` | 执行全部步骤 |

```python
await (
    Scenario("多步对话")
    .inject(qq.group_message("注册", group_id="500"))
    .settle()
    .assert_api_called("send_group_msg")
    .assert_api_text("send_group_msg", "请输入姓名")
    .reset_api()
    .inject(qq.group_message("张三", group_id="500"))
    .settle()
    .on("qq").assert_api_called("send_group_msg")
    .assert_api_params("send_group_msg", group_id="500")
    .run(harness)
)
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
| handler 没被调用 | 事件类型字符串不匹配 / Hook 拦截 | 检查注册的事件类型；打印 `h.mock_api.calls` 确认 |
| `assert_api().called()` 失败 | handler 未执行 / `settle` 时间不足 | 改为 `await h.settle(0.1)`；加 `print` 确认 handler 执行 |
| `asyncio` 警告/报错 | 缺少 `asyncio_mode` 标记 | 文件顶部加 `pytestmark = pytest.mark.asyncio(mode="strict")` |
| `ImportError` | 测试依赖未安装 | `uv pip install -e ".[test]"` |
| 插件加载失败 | `plugins_dir` 路径错误 / 缺少 `__init__.py` | 用 `Path(__file__).resolve().parents[N] / "..."` 确保绝对路径 |
| flaky（偶发失败） | 异步竞态 / settle 时间不稳定 | 用 `wait_event(predicate, timeout=2.0)` 替代固定 delay |
| Mock 返回值不对 | 未预设 response | `harness.mock_api.set_response("action", {...})` |
| `ValueError: 未注册平台` | inject 的事件 platform 与 harness platforms 不匹配 | 构造 harness 时传入对应平台 |
| `'BaseEvent' has no attr 'reply'` | 事件数据缺少 `platform="qq"` | QQ 数据模型已内置 `platform: str = "qq"` 默认值；检查自定义数据 |
