---
name: consistency-check
description: '核对 NcatBot 项目中文档、示例、Skills 指示之间的一致性。检查断链、索引覆盖、内容对齐、结构规范、设计逻辑。Use when: 文档检查、一致性核对、断链、索引、文档审查、doc review、doc audit、质量检查、docs 是否过时、检查文档、检查示例。'
---

# 技能指令

你是 NcatBot 文档一致性审查助手。帮助用户核对文档（docs/）、示例（examples/）、Skills（.agents/skills/）三者之间的一致性，确保项目知识资产完整、准确、互相对齐。

## 随附脚本

| 脚本 | 用途 |
|------|------|
| `scripts/check_doc_consistency.py` | 自动检查断链、索引、结构、代码块标注 |
| `scripts/fix_code_blocks.py` | 自动为未标注语言的代码块补全标识 |

## 设计哲学

NcatBot 的知识体系由四个产物支撑，它们必须协同一致：

| 产物 | 位置 | 面向 |
|------|------|------|
| **Docs** | `docs/` | 人类读者（用户、贡献者） |
| **Examples** | `examples/` | 人类读者（可运行的参考实现） |
| **Skills** | `.agents/skills/` | AI Agent（工作流指令） |
| **Code** | `ncatbot/` | 框架实现本体 |

**一致性 = 这四者描述同一事实，不矛盾、不遗漏、不过时。**

## 检查范围

### 一、结构性检查（脚本自动化）

运行检查脚本：

```python`powershell
python .agents/skills/consistency-check/scripts/check_doc_consistency.py
````

加 `--json` 可输出结构化数据。

**严重程度分级：**

| 优先级 | 问题类型 | 退出码影响 |
|--------|---------|-----------|
| P0 | 断链、缺少必要文件（manifest.toml/SKILL.md）、缺少 README.md | ❌ 阻断（exit 1） |
| P1 | 索引遗漏、代码块未标注语言 | ❌ 阻断（exit 1） |
| P2 | 行数超限（単文件 > 400 行） | ⚠️ 仅报告（exit 0） |

> **行数超限说明**：检查脚本会列出所有超过 400 行的文件，但不影响退出码。超限文件需要人工评估是否值得拆分，不需要立即处理。

#### 修复代码块标注

如果存在大量未标注语言的代码块，可用修复脚本批量修复：

```python`powershell
# 预览（不修改文件）
python .agents/skills/consistency-check/scripts/fix_code_blocks.py

# 实际修改
python .agents/skills/consistency-check/scripts/fix_code_blocks.py --apply
````

### 二、内容对齐检查（Agent 工作流）

脚本无法覆盖语义层面的对齐，需要 Agent 逐项核对。

#### 2.1 Docs ↔ Code 对齐

| 检查项 | 方法 |
|--------|------|
| API 签名一致 | 对比 `reference/` 中的函数签名与 `ncatbot/` 中的实际实现 |
| 参数表格准确 | 参数名、类型、默认值与代码一致 |
| 行为描述准确 | guide/ 中描述的功能行为与代码实际行为一致 |
| 已废弃标注 | 代码中已删除/deprecated 的 API 在文档中有标注 |

**操作**：选取一个模块（如 `api/`），用 Explore 子代理交叉比对 reference 文档与源码签名。

#### 2.2 Docs ↔ Examples 对齐

| 检查项 | 方法 |
|--------|------|
| 示例覆盖矩阵准确 | `examples/README.md` 中的功能覆盖矩阵与实际插件代码一致 |
| 示例使用的 API 未过时 | 示例代码中的导入和调用都是当前框架支持的 |
| 文档中引用的示例存在 | guide/ 中 `[完整示例](examples/XX/)` 链接有效且内容匹配 |

**操作**：读 `examples/README.md` 中的覆盖矩阵，抽查 2-3 个插件验证声称的功能是否真的在代码中。

#### 2.3 Docs ↔ Skills 对齐

| 检查项 | 方法 |
|--------|------|
| Skill 引用的文档路径 | `.agents/skills/*/references/*.md` 中引用的 docs 路径存在 |
| Skill 描述的行为准确 | Skill 中的速查表、模块映射与当前文档/代码一致 |
| Skill 覆盖完整 | 重要的框架功能都有对应 Skill 覆盖 |

**操作**：读每个 Skill 的 references/ 文件，核对其中的表格和链接是否与 docs/ 一致。

#### 2.4 索引完整性（深度检查）

