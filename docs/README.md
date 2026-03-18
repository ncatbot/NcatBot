# NcatBot 文档

> NcatBot 5.x 文档中心 — 完整导航、语义索引与推荐阅读路径。

---

## 快速导航

| 分类 | 说明 | 链接 |
|------|------|------|
| 核心概念 | 术语定义、用途、概念关系速查 | [concepts.md](concepts.md) |
| 架构概览 | 系统分层、模块职责、生命周期 | [architecture.md](architecture.md) |
| 使用指南 | 从入门到进阶的任务导向指南 | [guide/](guide/) |
| API 参考 | 完整 API 签名与参数细节 | [reference/](reference/) |
| 贡献指南 | 开发环境、内部实现、设计决策 | [contributing/](contributing/) |
| 元文档 | 文档编写规范与 AI 优化策略 | [meta/](meta/) |

---

## 文档目录树

```text
docs/
├── README.md                        # 文档中心首页（本文件）
├── architecture.md                  # 架构总览
├── concepts.md                      # 核心概念速查
│
├── guide/                           # 使用指南
│   ├── README.md                    #   指南首页 & Quick Reference
│   ├── quick_start/                 #   从零启动（3 篇）
│   │   ├── README.md                #     Quick Start 首页
│   │   ├── 1.install-config.md      #     安装与配置
│   │   ├── 2.non-plugin-mode.md     #     非插件模式启动
│   │   └── 3.plugin-mode.md         #     插件模式启动
│   ├── plugin/                      #   插件开发（11 篇）
│   │   ├── README.md                #     插件开发首页 & Quick Start
│   │   ├── 1.quick-start.md         #     快速入门
│   │   ├── 2.structure.md           #     插件结构（manifest / 目录 / 基类）
│   │   ├── 3.lifecycle.md           #     生命周期（加载与卸载）
│   │   ├── 4a.event-registration.md #     事件处理 — 注册方式
│   │   ├── 4b.event-advanced.md     #     事件处理 — 高级用法
│   │   ├── 4c.predicate-dsl.md      #     Predicate DSL（谓词组合）
│   │   ├── 5a.config-data.md        #     Mixin — 配置与数据
│   │   ├── 5b.rbac-schedule-event.md#     Mixin — 权限 / 定时 / 事件
│   │   ├── 6.hooks.md               #     Hook 机制（基础与内置钩子）
│   │   ├── 7a.patterns.md           #     高级主题 — 常用模式
│   │   └── 7b.case-studies.md       #     高级主题 — 实战案例
│   ├── send_message/                #   消息发送（按平台组织）
│   │   ├── README.md                #     消息发送首页 & Quick Start
│   │   ├── common/                  #     跨平台通用
│   │   │   ├── README.md
│   │   │   ├── 1_segments.md        #       消息段参考
│   │   │   └── 2_array.md           #       MessageArray 容器与链式构造
│   │   ├── qq/                      #     QQ 平台
│   │   │   ├── README.md
│   │   │   ├── 1_sugar.md           #       MessageSugarMixin 便捷接口
│   │   │   ├── 2_forward.md         #       合并转发
│   │   │   └── 3_examples.md        #       实战示例
│   │   └── bilibili/                #     Bilibili 平台
│   │       ├── README.md
│   │       └── 1_messaging.md       #       Bilibili 消息发送
│   ├── api_usage/                   #   Bot API 使用（按平台组织）
│   │   ├── README.md                #     API 使用首页 & Quick Start
│   │   ├── common/                  #     跨平台通用
│   │   │   ├── README.md
│   │   │   ├── 1_event_methods.md   #       事件对象方法（reply / delete / kick / ban）
│   │   │   └── 2_traits.md          #       Trait 跨平台接口
│   │   ├── qq/                      #     QQ 平台
│   │   │   ├── README.md
│   │   │   ├── 1_messaging.md       #       消息收发 API
│   │   │   ├── 2_manage.md          #       群管理 API
│   │   │   └── 3_query_support.md   #       信息查询与支持 API
│   │   └── bilibili/                #     Bilibili 平台
│   │       ├── README.md
│   │       ├── 1_live_room.md       #       直播间 API
│   │       ├── 2_private_msg.md     #       私信 API
│   │       ├── 3_comment.md         #       评论 API
│   │       └── 4_source_query.md    #       数据源查询 API
│   ├── configuration/               #   配置管理（1 篇）
│   │   ├── README.md                #     配置管理首页 & Quick Start
│   │   └── 1.config-security.md     #     配置管理与安全校验
│   ├── rbac/                        #   RBAC 权限管理（2 篇）
│   │   ├── README.md                #     权限管理首页 & Quick Start
│   │   ├── 1_model.md               #     权限模型
│   │   └── 2.integration.md         #     插件集成
│   ├── cli/                         #   CLI 命令行工具（1 篇）
│   │   ├── README.md                #     CLI 指南首页 & Quick Start
│   │   └── 1.commands.md            #     命令详解（初始化 / 启动 / 管理）
│   ├── testing/                     #   插件测试（3 篇）
│   │   ├── README.md                #     测试指南首页 & Quick Reference
│   │   ├── 1.quick-start.md         #     快速入门
│   │   ├── 2.harness.md             #     TestHarness 详解
│   │   └── 3.factory-scenario.md    #     工厂函数与 Scenario
│   └── multi_platform/              #   多平台开发（1 篇）
│       └── README.md                #     多平台开发指南
│
├── reference/                       # API 参考
│   ├── README.md                    #   参考首页 & 模块索引
│   ├── cli.md                       #   CLI 命令参考（全部命令签名与参数）
│   ├── api/                         #   Bot API 方法（按平台组织）
│   │   ├── README.md                #     API 方法首页 & Quick Start
│   │   ├── common/                  #     跨平台通用
│   │   │   └── traits.md            #       Trait 跨平台接口参考
│   │   ├── qq/                      #     QQ 平台
│   │   │   ├── 1_message_api.md     #       消息 API
│   │   │   ├── 2_manage_api.md      #       群管理 API
│   │   │   └── 3_info_support_api.md#       信息查询与支持 API
│   │   └── bilibili/                #     Bilibili 平台
│   │       └── 1_api.md             #       Bilibili API 参考
│   ├── events/                      #   事件类型（1 篇）
│   │   ├── README.md                #     事件参考首页 & Quick Start
│   │   ├── 1_common.md              #     通用事件基础（BaseEvent / Mixin / 工厂）
│   │   ├── 2_qq_events.md           #     QQ 事件实体
│   │   └── 3_bilibili_events.md     #     Bilibili 事件实体
│   ├── types/                       #   数据类型（4 篇）
│   │   ├── README.md                #     类型参考首页 & Quick Start
│   │   ├── 1_common_segments.md     #     通用消息段（跨平台）
│   │   ├── 2_message_array.md       #     MessageArray 容器
│   │   ├── 3_qq_segments.md         #     QQ 专属消息段
│   │   ├── 4_qq_responses.md        #     QQ/NapCat 响应类型
│   │   └── 5_bilibili_types.md      #     Bilibili 平台类型
│   ├── core/                        #   核心模块（3 篇）
│   │   ├── README.md                #     核心模块首页 & Quick Start
│   │   ├── 1_internals.md           #     Dispatcher / Event / EventStream 详解
│   │   ├── 2_predicate.md           #     Predicate DSL 完整 API 参考
│   │   └── 3_registry.md            #     Registry / Hook / Filter 参考
│   ├── plugin/                      #   插件系统（2 篇）
│   │   ├── README.md                #     插件系统首页 & Quick Start
│   │   ├── 1_base_class.md          #     基类详解
│   │   └── 2_mixins.md              #     Mixin 体系详解
│   ├── services/                    #   服务层（2 篇）
│   │   ├── README.md                #     服务层首页 & Quick Start
│   │   ├── 1_rbac_service.md        #     RBAC 服务
│   │   └── 2_config_task_service.md #     配置 / 定时任务服务
│   ├── adapter/                     #   适配器（2 篇）
│   │   ├── README.md                #     适配器首页 & Quick Start
│   │   ├── 1_connection.md          #     WebSocket 连接管理
│   │   └── 2_protocol.md            #     协议解析与事件转换
│   ├── utils/                       #   工具模块（3 篇）
│   │   ├── README.md                #     工具模块首页 & Quick Start
│   │   ├── 1a_config.md              #     配置管理（ConfigManager / Config 模型）
│   │   ├── 1b_io_logging.md         #     日志系统 + 网络工具（BoundLogger / HTTP）
│   │   └── 2_decorators_misc.md     #     装饰器与杂项工具
│   └── testing/                     #   测试框架（2 篇）
│       ├── README.md                #     测试框架首页 & 模块结构
│       ├── 1_harness.md             #     TestHarness / PluginTestHarness
│       └── 2_factory_scenario_mock.md #   工厂 / Scenario / Mock
│
├── contributing/                    # 贡献指南
│   ├── README.md                    #   贡献首页 & Quick Start
│   ├── development_setup/           #   开发环境搭建（1 篇）
│   │   ├── README.md
│   │   └── 1_advanced.md            #     高级配置（IDE / 调试 / 代码规范）
│   ├── design_decisions/            #   设计决策 ADR（2 篇）
│   │   ├── README.md
│   │   ├── 1_architecture.md        #     架构决策（分层 / 适配器模式）
│   │   └── 2_implementation.md      #     实现决策（Dispatcher / Hook / 热重载）
│   └── module_internals/            #   模块内部实现（2 篇）
│       ├── README.md
│       ├── 1.core_modules.md        #     核心模块实现
│       └── 2.plugin_service_modules.md # 插件与服务模块实现
│
└── meta/                            # 元文档
    └── README.md                    #   文档编写与维护规范
```

