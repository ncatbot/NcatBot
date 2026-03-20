---
name: testing
description: '编写和运行 NcatBot 测试。覆盖框架单元/集成/E2E 测试、插件测试、用户代码测试。Use when: 写测试、跑测试、测试失败、覆盖率、pytest、TestHarness、mock、插件测试、冒烟测试、回归测试、测试调试。'
---

# NcatBot 测试技能

编写、运行、调试 NcatBot 框架及插件的自动化测试。

## 适用场景

| 场景 | 说明 |
|------|------|
| 框架测试 | 为框架模块编写单元/集成/E2E 测试 |
| 插件测试 | 为自有或第三方插件编写测试 |
| 用户代码测试 | 为基于 NcatBot 的 bot 应用编写测试 |
| 测试调试 | 定位测试失败原因、修复 flaky test |
| 覆盖率提升 | 识别未覆盖路径并补充测试 |

## 工作流

```text
1. 确定测试类型 → 2. 选择工具 → 3. 编写测试 → 4. 运行验证 → 5. 修复问题
```

---

## Step 1：确定测试类型

根据测试目标选择测试层级：

| 测试层级 | 目标 | 位置 | 使用工具 |
|---------|------|------|---------|
| 单元测试 | 单个类/函数的隔离行为 | `tests/unit/<模块>/` | pytest + MockBotAPI |
| 集成测试 | 多模块协作链路 | `tests/integration/` | pytest + TestHarness |
| E2E 测试 | BotClient 完整生命周期 | `tests/e2e/` | TestHarness |
| 插件测试 | 插件加载/命令/生命周期 | 插件项目 `tests/` 或 `tests/e2e/plugin/` | PluginTestHarness |
| NapCat E2E | 真实 WebSocket 连接 | `tests/e2e/napcat/` | 引导式脚本（非 pytest） |

### 决策指南

- **测试某个工具函数/解析器？** → 单元测试
- **测试事件从接收到 handler 响应的完整流程？** → 集成测试
- **测试 BotClient 启停 + 事件注入？** → E2E 测试
- **测试自己写的插件？** → 插件测试（PluginTestHarness）
- **需要真实 QQ 连接验证？** → NapCat E2E

---

## Step 2：选择工具

### 核心测试 API

> 详细参考：[references/testing-api.md](./references/testing-api.md)

```python
from ncatbot.testing import (
    # 编排器
    TestHarness,          # 框架级测试（无插件）
    PluginTestHarness,    # 插件测试（加载指定插件）
    # 场景构建器
    Scenario,             # 链式多步骤场景
    # 事件工厂（8 个）
    group_message, private_message,
    friend_request, group_request,
    group_increase, group_decrease,
    group_ban, poke,
    # 插件发现
    discover_testable_plugins,
    generate_smoke_tests,
)
```

### TestHarness vs PluginTestHarness

| 特性 | TestHarness | PluginTestHarness |
|------|-------------|-------------------|
| 适用 | 框架级集成/E2E 测试 | **插件测试**（推荐） |
| 插件 | 不加载任何插件 | 选择性加载指定插件 |
| 插件查询 | ✗ | `get_plugin()` / `plugin_config()` / `plugin_data()` |
| 热重载 | ✗ | `reload_plugin()` |

### MockBotAPI 断言方法

```python
harness.api_called("send_group_msg")        # bool：是否调用过
harness.api_call_count("send_group_msg")     # int：调用次数
harness.get_api_calls("send_group_msg")      # list[APICall]：所有调用
harness.last_api_call("send_group_msg")      # APICall：最近一次
harness.reset_api()                          # 清空记录
```

---

## Step 3：编写测试

根据测试类型，参照对应模板编写测试。

### 3a. 框架单元测试

**目标**：隔离测试框架内部某个类/函数。

