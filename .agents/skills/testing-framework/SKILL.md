---
name: testing-framework
description: 'NcatBot 自定义测试框架：离线验证复杂链路，TestHarness/PluginTestHarness 使用、事件注入、Scenario 多步场景、运行与调试。Use when: TestHarness、PluginTestHarness、插件测试、事件注入、inject、settle、Scenario、离线测试、测试框架、怎么写集成测试、怎么写 E2E、MockBotAPI、跑测试、测试失败、调试测试。'
---

# NcatBot 测试框架

NcatBot 提供一套自定义测试框架，核心价值是：**在不启动 NapCat 的离线环境中**，通过 MockAdapter 拦截 API 调用，验证包含完整链路（事件解析 → Dispatcher 路由 → Handler 执行 → Bot API 调用）的集成测试和 E2E 测试。

> 测试设计原则、规范编号分配、测试索引维护 → **testing-design** 技能

---

## 核心运行模型

```text
TestHarness(platforms=["qq", "bilibili", "github"])
    │
    ├─ MockAdapter(qq)     → MockBotAPI     (IQQAPIClient)
    ├─ MockAdapter(bili)   → MockBiliAPI    (IBiliAPIClient)
    └─ MockAdapter(github) → MockGitHubAPI  (IGitHubAPIClient)
         │                       ↑ 全部继承 MockAPIBase
         │
    inject(event_data)  ──→  adapter.inject_event()
         │
         ▼
    AsyncEventDispatcher ──→ HandlerDispatcher ──→ Handler 执行
         │
         ▼
    MockAPIBase.calls  ← 记录所有 API 调用（APICall.params: dict）
         │
         ▼
    h.assert_api("send_group_msg").called().with_text("hello")  ← 断言点
```

test 不发起任何网络请求，`settle()` 等待 handler 跑完，再用 fluent 断言 API 验证。

---

## Step 1：选 Harness

| 我想做什么 | 使用 |
|-----------|------|
| 我是**框架开发者**，验证新模块正确接入事件管线（无插件） | `TestHarness` |
| 我是**插件用户**，离线验证我的插件命令响应/多步对话/权限 | `PluginTestHarness` |
| 我要测试**跨平台**场景（GitHub Issue → QQ 通知等） | `TestHarness(platforms=["qq", "github"])` |

```python
from ncatbot.testing import TestHarness, PluginTestHarness, Scenario
from ncatbot.testing import factories  # factories.qq / factories.bilibili / factories.github
```

完整工厂函数列表见 [references/testing-api.md](./references/testing-api.md)。

---

## Step 2：工作流 — 注入 → settle → 断言

### 框架开发者（TestHarness）

```python
import pytest
from ncatbot.testing import TestHarness
from ncatbot.testing import group_message

pytestmark = pytest.mark.asyncio(mode="strict")

async def test_handler_replies_to_group_message():
    """I-22: 完整链路：群消息 → handler → send_group_msg"""
    async with TestHarness() as h:
        async def handler(event):
            await event.reply("pong")

        h.bot.handler_dispatcher.register_handler("message.group", handler)
        await h.inject(group_message("ping", group_id="111"))
        await h.settle()

        h.assert_api("send_group_msg").called().with_params(group_id="111").with_text("pong")
```

### 插件用户（PluginTestHarness）

```python
import pytest
from pathlib import Path
from ncatbot.testing import PluginTestHarness
from ncatbot.testing import group_message

pytestmark = pytest.mark.asyncio(mode="strict")

PLUGINS_DIR = Path("plugins/")

async def test_my_plugin_responds():
    """PL-02: my_plugin 正确响应 'hello'"""
    async with PluginTestHarness(
        plugin_names=["my_plugin"],
        plugins_dir=PLUGINS_DIR,
    ) as h:
        await h.inject(group_message("hello", group_id="100"))
        await h.settle()
        h.assert_api("send_group_msg").called()
```

### Fluent 断言 API

