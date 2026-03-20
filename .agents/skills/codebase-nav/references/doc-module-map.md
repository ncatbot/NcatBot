# 文档-模块映射表

> 从文档路径到代码位置的完整对照，用于快速定位。

## guide/ → 代码模块

| 文档路径 | 对应代码模块 | 核心类/文件 |
|----------|-------------|------------|
| `guide/3. 插件开发/1. 快速开始.md` | `ncatbot/plugin/` | `NcatBotPlugin` |
| `guide/3. 插件开发/2. 插件结构.md` | `ncatbot/plugin/manifest.py` | `PluginManifest` |
| `guide/3. 插件开发/3. 生命周期.md` | `ncatbot/plugin/loader/` | `PluginLoader`, `PluginIndexer` |
| `guide/3. 插件开发/4. 事件注册.md` | `ncatbot/core/registry/` | `Registrar`, 装饰器 |
| `guide/3. 插件开发/5. 事件高级.md` | `ncatbot/core/registry/` | `HandlerDispatcher` |
| `guide/3. 插件开发/7. 配置与数据.md` | `ncatbot/plugin/mixin/` | ConfigMixin, DataMixin |
| `guide/3. 插件开发/8. RBAC 定时任务与事件.md` | `ncatbot/plugin/mixin/` | RBACMixin, TimeTaskMixin |
| `guide/3. 插件开发/9. Hooks.md` | `ncatbot/core/registry/` | Hook 机制与内置 Hook |
| `guide/3. 插件开发/10. 模式.md` | 多个模块 | 综合 |
| `guide/3. 插件开发/11. 案例研究.md` | 多个模块 | 综合 |
| `guide/4. 消息发送/` | `ncatbot/api/`, `ncatbot/types/common/segment/` | `BotAPIClient`, 消息段 |
| `guide/4. 消息发送/4. GitHub/` | `ncatbot/adapter/github/api/` | `GitHubBotAPI`, `CommentAPIMixin` |
| `guide/5. API 使用/` | `ncatbot/api/` | `BotAPIClient`, extensions |
| `guide/5. API 使用/4. GitHub/` | `ncatbot/adapter/github/api/` | `IssueAPIMixin`, `PRAPIMixin`, `QueryAPIMixin` |
| `guide/6. 配置管理/` | `ncatbot/utils/config/` | `ConfigManager` |
| `guide/7. RBAC 权限/` | `ncatbot/service/builtin/` | RBAC 服务 |
| `guide/8. 命令行工具/` | `ncatbot/cli/` | `main.py`, commands |
| `guide/9. 测试指南/` | `ncatbot/testing/` | `TestHarness` |
| `guide/10. 多平台开发/` | `ncatbot/api/`, `ncatbot/event/`, `ncatbot/app/` | `BotAPIClient`, `BaseEvent`, `BotClient` |

## reference/ → 代码模块

| 文档路径 | 对应代码模块 | 核心类/文件 |
|----------|-------------|------------|
| `reference/1. Bot API/2. QQ/1. 消息 API.md` | `ncatbot/api/qq/` | 消息发送方法 |
| `reference/1. Bot API/2. QQ/2. 管理 API.md` | `ncatbot/api/qq/` | 群管理方法 |
| `reference/1. Bot API/2. QQ/3. 信息支持 API.md` | `ncatbot/api/qq/` | 查询/辅助方法 |
| `reference/1. Bot API/4. GitHub/1. API.md` | `ncatbot/adapter/github/api/` | `GitHubBotAPI` (Issue/Comment/PR/Query Mixin) |
| `reference/2. 事件类型/1. 通用事件.md` | `ncatbot/event/` | 事件类层级 |
| `reference/2. 事件类型/4. GitHub 事件.md` | `ncatbot/event/github/` | GitHub 事件实体类 |
| `reference/3. 数据类型/1. 通用消息段.md` | `ncatbot/types/common/segment/` | 消息段类型 |
| `reference/3. 数据类型/6. GitHub 类型.md` | `ncatbot/types/github/` | GitHub 枚举、数据模型、Sender |
| `reference/3. 数据类型/2. 消息数组.md` | `ncatbot/types/common/segment/` | `MessageArray` |
| `reference/3. 数据类型/4. QQ 响应.md` | `ncatbot/types/napcat/` | API 响应类型 |
| `reference/4. 核心模块/1. 内部实现.md` | `ncatbot/core/` | Dispatcher, Registry |
| `reference/5. 插件系统/1. 基类.md` | `ncatbot/plugin/base.py`, `ncatbot_plugin.py` | 基类 |
| `reference/5. 插件系统/2. Mixins.md` | `ncatbot/plugin/mixin/` | Mixin 体系 |
| `reference/6. 服务层/1. RBAC 服务.md` | `ncatbot/service/builtin/` | RBAC |
| `reference/6. 服务层/2. 配置任务服务.md` | `ncatbot/service/builtin/` | Config, Schedule |
| `reference/7. 适配器/1. 连接.md` | `ncatbot/adapter/napcat/connection/` | WebSocket |
| `reference/7. 适配器/2. 协议.md` | `ncatbot/adapter/napcat/` | OB11Protocol, Parser |
| `reference/1. Bot API/README.md` | `ncatbot/api/`, `ncatbot/api/traits/`, `ncatbot/api/qq/`, `ncatbot/api/bilibili/`, `ncatbot/adapter/github/api/` | `BotAPIClient`, Trait 协议, 平台 API |
| `reference/8. 工具模块/1. 配置.md` | `ncatbot/utils/config/`, `ncatbot/utils/` | Config, ConfigManager |
| `reference/8. 工具模块/3. 装饰器与杂项.md` | `ncatbot/utils/` | 装饰器工具 |
| `reference/9. 测试框架/1. 测试工具.md` | `ncatbot/testing/harness.py` | TestHarness |
| `reference/9. 测试框架/2. 工厂场景与 Mock.md` | `ncatbot/testing/factory.py` | 工厂, Scenario |

