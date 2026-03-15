# NcatBot 文档

> NcatBot 5.x 文档中心

---

## 快速导航

| 分类 | 说明 | 链接 |
|------|------|------|
| 架构概览 | 系统架构与设计理念 | [architecture.md](architecture.md) |
| 使用指南 | 从入门到进阶 | [guide/](guide/) |
| API 参考 | 完整 API 文档 | [reference/](reference/) |
| 贡献指南 | 开发环境与贡献流程 | [contributing/](contributing/) |
| 元文档 | 文档编写与维护规范 | [meta/](meta/) |

---

## 文档目录树

```
docs/
├── README.md                        # 文档中心首页（本文件）
├── architecture.md                  # 架构总览
│
├── guide/                           # 使用指南
│   ├── README.md                    #   指南首页 & Quick Start
│   ├── plugin/                      #   插件开发（12 篇）
│   │   ├── README.md                #     插件开发首页 & Quick Start
│   │   ├── 1.quick-start.md         #     快速入门
│   │   ├── 2.structure.md           #     插件结构（manifest / 目录 / 基类）
│   │   ├── 3a.loading.md            #     生命周期 — 加载流程
│   │   ├── 3b.unloading.md          #     生命周期 — 卸载流程
│   │   ├── 4a.event-registration.md #     事件处理 — 注册方式
│   │   ├── 4b.event-advanced.md     #     事件处理 — 高级用法
│   │   ├── 5a.config-data.md        #     Mixin — 配置与数据
│   │   ├── 5b.rbac-schedule-event.md#     Mixin — 权限 / 定时 / 事件
│   │   ├── 6a.hook-basics.md        #     Hook — 基础用法
│   │   ├── 6b.hook-builtins.md      #     Hook — 内置钩子
│   │   ├── 7a.patterns.md           #     高级主题 — 常用模式
│   │   └── 7b.case-studies.md       #     高级主题 — 实战案例
│   ├── send_message/                #   消息发送（6 篇）
│   │   ├── README.md                #     消息发送首页 & Quick Start
│   │   ├── 1_quickstart.md          #     快速上手（三种发送方式）
│   │   ├── 2_segments.md            #     消息段参考
│   │   ├── 3_array.md               #     MessageArray 容器与链式构造
│   │   ├── 4_forward.md             #     合并转发
│   │   ├── 5_sugar.md               #     MessageSugarMixin 便捷接口
│   │   └── 6_examples.md            #     实战示例（14 个场景）
│   ├── api_usage/                   #   Bot API 使用（3 篇）
│   │   ├── README.md                #     API 使用首页 & Quick Start
│   │   ├── 1_messaging.md           #     消息收发 API
│   │   ├── 2_manage.md              #     群管理 API
│   │   └── 3_query_support.md       #     信息查询与支持 API
│   ├── configuration/               #   配置管理（2 篇）
│   │   ├── README.md                #     配置管理首页 & Quick Start
│   │   ├── 1_manager.md             #     ConfigManager 详解
│   │   └── 2_security.md            #     配置安全与校验
│   ├── rbac/                        #   RBAC 权限管理（3 篇）
│   │   ├── README.md                #     权限管理首页 & Quick Start
│   │   ├── 1_model.md               #     权限模型
│   │   ├── 2a_integration.md        #     插件集成（上）
│   │   └── 2b_integration.md        #     插件集成（下）
│   └── testing/                     #   插件测试（3 篇）
│       ├── README.md                #     测试指南首页 & Quick Start
│       ├── 1.quick-start.md         #     快速入门
│       ├── 2.harness.md             #     TestHarness 详解
│       └── 3.factory-scenario.md    #     工厂函数与 Scenario
│
├── reference/                       # API 参考
│   ├── README.md                    #   参考首页 & 模块索引
│   ├── api/                         #   Bot API 方法（4 篇）
│   │   ├── README.md                #     API 方法首页 & Quick Start
│   │   ├── 1a_message_api.md        #     消息 API（上）
│   │   ├── 1b_message_api.md        #     消息 API（下）
│   │   ├── 2_manage_api.md          #     群管理 API
│   │   └── 3_info_support_api.md    #     信息查询与支持 API
│   ├── events/                      #   事件类型（1 篇）
│   │   ├── README.md                #     事件参考首页 & Quick Start
│   │   └── 1_event_classes.md       #     事件类层级详解
│   ├── types/                       #   数据类型（2 篇）
│   │   ├── README.md                #     类型参考首页 & Quick Start
│   │   ├── 1_segments.md            #     消息段类型
│   │   └── 2_message_array.md       #     MessageArray
│   ├── core/                        #   核心模块（1 篇）
│   │   ├── README.md                #     核心模块首页 & Quick Start
│   │   └── 1_internals.md           #     BotClient / Registry / Dispatcher 内部
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
│   │   ├── 1a_io_logging.md         #     IO 与日志（上）
│   │   ├── 1b_io_logging.md         #     IO 与日志（下）
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
│   └── module_internals/            #   模块内部实现（4 篇）
│       ├── README.md
│       ├── 1a_core_modules.md       #     核心模块实现（上）
│       ├── 1b_core_modules.md       #     核心模块实现（下）
│       ├── 2a_plugin_service_modules.md # 插件与服务模块实现（上）
│       └── 2b_plugin_service_modules.md # 插件与服务模块实现（下）
│
└── meta/                            # 元文档
    └── README.md                    #   文档编写与维护规范
```

