---
name: codebase-nav
description: '导航 NcatBot 代码库：定位代码、理解模块、查阅文档。文档优先，非必要不读代码，通过问题分类 → 文档查阅 → 精准定位的流程找到目标。Use when: 定位代码、找代码、问题定位、代码在哪、哪个模块、哪个文件、issue 分析、bug 在哪、报错定位、功能在哪实现、架构理解、模块交互。'
---

# 代码库导航

根据用户描述的问题或功能需求，快速定位到 NcatBot 框架中的相关代码位置、理解模块职责和交互。

**核心原则**：文档优先，非必要不读代码。通过文档理解模块职责和边界，而非遍历源码。

## 工作流

```text
1. 分类问题 → 2. 查阅文档 → 3. 锁定模块 → 4. 精准定位（仅在必要时读代码）
```

---

## Step 1：分类问题

根据用户描述的**症状或需求**，对照下表判断涉及的模块区域。

### 问题症状速查表

| 症状 / 关键词 | 涉及模块 | 首先查阅的文档 |
|---|---|---|
| Bot 启动失败 / 连接不上 | adapter, app | `contributing/3. 模块内部实现/1. 核心模块.md` |
| 消息不响应 / handler 不触发 | core/registry, core/dispatcher | `guide/3. 插件开发/4. 事件注册.md` |
| API 调用报错 / 返回异常 | api, adapter/napcat/api | `reference/1. Bot API/README.md` → 对应方法 |
| 插件加载失败 / 找不到插件 | plugin/loader | `guide/3. 插件开发/3. 生命周期.md` |
| 插件卸载/热重载异常 | plugin/loader | `guide/3. 插件开发/3. 生命周期.md` |
| Hook/Filter 不生效 | core/registry/hook | `guide/3. 插件开发/9. Hooks.md` |
| 权限/RBAC 不工作 | service/builtin/rbac | `guide/7. RBAC 权限/1. RBAC 模型.md` |
| 定时任务不执行 | plugin/mixin/time_task_mixin, service/builtin/schedule | `reference/6. 服务层/2. 配置任务服务.md`。检查插件是否有与 task name 同名的方法，或是否显式传入了 callback |
| 配置读取错误 | utils/config | `guide/6. 配置管理/1. 配置安全.md` |
| 消息构造/消息段问题 | types/common/segment | `guide/4. 消息发送/1. 通用/1. 消息段.md` |
| 合并转发失败 | types/helper, api | `guide/4. 消息发送/2. QQ/2. 合并转发.md` |
| 事件字段缺失/解析错误 | event, types | `reference/2. 事件类型/1. 通用事件.md` |
| CLI 命令报错 | cli | `reference/10. CLI/1. 命令参考.md` |
| 非插件模式不工作 | app/client, core/registry | `guide/README.md`（非插件模式章节） |
| 日志/输出异常 | utils/logger | `reference/8. 工具模块/1. 配置.md` |
| 测试框架问题 | testing | `guide/9. 测试指南/README.md` |
| 平台适配器找不到/不工作 | adapter | `guide/2. 适配器/README.md` → 对应平台指南 |
| QQ 登录失败 / WebUI 连接不上 | adapter/napcat/setup | `guide/2. 适配器/1. NapCat QQ.md` |
| Bilibili 扫码登录失败 / 凭据失效 | adapter/bilibili/auth | `guide/2. 适配器/2. Bilibili.md` |
| GitHub Token 验证失败 / Webhook 不触发 | adapter/github | `guide/2. 适配器/3. GitHub.md` |
| QQ 专用类型/段错误 | types/qq | `reference/3. 数据类型/README.md` |
| 跨平台事件路由问题 | event/common/factory, core/registry | `guide/10. 多平台开发/README.md` |
| 多适配器/多平台配置 | app/client, api/client | `guide/10. 多平台开发/README.md` |

> **多症状并发时**：按事件处理链路（adapter → event → dispatcher → registry → handler）逐步排查，找到第一个偏离预期的环节。

### 无法直接分类时

1. 读 `docs/guide/11. 架构与概念/1. 架构总览.md` 的分层架构图，理解各层职责
2. 根据问题涉及的数据流方向（入站 vs 出站）缩小范围
3. 入站（收消息）：adapter → event → core → plugin
4. 出站（发消息/调API）：plugin → api → adapter

---

## Step 2：查阅文档

根据 Step 1 确定的模块，按以下优先级查阅文档：

### 文档查阅优先级

| 优先级 | 文档类型 | 路径 | 获取的信息 |
|--------|---------|------|-----------|
| 1 | 使用指南 | `docs/guide/<模块>/` | 预期行为、使用方式、常见模式 |
| 2 | API 参考 | `docs/reference/<模块>/` | 类签名、方法参数、返回值 |
| 3 | 模块内部实现 | `docs/contributing/3. 模块内部实现/` | 内部结构、调用链、设计约束 |
| 4 | 设计决策 | `docs/contributing/2. 设计决策/` | 为何如此设计、已知权衡 |

### 文档导航

> 详细导航参见：[references/doc-module-map.md](./references/doc-module-map.md)

**每个目录先读 `README.md`**，它包含该目录的概览和索引。

| 需要了解什么 | 去哪里找 |
|---|---|
| 某功能怎么用 | `docs/guide/` → 对应子目录 |
| 某类/方法的签名 | `docs/reference/` → 对应子目录 |
| 某模块内部如何实现 | `docs/contributing/3. 模块内部实现/` |
| 某设计为何如此 | `docs/contributing/2. 设计决策/` |
| 整体架构 | `docs/guide/11. 架构与概念/1. 架构总览.md` |

