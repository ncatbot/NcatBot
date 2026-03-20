---
name: code-nav
description: '定位 NcatBot 代码实现：锁定模块目录、找到关键类/函数、追踪调用链。当文档不够时才读代码，用搜索而非遍历。Use when: 找代码实现、哪个文件、哪个类、追踪调用链、定位 bug 行号、代码在哪、模块目录、源码定位。'
---

# 代码定位

根据已知的模块名称或类名，精准定位到 NcatBot 框架中的具体代码文件和关键类/函数。

**核心原则**：只在文档无法回答时才读代码。用搜索定位，不遍历模块。

> 如果还不知道涉及哪个模块，先使用 **doc-nav** 技能通过文档确定。

## 工作流

```text
1. 锁定模块（从模块速查表确定目录）
   → 2. 精准定位（搜索关键类名/函数名）
   → 3. 输出（文件路径 + 类名 + 职责）
```

---

## Step 1：锁定模块

通过 **doc-nav** 或已有信息，你应该已经知道涉及哪个模块。对照速查表锁定到具体目录：

### 核心模块速查表

| 模块 | 代码位置 | 核心类/文件 |
|------|---------|------------|
| 应用编排 | `ncatbot/app/` | `BotClient` |
| 事件分发 | `ncatbot/core/dispatcher/` | `AsyncEventDispatcher` |
| Handler 注册 | `ncatbot/core/registry/` | `HandlerDispatcher`, `Registrar` |
| 插件基类 | `ncatbot/plugin/` | `NcatBotPlugin`, `BasePlugin` |
| 插件加载 | `ncatbot/plugin/loader/` | `PluginLoader`, `PluginIndexer` |
| Bot API | `ncatbot/api/` | `BotAPIClient`, `IAPIClient` |
| 事件模型 | `ncatbot/event/` | `MessageEvent`, `NoticeEvent`, `RequestEvent` |
| 类型定义 | `ncatbot/types/` | Pydantic 数据模型 |
| 服务管理 | `ncatbot/service/` | `ServiceManager` |
| 测试框架 | `ncatbot/testing/` | `TestHarness` |

> 完整模块映射表（含所有子模块）：[references/module-code-map.md](./references/module-code-map.md)

---

## Step 2：精准定位

**只有当文档无法回答以下问题时，才读源代码**：

- 文档中未覆盖的实现细节
- 需要确认实际行为与文档描述是否一致
- 需要找到具体行号以定位 bug

### 读代码的三条原则

1. **用搜索（Explore 子代理）** 查找从文档中获得的关键类名/函数名
2. **只读目标文件**，不遍历整个模块
3. **追踪调用链时**，从已知入口顺着调用走，而非全局搜索

> 事件处理入站/出站链路参考：[references/event-chains.md](./references/event-chains.md)

---

## Step 3：输出

定位完成后，向用户提供：

1. **涉及的模块**：哪个层、哪个子模块
2. **关键文件**：具体路径（如 `ncatbot/core/dispatcher/dispatcher.py`）
3. **关键类/函数**：名称和简要职责
4. **相关文档**：供用户进一步了解的文档链接
5. **置信度说明**：是从文档确定的，还是需要进一步读代码确认