## contributing/ → 代码模块

| 文档路径 | 覆盖的代码范围 |
|----------|--------------|
| `contributing/3. 模块内部实现/1. 核心模块.md` | `ncatbot/core/`, `ncatbot/app/`, `ncatbot/adapter/` |
| `contributing/3. 模块内部实现/2. 插件服务模块.md` | `ncatbot/plugin/`, `ncatbot/service/` |
| `contributing/2. 设计决策/1. 架构决策.md` | 跨模块架构决策 |
| `contributing/2. 设计决策/2. 实现决策.md` | Dispatcher / Hook / 热重载实现决策 |

## 关键词 → 文档快速跳转

| 关键词 | 直达文档 |
|--------|---------|
| 插件、Plugin、BasePlugin | `guide/3. 插件开发/README.md` |
| 事件、Event、handler、on_message | `guide/3. 插件开发/4. 事件注册.md` |
| Hook、Filter、中间件 | `guide/3. 插件开发/9. Hooks.md` |
| 消息、发送、图片、语音 | `guide/4. 消息发送/README.md` |
| 消息段、Segment、MessageArray | `reference/3. 数据类型/1. 通用消息段.md` |
| 合并转发、Forward | `guide/4. 消息发送/2. QQ/2. 合并转发.md` |
| API、BotAPIClient | `guide/5. API 使用/README.md` |
| 群管理、禁言、踢人 | `guide/5. API 使用/2. QQ/2. 群管理.md` |
| 配置、Config、yaml | `guide/6. 配置管理/README.md` |
| RBAC、权限、角色 | `guide/7. RBAC 权限/README.md` |
| CLI、命令行、ncatbot | `guide/8. 命令行工具/README.md` |
| 定时任务、Schedule | `reference/6. 服务层/2. 配置任务服务.md` |
| 测试、Test、Harness | `guide/9. 测试指南/README.md` |
| 多平台、跨平台、适配器、platform | `guide/10. 多平台开发/README.md` |
| GitHub、Webhook、Polling、Issue、PR | `guide/5. API 使用/4. GitHub/README.md` |
| GitHub 事件、GitHubIssueEvent、GitHubPREvent | `reference/2. 事件类型/4. GitHub 事件.md` |
| GitHub API、GitHubBotAPI | `reference/1. Bot API/4. GitHub/1. API.md` |
| GitHub 类型、GitHubAction、GitHubRepo | `reference/3. 数据类型/6. GitHub 类型.md` |
| API Trait、IMessaging、IGroupManage | `reference/1. Bot API/README.md` |
| event Trait、Replyable、GroupScoped | `reference/2. 事件类型/README.md` |
| WebSocket、连接、断线 | `reference/7. 适配器/1. 连接.md` |
| 配置、Config、ConfigManager | `reference/8. 工具模块/1. 配置.md` |
| Dispatcher、分发 | `reference/4. 核心模块/1. 内部实现.md` |
| Registry、注册 | `reference/4. 核心模块/1. 内部实现.md` |
| 生命周期、启动、关闭 | `docs/guide/11. 架构与概念/1. 架构总览.md`（§5 生命周期） |