---

## 详细目录

### 顶层文档

- **[architecture.md](architecture.md)** — 系统架构全景。包含 7 层分层架构设计（Types → Adapter → Event → API → Core → Service → Plugin）、所有核心模块的职责与关键类、启动/事件处理/关闭的完整生命周期流程、插件开发模型与 Mixin 多继承体系。适合需要理解框架整体设计和模块关系的读者。

- **[concepts.md](concepts.md)** — 核心概念速查。以"术语→定义→用途→关键类→参见"的格式解释框架中的核心抽象：Adapter（协议适配）、Event/Dispatcher（事件驱动）、Registrar/Handler/Hook（注册与拦截）、Plugin/Mixin（插件化与能力组合）、MessageArray/Segment（消息构造）、Service/RBAC（服务层）。配有概念关系图，适合快速建立全局认知，或 AI Agent 按术语检索理解特定概念。

---

### guide/ — 使用指南

面向 Bot 开发者，按任务组织的从入门到进阶指南。

- **[guide/quick_start/](guide/quick_start/)** — 最小启动指南（3 篇）。覆盖安装 NcatBot（pip install）、配置 config.yaml 与 NapCat 连接、非插件模式启动（main.py 中用 `registrar` 装饰器直接注册回调）和插件模式启动（创建插件目录 + manifest.toml + NcatBotPlugin 子类）。从零到收到 Bot 的第一条回复的完整流程。

