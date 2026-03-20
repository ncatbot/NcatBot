# 检查项规范

> P0/P1/P2 严重程度定义及内容对齐标准以 [docs-maintenance/references/quality-spec.md](./../docs-maintenance/references/quality-spec.md) 为准；本文件定义各 Phase 的具体检查方法和报告格式。

## Phase A：Docs 内部链接完整性

### A1. 链接存在性（P0）

**提取规则**：
- `[text](<path>)` → 剥离 `<>` 得到 `path`
- `[text](path)` → 直接取 `path`
- 过滤掉 `http://` / `https://` 开头的外部链接
- 去除 `#section` 锚点部分，仅验证文件路径

**解析规则**：基于当前 `.md` 文件所在目录解析相对路径。

**报告格式**：
```
P0 BROKEN_LINK | <chapter>/<file>.md:L<line> | link: <path> | target not found
```

### A2. README 索引完整性（P0/P1）

**方法**：
1. `list_dir` 获取目录实际内容
2. 读取 `README.md`，提取其中引用的所有本地路径
3. 对比：
   - 文件/目录存在但 README 未引用 → P1 INDEX_MISSING
   - README 引用但文件/目录不存在 → P0 INDEX_DANGLING

**报告格式**：
```
P0 INDEX_DANGLING | <dir>/README.md:L<line> | references <path> | not found
P1 INDEX_MISSING  | <dir>/README.md | <filename> exists but not indexed
```

---

## Phase B：guide↔reference 内容对齐

### 主题域映射表

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

### 检查项（P1）

- 方法名差异：guide 说 `method_a()`，reference 说 `method_b()`
- 参数差异：参数名/类型/默认值不一致
- 返回类型差异

**报告格式**：
```
P1 GUIDE_REF_MISMATCH | guide/<file>:L<n> vs reference/<file>:L<m> | <api> | guide says X, ref says Y
```

---

## Phase C：examples 导入有效性

### C1. 导入路径检查（P1）

**方法**：提取 `.py` 文件中 `from ncatbot.xxx import yyy` 和 `import ncatbot.xxx`，验证 `ncatbot/xxx/` 目录或 `ncatbot/xxx.py` 文件存在。

**报告格式**：
```
P1 IMPORT_INVALID | examples/<example>/<file>.py:L<line> | from ncatbot.<path> | module not found
```

### C2. manifest.toml 字段检查（P1）

**方法**：读取 example 的 `manifest.toml`，对比 `ncatbot/cli/templates/plugin/manifest.toml` 中出现的字段名，标记缺少必填字段或使用已淘汰字段名。

**报告格式**：
```
P1 MANIFEST_FIELD | examples/<example>/manifest.toml | missing required field: <field>
```

---

## Phase D：Code↔Docs 防腐检查

### 模块映射表

| 代码模块 | Reference 文档 |
|---------|---------------|
| `ncatbot/api/` | `reference/1. Bot API/` |
| `ncatbot/event/` | `reference/2. 事件类型/` |
| `ncatbot/types/` | `reference/3. 数据类型/` |
| `ncatbot/core/` | `reference/4. 核心模块/` |
| `ncatbot/plugin/` | `reference/5. 插件系统/` |
| `ncatbot/service/` | `reference/6. 服务层/` |
| `ncatbot/adapter/` | `reference/7. 适配器/` |
| `ncatbot/utils/` | `reference/8. 工具模块/` |
| `ncatbot/testing/` | `reference/9. 测试框架/` |
| `ncatbot/cli/` | `reference/10. CLI/` |

### 检查项

| 问题 | 级别 |
|------|------|
| 代码已删除 API，docs 仍有描述 | P0 |
| 代码 API 签名变化（参数增删），docs 未更新 | P1 |
| 代码新增 public API，docs 无记录 | P2 |

**报告格式**：
```
P0 API_DELETED   | reference/<file>:L<n> | <ClassName.method> | not found in ncatbot/<module>/
P1 API_CHANGED   | reference/<file>:L<n> | <ClassName.method> | code: (a,b,c), docs: (a,b)
P2 API_UNDOCUMENTED | ncatbot/<module>/<file>.py | <ClassName.method> | no docs coverage
```
