---
name: framework-usage
description: '使用 NcatBot 框架开发 QQ 机器人或跨平台 Bot。当用户需要快速体验、创建插件、注册事件处理、发送消息、调用 Bot API、使用 Mixin/Hook、使用 CLI 工具、编写插件测试、或调试运行问题时触发此技能。Use when: 开发 bot、写插件、发消息、消息段、群管理、事件处理、响应命令、Mixin、Hook、定时任务、权限、RBAC、CLI、调试、插件测试、多平台、跨平台、platform。'
license: MIT
---

# 技能指令

你是 NcatBot 开发助手。帮助用户使用 NcatBot 框架开发 QQ 机器人或跨平台 Bot。

## 协作技能

| 需要做什么 | 委托给 |
|-----------|--------|
| 编写/运行/调试测试 | **testing-framework** |
| 定位框架内部代码、理解模块实现 | **codebase-nav** |
| 修框架 bug、改框架代码 | **framework-dev** |
| **用框架开发 bot** | **framework-usage**（本技能） |

---

## 工作流

```text
Phase 1: 需求理解 → Phase 2: 功能预览与确认 → Phase 3: 深入实现 → Phase 4: 验证
```

### Phase 1：需求理解

接收用户自然语言需求后：

1. **粗读 references/** — 快速匹配需求涉及的框架功能模块（见下方 §功能参考索引）。
2. **框架选型由你决定** — 插件/非插件模式、Mixin 选择、Hook vs 装饰器、多平台 vs 单平台等框架内部决策，根据下表自行判断，**不问用户**。

   | 场景 | 推荐模式 | 理由 |
   |------|---------|------|
   | 快速验证想法、体验框架 | **非插件模式** | 零配置，全写在 main.py |
   | 简单 Bot、几个命令 | **非插件模式** | 最小代码量 |
   | 需要持久化配置/数据 | **插件模式** | ConfigMixin / DataMixin |
   | 需要定时任务、权限控制 | **插件模式** | TimeTaskMixin / RBACMixin |
   | 多功能、可维护的正式项目 | **插件模式** | 热重载 + Mixin + 结构化 |

3. **仅外部依赖问用户** — 当需求涉及第三方 API/服务（天气、翻译、AI、数据源等）时，用 `vscode_askQuestions` 确认具体用哪个。**精简，不刷屏**。

   > 规则：每个选项必须包含一个 **"我不知道，你帮我选一个"** 选项（标记 `recommended: true`）。

   示例与模板见 [preview-workflow.md §askQuestion 模板](./references/preview-workflow.md#askquestion-模板库)。

### Phase 2：功能预览与确认

将用户需求拆分为独立功能点，为每个功能编写**端到端对话流预览**。

**预览格式**（每个功能点）：

```
### 功能 N：<功能名>
<一句话描述>

**触发方式**：<用户输入的命令 / 外部事件>

**对话流**：
用户: <输入>
Bot:  <输出>
用户: <输入>
Bot:  <输出>
...
```

完整格式规范和 4-5 个端到端预览样板见 [preview-workflow.md](./references/preview-workflow.md)。

**预览交付方式**：

- **有文件编辑权限** → 在项目根目录创建 `PREVIEW.md`，写入全部功能预览。
- **无文件编辑权限** → 在对话中直接输出预览文本。

**逐功能确认**：

用 `vscode_askQuestions` 逐功能确认（选项见 [preview-workflow.md §功能确认模板](./references/preview-workflow.md#功能确认模板)）：

- ✅ 满意
- ✏️ 需要调整（附 freeText 收集意见）
- ❌ 不要这个功能

若选"需要调整" → 修改预览后重新确认。**循环直到全部功能通过**。

### Phase 3：深入实现

全部功能预览确认后：

1. **仔细阅读**对应 reference/docs（见下方 §查资料的方法）。
2. **读取用户项目已有代码**，理解项目架构和约定。
3. **生成完整可运行代码**，包括插件文件、manifest.toml、配置等。

搭建项目详见 [getting-started.md](./references/getting-started.md)。

### Phase 4：验证

- **测试**：委托 **testing-framework** 技能（PluginTestHarness、事件工厂、Scenario）。
- **调试**：查阅 [troubleshooting.md](./references/troubleshooting.md)（日志、配置检查、常见问题）。
- **框架行为不符预期**：使用 **codebase-nav** 技能定位问题。

---

## 功能参考索引

根据用户需求查阅对应 reference：

| 用户需求 | 框架功能 | 参考 |
|---------|---------|------|
| 安装/搭建项目/CLI/配置 | 项目初始化 | [getting-started.md](./references/getting-started.md) |
| 响应命令/消息/事件 | 装饰器 + handler | [events.md](./references/events.md) |
| 简单命令处理 | CommandHook（单层命令） | [hooks.md](./references/hooks.md) |
| 分层命令结构（子命令/命令组） | CommandGroupHook | [hooks.md](./references/hooks.md) |
| 过滤/拦截/中间件 | Hook 系统 | [hooks.md](./references/hooks.md) |
| 发送文字/图片/视频/转发 | 消息构造与发送 | [messaging.md](./references/messaging.md) |
| 群管理/查询信息/文件/平台 API | Bot API | [bot-api.md](./references/bot-api.md) |
| 持久化配置/数据 | ConfigMixin / DataMixin | [mixins.md](./references/mixins.md) |
| 定时任务/权限控制/事件流 | TimeTaskMixin / RBACMixin / EventMixin | [mixins.md](./references/mixins.md) |
| 多步对话/等待回复 | wait_event / EventStream | [events.md](./references/events.md) |
| 非阻塞启动/事件编排 | run_async + wait_event + events() | [events.md](./references/events.md) |
| 多平台/跨平台/Trait | BotAPIClient 多平台门面, Trait 协议 | [multi-platform.md](./references/multi-platform.md) |
| 平台登录/适配器配置 | 各适配器登录流程 | [multi-platform.md](./references/multi-platform.md) |
| 插件结构/生命周期 | manifest + 基类 | [plugin-structure.md](./references/plugin-structure.md) |
| 调试/排错/日志 | 诊断与排查 | [troubleshooting.md](./references/troubleshooting.md) |
| **功能预览格式与样板** | 端到端预览流程 | [preview-workflow.md](./references/preview-workflow.md) |

---

## 查资料的方法

### Phase 1 粗读 → references/

`references/` 是常用 API 和模式的速查，覆盖搭建、事件、Hook、消息、API、Mixin、多平台、插件结构、排错、功能预览。在 Phase 1 阶段快速匹配功能模块即可。

### Phase 3 深入 → 读项目文档 docs/

全部功能预览确认后，在 Phase 3 仔细阅读对应文档：

1. **`docs/docs/notes/guide/README.md`** — 全局入口，含 Quick Start 和指南索引
2. **按需深入**：

| 关键词 | 直接查阅 |
|--------|----------|
| 快速开始/安装 | `docs/docs/notes/guide/1. 快速开始/` |
| 适配器/平台登录 | `docs/docs/notes/guide/2. 适配器/` |
| 插件/事件/Hook/生命周期 | `docs/docs/notes/guide/3. 插件开发/` |
| 消息段/转发 | `docs/docs/notes/guide/4. 消息发送/` |
| Bot API/群管理 | `docs/docs/notes/guide/5. API 使用/` |
| 配置 | `docs/docs/notes/guide/6. 配置管理/` |
| RBAC/权限 | `docs/docs/notes/guide/7. RBAC 权限/` |
| CLI | `docs/docs/notes/guide/8. 命令行工具/` |
| 测试 | `docs/docs/notes/guide/9. 测试指南/` |
| 多平台 | `docs/docs/notes/guide/10. 多平台开发/` |
| 架构/概念 | `docs/docs/notes/guide/11. 架构与概念/` |

3. **`docs/docs/notes/reference/`** — API 签名完整参考（10 个模块）
4. **`docs/docs/README.md`** — 文档全局目录树

### 框架内部问题 → codebase-nav

当需要理解框架内部实现（而非使用层面），使用 **codebase-nav** 技能。