- **[guide/plugin/](guide/plugin/)** — 插件开发完整指南（11 篇）。从 5 分钟快速入门出发，逐步深入：插件结构（manifest.toml 声明 / 目录约定 / 基类选择）、生命周期（on_load / on_unload / 热重载）、事件注册（装饰器 / 手动注册 / Predicate DSL 声明式过滤）、Mixin 能力（ConfigMixin 配置持久化 / DataMixin 数据存储 / RBACMixin 权限控制 / TimeTaskMixin 定时任务 / EventMixin 事件流与多步对话）、Hook 拦截链（权限检查 / 参数预处理 / 文本匹配 / 错误通知）、到实战模式与案例。

- **[guide/send_message/](guide/send_message/)** — 消息发送指南（5 篇）。介绍 3 种日常发送方式：`event.reply(text=)` 最快回复、`api.qq.post_group_msg(group_id, text=, image=)` 语法糖、`MessageArray` 链式构造复杂消息。覆盖所有消息段类型（文本 / 图片 / @/ 引用 / 表情 / 语音 / 视频）、MessageArray 容器与查询过滤、合并转发构造、便捷接口速查，并附常见场景实战示例。

- **[guide/api_usage/](guide/api_usage/)** — Bot API 使用指南（3 篇）。按功能域组织：消息收发（发送群/私聊消息、撤回、获取历史消息）、群管理（禁言 / 踢人 / 设管理员 / 群设置）、信息查询（群列表 / 成员信息 / 好友列表 / 登录信息）。每个 API 附完整签名和使用示例，覆盖语法糖、原子 API、Trait 接口三种调用方式。

