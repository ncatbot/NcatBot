---
name: testing-design
description: '设计 NcatBot 测试策略：测试分层决策、规范驱动原则、不测什么、分配规范编号、维护测试索引。Use when: 写什么测试、要不要测、测试设计、测试分层、规范编号、spec-id、测试索引、测试策略、应该加什么测试、不测什么、什么值得测。'
---

# NcatBot 测试设计技能

决定**写什么测试**、**测试层级选择**，以及如何维护规范编号和测试索引。

> **工具使用**（TestHarness / PluginTestHarness / Scenario / 运行命令）→ **testing-framework** 技能

---

## 测试设计原则

### 原则 1：集成测试 + 离线 E2E 优先

框架行为优先通过以下方式验证：

- **集成测试**（`tests/integration/`）：多模块协作链路
- **离线 E2E 测试**（`tests/e2e/`）：基于 `TestHarness` / `PluginTestHarness` 的完整生命周期

**单元测试仅在有明确隔离价值时使用**：

| ✅ 值得写单元测试 | ❌ 应用集成/E2E 测试替代 |
|-----------------|------------------------|
| 纯解析算法（段解析、CQ 码、配置迁移） | 事件处理全链路 |
| 无副作用的数据模型转换 | handler 注册与触发 |
| 独立工具函数边界值 | 插件加载与生命周期 |
| 错误层级/异常分类 | 多模块状态交互 |

### 原则 2：规范驱动（Spec-Driven）

每个测试用例必须对应一条**规范条目**，并在 docstring 第一行写明规范编号：

```python
async def test_registrar_on_collects_handler(fresh_registrar):
    """R-10: Registrar.on() 将 handler 收集到全局 _pending_handlers"""
    ...
```

测试是规范的**可执行版本**，不是代码的镜像。规范不存在的行为不要写测试。

### 原则 3：不测无意义用例

以下场景**不需要测试**：

| 反模式 | 原因 |
|--------|------|
| `assert obj is not None`（仅验证加载成功） | 无行为验证，意义不大 |
| `assert hasattr(module, "Symbol")` | 导入检查不是行为测试 |
| `obj.field = x; assert obj.field == x` | 平凡 setter，不验证副作用 |
| 重测框架/库已保证的行为（如 pydantic 字段验证） | 外部依赖不需重测 |

**例外**：若"加载成功"本身是规范的一部分（如 PL-01 插件加载），相关断言是有意义的。

### 原则 4：测试索引必须同步

新增测试时，**三处必须同时更新**：

1. 在 docstring 中写入规范编号（如 `R-10`）
2. 更新 `tests/README.md` 中对应前缀的范围（`R-01 ~ R-09` → `R-01 ~ R-10`）
3. 更新目录 README（`tests/unit/<module>/README.md` 或 `tests/integration/README.md` 等）

> **规范编号权威来源**：[`tests/README.md`](../../../tests/README.md)

### 原则 5：Fixture 必须清理

```python
# ✅ 异步 fixture 要 yield + teardown
@pytest_asyncio.fixture
async def event_dispatcher():
    d = AsyncEventDispatcher()
    yield d
    await d.close()  # 必须清理

# ✅ 全局状态在每次测试前/后清理
@pytest.fixture(autouse=True)
def clean_pending():
    _pending_handlers.clear()
    yield
    _pending_handlers.clear()
```

### 原则 6：asyncio_mode = strict

所有含异步测试的文件顶部声明：

```python
pytestmark = pytest.mark.asyncio(mode="strict")
```

### 原则 7：测试层级决策指南

```text
目标是什么？
├─ 纯算法/解析器/数据模型 ──────────────────→ 单元测试  tests/unit/<module>/
├─ 多模块协作链路（dispatcher → handler）──→ 集成测试  tests/integration/
├─ BotClient 完整生命周期 ───────────────────→ E2E       tests/e2e/test_bot_client.py
├─ 插件加载/命令/生命周期 ───────────────────→ 插件 E2E  tests/e2e/plugin/
└─ 真实 WebSocket 连接（QQ 在线）────────────→ NapCat E2E tests/e2e/napcat/（非 pytest）
```

---

## 测试索引维护 SOP

### Step 1：查阅规范编号权威列表

打开 **[`tests/README.md`](../../../tests/README.md)**，找到对应模块的前缀及当前最大序号。

若对应模块没有前缀，选一个不冲突的 2~3 字母缩写，补入 `tests/README.md` 的编号表。

### Step 2：分配编号

在该前缀最大序号上 +1。例如已有 `D-01 ~ D-09`，新增用 `D-10`。

### Step 3：写入 docstring

docstring **第一行**必须包含规范编号：

```python
async def test_dispatcher_routes_group_message(event_dispatcher):
    """D-10: AsyncEventDispatcher 正确路由群消息到 message.group 订阅者"""
    ...
```

### Step 4：更新 tests/README.md

更新对应行的范围，例如：

```diff
-| D | AsyncEventDispatcher | D-01 ~ D-09 |
+| D | AsyncEventDispatcher | D-01 ~ D-10 |
```

### Step 5：更新目录 README

在对应测试目录的 README.md 中补充测试条目，格式参照现有条目。

---

## 规范编号权威列表

完整前缀列表及已分配序号见：**[`tests/README.md`](../../../tests/README.md)**

`tests/README.md` 包含所有已注册前缀（T / S / CQ / D / H / K / R / I / B / PL / SC / PR / TS / LD 等 30+ 个）及当前最大序号，是分配新编号的唯一权威来源，不在 Skill 文件中单独维护副本。
