# 模块 → 代码位置完整映射表

从模块名到代码目录和核心类的完整对照。

## 全量模块速查表

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

## 文档路径 → 代码模块

### guide/ → 代码

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

### reference/ → 代码

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

### contributing/ → 代码

| 文档路径 | 覆盖的代码范围 |
|----------|--------------|
| `contributing/3. 模块内部实现/1. 核心模块.md` | `ncatbot/core/`, `ncatbot/app/`, `ncatbot/adapter/` |
| `contributing/3. 模块内部实现/2. 插件服务模块.md` | `ncatbot/plugin/`, `ncatbot/service/` |
| `contributing/2. 设计决策/1. 架构决策.md` | 跨模块架构决策 |
| `contributing/2. 设计决策/2. 实现决策.md` | Dispatcher / Hook / 热重载实现决策 |
