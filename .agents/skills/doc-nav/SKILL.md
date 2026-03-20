---
name: doc-nav
description: '通过文档理解 NcatBot 项目：查阅功能说明、API 签名、架构设计、预期行为。文档优先，按优先级分层查阅。Use when: 理解功能、查 API、架构理解、预期行为、怎么用、设计决策、模块职责、文档在哪。'
---

# 文档导航

根据用户描述的问题或需求，快速定位到正确的文档，理解模块职责、预期行为和接口设计。

**核心原则**：先读文档再读代码。通过文档理解"应该怎样"，而非遍历源码。

## 工作流

```text
1. 分类问题（确定涉及的模块区域）
   → 2. 定位文档（按优先级查阅）
   → 3. 输出（文档路径 + 阅读建议）
```

---

## Step 1：分类问题

根据用户描述的**症状或需求**，判断涉及的模块区域。

> 完整症状速查表：[references/symptom-doc-table.md](./references/symptom-doc-table.md)

### 无法直接分类时

1. 读 `docs/guide/11. 架构与概念/1. 架构总览.md` 的分层架构图
2. 根据数据流方向缩小范围：
   - 入站（收消息）：adapter → event → core → plugin
   - 出站（发消息/调API）：plugin → api → adapter

---

## Step 2：定位文档

按以下优先级查阅，**每个目录先读 `README.md`**：

| 优先级 | 文档类型 | 路径 | 获取的信息 |
|--------|---------|------|-----------|
| 1 | 使用指南 | `docs/guide/<模块>/` | 预期行为、使用方式、常见模式 |
| 2 | API 参考 | `docs/reference/<模块>/` | 类签名、方法参数、返回值 |
| 3 | 模块内部实现 | `docs/contributing/3. 模块内部实现/` | 内部结构、调用链、设计约束 |
| 4 | 设计决策 | `docs/contributing/2. 设计决策/` | 为何如此设计、已知权衡 |

### 快速导航

| 需要了解什么 | 去哪里找 |
|---|---|
| 某功能怎么用 | `docs/guide/` → 对应子目录 |
| 某类/方法的签名 | `docs/reference/` → 对应子目录 |
| 某模块内部如何实现 | `docs/contributing/3. 模块内部实现/` |
| 某设计为何如此 | `docs/contributing/2. 设计决策/` |
| 整体架构 | `docs/guide/11. 架构与概念/1. 架构总览.md` |

> 关键词快速跳转索引：[references/keyword-doc-index.md](./references/keyword-doc-index.md)

---

## Step 3：输出

向用户提供：

1. **推荐文档路径**：按阅读顺序排列
2. **阅读建议**：先读哪部分、重点关注什么
3. **模块区域**：涉及哪个层（guide / reference / contributing）
4. **下一步**：如需定位具体代码实现，委托 **code-nav** 技能