- **[guide/configuration/](guide/configuration/)** — 配置管理指南（1 篇）。config.yaml 完整结构说明（bot_uin / 适配器列表 / 插件开关）、多适配器配置方式、旧格式自动迁移机制、安全校验（敏感字段脱敏、类型检查）。

- **[guide/rbac/](guide/rbac/)** — RBAC 权限管理指南（2 篇）。Trie 权限树模型与层级路径（`admin.ban.temporary`）、角色定义与继承（owner > admin > moderator）、通配符匹配规则（`admin.*`）、rbac.json 配置格式、在插件中集成权限检查的 3 步流程（注册权限 → 配置角色 → 检查权限）。

- **[guide/cli/](guide/cli/)** — CLI 命令行工具指南（1 篇）。`ncatbot init`（初始化项目）、`run`（启动 Bot）、`dev`（开发模式，自动 debug + 热重载）、`config show/edit/reset`（配置管理）、`plugin list/enable/disable/reload`（插件管理）五大命令的用法与参数。

- **[guide/testing/](guide/testing/)** — 插件测试指南（3 篇）。PluginTestHarness 测试编排器的使用、事件注入与断言（`h.inject()` → `h.settle()` → `h.api_called()`）、8 个事件工厂函数（group_message / private_message / poke 等）、Scenario 链式场景构建器、自动冒烟测试生成。

- **[guide/multi_platform/](guide/multi_platform/)** — 多平台开发指南（1 篇）。Platform 概念（适配器的字符串标识）、Trait 协议（IMessaging / IGroupManage / IQuery 跨平台接口）、多适配器并行配置与运行、跨平台插件的编写策略。

---

### reference/ — API 参考

面向开发者查阅具体 API 签名、类型定义和参数细节。

- **[reference/api/](reference/api/)** — Bot API 方法参考（3 篇）。BotAPIClient / QQAPIClient 的所有公开方法完整签名、参数表格（参数名 | 类型 | 默认值 | 说明）和最简示例。按消息 API（send_group_msg / send_private_msg / delete_msg）、管理 API（set_group_ban / set_group_kick / set_group_admin）、查询 API（get_group_list / get_group_member_info / get_friend_list）分篇。含 Trait 跨平台接口说明。

- **[reference/events/](reference/events/)** — 事件类型参考（1 篇）。所有事件类的继承层级（BaseEvent → MessageEvent / NoticeEvent / RequestEvent）、各事件的字段定义（group_id / user_id / raw_message / ...）、Trait 协议（Replyable 可回复 / Deletable 可撤回 / Kickable 可踢出 / Bannable 可禁言 / GroupScoped 群相关 / HasSender 有发送者）。

- **[reference/types/](reference/types/)** — 数据类型参考（4 篇）。消息段完整属性表（PlainText / At / Image / Reply / Face / Record / Video 等每个段的全部字段）、MessageArray 全部方法签名（构造 / 链式添加 / 过滤查询 / 序列化）、API 响应 Pydantic 模型（消息响应 / 群组信息 / 用户信息 / 文件操作 / 系统状态）。

- **[reference/core/](reference/core/)** — 核心模块参考（3 篇）。AsyncEventDispatcher 事件广播引擎内部机制（Queue / EventStream / wait_event）、HandlerDispatcher 事件→Handler 匹配与 Hook 链执行流程、Predicate DSL 完整 API（P 基类 / 组合运算符 `*` `+` `~` / 工厂函数 from_event / same_user / msg_equals 等）、Registrar 注册接口与 Hook/Filter 全部内置实现。

- **[reference/plugin/](reference/plugin/)** — 插件系统参考（2 篇）。NcatBotPlugin 基类全部属性和方法签名（name / version / on_load / on_unload / api / ...）、所有 Mixin 的方法签名与参数表（EventMixin.wait_event / ConfigMixin.get_config / DataMixin.data / RBACMixin.check_permission / TimeTaskMixin.add_scheduled_task）。

- **[reference/services/](reference/services/)** — 服务层参考（2 篇）。RBACService 权限树 API（grant / revoke / check_permission / assign_role / PermissionTrie 内部实现）、TimeTaskService 定时任务接口（add_job / remove_job / cron 与间隔配置）、FileWatcherService 文件监控接口。

