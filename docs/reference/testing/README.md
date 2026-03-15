# 测试框架参考

> `ncatbot.testing` 模块完整 API 参考

---

## 模块结构

```
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

## pytest 集成速查

### Fixtures

| Fixture | 来源 | 说明 |
|---------|------|------|
| `harness` | `tests/conftest.py` | `TestHarness` async 上下文 |
| `mock_adapter` | `tests/conftest.py` | 独立 `MockAdapter` 实例 |
| `plugin_dir` | `conftest_plugin.py` | 从 `--plugin-dir` 获取路径 |

### Markers

| Marker | 说明 |
|--------|------|
| `@pytest.mark.plugin(name="xxx")` | 标记为特定插件的测试 |

### CLI 选项

| 选项 | 说明 |
|------|------|
| `--plugin-dir=PATH` | 指定插件根目录（用于插件自动发现） |

---

## 深入阅读

| 文档 | 说明 |
|------|------|
| [TestHarness + PluginTestHarness](1_harness.md) | 编排器完整 API 签名 |
| [Factory + Scenario + Mock](2_factory_scenario_mock.md) | 工厂函数、场景构建器、Mock API 签名 |
| [测试使用指南](../../guide/testing/) | 教程风格的测试入门 |
