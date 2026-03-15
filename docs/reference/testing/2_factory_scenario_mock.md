# Factory + Scenario + Mock

> 事件工厂函数、场景构建器、Mock 适配器完整 API 参考

---

## 事件工厂函数

所有函数返回经 `model_validate` 验证的 Pydantic 模型实例。

### group_message

```python
group_message(
    text: str = "hello",
    *,
    group_id: str = "100200",
    user_id: str = "99999",
    nickname: str = "测试用户",
    message_id: Optional[str] = None,    # 自动递增
    self_id: str = "10001",
    message: Optional[list] = None,      # 自定义消息段
    raw_message: Optional[str] = None,   # 默认等于 text
    sub_type: str = "normal",
    **extra: Any,
) -> GroupMessageEventData
```

### private_message

```python
private_message(
    text: str = "hello",
    *,
    user_id: str = "99999",
    nickname: str = "测试用户",
    message_id: Optional[str] = None,
    self_id: str = "10001",
    message: Optional[list] = None,
    raw_message: Optional[str] = None,
    sub_type: str = "friend",
    **extra: Any,
) -> PrivateMessageEventData
```

### friend_request

```python
friend_request(
    user_id: str = "99999",
    comment: str = "请求加好友",
    flag: str = "flag_123",
    *,
    self_id: str = "10001",
    **extra: Any,
) -> FriendRequestEventData
```

### group_request

```python
group_request(
    user_id: str = "99999",
    group_id: str = "100200",
    comment: str = "请求加群",
    flag: str = "flag_456",
    sub_type: str = "add",
    *,
    self_id: str = "10001",
    **extra: Any,
) -> GroupRequestEventData
```

### group_increase

```python
group_increase(
    user_id: str = "99999",
    group_id: str = "100200",
    operator_id: str = "10001",
    sub_type: str = "approve",
    *,
    self_id: str = "10001",
    **extra: Any,
) -> GroupIncreaseNoticeEventData
```

### group_decrease

```python
group_decrease(
    user_id: str = "99999",
    group_id: str = "100200",
    operator_id: str = "10001",
    sub_type: str = "kick",
    *,
    self_id: str = "10001",
    **extra: Any,
) -> GroupDecreaseNoticeEventData
```

### group_ban

```python
group_ban(
    user_id: str = "99999",
    group_id: str = "100200",
    operator_id: str = "10001",
    duration: int = 600,
    sub_type: str = "ban",
    *,
    self_id: str = "10001",
    **extra: Any,
) -> GroupBanNoticeEventData
```

### poke

```python
poke(
    user_id: str = "99999",
    target_id: str = "10001",
    group_id: str = "100200",
    *,
    self_id: str = "10001",
    **extra: Any,
) -> PokeNotifyEventData
```

---

## Scenario

```python
from ncatbot.testing import Scenario
```

链式测试场景构建器。所有链式方法返回 `self`。

### 构造

```python
Scenario(name: str = "") -> Scenario
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | 场景名称（出现在失败消息中） |

### 链式方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `inject` | `inject(event_data: BaseEventData) -> Scenario` | 注入事件步骤 |
| `inject_many` | `inject_many(events: List[BaseEventData]) -> Scenario` | 注入多事件步骤 |
| `settle` | `settle(delay: float = 0.05) -> Scenario` | 等待步骤 |
| `assert_api_called` | `assert_api_called(action: str, **match) -> Scenario` | API 调用断言 |
| `assert_api_not_called` | `assert_api_not_called(action: str) -> Scenario` | API 未调用断言 |
| `assert_api_count` | `assert_api_count(action: str, count: int) -> Scenario` | 调用次数断言 |
| `assert_that` | `assert_that(predicate: Callable[[TestHarness], None], desc: str = "") -> Scenario` | 自定义断言 |
| `reset_api` | `reset_api() -> Scenario` | 清空调用记录 |

### 执行

```python
async run(harness: TestHarness) -> None
```

按顺序执行所有步骤。失败时抛出 `AssertionError`，包含场景名和步骤编号。

---

## APICall

```python
from ncatbot.adapter.mock.api import APICall
```

```python
@dataclass
class APICall:
    action: str      # API 方法名（如 "send_group_msg"）
    args: tuple      # 位置参数
    kwargs: dict     # 关键字参数