```python
import pytest
from ncatbot.testing import group_message

pytestmark = pytest.mark.asyncio(mode="strict")

async def test_dispatcher_routes_group_message(event_dispatcher):
    """D-XX: AsyncEventDispatcher 正确路由群消息"""
    received = []
    async def handler(event):
        received.append(event)

    event_dispatcher.subscribe("message.group", handler)
    await event_dispatcher.callback(group_message("hello"))
    assert len(received) == 1
```

**关键约束**：
- 使用 `conftest.py` 中的 fixture（`mock_api`, `event_dispatcher`, `handler_dispatcher`, `fresh_registrar`）
- 遵循规范编号体系（参见 [references/spec-ids.md](./references/spec-ids.md)）
- `asyncio_mode = "strict"`，所有异步测试需标记 `pytest.mark.asyncio`

### 3b. 框架集成测试

**目标**：验证多模块协作链路。

```python
import pytest
from ncatbot.testing import TestHarness, group_message

pytestmark = pytest.mark.asyncio(mode="strict")

async def test_event_pipeline_group_message():
    """I-XX: 群消息事件走完 Dispatcher → Handler → API 全链路"""
    async with TestHarness() as h:
        await h.inject(group_message("hello", group_id="111"))
        await h.settle()
        assert h.api_called("send_group_msg")
```

### 3c. 插件测试

**目标**：验证插件加载、命令响应、生命周期。

```python
import pytest
from pathlib import Path
from ncatbot.testing import PluginTestHarness, group_message

pytestmark = pytest.mark.asyncio(mode="strict")

async def test_plugin_loads():
    """加载测试：插件正确加载"""
    async with PluginTestHarness(
        plugin_names=["my_plugin"],
        plugin_dir=Path("plugins/"),
    ) as h:
        assert "my_plugin" in h.loaded_plugins

async def test_plugin_responds_to_command():
    """命令测试：插件正确响应指令"""
    async with PluginTestHarness(
        plugin_names=["hello_world"],
        plugin_dir=Path("examples/qq/01_hello_world"),
    ) as h:
        await h.inject(group_message("hello", group_id="100"))
        await h.settle()
        assert h.api_called("send_group_msg")
```

### 3d. Scenario 链式场景

**目标**：测试多步对话或复杂交互。

```python
async def test_multi_step_dialog():
    async with PluginTestHarness(plugin_names=["qa_bot"]) as h:
        await (
            Scenario(h)
            .inject(group_message("开始测验"))
            .settle()
            .assert_api_called("send_group_msg")
            .inject(group_message("A"))
            .settle()
            .assert_api_called("send_group_msg")
            .run()
        )
```

---

## Step 4：运行测试

### 运行命令

```powershell
# 激活环境（如未激活）
.venv\Scripts\activate.ps1

# 全部测试
python -m pytest tests/ -v -o "addopts="

# 单元测试
python -m pytest tests/unit/ -v -o "addopts="

# 指定模块
python -m pytest tests/unit/core/ -v -o "addopts="

# 指定测试文件
python -m pytest tests/unit/core/test_dispatcher.py -v -o "addopts="

# 带覆盖率
python -m pytest tests/ --cov=ncatbot --cov-report=term-missing -v -o "addopts="

# 只跑失败的测试
python -m pytest tests/ --lf -v -o "addopts="

# 插件冒烟测试
python -m pytest tests/ -m smoke -v -o "addopts="
```

> **注意**：使用 `-o "addopts="` 覆盖 pyproject.toml 中的默认 addopts，避免在开发阶段强制开启覆盖率收集。

### NapCat E2E（真实连接）

```powershell
$env:NAPCAT_TEST_GROUP="123456"
$env:NAPCAT_TEST_USER="654321"
python tests/e2e/napcat/run.py
```

---

## Step 5：修复测试问题

### 常见失败原因表