---

## 详细目录

### guide/ — 使用指南

| 目录 | 说明 | 篇数 | 难度 |
|------|------|------|------|
| [plugin/](guide/plugin/) | 插件开发完整指南 | 12 | ⭐ - ⭐⭐⭐ |
| [send_message/](guide/send_message/) | 消息发送指南 | 6 | ⭐ |
| [api_usage/](guide/api_usage/) | Bot API 使用指南 | 3 | ⭐⭐ |
| [configuration/](guide/configuration/) | 配置管理指南 | 2 | ⭐⭐ |
| [rbac/](guide/rbac/) | RBAC 权限管理指南 | 3 | ⭐⭐⭐ |
| [testing/](guide/testing/) | 插件测试指南 | 3 | ⭐⭐ |

#### plugin/ — 插件开发

从快速入门到高级主题的完整路径：

1. [快速入门](guide/plugin/1.quick-start.md) — 5 分钟跑通第一个插件
2. [插件结构](guide/plugin/2.structure.md) — manifest.toml、目录布局、基类选择
3. 生命周期：[加载流程](guide/plugin/3a.loading.md) ｜ [卸载流程](guide/plugin/3b.unloading.md)
4. 事件处理：[注册方式](guide/plugin/4a.event-registration.md) ｜ [高级用法](guide/plugin/4b.event-advanced.md)
5. Mixin 能力：[配置与数据](guide/plugin/5a.config-data.md) ｜ [权限/定时/事件](guide/plugin/5b.rbac-schedule-event.md)
6. Hook 机制：[基础用法](guide/plugin/6a.hook-basics.md) ｜ [内置钩子](guide/plugin/6b.hook-builtins.md)
7. 高级主题：[常用模式](guide/plugin/7a.patterns.md) ｜ [实战案例](guide/plugin/7b.case-studies.md)

#### send_message/ — 消息发送

- [快速上手](guide/send_message/1_quickstart.md) — 三种发送方式速览
- [消息段参考](guide/send_message/2_segments.md) — 所有消息段类型详解
- [MessageArray](guide/send_message/3_array.md) — 消息容器与链式构造
- [合并转发](guide/send_message/4_forward.md) — ForwardNode / Forward 构造
- [便捷接口](guide/send_message/5_sugar.md) — MessageSugarMixin 速查
- [实战示例](guide/send_message/6_examples.md) — 14 个常见场景

#### api_usage/ — Bot API 使用

- [消息收发](guide/api_usage/1_messaging.md) — 消息发送与接收 API
- [群管理](guide/api_usage/2_manage.md) — 群管理相关 API
- [信息查询与支持](guide/api_usage/3_query_support.md) — 查询与辅助 API

#### configuration/ — 配置管理

- [ConfigManager 详解](guide/configuration/1_manager.md) — 配置管理器核心用法
- [配置安全与校验](guide/configuration/2_security.md) — 安全检查与字段校验

#### rbac/ — RBAC 权限管理

- [权限模型](guide/rbac/1_model.md) — RBAC 模型与概念
- [插件集成（上）](guide/rbac/2a_integration.md) — 权限注册与角色分配
- [插件集成（下）](guide/rbac/2b_integration.md) — 权限检查与实战

#### testing/ — 插件测试

- [快速入门](guide/testing/1.quick-start.md) — 5 步写出第一个测试
- [TestHarness 详解](guide/testing/2.harness.md) — 编排器完整用法
- [工厂与 Scenario](guide/testing/3.factory-scenario.md) — 事件工厂函数与场景构建

---

### reference/ — API 参考

| 目录 | 说明 | 篇数 |
|------|------|------|
| [api/](reference/api/) | Bot API 方法参考 | 4 |
| [events/](reference/events/) | 事件类型参考 | 1 |
| [types/](reference/types/) | 数据类型参考 | 2 |
| [core/](reference/core/) | 核心模块参考 | 1 |
| [plugin/](reference/plugin/) | 插件系统参考 | 2 |
| [services/](reference/services/) | 服务层参考 | 2 |
| [adapter/](reference/adapter/) | 适配器参考 | 2 |
| [utils/](reference/utils/) | 工具模块参考 | 3 |
| [testing/](reference/testing/) | 测试框架参考 | 2 |

