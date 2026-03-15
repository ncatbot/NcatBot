# 插件测试指南

> 为你的 NcatBot 插件编写自动化测试

---

## Quick Start

5 步写出第一个插件测试：

### 1. 安装测试依赖

```bash
uv pip install ncatbot55[test]
```

### 2. 创建测试文件

在插件项目中创建 `tests/test_my_plugin.py`：

```python
import pytest
from ncatbot.testing import PluginTestHarness, group_message

pytestmark = pytest.mark.asyncio
```

### 3. 编写加载测试

```python
async def test_plugin_loads():
    async with PluginTestHarness(
        plugin_names=["my_plugin"],
        plugin_dir=Path("plugins/"),
    ) as h:
        assert "my_plugin" in h.loaded_plugins
```

### 4. 编写命令测试

```python
async def test_hello_command():
    async with PluginTestHarness(
        plugin_names=["hello_world"],
        plugin_dir=Path("examples/01_hello_world"),
    ) as h:
        await h.inject(group_message("hello", group_id="100", user_id="99"))
        await h.settle()
        assert h.api_called("send_group_msg")
```

### 5. 运行测试

```bash
python -m pytest tests/ -v
```

> **下一步：** 阅读 [快速入门](1.quick-start.md) 了解完整的测试编写流程。

---

## 速查参考

### TestHarness vs PluginTestHarness

| 特性 | TestHarness | PluginTestHarness |
|------|-------------|-------------------|
| 适用场景 | 框架级集成测试 | **插件开发者测试**（推荐） |
| 插件加载 | 不加载任何插件 | 选择性加载指定插件 + 依赖 |
| 插件查询 | ✗ | `get_plugin()` / `plugin_config()` / `plugin_data()` |
| 热重载 | ✗ | `reload_plugin()` |
| skip_builtin | — | 默认 True（不加载内置插件） |

### 事件工厂函数一览

| 函数 | 返回类型 | 默认关键参数 |
|------|---------|-------------|
| `group_message(text)` | `GroupMessageEventData` | `group_id="100200"`, `user_id="99999"` |
| `private_message(text)` | `PrivateMessageEventData` | `user_id="99999"` |
| `friend_request()` | `FriendRequestEventData` | `user_id="99999"`, `comment="请求加好友"` |
| `group_request()` | `GroupRequestEventData` | `group_id="100200"`, `user_id="99999"` |
| `group_increase()` | `GroupIncreaseNoticeEventData` | `group_id="100200"`, `user_id="99999"` |
| `group_decrease()` | `GroupDecreaseNoticeEventData` | `group_id="100200"`, `user_id="99999"` |
| `group_ban()` | `GroupBanNoticeEventData` | `duration=600` |
| `poke()` | `PokeNotifyEventData` | `target_id="10001"` |

### Scenario 链式方法一览

| 方法 | 说明 |
|------|------|
| `.inject(event)` | 注入一个事件 |
| `.inject_many(events)` | 注入多个事件 |
| `.settle(delay=0.05)` | 等待 handler 处理 |
| `.assert_api_called(action, **match)` | 断言 API 被调用（可选参数匹配） |
| `.assert_api_not_called(action)` | 断言 API 未被调用 |
| `.assert_api_count(action, count)` | 断言调用次数 |
| `.assert_that(predicate, desc)` | 自定义断言 |
| `.reset_api()` | 清空调用记录 |
| `.run(harness)` | 执行全部步骤 |

---

## 章节索引

| 章节 | 说明 | 难度 |
|------|------|------|
| [1. 快速入门](1.quick-start.md) | 5 分钟写出第一个插件测试 | ⭐ |
| [2. Harness 详解](2.harness.md) | TestHarness 与 PluginTestHarness 深入使用 | ⭐⭐ |
| [3. 工厂与场景](3.factory-scenario.md) | 事件工厂、Scenario 构建器、自动冒烟测试 | ⭐⭐ |

---

## 推荐阅读路线

| 我想… | 路径 |
|-------|------|
| **快速给插件加测试** | 1.quick-start → 本页速查表 |
| **深入了解测试能力** | 1 → 2 → 3 |
| **查 API 签名** | → [测试 API 参考](../../reference/testing/) |

---

## 相关资源

| 资源 | 链接 |
|------|------|
| 测试 API 参考 | [reference/testing/](../../reference/testing/) |
| 插件开发指南 | [guide/plugin/](../plugin/) |
| 开发环境搭建 | [contributing/development_setup/](../../contributing/development_setup/) |
| 示例插件 | [examples/](../../../examples/) |