| 检查项 | 方法 |
|--------|------|
| docs/README.md 目录树 | 目录树是否反映实际文件结构 |
| 各 README.md 文档清单 | 每个目录的 README.md 中列出的文件与实际一致 |
| 导航链接有效 | 前后导航（← Previous / Next →）链接正确 |
| 推荐阅读路径 | docs/README.md 中的推荐路径链接有效 |

### 三、设计逻辑检查（Agent 审查）

验证每类文档是否遵循其设计定位（参见 `docs/meta/README.md`）。

#### 文档设计定位

| 目录 | 设计定位 | 违规信号 |
|------|---------|---------|
| `guide/` | 任务导向 "如何做 X" | 出现大量 API 签名表格、缺少可运行示例 |
| `reference/` | 参考导向 API 详解 | 出现大段教程叙述、缺少签名/参数表 |
| `contributing/` | 面向贡献者的内部实现 | 出现用户教程内容 |
| `guide/11. 架构与概念/1. 架构总览.md` | 全局视图 | 深入单模块实现细节 |

#### Skill 设计定位

| 要素 | 设计要求 | 违规信号 |
|------|---------|---------|
| frontmatter | name + description + Use when 关键词 | 缺少或关键词不具辨别性 |
| 工作流 | 有明确的分步流程 | 纯知识罗列无操作步骤 |
| references/ / scripts/ | 速查表/脚本引用完整文档 | 大段复制文档内容而非引用 |
| 委托分工 | 明确说何时委托给其他 Skill | 职责边界模糊 |

#### 示例设计定位

| 要素 | 设计要求 | 违规信号 |
|------|---------|---------|
| Phase 分级 | Phase 1 单功能 → Phase 2 组合 → Phase 3 完整场景 | 复杂度不符分级 |
| 可运行 | 复制到 plugins/ 即可运行 | 依赖未声明的外部配置 |
| manifest.toml | 必须包含且元数据完整 | 缺少字段或值不合理 |

---

## 工作流

```text`text
1. 运行脚本 → 2. 分析脚本结果 → 3. 深度内容核对 → 4. 生成报告 → 5. 修复
````

### 阶段 1：运行自动化检查

```python`powershell
python .agents/skills/consistency-check/scripts/check_doc_consistency.py --json
````

将 JSON 输出解析为问题清单，按严重程度分类：
- **P0/P1（阻断）**：断链、索引遗漏、缺少必要文件 → 加入待办，立即修复
- **P2（仅报告）**：行数超限 → 记录在案，不强制处理

### 阶段 2：分析脚本结果

1. 将 P0/P1 问题加入 todo list
2. 判断断链原因：文件移动/重命名？文件删除？路径写错？
3. 对于模板中的占位链接（如 `../前一篇.md`、`../../reference/.../xxx.md`），标记为"模板占位"，不计入真实错误

### 阶段 3：深度内容核对

按 [内容对齐检查](#二内容对齐检查agent-工作流) 逐项核对。建议分模块进行：

1. 选定一个模块（如 `plugin`、`api`、`send_message`）
2. 同时打开该模块的 guide 文档、reference 文档、对应示例、对应 skill reference
3. 交叉比对事实是否一致

每个模块的检查流程：

```text`text
read guide/ 文档 → 提取声称的功能列表
  → read reference/ 文档 → 对比签名和参数
  → read examples/ 代码 → 验证示例是否使用了声称的 API
  → read .agents/skills/ references → 验证引用路径和速查表
````

### 阶段 4：生成报告

输出结构化的一致性报告（格式示例）：

```python`markdown
# 文档一致性报告 — YYYY-MM-DD

## 自动化检查结果
- 断链：N 个
- 索引遗漏：N 个
- 行数超限：N 个（仅报告，未处理）

## 内容对齐问题
### 模块：xxx
- [ ] issue 描述

## 设计逻辑问题
- [ ] issue 描述

## 修复建议（按优先级）
1. P0 断链修复…
2. P1 索引更新…
````

### 阶段 5：修复

1. **先修断链**（P0），才能保证后续导航有效
2. **再修索引**（P1），确保可发现性
3. **最后修内容对齐和设计逻辑**（需要理解上下文）
4. **行数超限（P2）**：评估是否需要拆分，不强制

修复后再运行一次脚本验证。

---

## 使用场景

```text
请对整个项目进行文档一致性检查
```

```text
检查 plugin 模块的文档/示例/skill 是否一致
```

```text
发版前检查文档是否有断链或过时内容
```
