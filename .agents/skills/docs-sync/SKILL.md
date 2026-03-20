---
name: docs-sync
description: '整体/局部防腐检查：Docs 内部链接断裂、README 索引不同步、guide↔reference 内容不一致、examples 导入过时、Code↔Docs API 对齐。逐文件检查，最大化并发 subagent。Use when: docs 防腐、docs 链接、docs 断链、断链检查、docs 审计、docs audit、code docs 对齐、reference 过时、guide reference 不同步、examples 检查、定期检查。'
---

# Docs 同步审计

指定范围内的防腐检查（局部或全量），确保：

1. **Docs 内部链接**完好（相对路径目标存在，README 索引与目录一致）
2. **guide ↔ reference** API 描述对齐
3. **examples** 导入路径和 manifest 格式有效
4. **Code ↔ Docs** public API 对齐（防腐补充 framework-dev 的开发时同步）

> **与 framework-dev 的分工**：framework-dev 是开发时主动同步（每次变更四位一体），docs-sync 是周期性被动审计（捕捉漏掉的对齐）。

> **与 docs-maintenance 的分工**：docs-sync 负责"发现问题 + 生成报告"，docs-maintenance 负责"执行修复"。质量标准参见 [docs-maintenance/references/quality-spec.md](./../docs-maintenance/references/quality-spec.md)。

---

## 工作流

```text
1. 枚举 → 2. Phase A（链接完整性）+ Phase D（Code↔Docs）并发
       → 3. Phase B（guide↔reference 内容）+ Phase C（examples）并发
       → 4. 汇总 → 5. 修复
```

### Step 1：枚举

列出所有待检目录：

```
docs/docs/notes/guide/     → 11 个子章节目录
docs/docs/notes/reference/  → 10 个子章节目录
docs/docs/notes/contributing/ → 子目录
docs/docs/examples/          → common/qq/bilibili/github/cross_platform
```

### Step 2：Phase A — Docs 内部链接完整性（并发，每章节一个 Explore subagent，约 25 个）

为 guide/ 每个章节目录、reference/ 每个章节目录、contributing/、examples/ 各子目录，各启动 1 个 Explore subagent。

每个 subagent 逐文件遍历其章节下所有 `.md` 文件：

**A1. 链接存在性**
- 提取所有 `[text](<path>)` 和 `[text](path)` 链接
- `<>` 格式需剥离尖括号得到实际路径
- 基于当前文件目录解析相对路径，验证目标是否存在
- 锚点 `#section` 部分忽略（不验证锚点有效性）
- 排除 `http://` / `https://` 外部链接

**A2. README 索引完整性**
- 读取目录下 `README.md` 中的链接列表和表格引用
- 对比目录中实际存在的 `.md` 文件和子目录
- 检查是否有遗漏（文件存在但 README 未引用）或多余（README 引用但文件不存在）

### Step 2（并发）：Phase D — Code↔Docs 防腐检查（并发，10 个 Explore subagent）

每个代码模块与其对应的 reference 文档进行 API 对比：

| 代码模块 | Reference 文档 |
|---------|---------------|
| `ncatbot/api/` | `docs/docs/notes/reference/1. Bot API/` |
| `ncatbot/event/` | `docs/docs/notes/reference/2. 事件类型/` |
| `ncatbot/types/` | `docs/docs/notes/reference/3. 数据类型/` |
| `ncatbot/core/` | `docs/docs/notes/reference/4. 核心模块/` |
| `ncatbot/plugin/` | `docs/docs/notes/reference/5. 插件系统/` |
| `ncatbot/service/` | `docs/docs/notes/reference/6. 服务层/` |
| `ncatbot/adapter/` | `docs/docs/notes/reference/7. 适配器/` |
| `ncatbot/utils/` | `docs/docs/notes/reference/8. 工具模块/` |
| `ncatbot/testing/` | `docs/docs/notes/reference/9. 测试框架/` |
| `ncatbot/cli/` | `docs/docs/notes/reference/10. CLI/` |

每个 subagent：
1. 读 `ncatbot/<module>/__init__.py` + 关键公开类文件（`__all__` 导出或主要类定义）
2. 提取 public API：类名、方法名、参数签名
3. 读对应 reference 文档中列出的类/方法/参数
4. 对比：
   - **已删除**：代码中不存在但文档仍描述（P0）
   - **已改名/签名变化**：方法名或参数不匹配（P1）
   - **新增未覆盖**：代码中有但文档未记录（P2）