---

## Step 3：锁定模块

通过文档阅读，你应该已经知道：

1. **哪个模块**负责该功能
2. **预期行为**是什么
3. **关键类/函数**的名称

此时对照模块速查表，锁定到具体目录：

| 模块 | 代码位置 | 核心类/文件 |
|------|---------|------------|
| 应用编排 | `ncatbot/app/` | `BotClient` |
| 事件分发 | `ncatbot/core/dispatcher/` | `AsyncEventDispatcher` |
| Handler 注册 | `ncatbot/core/registry/` | `HandlerDispatcher`, `Registrar` |
| Hook 机制 | `ncatbot/core/registry/` | Hook 相关 |
| 插件基类 | `ncatbot/plugin/` | `NcatBotPlugin`, `BasePlugin` |
| 插件加载 | `ncatbot/plugin/loader/` | `PluginLoader`, `PluginIndexer` |
| Mixin 扩展 | `ncatbot/plugin/mixin/` | Event / TimeTask / RBAC / Config / Data |
| Bot API | `ncatbot/api/` | `BotAPIClient`, `IAPIClient` |
| API 语法糖 | `ncatbot/api/qq/sugar.py` | `QQMessageSugarMixin` |
| NapCat 适配 | `ncatbot/adapter/napcat/` | `NapCatAdapter` |
| WebSocket | `ncatbot/adapter/napcat/connection/` | WebSocket + OB11Protocol |
| 事件解析 | `ncatbot/adapter/napcat/` | `NapCatEventParser` |
| 事件模型 | `ncatbot/event/` | `MessageEvent`, `NoticeEvent`, `RequestEvent` |
| 事件通用层 | `ncatbot/event/common/` | `BaseEvent`, `create_entity()`, `register_platform_factory()` |
| 事件 QQ 层 | `ncatbot/event/qq/` | `GroupMessageEvent`, `FriendRequestEvent` |
| 事件 Trait | `ncatbot/event/common/mixins.py` | `Replyable`, `GroupScoped`, `Deletable` |
| 类型定义 | `ncatbot/types/` | Pydantic 数据模型 |
| 类型通用层 | `ncatbot/types/common/` | `BaseEventData`, `BaseSender`, `MessageSegment` |
| 类型 QQ 层 | `ncatbot/types/qq/` | `GroupSender`, `Face`, `Forward` |
| API Trait | `ncatbot/api/traits/` | `IMessaging`, `IGroupManage`, `IQuery`, `IFileTransfer` |
| 平台 API | `ncatbot/api/qq/`, `ncatbot/api/bilibili/` | `QQAPIClient`, `IQQAPIClient` |
| Bilibili 认证 | `ncatbot/adapter/bilibili/auth.py` | `qrcode_login()` 扫码登录 |
| Bilibili 凭据持久化 | `ncatbot/adapter/bilibili/credential_store.py` | `save_credential_to_config()` |
| 消息段 | `ncatbot/types/common/segment/` | text / media / array |
| API 响应类型 | `ncatbot/types/napcat/` | SendMessageResult, GroupInfo, LoginInfo 等 |
| API 错误 | `ncatbot/api/errors.py` | APIError, APIRequestError 等 |
| 服务管理 | `ncatbot/service/` | `ServiceManager` |
| RBAC 服务 | `ncatbot/service/builtin/` | RBAC 相关 |
| 定时任务 | `ncatbot/service/builtin/` | Schedule 相关 |
| 配置管理 | `ncatbot/utils/config/` | `ConfigManager` |
| 日志 | `ncatbot/utils/logger/` | Logger 相关 |
| CLI | `ncatbot/cli/` | `main.py`, `commands/` |
| 测试框架 | `ncatbot/testing/` | `TestHarness` |

---

## Step 4：精准定位（仅在必要时）

**只有当文档无法回答以下问题时，才读源代码**：

- 文档中未覆盖的实现细节
- 需要确认实际行为与文档描述是否一致
- 需要找到具体行号以定位 bug

### 读代码的策略

1. **用搜索（Explore 子代理）** 查找从文档中获得的关键类名/函数名
2. **只读目标文件**，不遍历整个模块
3. **追踪调用链时**，从已知入口顺着调用走，而非全局搜索

### 事件处理链路参考

当需要追踪"消息从接收到处理"的完整链路时：

```text
NapCatAdapter（WebSocket 收消息）
  → OB11Protocol（解析 OneBot 协议）
  → NapCatEventParser（构造事件实体）
  → AsyncEventDispatcher（广播事件）
  → HandlerDispatcher（匹配 handler + 执行 Hook 链）
  → 用户 handler 函数
```

### 出站链路参考

```text
用户调用 BotAPIClient 方法
  → IAPIClient 接口
  → NapCatBotAPI 实现
  → WebSocket 发送请求
```

---

## 输出格式

定位完成后，向用户提供：

1. **涉及的模块**：哪个层、哪个子模块
2. **关键文件**：具体路径（如 `ncatbot/core/dispatcher/dispatcher.py`）
3. **关键类/函数**：名称和简要职责
4. **相关文档**：供用户进一步了解的文档链接
5. **置信度说明**：是从文档确定的，还是需要进一步读代码确认
