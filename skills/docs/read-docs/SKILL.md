# read-docs — 高效阅读 NcatBot 文档

## 触发条件

当需要从文档中查找信息来回答用户问题、定位 API 用法、理解系统设计时，使用此技能。

---

## 文档全景

NcatBot 文档位于 `docs/`，分为四个部分：

| 目录/文件 | 用途 | 优先查阅时机 |
|-----------|------|-------------|
| `architecture.md` | 系统架构与模块关系 | 理解整体设计、模块间交互 |
| `guide/` | 任务导向教程 | 学习"如何做 X" |
| `reference/` | 完整 API 参考 | 查函数签名、参数、返回值 |
| `contributing/` | 内部实现与设计决策 | 理解框架内部、参与开发 |

---

## 查找策略：按问题类型选路径

### 问题类型 A：用户想学某个功能（"如何..."）

**路径**：`guide/README.md` → 找对应子目录 → 子目录 `README.md` → 目标文档

```
docs/guide/README.md        ← 快速定位子目录
  └── plugin/README.md      ← 插件开发入口
  └── send_message/README.md ← 消息发送入口
  └── testing/README.md     ← 测试入口
  ...（按主题选择）
```

常用子目录速查：

| 用户问题关键词 | 直接跳到 |
|---------------|----------|
| 插件/Plugin/事件处理/生命周期/Hook | `guide/plugin/` |
| 发消息/消息段/图片/语音/转发 | `guide/send_message/` |
| Bot API/调用接口/群管理 | `guide/api_usage/` |
| 配置/config.yaml/ConfigManager | `guide/configuration/` |
| 权限/RBAC/角色/用户组 | `guide/rbac/` |
| 测试/单元测试/PluginTestHarness | `guide/testing/` |

### 问题类型 B：查某个类/方法的签名或参数

**路径**：`reference/README.md` → 找对应子目录 → 目标文档

常用参考速查：

| 查找对象 | 文档位置 |
|----------|----------|
| BotClient / Registry / Dispatcher | `reference/core/1_internals.md` |
| 发消息 API（send_group_msg 等） | `reference/api/1a_message_api.md` 或 `1b_message_api.md` |
| 群管理 API | `reference/api/2_manage_api.md` |
| 查询/辅助 API | `reference/api/3_info_support_api.md` |
| 消息段类型（Text/Image/At...） | `reference/types/1_segments.md` |
| MessageArray | `reference/types/2_message_array.md` |
| 事件类层级（GroupMessageEvent 等） | `reference/events/1_event_classes.md` |
| NcatBotPlugin 基类 | `reference/plugin/1_base_class.md` |
| Mixin 体系 | `reference/plugin/2_mixins.md` |
| RBAC 服务 | `reference/services/1_rbac_service.md` |
| 配置/定时任务服务 | `reference/services/2_config_task_service.md` |
| WebSocket 连接 | `reference/adapter/1_connection.md` |
| 协议解析 | `reference/adapter/2_protocol.md` |
| IO/日志工具 | `reference/utils/1a_io_logging.md` |
| 装饰器/杂项工具 | `reference/utils/2_decorators_misc.md` |
| TestHarness 参考 | `reference/testing/1_harness.md` |

### 问题类型 C：理解某个设计决策或内部实现

**路径**：`contributing/README.md` → `design_decisions/` 或 `module_internals/`

| 关键词 | 文档位置 |
|--------|----------|
| 分层架构/适配器模式/设计理念 | `contributing/design_decisions/1_architecture.md` |
| Dispatcher/Hook/热重载 实现决策 | `contributing/design_decisions/2_implementation.md` |
| 核心模块实现细节 | `contributing/module_internals/1a_core_modules.md` |
| 插件系统/服务层实现细节 | `contributing/module_internals/2a_plugin_service_modules.md` |

### 问题类型 D：全局架构 / 模块交互

直接读 `architecture.md`，它是唯一一个不受 locs 限制、覆盖全局的文档。

---

## 高效阅读技巧

### 技巧 1：先读 README.md，再决定是否深入

每个目录都有 `README.md`，它包含：概览表格、快速路径、推荐阅读顺序。  
先读 README，80% 的问题可以在这里得到"指针"，然后再读具体文件。

### 技巧 2：有序文件从第 1 篇开始

带数字前缀的文件（`1.xxx.md`、`2.xxx.md`）有阅读依赖关系。  
不要跳读 `3.xxx.md` 而跳过 `1.xxx.md`，否则会缺少前提知识。

### 技巧 3：指南与参考互补

`guide/` 教你**怎么用**，`reference/` 告诉你**有什么参数**。  
碰到 "这个函数有哪些参数" → 去 `reference/`；  
碰到 "我的场景该怎么写" → 去 `guide/`。

### 技巧 4：利用链接追踪

文档末尾的"延伸阅读"、"相关文档"链接是精心选择的：  
读完一篇后跟随链接是比全局搜索更准确的查找方式。

---

## 减少读取量的原则

1. **先看目录树**：`docs/README.md` 的目录树是全局索引，一次读取即可定位所有文件。
2. **先读 README，再按需深入**：不要一次性读完整个 `guide/plugin/` 目录的所有 12 篇。
3. **参考文档有层级**：先看文件顶部的签名/类定义，如果够用就不必读完整个文件。
4. **带数字的文件有摘要**：每篇文档开头的 `>` 引用块是该文档的一句话摘要，快速判断是否需要深读。