```

---

## MockBotAPI

```python
from ncatbot.adapter.mock import MockBotAPI
```

`IBotAPI` 的完整 Mock 实现。记录所有调用，返回可配置响应。

### 调用记录方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `calls` | `@property -> List[APICall]` | 所有调用记录 |
| `called` | `called(action: str) -> bool` | 是否被调用 |
| `call_count` | `call_count(action: str) -> int` | 调用次数 |
| `get_calls` | `get_calls(action: str) -> List[APICall]` | 获取匹配调用 |
| `last_call` | `last_call(action: str = None) -> Optional[APICall]` | 最近一次调用 |
| `reset` | `reset() -> None` | 清空记录 |

### 响应配置

```python
set_response(action: str, response: Any) -> None
```

未配置的 action 返回 `{}`。

### 已实现的 API 方法

| 分类 | action 名称 |
|------|------------|
| **消息** | `send_private_msg`, `send_group_msg`, `delete_msg`, `send_forward_msg` |
| **群管理** | `set_group_kick`, `set_group_ban`, `set_group_whole_ban`, `set_group_admin`, `set_group_card`, `set_group_name`, `set_group_leave`, `set_group_special_title` |
| **请求** | `set_friend_add_request`, `set_group_add_request` |
| **查询** | `get_login_info`, `get_stranger_info`, `get_friend_list`, `get_group_info`, `get_group_list`, `get_group_member_info`, `get_group_member_list`, `get_msg`, `get_forward_msg` |
| **文件** | `upload_group_file`, `get_group_root_files`, `get_group_file_url`, `delete_group_file` |
| **互动** | `send_like`, `send_poke` |

---

## MockAdapter

```python
from ncatbot.adapter.mock import MockAdapter
```

`BaseAdapter` 的内存实现，无网络通信。

| 属性/方法 | 签名 | 说明 |
|----------|------|------|
| `mock_api` | `@property -> MockBotAPI` | Mock API 实例 |
| `connected` | `@property -> bool` | 是否已连接 |
| `inject_event` | `async inject_event(data: BaseEventData) -> None` | 注入事件到 dispatcher |
| `stop` | `stop() -> None` | 停止 listen 循环 |
| `get_api` | `get_api() -> IBotAPI` | 返回 MockBotAPI |

> 通常通过 `TestHarness.adapter` 访问，无需直接实例化。

---

## 插件发现

### discover_testable_plugins

```python
discover_testable_plugins(plugin_dir: Path) -> List[PluginManifest]
```

扫描目录下所有含 `manifest.toml` 的子文件夹，返回解析后的 `PluginManifest` 列表。

### generate_smoke_tests

```python
generate_smoke_tests(manifests: List[PluginManifest]) -> str
```

批量生成冒烟测试代码（完整 pytest 文件）。

### generate_smoke_test

```python
generate_smoke_test(manifest: PluginManifest) -> str
```

为单个插件生成冒烟测试代码片段。

---

## conftest_plugin.py — pytest 插件

### CLI 选项

| 选项 | 说明 |
|------|------|
| `--plugin-dir=PATH` | 插件根目录路径 |

### Markers

| Marker | 说明 |
|--------|------|
| `@pytest.mark.plugin(name="xxx")` | 标记特定插件测试 |
| `@pytest.mark.plugin_names(names)` | 指定要加载的插件名列表 |
| `@pytest.mark.plugin_dir(dir)` | 指定插件目录 |

### Fixtures

| Fixture | 说明 |
|---------|------|
| `plugin_dir` | 从 `--plugin-dir` 获取的 `Path` |

### 辅助函数

```python
get_testable_plugin_names(plugin_dir: str) -> List[str]
```

返回目录下所有可测试插件名。

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [TestHarness + PluginTestHarness](1_harness.md) | 编排器 API |
| [测试指南：工厂与场景](../../guide/testing/3.factory-scenario.md) | 教程风格的用法说明 |
