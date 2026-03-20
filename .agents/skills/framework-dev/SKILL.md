---
name: framework-dev
description: '开发与维护 NcatBot 框架本体。调试 bug、开发新功能、维护文档、维护 Skill、代码审查、重构。Use when: 框架调试、debug、fix bug、feat、新功能、文档维护、Skill 维护、代码贡献、模块修改、代码审查、重构。'
license: MIT
---

# 技能指令

你是 NcatBot 框架开发助手。帮助用户对框架本体进行一切变更：修 bug、加功能、改文档、重构代码。

## 设计哲学：四位一体

NcatBot 项目中，**skill、docs、code、test** 是不可分割的整体。任何变更都必须同时触及这四项：

| 产物 | 说明 | 不同步的后果 |
|------|------|-------------|
| **Code** | 实现代码 | 功能不存在 |
| **Test** | 测试代码 | 无法验证正确性，回归无保障 |
| **Docs** | 用户文档 + 参考文档 | 用户不知道怎么用，贡献者不知道怎么改 |
| **Skill** | Agent 技能知识 | AI 助手无法正确引导后续开发 |

**变更检查清单**（每次提交前过一遍）：

- [ ] Code：实现/修复已完成
- [ ] Test：新增或更新了测试（→ **testing** 技能）
- [ ] Docs：guide / reference / architecture 已同步（→ [文档维护](#文档维护)）
- [ ] Skill：如变更影响 agent 技能的知识，同步更新相关 `.agents/skills/` 文件

## 协作技能

| 需要做什么 | 委托给 |
|-----------|--------|
| 定位代码、理解模块、导航文档 | **codebase-nav** |
| 编写测试、运行测试、调试测试 | **testing** |
| 执行变更（修 bug / 加功能 / 改文档） | **framework-dev**（本技能） |

---

## 统一变更工作流

无论 fix 还是 feat，都遵循同一流程：

```text
1. 规划 → 2. 定位（→ codebase-nav）→ 3. 执行变更 → 4. 验证（→ testing）→ 5. 收尾
```

### 阶段 1：规划

1. **分析需求**，判断任务类型：

| 类型 | 判断标准 | 分支前缀 |
|------|---------|---------|
| Bug 修复 | 现有行为与文档/预期不符 | `fix/` |
| 新功能 | 新增用户可见能力 | `feat/` |
| 重构 | 优化内部结构，不改外部行为 | `refactor/` |
| 文档 | 纯文档变更 | `docs/` |

2. **用 todo list 拆分任务**。每个 todo 应对应一个可验证的小步骤。

### 阶段 2：定位

使用 **codebase-nav** 技能，输入问题症状或功能需求，获取：
- 涉及的模块和文件
- 相关文档路径
- 预期行为（来自文档）

需要定位 Bug 时，使用 [references/hard-bug-debugging.md](./references/hard-bug-debugging.md) 的实验式调试流程，而不是通过纯代码阅读推演。

### 阶段 3：执行变更

根据任务类型执行。核心原则：**最小改动 + 四位一体**。

#### Fix（Bug 修复）

1. 明确"应该怎样"与"实际怎样"的差距
2. 修改代码，保持最小改动
3. 同步文档（如修改涉及公开行为）

#### Feat（新功能）

1. 先设计接口：函数签名、参数、返回值
2. 实现代码，遵循现有模块的风格
3. 编写对应文档：
   - `docs/guide/` — 使用教程（如何用新功能）
   - `docs/reference/` — API 签名参考
   - 如涉及新模块：更新 `docs/guide/11. 架构与概念/1. 架构总览.md`

#### Refactor（重构）

1. 确认外部行为不变（现有测试作为契约）
2. 修改内部实现
3. 更新 `docs/contributing/` 中的模块内部文档

#### Docs（纯文档）

→ 跳转 [文档维护](#文档维护)

### 阶段 4：验证

使用 **testing** 技能：

1. 运行现有测试确认无回归
2. 新增/更新测试覆盖本次变更
3. 运行完整测试套件确认无副作用

### 阶段 5：收尾

1. **四位一体检查**：Code ✓ Test ✓ Docs ✓ Skill ✓
2. **代码风格**：`ruff format .` + `ruff check . --fix`
3. **docs submodule**：若修改了 `docs/` 下文件，需先在 docs 子仓库内 commit + push，再在主仓库 `git add docs` 更新指针
4. **留痕**：使用文件创建工具在  `memory/` 目录创建工作记录

```markdown
# [日期] 简要标题

## 变更类型
fix / feat / refactor / docs

## 内容
- 问题/需求描述
- 改动的文件和原因

## 四位一体
- Code: path/to/file.py
- Test: tests/xxx/test_yyy.py
- Docs: docs/guide/xxx, docs/reference/yyy
- Skill: .agents/skills/xxx（如适用）

## 备注
```

文件命名：`memory/YYYY-MM-DD_简要描述.md`

---

## 文档维护

> 详细参考：[references/docs-maintenance.md](./references/docs-maintenance.md)

> **重要**：`docs/` 是 Git submodule（独立仓库 `huan-yp/NcatBotDocs`）。编辑 docs 下的文件后，需要在 docs 子仓库内单独提交并推送，然后在主仓库更新 submodule 指针。详见 release skill 中的「docs 变更的提交流程」。

### 关键约束

- 单文件 ≤ 400 locs（目标 < 200）
- 每新增/删除文件，同步更新父目录 `README.md` 和 `docs/README.md`
- 相对路径链接，禁止硬编码站点绝对路径
- 代码块标注语言（`python` / `toml` / `bash`）

### 文档类型与目录

| 类型 | 目录 | 判断标准 |
|------|------|---------|
| "如何做 X" 教程 | `docs/guide/` | 任务导向，有步骤 |
| 类/函数 API 详解 | `docs/reference/` | 参考导向，有签名 |
| 内部实现/设计决策 | `docs/contributing/` | 面向框架贡献者 |
| 全局架构 | `docs/guide/11. 架构与概念/1. 架构总览.md` | 跨模块视图 |

### 代码变更后的文档同步

1. 修改涉及公开 API → 更新 `reference/` 签名、参数表格
2. 修改用户可见行为 → 更新 `guide/` 相关示例
3. 新增/删除文件 → 更新目录索引（父 `README.md` + `docs/README.md`）
4. 修改架构 → 更新 `docs/guide/11. 架构与概念/1. 架构总览.md`
5. 修改多平台相关代码 → 更新 `docs/guide/10. 多平台开发/`

### 多平台相关变更

添加新平台时需创建：
- `ncatbot/types/<platform>/` — 平台专用数据类型
- `ncatbot/event/<platform>/` — 平台专用事件实体 + 工厂
- `ncatbot/api/<platform>/` — 平台 API 抽象接口
- `ncatbot/adapter/<platform>/` — 平台适配器

通用层（`types/common`、`event/common`、`api/traits`）变更需检查所有平台兼容性。

---

## 导入规范

NcatBot 框架按 **一级 layer** 划分模块边界，5.2 多平台架构引入了 **平台子模块** 作为合法的第二级导入层。

### 一级 Layer 列表

`adapter` / `api` / `app` / `cli` / `core` / `event` / `plugin` / `service` / `testing` / `types` / `utils`

### 规则 1：跨 layer — 绝对导入，最多到二级（平台子模块）

不同 layer 之间互相引用时，使用 `from ncatbot.<layer> import ...`。当需要平台特定类型时，允许到 **平台子模块**（`<layer>.<platform>`），但 **禁止** 更深层导入。

```python
# ✅ 一级导入 — 平台无关
from ncatbot.core import registrar, AsyncEventDispatcher
from ncatbot.utils import get_log
from ncatbot.types import MessageArray, PlainText, At, Image

# ✅ 二级导入 — 平台特定（event / types / api 的平台子模块）
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent
from ncatbot.types.qq import ForwardConstructor, Face
from ncatbot.api.qq import QQAPIClient

# ❌ 三级及更深 — 禁止
from ncatbot.core.registry import registrar
from ncatbot.types.common.segment import PlainText
from ncatbot.event.qq.message import GroupMessageEvent
```

**允许二级导入的平台子模块**（白名单）：

| Layer | 允许的二级子模块 | 典型导入 |
|-------|-----------------|---------|
| `event` | `event.qq`, `event.bilibili`, `event.common` | `GroupMessageEvent`, `NoticeEvent` |
| `types` | `types.qq`, `types.bilibili`, `types.common`, `types.napcat` | `ForwardConstructor`, `Face`, `SendMessageResult` |
| `api` | `api.qq`, `api.bilibili`, `api.traits` | `QQAPIClient`, `IMessaging` |
| `adapter` | `adapter.napcat`, `adapter.mock`, `adapter.bilibili` | `NapCatAdapter`, `MockAdapter` |

其他 layer（`core`、`plugin`、`utils`、`app`、`service`、`cli`、`testing`）**只允许一级导入**。

### 规则 2：同 layer 内部 — 相对导入

同一个一级 layer 内部的模块互相引用时，**必须**使用相对导入。

```python
# ✅ 正确（在 utils/config/manager.py 中）
from ..logger import get_early_logger
from .models import Config

# ❌ 错误 — 同 layer 内用了绝对导入
from ncatbot.utils.logger import get_early_logger
```

### 规则 3：外部示例 — 遵循规则 1

`examples/`、`docs/`、`.agents/skills/` 中的代码与用户代码一样，遵循规则 1：一级 + 白名单内的二级。

```python
# ✅ 用户代码 / 示例代码
from ncatbot.core import registrar, from_event, Hook
from ncatbot.plugin import NcatBotPlugin
from ncatbot.event.qq import GroupMessageEvent, FriendRequestEvent
from ncatbot.types import MessageArray, PlainText, At
from ncatbot.types.qq import ForwardConstructor
from ncatbot.utils import get_log

# ❌ 三级导入 — 禁止
from ncatbot.core.registry import registrar
from ncatbot.event.qq.message import GroupMessageEvent
```

### 规则 4：TYPE_CHECKING 守护

框架内部在类型注解中引用其他 layer 的类时，使用 `TYPE_CHECKING` 块避免循环导入：

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ncatbot.core import AsyncEventDispatcher, Event
    from ncatbot.types.qq import EventType
```

### 唯一例外

访问 layer 内部的 **私有实现** (以 `_` 开头)，允许框架内部代码使用深层绝对导入：

```python
# 允许：框架内部访问私有上下文变量
from ncatbot.core.registry.context import _current_plugin_ctx
```

### 新增导出检查

新增公共 API 导出时，必须在对应 layer 的 `__init__.py` 中注册。如果 `__init__.py` 中没有某个符号，说明它不是公共 API。

---

## 环境与规范

### 环境搭建

```bash
git clone https://github.com/<your-username>/NcatBot.git
cd NcatBot
uv sync
.venv\Scripts\activate.ps1
```

### 分支与提交

- 分支命名：`feat/xxx`、`fix/xxx`、`refactor/xxx`、`docs/xxx`
- Commit 格式：[Conventional Commits](https://www.conventionalcommits.org/)
- 代码风格：`ruff format .` + `ruff check . --fix`
