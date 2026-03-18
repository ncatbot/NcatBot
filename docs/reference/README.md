# API 参考

> 所有模块的完整 API 参考文档

---

## Quick Reference

### 按需查找

| 你在找… | 去这里 | 关键类/模块 |
|---------|--------|------------|
| 消息发送方法签名 | [api/](api/) | `QQMessaging`, `QQMessageSugarMixin` |
| 群管理/好友/账号操作 | [api/](api/) | `QQManage` |
| 信息查询（群/好友/消息） | [api/](api/) | `QQQuery` |
| 文件上传/下载 | [api/](api/) | `QQFile` |
| 事件类型和属性 | [events/](events/) | `GroupMessageEvent`, `NoticeEvent`, `RequestEvent` |
| 消息段类型（PlainText/At/Image） | [types/](types/) | `MessageSegment`, `MessageArray` |
| 装饰器注册和 Hook | [core/](core/) | `Registrar`, `Hook`, `HookStage` |
| Predicate DSL | [core/](core/) | `same_user`, `has_keyword`, `msg_matches` |
| 插件基类和 Mixin | [plugin/](plugin/) | `NcatBotPlugin`, `ConfigMixin`, `EventMixin` |
| RBAC/定时任务服务 | [services/](services/) | `RBACService`, `TimeTaskService` |
| 适配器接口 | [adapter/](adapter/) | `BaseAdapter`, `AdapterRegistry` |
| 日志/网络/配置工具 | [utils/](utils/) | `get_log`, `ConfigManager`, `post_json` |
| 测试框架 | [testing/](testing/) | `PluginTestHarness`, `Scenario` |
| CLI 命令 | [cli.md](cli.md) | `ncatbot init/run/dev` |

---

## 模块索引

| 目录 | 说明 |
|------|------|
| [api/](api/) | Bot API 方法参考 |
| [events/](events/) | 事件类型参考 |
| [types/](types/) | 数据类型参考（消息段、MessageArray） |
| [core/](core/) | 核心模块参考（Dispatcher、Predicate DSL、Registry / Hook） |
| [plugin/](plugin/) | 插件系统参考（基类、Mixin） |
| [services/](services/) | 服务层参考（RBAC、定时任务、配置存储） |
| [adapter/](adapter/) | 适配器参考（WebSocket、协议处理） |
| [utils/](utils/) | 工具模块参考（日志、IO、装饰器） |
| [cli.md](cli.md) | CLI 命令参考（全部命令签名与参数） |
| [testing/](testing/) | 测试框架参考（TestHarness、事件工厂、Mock） |

---

## 交叉引用

| 如果你在找… | 去这里 |
|------------|--------|
| 插件开发教程 | [guide/plugin/](../guide/plugin/) |
| 消息发送教程 | [guide/send_message/](../guide/send_message/) |
| 插件测试教程 | [guide/testing/](../guide/testing/) |
| CLI 命令用法 | [guide/cli/](../guide/cli/) |
| 设计决策（为什么这样设计） | [contributing/design_decisions/](../contributing/design_decisions/) |
| 模块内部实现细节 | [contributing/module_internals/](../contributing/module_internals/) |
