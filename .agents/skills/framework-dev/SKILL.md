---
name: framework-dev
description: '开发与维护 NcatBot 框架本体。调试 bug、开发新功能、维护 Skill、代码审查、重构。Use when: 框架调试、debug、fix bug、feat、新功能、Skill 维护、代码贡献、模块修改、代码审查、重构。'
license: MIT
---

# 技能指令

你是 NcatBot 框架开发助手。帮助用户对框架本体进行一切变更：修 bug、加功能、重构代码。

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
- [ ] Test：新增或更新了测试（→ **testing-framework** 技能）
- [ ] Docs：guide / reference / architecture 已同步（→ **docs-maintenance** 技能）
- [ ] Skill：如变更影响 agent 技能的知识，同步更新相关 `.agents/skills/` 文件

## 协作技能

| 需要做什么 | 委托给 |
|-----------|--------|
| 定位代码、理解模块、导航文档 | **codebase-nav** |
| 编写测试、运行测试、调试测试 | **testing-framework** |
| 编写/编辑文档、一致性检查、索引同步 | **docs-maintenance** |
| 执行变更（修 bug / 加功能） | **framework-dev**（本技能） |

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
3. 编写对应文档（委托 **docs-maintenance** 技能执行编辑）：
   - `docs/docs/notes/guide/` — 使用教程（如何用新功能）
   - `docs/docs/notes/reference/` — API 签名参考
   - 如涉及新模块：更新 `docs/docs/notes/guide/11. 架构与概念/1. 架构总览.md`

#### Refactor（重构）

1. 确认外部行为不变（现有测试作为契约）
2. 修改内部实现
3. 更新 `docs/docs/notes/contributing/` 中的模块内部文档

#### Docs（纯文档）

→ 委托 **docs-maintenance** 技能

### 阶段 4：验证

使用 **testing-framework** 技能：

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
- Docs: docs/docs/notes/guide/xxx, docs/docs/notes/reference/yyy
- Skill: .agents/skills/xxx（如适用）

## 备注
```

文件命名：`memory/YYYY-MM-DD_简要描述.md`

---

### 多平台相关变更

添加新平台时需创建：
- `ncatbot/types/<platform>/` — 平台专用数据类型
- `ncatbot/event/<platform>/` — 平台专用事件实体 + 工厂
- `ncatbot/api/<platform>/` — 平台 API 抽象接口
- `ncatbot/adapter/<platform>/` — 平台适配器

通用层（`types/common`、`event/common`、`api/traits`）变更需检查所有平台兼容性。

---

## 导入规范

详见 [references/import-conventions.md](./references/import-conventions.md)。核心原则：

- **跨 layer 绝对导入**，最多到二级平台子模块（`from ncatbot.<layer> import ...` 或 `from ncatbot.<layer>.<platform> import ...`），禁止三级及更深
- **同 layer 内部相对导入**（`from ..module import ...`）
- 仅 `event`、`types`、`api`、`adapter` 允许二级平台子模块导入，其他 layer 只允许一级
- 类型注解跨 layer 引用使用 `TYPE_CHECKING` 守护
- 新增公共 API 必须在对应 layer 的 `__init__.py` 中注册

---

## 分支与提交

- 分支命名：`feat/xxx`、`fix/xxx`、`refactor/xxx`、`docs/xxx`
- Commit 格式：[Conventional Commits](https://www.conventionalcommits.org/)
- 代码风格：`ruff format .` + `ruff check . --fix`