### Step 3：Phase B — guide↔reference 内容对齐（并发，约 8 个 Explore subagent）

按主题域各起一个 subagent，对比 guide 和 reference 中对同一 API 的描述：

| 主题域 | Guide 路径 | Reference 路径 |
|-------|-----------|---------------|
| 插件系统 | `guide/3. 插件开发/` | `reference/5. 插件系统/` |
| 消息发送 | `guide/4. 消息发送/` | `reference/3. 数据类型/` |
| Bot API | `guide/5. API 使用/` | `reference/1. Bot API/` |
| 配置管理 | `guide/6. 配置管理/` | `reference/8. 工具模块/1. 配置.md` |
| RBAC | `guide/7. RBAC 权限/` | `reference/6. 服务层/1. RBAC 服务.md` |
| CLI | `guide/8. 命令行工具/` | `reference/10. CLI/` |
| 测试 | `guide/9. 测试指南/` | `reference/9. 测试框架/` |
| 多平台 | `guide/10. 多平台开发/` | `reference/7. 适配器/` + `reference/1. Bot API/` |

每个 subagent 读取两端文件，对比 API 方法名、参数、返回类型是否一致。

### Step 3（并发）：Phase C — examples 导入有效性（并发，每 example 目录一个 Explore subagent）

检查每个 example 的 `.py` 文件：
- `from ncatbot.*` 导入路径是否在 `ncatbot/` 目录中可解析
- `manifest.toml` 字段名是否与 `ncatbot/cli/templates/plugin/manifest.toml` 模板一致

### Step 4：汇总

聚合 Phase A/B/C/D 全部 subagent 输出，按 severity 排序生成报告。

报告格式参见 [references/report-template.md](./references/report-template.md)。

### Step 5：修复

将报告交给 **docs-maintenance** 执行修复（按 quality-spec.md 中 P0→P1→P2 顺序）。

| 问题类型 | 修复方式 |
|---------|----------|
| P0 断链 | 修正链接路径 |
| P0 README 索引多余 | 删除无效条目 |
| P0 已删除 API 仍在文档 | 从 reference/ 中移除或标记废弃 |
| P1 guide↔reference 不一致 | 以代码为权威，同步两端文档 |
| P1 examples 导入失效 | 更新导入路径 |
| P1 API 签名变化 | 更新 reference 签名 |

## 协作技能

| 需要做什么 | 委托给 |
|-----------|--------|
| 质量标准（P0/P1/P2 定义 + 内容对齐标准） | **docs-maintenance/references/quality-spec.md** |
| 修复所有发现的问题 | **docs-maintenance** |
| 运行自动化脚本 | `python .agents/scripts/check_doc_consistency.py` |
| P2 新增 API 未覆盖 | 仅报告（委托 docs-maintenance 补写） |
| P2 措辞差异 | 仅报告 |

> Docs 内容可直接修复。发现 Code 端需改 → 委托 **framework-dev**。

---

## Severity 分级

| 级别 | 问题类型 | 处理 |
|------|---------|------|
| P0 | 链接目标不存在、README 索引引用失效、Code 已删除 API 仍在 docs | 必须修复 |
| P1 | guide↔reference 不一致、examples 无效导入、Code API 签名与 docs 不符 | 应当修复 |
| P2 | 新增 API 未覆盖、措辞差异 | 仅报告 |

---

## VuePress 链接语法

- 路径含空格时用 `<>` 包裹：`[text](<3. 插件开发/README.md>)`
- 锚点写在 `>` 后面：`[text](<file.md>#section)`
- 纯 URL 用 `<https://...>`
- 全部使用相对路径，禁止硬编码站点绝对路径

详见 [references/link-syntax.md](./references/link-syntax.md)。

---

## 协作技能

| 需要做什么 | 委托给 |
|-----------|--------|
| Code 端需要修改 | **framework-dev** |
| 发现 docs↔skill 不同步 | **skills-sync** |
| 补写新文档 | **docs-maintenance** |
| 理解代码以核对 API | **codebase-nav** |