- **[reference/adapter/](reference/adapter/)** — 适配器参考（2 篇）。BaseAdapter 抽象接口（connect / disconnect / listen / call_api）、NapCatWebSocket 连接管理（心跳 / 断线重连 / 连接池）、OB11Protocol 协议解析（UUID echo 匹配 / asyncio.Future 响应映射 / 事件数据标准化）。

- **[reference/utils/](reference/utils/)** — 工具模块参考（3 篇）。ConfigManager 配置管理器（加载 / 更新 / 保存 / 旧格式迁移）、日志系统（get_log / 日志级别 / 格式配置）、网络请求工具（post_json / get_json / download_file）、装饰器（限流 / 重试）与杂项工具函数。

- **[reference/cli.md](reference/cli.md)** — CLI 命令参考。所有命令的完整签名、选项（`--debug` / `--no-hot-reload` / `--plugin-dir`）、退出码。

- **[reference/testing/](reference/testing/)** — 测试框架参考（2 篇）。TestHarness / PluginTestHarness 全部方法签名（inject / settle / api_called / get_replies / ...）、8 个事件工厂函数的参数表、Scenario 链式构建器 API、MockAdapter 与 MockBotAPI 行为说明。

---

### contributing/ — 贡献指南

面向框架贡献者，内部实现细节和设计理由。

- **[contributing/development_setup/](contributing/development_setup/)** — 开发环境搭建（1 篇）。Fork & Clone、uv 依赖安装、虚拟环境激活、pre-commit 钩子安装、IDE 配置（VS Code launch.json / PyCharm 运行配置）、调试器设置（pdb / VS Code 断点）、ruff 代码规范化。

- **[contributing/design_decisions/](contributing/design_decisions/)** — 设计决策 ADR（2 篇）。9 条已采纳的架构与实现决策记录：ADR-001 七层分层架构、ADR-002 适配器模式与依赖反转、ADR-003 AsyncEventDispatcher 纯广播设计、ADR-004 ContextVar 隔离注册上下文、ADR-005 Mixin 多继承 vs 组合。每条含背景、决策、理由、替代方案和后果分析。

- **[contributing/module_internals/](contributing/module_internals/)** — 模块内部实现（2 篇）。从 WebSocket 连接建立到 OB11 协议 UUID 匹配、AsyncEventDispatcher 广播实现、HandlerDispatcher 平台感知匹配、插件拓扑排序（Kahn 算法）加载、RBAC Trie 权限树实现、FileWatcher 热重载防抖机制的完整数据流和实现细节。

---

### meta/ — 元文档

- **[meta/README.md](meta/README.md)** — 文档编写与维护规范。目录编排约定（整体结构 / README 用途 / 文件命名）、内容规范（规模限制 / 渐进式披露 / 各类文档内容要求）、写作风格（语言 / 标题层级 / 引用规范）、维护流程（同步更新 / 验证清单）、AI 阅读优化策略（H1+摘要行 / 语义化索引 / Quick Reference 规范 / 概念地图 / 渐进式深度）。

---

## 推荐阅读路径

| 我想… | 路径 |
|-------|------|
| **从零开始运行 Bot** | [guide/quick_start/](guide/quick_start/) |
| **快速理解框架概念** | [concepts.md](concepts.md) → [architecture.md](architecture.md) |
| **开发一个插件** | [guide/plugin/](guide/plugin/) → [guide/api_usage/](guide/api_usage/) |
| **发送各种消息** | [guide/send_message/](guide/send_message/) |
| **查 API 签名** | [reference/api/](reference/api/) |
| **了解权限控制** | [guide/rbac/](guide/rbac/) → [reference/services/](reference/services/) |
| **为插件编写测试** | [guide/testing/](guide/testing/) → [reference/testing/](reference/testing/) |
| **参与贡献** | [contributing/](contributing/) |
| **AI Agent 快速了解框架** | [concepts.md](concepts.md) → [architecture.md](architecture.md) → 按需深入 guide/ 或 reference/ |
| **配置 Bot** | [guide/configuration/](guide/configuration/) |
| **使用 CLI** | [guide/cli/](guide/cli/) → [reference/cli.md](reference/cli.md) |
| **贡献代码** | [contributing/development_setup/](contributing/development_setup/) → [architecture.md](architecture.md) → [contributing/design_decisions/](contributing/design_decisions/) |
| **理解内部实现** | [architecture.md](architecture.md) → [contributing/module_internals/](contributing/module_internals/) |
