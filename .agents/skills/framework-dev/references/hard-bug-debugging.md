# Fix 工作流参考

> **核心原则**：禁止通过纯代码阅读链路推演根因——即使看起来显而易见。先从外部症状建立假设，通过插桩日志和最小复现测试验证，再做修复。

> **完整 fix 生命周期**：症状 → 插桩 → 复现测试 → 根因 → 修复 → 回归 → （按需）同步文档

---

## 快速路径（根因已知）

1. 明确"应该怎样"与"实际怎样"的差距
2. 最小改动修复
3. 运行受影响测试：`python -m pytest tests/ -o "addopts=" -k "<相关关键词>"`
4. 若修复涉及公开行为变更 → 通过 **docs-maintenance** 技能同步文档

---

## 实验式调试（根因不明确）

当 bug 的根因不明确时，**禁止通过纯代码阅读链路推演定位**。使用以下流程：

## 流程

```text
1. 观察症状 → 2. 插桩日志 → 3. 编写复现测试 → 4. 从日志定位根因 → 5. 修复 + 回归
```

### Step 1：观察症状

从用户报告或运行日志中提取关键信息：

- **"发生了什么"**：实际行为（如 handler 执行了 2 次）
- **"应该怎样"**：预期行为（如 handler 应执行 1 次）
- **事件流路径**：从日志推断事件经过了哪些组件

**不要在此步骤阅读源码**。只从外部可观测信息建立假设。

### Step 2：插桩日志

在疑似路径的**关键节点**添加 `LOG.debug()` 日志，打印：

- 函数被调用时的入参
- 集合/列表的长度和内容
- 对象的 `id()`（区分是否同一实例）

关键插桩位置（按模块）：

| 模块 | 插桩点 | 打印内容 |
|------|--------|---------|
| `registrar.py` → `on()` | handler 被收集时 | `func.__name__`, `event_type`, `pending_count` |
| `registrar.py` → `flush_pending()` | 批量注册前 | `len(handlers)`, `[f.__name__]` |
| `dispatcher.py` → `_dispatch()` | handler 收集后 | `len(handlers)`, `[(name, event_type, id)]` |
| `dispatcher.py` → `_dispatch()` | 每个 handler 执行前 | `func.__name__`, `plugin_name`, `id(entry)` |

**原则**：
- 用 `LOG.debug()` 级别，不影响生产日志
- 包含 `id()` 以区分"同一对象"与"内容相同的不同对象"
- 列表打印长度 + 内容，不只打印"是否为空"

### Step 3：编写复现测试

使用测试框架**最小化复现**问题。模板：

```python
import asyncio
import logging
import pytest

from ncatbot.adapter import MockBotAPI
from ncatbot.core import AsyncEventDispatcher
from ncatbot.core import HandlerDispatcher
from ncatbot.core import Registrar, flush_pending, _pending_handlers
from ncatbot.testing import factory

pytestmark = pytest.mark.asyncio

@pytest.fixture(autouse=True)
def clean_pending():
    _pending_handlers.clear()
    yield
    _pending_handlers.clear()


async def test_reproduce_bug(caplog):
    """复现：描述预期 vs 实际"""
    reg = Registrar()
    ed = AsyncEventDispatcher()
    hd = HandlerDispatcher(api=MockBotAPI())
    hd.start(ed)

    call_count = 0

    # 模拟用户的装饰器用法
    @reg.on_group_message()
    @reg.on_command("xxx")
    async def handler(event):
        nonlocal call_count
        call_count += 1

    flush_pending(hd, "__global__")

    with caplog.at_level(logging.DEBUG):
        await ed.callback(factory.group_message("xxx", group_id="123"))
        await asyncio.sleep(0.1)

    # 断言预期行为
    assert call_count == 1, f"handler 被执行了 {call_count} 次"

    await hd.stop()
    await ed.close()
```

**运行**：

```powershell
python -m pytest tests/unit/core/test_xxx.py -v -s -o "addopts="
```

`-s` 显示 print 输出，`-v` 显示详细测试名。

### Step 4：从日志定位根因

