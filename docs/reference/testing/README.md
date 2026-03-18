# 测试框架参考

> `ncatbot.testing` 模块完整 API 参考

---

## Quick Reference

```python
from ncatbot.testing import TestHarness, PluginTestHarness, group_message
```

### 核心组件

| 组件 | 说明 |
|------|------|
| `TestHarness` | 轻量无插件测试 — 注册 handler 并注入事件 |
| `PluginTestHarness` | 完整插件测试 — 加载真实插件目录并模拟事件流 |
| `Scenario` | 链式构建器 — 编排多步交互场景 |
| `MockAdapter` / `MockBotAPI` | 内存模拟 — 无需网络连接 |

### 事件工厂函数（8 个）

| 函数 | 说明 |
|------|------|
| `group_message(content, group_id=, user_id=)` | 群消息 |
| `private_message(content, user_id=)` | 私聊消息 |
| `friend_request(user_id=)` | 好友请求 |
| `group_request(group_id=, user_id=)` | 加群请求 |
| `group_increase(group_id=, user_id=)` | 群成员增加 |
| `group_decrease(group_id=, user_id=)` | 群成员减少 |
| `group_ban(group_id=, user_id=)` | 群禁言 |
| `poke(group_id=, user_id=)` | 戳一戳 |

典型用法：`PluginTestHarness` → `h.inject(group_message(...))` → `h.settle()` → `h.api_called("send_group_msg")`

---

## 模块结构

```python
ncatbot/testing/              # 测试框架公开 API
├── __init__.py               # 公开导出
├── harness.py                # TestHarness
├── plugin_harness.py         # PluginTestHarness
├── factory.py                # 事件工厂函数（8 个）
├── scenario.py               # Scenario 链式构建器
├── discovery.py              # 插件发现 + 冒烟测试生成
└── conftest_plugin.py        # pytest 插件（marker + fixture）

ncatbot/adapter/mock/         # Mock 适配器（内部使用）
├── adapter.py                # MockAdapter
└── api.py                    # MockBotAPI + APICall
```

---

## 公开导出

```python
from ncatbot.testing import (
    # 编排器
    TestHarness,
    PluginTestHarness,
    # 场景构建器
    Scenario,
    # 事件工厂
    group_message,
    private_message,
    friend_request,
    group_request,
    group_increase,
    group_decrease,
    group_ban,
    poke,
    # 插件发现
    discover_testable_plugins,
    generate_smoke_tests,
)
```

---

## 类 / 函数索引

| 名称 | 类型 | 详细文档 |
|------|------|---------|
| `TestHarness` | class | [1_harness.md](1_harness.md#testharness) |
| `PluginTestHarness` | class | [1_harness.md](1_harness.md#plugintestharness) |
| `Scenario` | class | [2_factory_scenario_mock.md](2_factory_scenario_mock.md#scenario) |
| `group_message()` | function | [2_factory_scenario_mock.md](2_factory_scenario_mock.md#事件工厂函数) |
| `private_message()` | function | [2_factory_scenario_mock.md](2_factory_scenario_mock.md#事件工厂函数) |
| `friend_request()` | function | [2_factory_scenario_mock.md](2_factory_scenario_mock.md#事件工厂函数) |
| `group_request()` | function | [2_factory_scenario_mock.md](2_factory_scenario_mock.md#事件工厂函数) |
| `group_increase()` | function | [2_factory_scenario_mock.md](2_factory_scenario_mock.md#事件工厂函数) |
| `group_decrease()` | function | [2_factory_scenario_mock.md](2_factory_scenario_mock.md#事件工厂函数) |
| `group_ban()` | function | [2_factory_scenario_mock.md](2_factory_scenario_mock.md#事件工厂函数) |
| `poke()` | function | [2_factory_scenario_mock.md](2_factory_scenario_mock.md#事件工厂函数) |
| `MockBotAPI` | class | [2_factory_scenario_mock.md](2_factory_scenario_mock.md#mockbotapi) |
| `MockAdapter` | class | [2_factory_scenario_mock.md](2_factory_scenario_mock.md#mockadapter) |
| `APICall` | dataclass | [2_factory_scenario_mock.md](2_factory_scenario_mock.md#apicall) |
| `discover_testable_plugins()` | function | [2_factory_scenario_mock.md](2_factory_scenario_mock.md#插件发现) |
| `generate_smoke_tests()` | function | [2_factory_scenario_mock.md](2_factory_scenario_mock.md#插件发现) |

---

## 本目录索引

| 文件 | 说明 |
|------|------|
| [1_harness.md](1_harness.md) | TestHarness + PluginTestHarness 完整 API |
| [2_factory_scenario_mock.md](2_factory_scenario_mock.md) | 工厂函数、Scenario 构建器、MockAdapter / MockBotAPI |
