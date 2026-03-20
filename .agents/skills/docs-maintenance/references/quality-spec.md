# 文档质量标准（quality-spec）

> 本文件定义"什么是正确"的标准，供 docs-maintenance（修复执行）和 docs-sync（审计检查）共同参考。

## 严重程度定义

| 优先级 | 问题类型 | 退出码 |
|--------|---------|--------|
| P0 | 断链、缺少 README.md / manifest.toml / SKILL.md | exit 1 |
| P1 | 索引遗漏、代码块未标注语言、API 签名/参数不一致 | exit 1 |
| P2 | 行数超限（> 400 行）、新增 API 无文档 | exit 0（仅报告） |

## 结构性检查项

| 检查项 | 级别 | 说明 |
|--------|------|------|
| 断链（相对链接指向不存在的文件） | P0 | 使用 `check_doc_consistency.py` 自动发现 |
| 缺少 README.md | P0 | `docs/` 下含 `.md` 文件的目录 |
| 示例缺文件 | P0 | `docs/docs/examples/<platform>/<example>/` 缺 manifest.toml 或 main.py |
| Skill 缺文件 | P0 | `.agents/skills/<name>/` 缺 SKILL.md |
| 索引遗漏 | P1 | `.md` 文件未在父 `README.md` 中被引用 |
| 代码块未标注语言 | P1 | 使用 `fix_code_blocks.py` 自动修复 |
| 行数超限 | P2 | 单文件 > 400 行（仅报告） |

## 内容对齐标准

### Docs ↔ Code

| 检查项 | 标准 |
|--------|------|
| API 签名一致 | `notes/reference/` 函数签名与 `ncatbot/` 实现完全一致 |
| 参数表格准确 | 参数名、类型、默认值与代码一致 |
| 行为描述准确 | `notes/guide/` 描述的功能行为与代码实际行为一致 |
| 已废弃标注 | 代码中已删除/deprecated 的 API 在文档中有废弃标注 |

### Docs ↔ Examples

| 检查项 | 标准 |
|--------|------|
| 示例覆盖矩阵准确 | `docs/docs/examples/README.md` 覆盖矩阵与实际插件代码一致 |
| 示例 API 未过时 | 示例中的导入和调用是当前框架支持的 |
| 引用的示例存在 | `notes/guide/` 中引用的示例链接有效且内容匹配 |

### Docs ↔ Skills

| 检查项 | 标准 |
|--------|------|
| Skill 引用的文档路径 | `.agents/skills/*/references/*.md` 引用的路径均存在 |
| Skill 描述行为准确 | Skill 速查表、模块映射与当前文档/代码一致 |
| Skill 覆盖完整 | 重要框架功能都有对应 Skill 覆盖 |

### 索引完整性

| 检查项 | 标准 |
|--------|------|
| `docs/docs/notes/README.md` 目录树 | 目录树反映实际文件结构 |
| 各 README.md 文档清单 | 列出的文件与实际一致，无遗漏/多余 |
| 导航链接有效 | 前后导航（← Previous / Next →）链接正确 |

---

## 设计逻辑检查表

### 文档设计定位

| 目录 | 设计定位 | 违规信号 |
|------|---------|---------|
| `notes/guide/` | 任务导向 "如何做 X" | 大量 API 签名表格、缺可运行示例 |
| `notes/reference/` | 参考导向 API 详解 | 大段教程叙述、缺签名/参数表 |
| `notes/contributing/` | 面向贡献者的内部实现 | 出现用户教程内容 |
| `notes/guide/11. 架构与概念/1. 架构总览.md` | 全局视图 | 深入单模块实现细节 |

### Skill 设计定位

| 要素 | 设计要求 | 违规信号 |
|------|---------|---------|
| frontmatter | name + description + Use when 关键词 | 缺少或关键词不具辨别性 |
| 工作流 | 有明确的分步流程 | 纯知识罗列无操作步骤 |
| references/ / scripts/ | 速查表/脚本引用完整文档 | 大段复制文档内容而非引用 |
| 委托分工 | 明确说何时委托给其他 Skill | 职责边界模糊 |

### 示例设计定位

| 要素 | 设计要求 | 违规信号 |
|------|---------|---------|
| 平台分类 | 按 common/qq/bilibili/github/cross_platform 归类 | 示例放在错误平台目录 |
| 可运行 | 复制到 plugins/ 即可运行 | 依赖未声明的外部配置 |
| manifest.toml | 必须包含且元数据完整 | 缺少字段或值不合理 |