| 症状 | 可能原因 | 排查方式 |
|------|---------|---------|
| `handler 没被调用` | 事件类型不匹配 / Hook 过滤 | 检查注册的事件类型字符串、Hook 过滤条件 |
| `api_called 返回 False` | handler 没执行 / settle 时间不够 | 增加 `settle(delay=0.1)`，打日志确认 handler 执行 |
| `asyncio 警告/报错` | 缺少 `asyncio_mode` 标记 | 确保 `pytestmark = pytest.mark.asyncio(mode="strict")` |
| `ImportError` | 测试依赖未安装 | `uv pip install -e ".[test]"` |
| `插件加载失败` | plugin_dir 路径错误 / 插件结构不对 | 检查 `plugin_dir` 和插件的 `__init__.py` |
| `flaky test（时而通过时而失败）` | 异步竞态 / settle 时间不足 | 增加 settle delay 或用 `wait_event()` |
| `Mock 返回值不对` | 未配置 response | 用 `mock_api.set_response("action", {...})` 预设返回 |
| `platform 过滤不生效` | MockAdapter 默认 `platform="qq"` | 确认事件数据的 `platform` 字段与适配器 platform 一致 |
| `'BotAPIClient' has no attr 'post_group_msg'` | 插件用了 `self.api.xxx` 而非 `self.api.qq.xxx` | `BotAPIClient` 是多平台路由器，QQ sugar 方法在 `self.api.qq` 上 |
| `'BaseEvent' has no attr 'reply'` | 事件数据缺少 `platform="qq"` 导致工厂回退到 BaseEvent | 确保 QQ 数据模型有 `platform: str = "qq"` 默认值 |

### 多平台测试

MockAdapter 默认 `platform="mock"`，如测试 `platform="qq"` 相关逻辑需显式配置：

```python
from ncatbot.adapter.mock import MockAdapter

adapter = MockAdapter(platform="qq")
async with TestHarness(adapter=adapter) as h:
    await h.inject(group_message("hello"))
    ...
```

> 详见 [references/testing-api.md](./references/testing-api.md) 中「MockAdapter 平台参数」一节。

### 调试技巧

1. **pytest -s 查看输出**：`python -m pytest tests/xxx -v -s -o "addopts="`
2. **缩小范围**：用 `-k "test_name"` 只跑单个测试
3. **增加日志**：在 handler 中加 `print()` 或用 logging
4. **检查事件数据**：打印工厂函数返回的 event data，确认字段值
5. **检查调用记录**：`print(harness.api_calls)` 查看所有 API 调用

---

## 文档参考

| 文档 | 路径 | 说明 |
|------|------|------|
| 快速入门 | `docs/guide/9. 测试指南/1. 快速开始.md` | 第一个测试的完整流程 |
| TestHarness 深入 | `docs/guide/9. 测试指南/2. 测试工具.md` | 编排器详细用法 |
| 工厂与场景 | `docs/guide/9. 测试指南/3. 工厂与场景.md` | 事件构造 + Scenario |
| API 参考 | `docs/reference/9. 测试框架/README.md` | 完整 API 签名索引 |
| Harness API | `docs/reference/9. 测试框架/1. 测试工具.md` | TestHarness / PluginTestHarness 详细 API |
| 工厂/Mock API | `docs/reference/9. 测试框架/2. 工厂场景与 Mock.md` | 事件工厂 + MockBotAPI 详细 API |
| 测试套件说明 | `tests/README.md` | 现有测试的目录结构和规范编号 |

---

## 规范编号体系

框架测试使用规范编号标识每个测试用例，便于追踪和引用。

> 详细列表参见：[references/spec-ids.md](./references/spec-ids.md)

| 前缀 | 模块 | 示例 |
|------|------|------|
| T | Types / Segments | T-01 ~ T-14 |
| E | Event Factory | E-01 ~ E-07 |
| D | AsyncEventDispatcher | D-01 ~ D-09 |
| H | HandlerDispatcher | H-01 ~ H-12 |
| K | Hook System | K-01 ~ K-07 |
| R | Registrar | R-01 ~ R-06 |
| M | Plugin Mixin | M-01 ~ M-41 |
| I | Integration | I-01 ~ I-21 |
| B | BotClient E2E | B-01 ~ B-05 |