测试失败时，检查 `caplog` 或终端输出中的 debug 日志：

- 哪个步骤的数量不对？（如 pending 里有 2 个函数）
- 哪个对象被重复添加？（通过 `id()` 确认）
- 是"收集阶段"还是"分发阶段"的问题？

**从日志反向定位**到具体代码行，而不是从代码顺序正向推演。

### Step 5：修复 + 回归

1. 最小改动修复根因
2. 将复现测试改为**正式规范测试**（添加规范编号，去掉 print）
3. `python -m pytest tests/ -o "addopts="` 运行完整套件确认无回归
4. 若修复涉及公开行为变更（接口签名、事件字段、配置项等），通过 **docs-maintenance** 技能同步文档

## 实战案例

### 堆叠装饰器导致 handler 执行两次 (R-07 ~ R-09)

**症状**：用户发送 1 条消息，插件收到并回复了 2 次。

**插桩**：在 `registrar.on()` 的 `append` 处加日志 → 发现同一 `func` 被 `on()` 调用了 2 次。

**复现**：`@on_group_message()` + `@on_command("loli")` 堆叠 → pending 列表长度为 2。

**根因**：便捷装饰器（`on_command` 等）内部调用 `self.on()`，每次调用都会 `append(func)`。

**修复**：在 `on()` 中增加 `if func not in pending_list` 去重检查。

### `__init__.py` 导入入口模块导致 handler 双重注册 (R-10 ~ R-11)

**症状**：用户发送 1 条消息，插件收到并回复了 2 次。dispatcher 日志显示同一插件的每个 handler 注册了 2 份（id 不同）。

**与 R-07 的区别**：R-07 的去重检查（`if func not in pending_list`）仍正常通过——因为这次重复的是**不同的函数对象**，而非同一对象被多次 append。

**插桩**：在 `dispatcher._dispatch()` 打印收集到的 handler 列表含 `id()` → 发现同名 handler 出现两次，id 不同。

**复现**：插件 `__init__.py` 含 `from .main import PluginClass`：
1. `load_module()` exec `__init__.py` → 触发 `from .main import ...` → Python import system 加载 main.py → 装饰器第一次运行
2. `load_module()` 继续执行 → `module_from_spec()` 创建新 module 对象 → `exec_module()` 无条件重新执行 main.py → 装饰器第二次运行（新函数对象）

**根因**：`exec_module()` 是底层 API，不查 `sys.modules` 缓存；`load_module()` 在步骤 2 没有检查入口模块是否已被步骤 1 间接导入。

**修复**：在 `load_module()` 的入口模块加载处，先检查 `sys.modules.get(module_name)`，命中则直接返回已有模块。

### `Optional[T]` 参数绑定静默失败 (K-22a ~ K-22e)

**症状**：插件 `@registrar.qq.on_group_command("授权")` 的 handler 声明 `target: Optional[At] = None`，群内发送 `授权 @用户` 后 `target` 始终为 `None`，At 段未被绑定。

**分类**：根因已知类——纯类型检查函数不处理泛型，无需插桩（可直接走快速路径）。

**定位**：`ncatbot/core/registry/_command_binding.py` → `_is_type()` 函数。`Optional[At]` 是 `Union[At, None]`，`_is_type(annotation, At)` 逐条检查：
- `annotation is At` → False（annotation 是 `Union`）
- `isinstance(annotation, type) and issubclass(...)` → False（Union 不是 type）
- `isinstance(annotation, str)` → False
- 返回 `False` → `bind_params` 走到 else 分支，把 At 段当 str/token 匹配 → 匹配不到 → 使用默认值

**修复**：在 `_is_type()` 末尾增加 Union 解包：
```python
from typing import Union, get_args, get_origin

origin = get_origin(annotation)
if origin is Union:
    return any(_is_type(arg, target) for arg in get_args(annotation) if arg is not type(None))
```

**教训**：Python 类型注解内省必须处理 `Optional[T]` / `Union[T, None]`。任何新增的类型判断函数都应将 `get_origin()` + `get_args()` 作为标准检查步骤。
