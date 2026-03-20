---
name: skills-sync
description: '检查、报告、修复 Skills 间链接内容不同步，以及 Skills↔Docs 内容链接不同步。逐文件检查，最大化并发 subagent。Use when: skill 同步、skill 断链、skill 引用、skill 过时、skill audit、skills 一致性、skill 检查、skill↔docs。'
---

# Skills 同步审计

检查所有 `.agents/skills/` 下的 Skill 文件（SKILL.md + references/*.md），确保：

1. **Skill 内部链接**完好（references、scripts 文件存在）
2. **Skill 间协作引用**一致（`**skill-name**` 格式引用的 skill 存在且文本准确）
3. **Skill→Docs 引用**有效（docs 路径存在且 API 描述一致）

---

## 工作流

```text
1. 枚举 → 2. Phase A（per-skill 链接检查）→ 3. Phase B（skill 对内容一致）→ 4. 汇总 → 5. 修复
```

### Step 1：枚举

`list_dir .agents/skills/` 获取所有 skill 目录名。

当前 skill 清单：`code-nav` · `codebase-nav` · `doc-nav` · `docs-maintenance` · `docs-sync` · `framework-dev` · `framework-usage` · `plugin-migration` · `release` · `skills-sync` · `testing-design` · `testing-framework`

### Step 2：Phase A — per-skill 链接检查（并发，每 skill 一个 Explore subagent）

为每个 skill 目录启动 1 个 **Explore** subagent，逐文件扫描 `SKILL.md` + `references/*.md`：

**2a. 内部 references 断链**
- 提取所有 `[text](path)` 链接
- 路径以 `./references/` 或 `../scripts/` 开头的 → 验证目标文件存在
- 分类为 P0（文件不存在）

**2b. 协作技能引用有效性**
- 在 SKILL.md 中搜索 `**xxx**` 格式的技能引用
- 验证 `.agents/skills/<xxx>/SKILL.md` 是否存在
- 分类为 P0（skill 不存在）

**2c. Docs 引用有效性**
- 在 references/*.md 中搜索 docs 路径引用（`docs/guide/...`、`docs/reference/...` 等）
- 验证 `docs/docs/notes/<path>` 或 `docs/docs/examples/<path>` 是否存在
- 分类为 P0（路径不存在）

**2d. Docs 内容对比**（仅对有效 docs 引用）
- 读取 docs 目标文件，提取 API 名/签名
- 与 skill references 中描述的 API 名/签名/参数对比
- 分类为 P1（明显不一致）或 P2（轻微措辞差异）

### Step 3：Phase B — skill 对间内容一致（并发，约 5 个 subagent）

互相引用的 skill 对，检查对同一概念的描述是否矛盾：

| Skill 对 | 检查点 |
|----------|--------|
| `testing` ↔ `testing-design` | 测试层级划分、规范编号体系 |
| `testing` ↔ `testing-framework` | TestHarness API、Scenario 用法 |
| `docs-maintenance` ↔ `framework-dev` | 四位一体变更清单、协作出口 |
| `doc-nav` ↔ `codebase-nav` ↔ `code-nav` | 导航链路、委托关系 |
| `framework-usage` ↔ `plugin-migration` | API 映射表 vs 当前 API 速查 |

每个 subagent 读取两端 SKILL.md + references，对比同名概念描述，标记矛盾为 P1。

### Step 4：汇总

聚合 Phase A + B 全部 subagent 输出，按 severity 排序生成报告，格式参见 [references/report-template.md](./references/report-template.md)。

### Step 5：修复

按以下策略执行修复：

| 问题类型 | 修复方式 |
|---------|---------|
| P0 内部断链 | 修正链接路径或删除失效引用 |
| P0 skill 不存在 | 修正为正确 skill 名或删除引用 |
| P0 docs 路径不存在 | 修正路径或标记待创建 |
| P1 API 不一致 | 以 Code 为权威，更新 Skill references |
| P1 skill 对矛盾 | 以较新/更详细的一方为准，同步另一方 |
| P2 措辞差异 | 仅报告，不自动修复 |

可为每个需修复的 skill 并发启动修复操作。

---

## Severity 分级

| 级别 | 问题类型 | 处理 |
|------|---------|------|
| P0 | 内部文件断链、docs 路径不存在、引用不存在的 skill | 必须修复 |
| P1 | skill 描述的 API 与 docs 签名明显不一致、skill 对间矛盾 | 应当修复 |
| P2 | 措辞轻微过时，不影响功能理解 | 仅报告 |

---

## 协作技能

| 需要做什么 | 委托给 |
|-----------|--------|
| 发现 docs 内部有问题 | **docs-sync** |
| 需要修复 docs 内容 | **docs-maintenance** |
| 需要理解代码以核对 API | **codebase-nav** |
