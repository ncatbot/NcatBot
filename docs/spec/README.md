# NcatBot 架构规范（v5.0）

> 本规范是 NcatBot v5.0 架构重设计的权威文档，采用**规范驱动开发**模式：先定义规范，再按规范实施。
>
> 所有代码变更必须符合本规范。规范变更需经过 Review 后方可更新。

## 规范文档目录

| 编号 | 文档 | 说明 | 状态 |
|------|------|------|------|
| SPEC-00 | [架构总则](./00-架构总则.md) | 四层架构模型、层间依赖规则、目录结构 | 📝 Draft |
| SPEC-01 | [Adapter 规范](./01-Adapter规范.md) | BaseAdapter 接口、职责边界、注册机制、NapCat 实现要求 | 📝 Draft |
| SPEC-02 | [Service 规范](./02-Service规范.md) | 准入标准、BaseService 接口、ServiceManager 精简、内置服务清单 | 📝 Draft |
| SPEC-03 | [Registry 规范](./03-Registry规范.md) | RegistryEngine 定位、与 EventBus 集成、命令/过滤器生命周期 | 📝 Draft |
| SPEC-04 | [API 抽象接口规范](./04-API抽象接口规范.md) | IBotAPI 接口定义、APIComponent 基类、事件上下文绑定 | 📝 Draft |
| SPEC-05 | [Event 标准模型规范](./05-Event标准模型规范.md) | 标准事件体系、Adapter 转换契约、ContextMixin 改造 | 📝 Draft |
| SPEC-06 | [生命周期规范](./06-生命周期规范.md) | 启动流程、关闭流程、事件流、API 调用流 | 📝 Draft |
| SPEC-07 | [迁移计划](./07-迁移计划.md) | 组件迁移映射、分阶段实施路线、验证标准 | 📝 Draft |

## 核心设计决策

| 决策 | 结论 |
|------|------|
| 多平台支持 | 内外分离，外部平台扩展抽象化（含环境安装、通信） |
| unified_registry 归属 | 提升到 Core 层，作为 RegistryEngine |
| API 层 | 引入 IBotAPI 抽象接口，Adapter 负责映射 |
| Service 层 | 重新定义概念和边界，仅保留平台无关的内部服务 |
| Event 模型 | 当前模型作为标准，Adapter 负责协议到标准模型的转换 |
| 向后兼容 | 允许破坏性变更 |
| Adapter 粒度 | 完整平台适配（环境部署 + 认证 + 连接 + 协议 + API 映射） |

## 术语表

| 术语 | 定义 |
|------|------|
| **Adapter** | 平台适配器，封装与外部平台的全部交互 |
| **Service** | 平台无关的、可选的、有状态的内部能力提供者 |
| **RegistryEngine** | 命令/过滤器/事件处理器的统一注册与执行引擎 |
| **IBotAPI** | 与协议无关的 Bot 操作抽象接口 |
| **EventBus** | 发布-订阅模式的事件分发中心 |
| **NcatBotEvent** | 框架内部的事件包装对象 |
| **BaseEvent** | 标准事件模型基类（MessageEvent 等的父类） |
