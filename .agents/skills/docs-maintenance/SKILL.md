---
name: docs-maintenance
description: '维护 NcatBot 项目文档、示例、Skills 知识资产。编写/编辑文档、修复文档问题、文档结构规范审查。Use when: 写文档、改文档、新增文档、修复断链、修复索引、修复代码块标注、文档规范、文档模板、文档结构设计、docs maintenance。'
---

# 技能指令

你是 NcatBot 文档与知识资产维护助手。确保 Docs / Examples / Skills / Code 四产物描述同一事实，不矛盾、不遗漏、不过时。

## 随附脚本

| 脚本 | 用途 |
|------|------|
| `.agents/scripts/check_doc_consistency.py` | 自动检查断链、索引、结构、代码块标注 |
| `.agents/scripts/fix_code_blocks.py` | 自动为未标注语言的代码块补全标识 |

## 四产物一致性

| 产物 | 位置 | 面向 |
|------|------|------|
| **Docs** | `docs/docs/notes/` | 人类读者 |
| **Examples** | `docs/docs/examples/` | 人类读者（可运行参考实现） |
| **Skills** | `.agents/skills/` | AI Agent |
| **Code** | `ncatbot/` | 框架实现本体 |

## 关键路径

> `docs/` 是 Git submodule（`huan-yp/NcatBotDocs`），变更后需在子仓库单独提交推送，再更新主仓库指针。详见 **release** 技能。

| 简写 | 实际路径 |
|------|---------|
| `guide/` | `docs/docs/notes/guide/` |
| `reference/` | `docs/docs/notes/reference/` |
| `contributing/` | `docs/docs/notes/contributing/` |
| `examples/` | `docs/docs/examples/` |

## 文档编排逻辑

### Guide — 学习路径设计

| 阶段 | 章节 | 定位 |
|------|------|------|
| 入门 | 1–2 | 快速上手 → 连接平台适配器 |
| 核心开发 | 3 | 插件开发（11 篇渐进：结构→生命周期→事件→谓词→配置→Hooks→模式→案例） |
| 扩展能力 | 4–8 | 消息发送 / API 使用 / 配置管理 / RBAC / CLI |
| 工程化 | 9–10 | 测试指南 / 多平台开发 |
| 背景知识 | 11 | 架构与概念（**有意后置**：先动手跑起来，再回头理解原理） |

### Reference — 查阅频率排序

| 层次 | 章节 | 内容 |
|------|------|------|
| 用户感知层 | 1–3 | Bot API → 事件类型 → 数据类型 |
| 框架核心层 | 4–6 | 核心模块 → 插件系统 → 服务层 |
| 基础设施层 | 7–8 | 适配器 → 工具模块 |
| 开发工具层 | 9–10 | 测试框架 → CLI |

### 通用规律

- **跨平台章节**子目录顺序固定：`1. 通用/ → 2. QQ/ → 3. Bilibili/ → 4. GitHub/`
- **每个子目录必须有 README.md**（Hub 页/章节导览）；仅含单一叶子文件的目录可豁免
- **子目录 vs 单文件**：需按平台或功能模块切分时建子目录，否则用单文件平铺
- 新增章节时数字前缀须连续，不得跳号

---

## 工作流

### 编写文档

```text
1. 定位目录 → 2. 确定文件名 → 3. 选模板 → 4. 编写内容 → 5. 同步索引 → 6. 验证
```

详细规范、文件模板（A/B/C）、命名规则、验证清单 → [references/docs-maintenance.md](./references/docs-maintenance.md)

代码变更后的同步触发规则 → [references/docs-maintenance.md § 代码变更后的文档同步触发规则](./references/docs-maintenance.md)

### 修复已发现问题

收到 docs-sync 审计报告后：

```text
1. 按 P0 → P1 → P2 顺序修复 → 2. 运行脚本验证 → 3. 提交
```

**修复方式速查：**

| 问题类型 | 修复方式 |
|---------|----------|
| P0 断链 | 修正链接路径（参见链接规范：[references/docs-maintenance.md](./references/docs-maintenance.md)） |
| P0 README 索引多余 | 删除无效条目 |
| P0 已删除 API 仍在文档 | 从 reference/ 中移除或标记废弃 |
| P1 索引遗漏 | 在父目录 README.md 补充引用 |
| P1 代码块未标注语言 | 运行 `.agents/scripts/fix_code_blocks.py --apply` 自动修复 |
| P1 guide↔reference 不一致 | 以代码为权威，同步两端文档 |
| P2 行数超限 | 评估是否拆分文件 |

修复后运行 `.agents/scripts/check_doc_consistency.py` 验证。

质量标准（P0/P1/P2 详细定义、内容对齐标准、设计逻辑检查表）→ [references/quality-spec.md](./references/quality-spec.md)

---

## 协作技能

| 需要做什么 | 委托给 |
|-----------|--------|
| 链接检查、审计、生成报告 | **docs-sync** |
| 代码变更后触发文档同步 | **framework-dev**（四位一体检查后委托本技能） |
| 编写测试、验证示例可运行 | **testing-framework** |
| submodule 指针更新 + 发版前检查 | **release** |
| 定位代码以核对 docs↔code 对齐 | **codebase-nav** |
