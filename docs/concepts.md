# 核心概念

> NcatBot 核心概念速查 — 术语定义、用途、关键类、概念关系一览。用于快速建立全局认知，或按术语检索理解特定概念。

---

## 概念地图

```text
                        ┌──────────────┐
                        │  BotClient   │ ← 编排入口：组装一切，管理生命周期
                        └──────┬───────┘
              ┌────────────────┼───────────────┐
              ▼                ▼               ▼
      ┌──────────────┐ ┌────────────┐  ┌─────────────┐
      │   Adapter    │ │  Service   │  │ PluginLoader │
      │ (NapCat/Mock)│ │ (RBAC/     │  │ (依赖解析 +  │
      │              │ │  Schedule/ │  │  热重载)     │
      └──────┬───────┘ │  Watcher)  │  └──────┬──────┘
             │         └────────────┘         │
             ▼                                ▼
    ┌─────────────────┐              ┌─────────────────┐
    │    Dispatcher    │              │     Plugin       │
    │ (事件广播 +      │◄────────────│ (NcatBotPlugin   │
    │  Handler 分发)  │  注册 Handler │  + Mixin 能力)   │
    └────────┬────────┘              └─────────────────┘
             │                                │
             ▼                                │ 使用
    ┌─────────────────┐              ┌────────┴────────┐
    │  Event / Entity  │              │   Registrar     │
    │ (BaseEventData + │              │ (装饰器注册 +    │
    │  Trait 协议)     │              │  Hook / Filter) │
    └────────┬────────┘              └─────────────────┘
             │
             ▼
    ┌─────────────────┐
    │   API Client     │
    │ (BotAPIClient +  │
    │  QQAPIClient +   │
    │  Sugar)          │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ MessageArray /   │
    │ Segment          │
    │ (消息构造与解析)  │
    └─────────────────┘
```

数据流向：Adapter 接收原始数据 → Dispatcher 广播事件 → Handler（经 Hook 链）执行回调 → API Client 发送响应。

---

## 1. 适配器与平台 (Adapter / Platform / Trait)

### Adapter — 协议适配器

将特定平台的通信协议转换为框架统一的事件流和 API 接口。每个 Adapter 封装一个平台的 WebSocket 连接管理、协议解析、事件标准化和 API 调用转换。

**用途**：
- 隔离平台差异 — 插件代码无需关心底层协议细节
- 多平台并行 — 单个 BotClient 可同时运行 NapCat + Bilibili 等多个适配器
- 可扩展 — 新增平台只需实现 BaseAdapter 接口，零修改已有代码

**内置适配器**：NapCatAdapter（QQ，OneBot v11）、MockAdapter（测试用模拟）

**关键类**：`BaseAdapter`、`AdapterRegistry`、`NapCatAdapter`、`MockAdapter`

### Platform — 平台标识

字符串标识符（`"qq"` / `"bilibili"` / `"mock"`），决定事件路由到哪个适配器、API 调用走哪条通道。

**用途**：在多适配器模式下区分事件来源和 API 目标。

### Trait — 跨平台 API 协议

定义跨平台统一的 API 能力接口：`IMessaging`（消息收发）、`IGroupManage`（群管理）、`IQuery`（信息查询）、`IFileTransfer`（文件操作）。

**用途**：让插件编写平台无关的代码 — 只依赖 Trait 接口而不依赖具体平台 API。

**参见**：[适配器参考](reference/adapter/)、[多平台开发指南](guide/multi_platform/)

---

## 2. 事件系统 (Event / EventStream / Dispatcher)

### Event — 事件实体

适配器接收到的原始数据经 `create_entity()` 工厂函数包装为事件实体。事件实体携带平台信息和 Trait 能力（如 `Replyable` 允许直接回复、`GroupScoped` 提供 `group_id`）。

**用途**：
- 统一数据模型 — 不同平台的消息/通知/请求统一为同一套事件类型
- Trait 赋能 — 事件对象自带操作能力（`event.reply()`、`event.delete()`）

**关键类**：`BaseEvent`、`BaseEventData`、`GroupMessageEvent`、`PrivateMessageEvent`

### EventStream — 异步事件流

`AsyncEventDispatcher` 的消费接口，每个监听者获得独立的队列（互不阻塞）。支持 `async with` + `async for` 消费模式。

**用途**：
- 多步对话 — 在 Handler 中等待用户的后续输入
- 后台监控 — 持续监听特定类型的事件
- 插件间协调 — 订阅其他插件产生的事件

### Dispatcher — 事件分发器

分为两层：`AsyncEventDispatcher`（纯广播，一对多分发事件到所有订阅者）和 `HandlerDispatcher`（事件→Handler 匹配与执行，含 Hook 链调用）。

