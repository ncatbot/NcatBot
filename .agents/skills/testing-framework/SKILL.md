---
name: testing-framework
description: 'NcatBot 自定义测试框架：离线验证复杂链路，TestHarness/PluginTestHarness 使用、事件注入、Scenario 多步场景、运行与调试。Use when: TestHarness、PluginTestHarness、插件测试、事件注入、inject、settle、Scenario、离线测试、测试框架、怎么写集成测试、怎么写 E2E、MockBotAPI、跑测试、测试失败、调试测试。'
---

# NcatBot 测试框架

NcatBot 提供一套自定义测试框架，核心价值是：**在不启动 NapCat 的离线环境中**，通过 MockAdapter 拦截 API 调用，验证包含完整链路（事件解析 → Dispatcher 路由 → Handler 执行 → Bot API 调用）的集成测试和 E2E 测试。

> 测试设计原则、规范编号分配、测试索引维护 → **testing-design** 技能

---

## 核心运行模型

```
MockAdapter
    │
    ├─ inject(event_data)          # 注入构造好的事件
    │       │
    │       ▼
    │  AsyncEventDispatcher        # 路由到对应 handler
    │       │
    │       ▼
    │    Handler 执行              # 插件/框架 handler 运行
    │       │
    │       ▼
    └─ MockBotAPI.calls            # 记录所有 API 调用 ← 断言点
```

test 不发起任何网络请求，`settle()` 等待 handler 跑完，再对 `api_calls` 断言。

---

## Step 1：选 Harness

| 我想做什么 | 使用 |
|-----------|------|
| 我是**框架开发者**，验证新模块正确接入事件管线（无插件） | `TestHarness` |
| 我是**插件用户**，离线验证我的插件命令响应/多步对话/权限 | `PluginTestHarness` |

```python
from ncatbot.testing import TestHarness, PluginTestHarness, Scenario
from ncatbot.testing import group_message, private_message  # 以及其余 6 个事件工厂
```

完整工厂函数列表见 [references/testing-api.md](./references/testing-api.md)。

---

## Step 2：工作流 — 注入 → settle → 断言

### 框架开发者（TestHarness）

框架开发者直接在 Harness 上注册 handler 进行测试，无需加载任何插件：

```python
import pytest
from ncatbot.testing import TestHarness, group_message

pytestmark = pytest.mark.asyncio(mode="strict")

async def test_handler_replies_to_group_message():
    """I-22: 完整链路：群消息 → handler → send_group_msg"""
    async with TestHarness() as h:
        async def handler(event):
            await event.reply("pong")

        h.bot.handler_dispatcher.register_handler("message.group", handler)
        await h.inject(group_message("ping", group_id="111"))
        await h.settle()

        assert h.api_called("send_group_msg")
```

### 插件用户（PluginTestHarness）

插件用户指向本地插件目录，按名加载，然后注入事件验证行为：

```python
import pytest
from pathlib import Path
from ncatbot.testing import PluginTestHarness, group_message

pytestmark = pytest.mark.asyncio(mode="strict")

PLUGIN_DIR = Path("plugins/")  # 插件所在目录

async def test_my_plugin_responds():
    """PL-02: my_plugin 正确响应 'hello'"""
    async with PluginTestHarness(
        plugin_names=["my_plugin"],
        plugin_dir=PLUGIN_DIR,
    ) as h:
        await h.inject(group_message("hello", group_id="100"))
        await h.settle()
        assert h.api_called("send_group_msg")
```

**常用断言**（全部方法见 [references/testing-api.md](./references/testing-api.md)）：

```python
h.api_called("send_group_msg")          # 是否调用过
h.api_call_count("send_group_msg")      # 调用次数
h.last_api_call("send_group_msg")       # 最近一次 APICall
h.reset_api()                           # 清空记录（多步测试中间断言用）
```

---

## Step 3：多步场景（Scenario）

当测试涉及多轮交互（多步对话、中间断言后重置）时，用 `Scenario` 链式构建：

```python
from ncatbot.testing import Scenario

async def test_registration_flow():
    """PL-40: 注册 → 输入名字 → 确认"""
    async with PluginTestHarness(
        plugin_names=["multi_step_dialog"], plugin_dir=PLUGIN_DIR
    ) as h:
        await (
            Scenario("registration")
            .inject(group_message("注册", group_id="500", user_id="111"))
            .settle()
            .assert_api_called("send_group_msg")   # 应提示输入名字
            .reset_api()
            .inject(group_message("张三", group_id="500", user_id="111"))
            .settle()
            .assert_api_called("send_group_msg")   # 应提示确认
            .run(h)                                # 必须传入 harness
        )
```

全部 Scenario 方法（`assert_api_not_called` / `assert_api_count` / `assert_that` 等）见 [references/testing-api.md](./references/testing-api.md)。

---

## Step 4：运行

```powershell
# 先激活环境
.venv\Scripts\activate.ps1

# 运行与框架相关的集成/E2E 测试（-o "addopts=" 跳过默认覆盖率收集）
python -m pytest tests/integration/ tests/e2e/ -v -o "addopts="

# 只跑指定测试
python -m pytest tests/e2e/plugin/ -k "test_my_plugin" -v -o "addopts="

# 排查时输出 stdout
python -m pytest tests/e2e/ -v -s -o "addopts="

# 只重跑最近失败的
python -m pytest tests/ --lf -v -o "addopts="
```

---

## 常见失败

| 症状 | 最可能原因 | 快速修复 |
|------|-----------|---------|
| handler 没被调用 | 事件类型字符串不匹配 / Hook 拦截 | 检查注册的事件类型，打印 `h.api_calls` |
| `api_called` 返回 False | settle 时间不够 | 改为 `await h.settle(0.1)` |
| 插件加载失败 | `plugin_dir` 路径错误或插件缺少 `__init__.py` | 用 `Path(__file__).parents[N] / "..."` 确保绝对路径 |
| flaky（偶发失败） | 异步竞态 | 用 `wait_event()` 替代固定 delay |
| `'BaseEvent' has no attr 'reply'` | 事件数据缺少 `platform="qq"` | 事件工厂已默认 `platform="qq"`，检查自定义数据是否遗漏 |

更多排障条目见 [references/testing-api.md — 常见失败扩展](./references/testing-api.md#常见失败扩展)。

---

## 参考

- [references/testing-api.md](./references/testing-api.md) — TestHarness / PluginTestHarness / Scenario / MockBotAPI 完整 API 签名 + 常见失败扩展
- 框架测试目录：`tests/integration/`、`tests/e2e/`（包含可参考的真实用例）