#### api/ — Bot API 方法

- [消息 API（上）](reference/api/1a_message_api.md) — 消息发送 / 接收方法签名
- [消息 API（下）](reference/api/1b_message_api.md) — 消息发送续篇
- [群管理 API](reference/api/2_manage_api.md) — 群管理方法签名
- [信息查询与支持 API](reference/api/3_info_support_api.md) — 查询 / 文件操作方法签名

#### events/ — 事件类型

- [事件类层级详解](reference/events/1_event_classes.md) — BaseEvent / MessageEvent / NoticeEvent / RequestEvent

#### types/ — 数据类型

- [消息段类型](reference/types/1_segments.md) — Text / Image / At / Reply / Face / ...
- [MessageArray](reference/types/2_message_array.md) — 消息容器完整 API

#### core/ — 核心模块

- [核心内部](reference/core/1_internals.md) — BotClient / Registry / Dispatcher / Hook / EventStream

#### plugin/ — 插件系统

- [基类详解](reference/plugin/1_base_class.md) — BasePlugin / NcatBotPlugin
- [Mixin 详解](reference/plugin/2_mixins.md) — ConfigMixin / DataMixin / RBACMixin / TimeTaskMixin / ...

#### services/ — 服务层

- [RBAC 服务](reference/services/1_rbac_service.md) — 角色权限访问控制
- [配置/定时任务服务](reference/services/2_config_task_service.md) — TimeTask / FileWatcher / ConfigService

#### adapter/ — 适配器

- [连接管理](reference/adapter/1_connection.md) — WebSocket 连接与重连策略
- [协议解析](reference/adapter/2_protocol.md) — OneBot v11 协议解析与事件转换

#### utils/ — 工具模块

- [IO 与日志（上）](reference/utils/1a_io_logging.md) — 日志器、文件读写
- [IO 与日志（下）](reference/utils/1b_io_logging.md) — 网络请求、下载工具
- [装饰器与杂项](reference/utils/2_decorators_misc.md) — 装饰器、辅助函数

#### testing/ — 测试框架

- [TestHarness](reference/testing/1_harness.md) — TestHarness / PluginTestHarness API
- [工厂/Scenario/Mock](reference/testing/2_factory_scenario_mock.md) — 事件工厂、Scenario 构建器、MockBotAPI

---

### contributing/ — 贡献指南

| 目录 | 说明 | 篇数 |
|------|------|------|
| [development_setup/](contributing/development_setup/) | 开发环境搭建 | 1 |
| [design_decisions/](contributing/design_decisions/) | 设计决策记录（ADR） | 2 |
| [module_internals/](contributing/module_internals/) | 模块内部实现详解 | 4 |

#### development_setup/ — 开发环境

- [高级配置](contributing/development_setup/1_advanced.md) — IDE 配置、调试、代码规范

#### design_decisions/ — 设计决策

- [架构决策](contributing/design_decisions/1_architecture.md) — 分层架构、适配器模式
- [实现决策](contributing/design_decisions/2_implementation.md) — Dispatcher、Hook、热重载

#### module_internals/ — 模块内部实现

- [核心模块实现（上）](contributing/module_internals/1a_core_modules.md) — WebSocket / Dispatcher / Registry
- [核心模块实现（下）](contributing/module_internals/1b_core_modules.md) — Hook / EventStream / 拓扑排序
- [插件与服务模块实现（上）](contributing/module_internals/2a_plugin_service_modules.md) — 插件加载器 / 热重载
- [插件与服务模块实现（下）](contributing/module_internals/2b_plugin_service_modules.md) — RBAC Trie / 定时任务

---

## 推荐阅读路径

| 我想… | 路径 |
|-------|------|
| **开发一个插件** | [guide/plugin/](guide/plugin/) → [guide/api_usage/](guide/api_usage/) |
| **发送各种消息** | [guide/send_message/](guide/send_message/) |
| **查 API 签名** | [reference/api/](reference/api/) |
| **了解权限控制** | [guide/rbac/](guide/rbac/) → [reference/services/](reference/services/) |
| **为插件编写测试** | [guide/testing/](guide/testing/) → [reference/testing/](reference/testing/) |
| **参与贡献** | [contributing/](contributing/) |
| **配置 Bot** | [guide/configuration/](guide/configuration/) |
| **贡献代码** | [contributing/development_setup/](contributing/development_setup/) → [architecture.md](architecture.md) → [contributing/design_decisions/](contributing/design_decisions/) |
| **理解内部实现** | [architecture.md](architecture.md) → [contributing/module_internals/](contributing/module_internals/) |