**用途**：
- 解耦事件生产与消费 — 适配器只管生产事件，不关心谁消费
- 多消费者并行 — 每个 EventStream 独立队列，一个消费者阻塞不影响其他

**关键类**：`AsyncEventDispatcher`、`HandlerDispatcher`

**参见**：[事件类型参考](reference/events/)、[核心模块参考](reference/core/)

---

## 3. 注册与拦截 (Registrar / Handler / Hook / Filter)

### Registrar — 全局注册器

提供装饰器 API，将函数注册为事件 Handler。通过 ContextVar 在模块加载期隔离各插件的注册上下文，确保 Handler 归属正确的插件。

**用途**：
- 声明式注册 — `@registrar.on_group_command("hello")` 一行代码完成事件绑定
- 自动参数绑定 — 命令装饰器自动为 Handler 附加 CommandHook，解析消息中的 `str`、`int`、`At` 参数

**核心装饰器**：
- 命令：`on_group_command()` / `on_private_command()` / `on_command()`
- 消息：`on_group_message()` / `on_private_message()` / `on_message()`
- 事件：`on_notice()` / `on_request()` / `on_poke()` / `on_friend_request()` / `on(event_type)`

### Handler — 事件处理器

注册的回调函数，关联到特定的 EventType + Predicate 条件。支持 `priority` 优先级排序。

**用途**：框架事件处理的基本单元 — 每个 Handler 就是一个功能点的入口。

### Hook — 拦截钩子

三阶段拦截链：`BEFORE_CALL`（Handler 执行前）→ `AFTER_CALL`（执行后）→ `ON_ERROR`（异常时）。每阶段可挂载多个 Hook，按优先级排序执行。BEFORE_CALL Hook 可返回 `SKIP` 阻止 Handler 执行。

**用途**：
- **权限检查** — 在 Handler 执行前验证用户权限，无权限则 SKIP
- **参数预处理** — CommandHook 自动从消息中解析命令名和参数，绑定到函数签名
- **文本匹配** — StartsWithHook / KeywordHook / RegexHook 匹配消息内容
- **日志审计** — AFTER_CALL Hook 记录谁触发了什么命令
- **错误通知** — ON_ERROR Hook 在 Handler 异常时通知管理员

### Filter — 过滤器（BEFORE_CALL Hook 的特化）

Filter 不是独立概念，而是所有返回 `SKIP` 来阻止 Handler 执行的 BEFORE_CALL Hook 的统称。

**内置 Filter**：
- `MessageTypeFilter("group"|"private")` — 消息来源过滤
- `SelfFilter()` — 过滤 Bot 自身发送的消息
- `PlatformFilter("qq")` — 平台过滤
- `PostTypeFilter()` / `SubTypeFilter()` — 事件类型过滤
- `CommandHook("命令名")` — 命令前缀匹配 + 参数解析（最常用，由命令装饰器自动附加）

**关键类**：`Registrar`、`HandlerEntry`、`HookManager`

**参见**：[Hook 机制指南](guide/plugin/6.hooks.md)、[Registry 参考](reference/core/3_registry.md)

---

## 4. 插件系统 (Plugin / Mixin / Lifecycle)

### Plugin — 插件

功能模块化的基本单元。每个插件是一个独立目录，含 `manifest.toml`（元信息）和 Python 模块。插件通过 PluginLoader 加载，支持依赖声明和拓扑排序。

**用途**：
- 功能隔离 — 每个功能封装为独立插件，独立开发/测试/部署
- 热重载 — 运行时修改代码自动重载，无需重启 Bot
- 依赖管理 — 声明式依赖，自动按序加载

### NcatBotPlugin — 推荐基类

组合了所有 Mixin 能力的插件基类。继承它即获得配置持久化、数据存储、权限控制、定时任务、事件流等全部能力。

### Mixin — 能力混入

通过多继承组合到 NcatBotPlugin 中，每个 Mixin 提供一种独立能力。MRO 保证 `on_load()` / `on_unload()` 按固定顺序执行，单个 Mixin 故障不影响其他。

| Mixin | 提供的能力 | 典型用途 |
|-------|-----------|---------|
| **EventMixin** | 事件流 + `wait_event()` | 监听事件、多步对话 |
| **TimeTaskMixin** | 定时任务 | 定时推送、定期清理 |
| **RBACMixin** | 权限控制 | 管理员命令保护、分级权限 |
| **ConfigMixin** | YAML 配置持久化 | 可修改的插件配置 |
| **DataMixin** | JSON 数据持久化 | 计数器、用户数据、状态存储 |

### Lifecycle — 插件生命周期

`on_load()` → 运行中 → `on_unload()`。加载时初始化资源和注册 Handler，卸载时清理资源和取消注册。热重载 = unload + 重新 import + load。

