# 检查项规范

## Phase A：per-skill 检查

### A1. 内部 references 断链（P0）

**方法**：正则提取 `[text](path)` 中路径以 `./` 或 `../` 开头的本地引用，用 `Test-Path` 验证目标文件是否存在。

**报告格式**：
```
P0 BROKEN_LINK | <skill>/<file>.md:L<line> | link: <path> | target not found
```

### A2. 协作技能引用（P0）

**方法**：正则提取 SKILL.md 中 `**<name>**` 格式出现在"协作技能"表格或"委托给"语境中的名称，验证 `.agents/skills/<name>/SKILL.md` 存在。

**排除**：`**Code**`、`**Test**`、`**Docs**`、`**Skill**` 等非技能名关键字。

**报告格式**：
```
P0 MISSING_SKILL | <skill>/SKILL.md:L<line> | references skill **<name>** | directory not found
```

### A3. Docs 引用路径（P0）

**方法**：在 references/*.md 中搜索形如 `docs/guide/...`、`docs/reference/...`、`docs/docs/examples/...` 的路径文本。映射规则：
- `docs/guide/X` → `docs/docs/notes/guide/X`
- `docs/reference/X` → `docs/docs/notes/reference/X`
- `docs/docs/examples/X` → `docs/docs/examples/X`

验证映射后的路径是否存在。

**报告格式**：
```
P0 DOCS_PATH_MISSING | <skill>/references/<file>.md:L<line> | path: <docs_path> | not found in workspace
```

### A4. Docs 内容对比（P1/P2）

**方法**：对 A3 中验证存在的 docs 引用，读取目标文件，提取 API 类名/方法名/参数，与 skill references 中描述对比。

**判定标准**：
- P1：方法名不同、参数列表明显不匹配（增删参数）
- P2：参数描述措辞不同但含义相同

**报告格式**：
```
P1 API_MISMATCH | <skill>/references/<file>.md:L<line> | <api_name> | skill says <X>, docs says <Y>
```

## Phase B：skill 对一致性

**方法**：读取两端 SKILL.md + references，搜索同名概念（如 TestHarness、Scenario、四位一体等），对比描述是否矛盾。

**判定标准**：
- P1：同一概念的定义/参数/行为不同
- P2：措辞差异但含义一致

**报告格式**：
```
P1 SKILL_CONFLICT | <skillA> vs <skillB> | concept: <name> | <description of conflict>
```
