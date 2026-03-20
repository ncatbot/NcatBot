# 文档维护规范

## 核心约束

- 单文件 ≤ 400 locs（含空行）；目标 < 200 locs
- 每新增/删除文件，必须同步更新父目录 `README.md` 和 `docs/docs/notes/README.md`
- 代码块必须标注语言（`python` / `toml` / `bash`）

## 链接规范

- 全部使用相对路径，禁止硬编码站点绝对路径
- 路径含空格时（如含数字前缀的目录 `3. 插件开发/`），必须用 `<>` 包裹路径部分：
  ```markdown
  [插件开发](<../3. 插件开发/README.md>)
  [快速开始](<../3. 插件开发/1. 快速开始.md>)
  ```
- 锚点跟在 `>` 后面写，不写在 `<>` 内：`[标题](<file.md>#section)`
- 纯 URL 自动链接用 `<https://...>` 格式

## Step 1：定位目录

| 文档类型 | 目录 | 判断标准 |
|----------|------|----------|
| "如何做 X" 教程 | `docs/docs/notes/guide/` | 任务导向，有步骤，有示例 |
| 类/函数 API 详解 | `docs/docs/notes/reference/` | 参考导向，有签名、参数表格 |
| 内部实现/设计决策 | `docs/docs/notes/contributing/` | 面向框架贡献者 |
| 系统全局架构 | `docs/docs/notes/guide/11. 架构与概念/1. 架构总览.md` | 跨模块视图 |

## Step 2：确定文件名

1. 查看目标目录已有文件的命名风格
2. 有序系列 → `数字前缀.主题.md`（如 `3. 生命周期.md`）
3. 独立参考 → `数字_主题.md`（如 `1. 消息 API.md`）
4. 新子目录需创建 `README.md`

## Step 3：选模板

### 模板 A：指南文档（guide/）

```markdown
# 标题（动词短语）

> 一句话：本文档教你做什么。

## 前提条件

- 已完成 [上一步](../前一篇.md)

## 基础用法

## 进阶用法（可选）

## 延伸阅读

- [相关参考](../../reference/.../xxx.md)
```

### 模板 B：参考文档（reference/）

```markdown
# 模块/类名 参考

> 一句话描述。

## 类/函数签名

## 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `x` | `int` | — | 必填 |

## 示例

## 注意事项
```

### 模板 C：子目录 README.md

```markdown
# 子目录名 — 一句话说明

> 面向哪类读者

## 快速开始

## 文档清单

| 文件 | 说明 | 难度 |
|------|------|------|

## 推荐阅读顺序
```

## Step 4：同步索引

### 4.1 父目录 README.md

在"文档清单"表格新增一行。

### 4.2 docs/docs/notes/README.md 目录树

在对应位置新增：

```text
│   ├── 新文件名.md              #   说明
```

## Step 5：验证

- [ ] 文件 locs ≤ 400（`Get-Content 文件路径 | Measure-Object -Line`）
- [ ] 父目录 `README.md` 已更新
- [ ] `docs/docs/notes/README.md` 目录树已更新
- [ ] 所有内部链接使用相对路径，无断链
- [ ] 代码块已标注语言
- [ ] 无 TODO / 占位文本

## 常见场景

### 文件超出 400 locs

1. 按逻辑拆分为 `Xa.主题.md` + `Xb.主题.md`
2. 原文件末尾加"延伸阅读"链接
3. 更新父目录和 `docs/docs/notes/README.md`

### 代码重构后同步 API 文档

1. 找 `docs/docs/notes/reference/` 对应文档
2. 更新签名、参数表格
3. 检查 `docs/docs/notes/guide/` 中引用该 API 的示例

### 新增公开 API

1. 在 `docs/docs/notes/reference/` 添加条目
2. 超 400 locs 则拆分
3. 在 `docs/docs/notes/guide/` 添加示例

### 废弃 API

```markdown
> **已废弃（v5.x）**：请改用 [`NewApi`](./xxx.md#new-api)。
```

## 代码变更后的文档同步触发规则

代码变更发生后，根据变更类型触发对应文档更新：

| 变更类型 | 触发动作 |
|----------|----------|
| 公开 API 签名/参数/返回值变更 | 更新 `docs/docs/notes/reference/` 对应文档的签名、参数表格 |
| 用户可见行为变更（输出、副作用、约束） | 更新 `docs/docs/notes/guide/` 相关示例和描述 |
| 新增/删除源文件或模块 | 更新目录索引（父 `README.md` + `docs/docs/notes/README.md`） |
| 跨模块架构调整 | 更新 `docs/docs/notes/guide/11. 架构与概念/1. 架构总览.md` |
| 多平台适配代码变更 | 更新 `docs/docs/notes/guide/10. 多平台开发/` 对应文档 |

**废弃 API 固定格式**（在 reference/ 中标注）：

```markdown
> **已废弃（v5.x）**：请改用 [`NewApi`](./xxx.md#new-api)。
```