**关键类**：`NcatBotPlugin`、`BasePlugin`、`PluginLoader`、`DependencyResolver`

**参见**：[插件开发指南](guide/plugin/)、[插件系统参考](reference/plugin/)

---

## 5. 消息模型 (MessageArray / Segment)

### Segment — 消息段

消息的原子单元，对应 OneBot v11 的 CQ 码。每种段类型是一个 Pydantic 模型。

**常用段类型**：
- `PlainText` — 纯文本
- `At` — @某人（`user_id="all"` 为 @全体）
- `Image` — 图片（URL 或本地路径，`type=1` 为闪照）
- `Reply` — 引用回复
- `Face` — QQ 表情
- `Record` — 语音
- `Video` — 视频

### MessageArray — 消息容器

Segment 的有序容器，支持链式构造（`.add_text().add_at().add_image()`）和查询过滤（`.filter(At)` 获取所有 @段）。

**用途**：
- 自由组装 — 混合文本、图片、@、引用等构建复杂消息
- 结构化解析 — 从收到的消息中按类型提取特定段
- 参数绑定来源 — CommandHook 从 MessageArray 中提取 `At`、`Image` 等参数

### Sugar — 语法糖

`QQMessageSugarMixin` 提供的关键字快捷发消息方式：`api.qq.post_group_msg(group_id, text="...", image="...", at=uid)`。自动将关键字组装为 MessageArray。

**用途**：避免手动构造 MessageArray — 简单消息一行搞定。

**关键类**：`Segment`（各子类）、`MessageArray`、`QQMessageSugarMixin`

**参见**：[消息发送指南](guide/send_message/)、[类型参考](reference/types/)

---

## 6. 服务层 (Service / RBAC / Schedule)

### Service — 可插拔服务

生命周期由 ServiceManager 管理的单例组件。提供插件可共享的后台功能。

**用途**：
- 跨插件共享 — 多个插件共用同一个 RBAC 服务或定时任务调度器
- 生命周期管理 — 随 Bot 启动加载，关闭时自动清理

### RBACService — 权限服务

基于 Trie 树的权限管理。支持层级权限路径（`admin.ban.temporary`）、通配符匹配（`admin.*`）、角色继承。

**用途**：
- 命令权限控制 — 限制敏感命令仅管理员可用
- 分级权限 — 不同角色（owner > admin > moderator > user）拥有不同权限范围
- 插件集成 — 通过 RBACMixin 一行代码检查权限

### TimeTaskService — 定时任务服务

支持间隔时间（`"60s"` / `"1h"`）和 cron 表达式的任务调度。

**用途**：
- 定时推送 — 每日新闻、整点报时
- 定期清理 — 清理过期数据、刷新缓存
- 心跳检测 — 定期检查服务状态

### FileWatcherService — 文件监控服务

监控插件 `.py` 文件变化，触发热重载。

**用途**：开发模式下修改代码自动重载，无需手动重启 Bot。

**关键类**：`BaseService`、`ServiceManager`、`RBACService`、`TimeTaskService`、`FileWatcherService`

**参见**：[RBAC 指南](guide/rbac/)、[服务层参考](reference/services/)

---

## 7. Predicate DSL — 声明式事件过滤

将 lambda 过滤条件替换为可组合的运算符表达式，用于 `wait_event()` 和事件流过滤。

**用途**：
- 多步对话 — 等待同一用户在同一群的下一条消息：`from_event(event) * msg_equals("确认")`
- 可读性 — 比嵌套 lambda 和 hasattr 检查更直观
- 可组合 — `*`（AND）、`+`（OR）、`~`（NOT）运算符自由组合

**核心工厂函数**：`from_event()`（自动推导会话上下文）、`same_user()`、`same_group()`、`msg_equals()`、`msg_matches()`

**参见**：[Predicate DSL 指南](guide/plugin/4c.predicate-dsl.md)、[Predicate API 参考](reference/core/2_predicate.md)

---

## 8. 编排入口 (BotClient)

### BotClient — 应用编排器

Composition Root — 组装适配器、分发器、插件加载器、服务管理器和 API 客户端，管理整个 Bot 的生命周期。

**用途**：
- 零配置启动 — `BotClient().run()` 从 `config.yaml` 自动加载一切
- 异步非阻塞启动 — `await BotClient().run_async()` 完成 startup 后立即返回，`bot.api` / `bot.dispatcher` 可用于自定义事件编排
- 多适配器编排 — 同时连接多个平台
- 生命周期管理 — 启动（配置→适配器→分发器→插件→服务→监听）→ 关闭（逆序清理）

**关键类**：`BotClient`

**参见**：[架构文档 §4.10](architecture.md)、[Quick Start](guide/quick_start/)
