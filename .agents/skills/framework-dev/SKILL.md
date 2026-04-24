---
name: framework-dev
description: '开发与维护 NcatBot 框架本体。调试 bug、开发新功能、维护 Skill、代码审查、重构。Use when: 框架调试、debug、fix bug、feat、新功能、Skill 维护、代码贡献、模块修改、代码审查、重构。'
license: MIT
---

# 技能指令

你是 NcatBot 框架开发助手。帮助用户对框架本体进行一切变更：修 bug、加功能、重构代码。

## 随附脚本

| 脚本 | 用途 |
|------|------|
| `.agents/scripts/check_imports.py` | 自动检查导入规范（Rule 1 跨层深度 + Rule 2 同层相对导入） |
| `.agents/scripts/check_runtime_imports.py` | 扫描非顶层运行时导入，分类报告（`--stat` 汇总 / `--strict` CI 门禁） |

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
| 理解设计意图、查阅架构与 API | **doc-nav** |
| 编写测试、运行测试、调试测试 | **testing-framework** |
| 编写/编辑文档、一致性检查、索引同步 | **docs-maintenance** |
| 发布版本、推送变更、管理 docs submodule | **release** |

---

## Fix 工作流（`fix/`）

**核心原则：日志优先，禁止通过纯代码阅读推演定位根因。**

完整生命周期：**症状 → 插桩日志 → 最小复现测试 → 从日志定根因 → 修复 → 回归 → （按需）同步文档**

→ 详见 [references/hard-bug-debugging.md](./references/hard-bug-debugging.md)（完整流程、插桩位置速查、实战案例）

## Feat 工作流（`feat/`）

**核心原则：先读文档理解设计意图，再找实现位置；接口设计优先于编码。**

流程：读文档（**doc-nav**）→ 接口设计 → 编码 → 写文档（**docs-maintenance**）

→ 详见 [references/feat-workflow.md](./references/feat-workflow.md)（文档路径速查、接口设计检查点、docs 委托指南）

## Refactor 工作流（`refactor/`）

**核心原则：现有测试即契约，外部行为不得改变。**

1. 以现有测试套件确认外部行为基线
2. 修改内部实现，保持最小改动范围
3. 如有内部模块文档需更新，委托 **docs-maintenance** 同步 `contributing/`

## Docs 工作流（`docs/`）

→ 委托 **docs-maintenance** 技能执行。

---

## 收尾（每次变更后）

1. **四位一体检查**：Code ✓ Test ✓ Docs ✓ Skill ✓
2. **代码风格**：`ruff format .` + `ruff check . --fix`
3. **docs submodule**：若改动了 `docs/` 文件 → 参见 **release** 技能的 commit 编排流程
4. **留痕**：在 `memory/` 目录创建工作记录 → 模板见 [references/memory-template.md](./references/memory-template.md)
5. **多平台变更**：若涉及新平台或跨平台接口 → 见 [references/multi-platform.md](./references/multi-platform.md)

---

## 导入规范

详见 [references/import-conventions.md](./references/import-conventions.md)。核心原则：

- **跨 layer 绝对导入**，最多到二级平台子模块（`from ncatbot.<layer> import ...`），禁止三级及更深
- **同 layer 内部相对导入**（`from ..module import ...`）
- **运行时导入（Rule 5）**：默认放顶层；仅可选依赖 / CLI 懒加载 / 已确认循环 / 平台条件允许延迟
- 新增公共 API 必须在对应 layer 的 `__init__.py` 中注册
- 验证：`check_imports.py`（架构规范）+ `check_runtime_imports.py --strict`（运行时导入），均须 0 违规

---

## 适配器 CLI 配置钩子

各适配器通过 `cli_configure()` 类方法为 `ncatbot init` / `ncatbot adapter` 提供交互式配置。含智能跳过逻辑（如 NapCat 自动安装跳过 WS/WebUI 输入、Bilibili 扫码跳过凭据输入）。

→ 详见 [references/adapter-cli-hooks.md](./references/adapter-cli-hooks.md)（实现位置、跳过设计、新适配器实现规则）

---

## 分支与提交

- 分支命名：`feat/xxx`、`fix/xxx`、`refactor/xxx`、`docs/xxx`
- Commit 格式：[Conventional Commits](https://www.conventionalcommits.org/)
- 代码风格：`ruff format .` + `ruff check . --fix`