```python
# 存在性
h.assert_api("send_group_msg").called()
h.assert_api("send_group_msg").not_called()
h.assert_api("send_group_msg").times(2)

# 参数匹配（基于 APICall.params: dict）
h.assert_api("send_group_msg").with_params(group_id="999")
h.assert_api("set_group_ban").with_params(group_id="100", duration=600)

# 文本匹配（跨平台感知：QQ segments / Bilibili text / GitHub body）
h.assert_api("send_group_msg").with_text("hello")
h.assert_api("send_danmu").with_text("弹幕")

# 链式组合
h.assert_api("send_group_msg").called().with_params(group_id="999").with_text("pong")

# 自定义条件
h.assert_api("send_group_msg").where(lambda c: len(c.params["message"]) > 3)

# 取值
call = h.assert_api("send_group_msg").last    # 最后一次匹配
calls = h.assert_api("send_group_msg").calls  # 所有匹配

# 平台作用域
h.on("qq").assert_api("send_group_msg").called()
h.on("github").assert_api("create_issue_comment").not_called()

# MockAPI 直接访问（仍可用）
h.mock_api.called("send_group_msg")           # bool
h.mock_api.call_count("send_group_msg")       # int
h.mock_api_for("bilibili").get_calls("send_danmu")  # 指定平台

# 重置
h.reset_api()              # 清空全部平台
h.reset_api("qq")          # 只清空 QQ
```

---

## Step 3：多步场景（Scenario）

当测试涉及多轮交互（多步对话、中间断言后重置）时，用 `Scenario` 链式构建：

```python
from ncatbot.testing import Scenario
from ncatbot.testing import group_message

async def test_dialog_flow():
    """PL-40: 菜单 → 选择 → 执行"""
    async with PluginTestHarness(
        plugin_names=["dialog_and_menu_qq"], plugins_dir=PLUGINS_DIR
    ) as h:
        await (
            Scenario("dialog")
            .inject(group_message("菜单", group_id="500", user_id="111"))
            .settle()
            .assert_api_called("send_group_msg")
            .reset_api()
            .inject(group_message("1", group_id="500", user_id="111"))
            .settle()
            .assert_api_called("send_group_msg")
            .run(h)
        )
```

Scenario 新增方法：

```python
.on("qq").assert_api_called("send_group_msg")       # 平台作用域
.assert_api_params("send_group_msg", group_id="100") # 参数匹配
.assert_api_text("send_group_msg", "hello")           # 文本匹配
.assert_api_where("send_group_msg", lambda c: ...)    # 自定义条件
```

全部 Scenario 方法见 [references/testing-api.md](./references/testing-api.md)。

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
| handler 没被调用 | 事件类型字符串不匹配 / Hook 拦截 | 检查注册的事件类型，打印 `h.mock_api.calls` |
| `assert_api().called()` 失败 | settle 时间不够 | 改为 `await h.settle(0.1)` |
| 插件加载失败 | `plugins_dir` 路径错误或插件缺少 `__init__.py` | 用 `Path(__file__).parents[N] / "..."` 确保绝对路径 |
| flaky（偶发失败） | 异步竞态 | 用 `wait_event()` 替代固定 delay |
| `'BaseEvent' has no attr 'reply'` | 事件数据缺少 `platform="qq"` | 事件工厂已默认 `platform="qq"`，检查自定义数据是否遗漏 |
| `ValueError: 未注册平台` | inject 的事件 platform 与 harness platforms 不匹配 | 构造 harness 时传入对应平台 |

更多排障条目见 [references/testing-api.md — 常见失败扩展](./references/testing-api.md#常见失败扩展)。

---

## 参考

- [references/testing-api.md](./references/testing-api.md) — 完整 API 签名（TestHarness / PluginTestHarness / Scenario / MockAPIBase / APICallAssertion / 工厂函数）
- 框架测试目录：`tests/integration/`、`tests/e2e/`（包含可参考的真实用例）
