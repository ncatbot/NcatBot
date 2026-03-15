# API 参考

> 所有模块的完整 API 参考文档

---

## 模块索引

| 目录 | 说明 |
|------|------|
| [api/](api/) | Bot API 方法参考 |
| [events/](events/) | 事件类型参考 |
| [types/](types/) | 数据类型参考（消息段、MessageArray） |
| [core/](core/) | 核心模块参考（BotClient、Registry、Dispatcher） |
| [plugin/](plugin/) | 插件系统参考（基类、Mixin） |
| [services/](services/) | 服务层参考（RBAC、定时任务、配置存储） |
| [adapter/](adapter/) | 适配器参考（WebSocket、协议处理） |
| [utils/](utils/) | 工具模块参考（日志、IO、装饰器） |
| [testing/](testing/) | 测试框架参考（TestHarness、事件工厂、Mock） |

---

## api/ — Bot API 方法

Bot 可调用的所有 API 方法签名，按功能分类：

- 消息发送（send_private_msg / send_group_msg / ...）
- 群管理（set_group_kick / set_group_ban / ...）
- 信息查询（get_login_info / get_stranger_info / ...）
- 文件操作（upload_group_file / get_group_file_url / ...）

> 旧版单文件参考：[api.md](api.md)

---

## events/ — 事件类型

所有事件实体的字段定义与继承关系：

- **BaseEvent** — 事件基类
- **MessageEvent** — 消息事件（私聊 / 群聊）
- **NoticeEvent** — 通知事件（群成员变动、撤回等）
- **RequestEvent** — 请求事件（加好友、加群请求）

> 旧版单文件参考：[events.md](events.md)

---

## types/ — 数据类型

消息段类型、枚举值、Pydantic 数据模型：

- **消息段** — Text / Image / At / Reply / Face / ...
- **MessageArray** — 消息容器，链式构造
- **枚举** — 事件类型、消息类型、角色类型等

> 旧版单文件参考：[types.md](types.md)

---

## core/ — 核心模块

框架核心引擎：

- **BotClient** — 机器人客户端，入口与生命周期管理
- **Registry** — 处理器注册表，路由映射
- **Dispatcher** — 事件分发器，匹配 → 排序 → 派发
- **Hook** — 钩子链管理，中间件执行
- **EventStream** — 事件流，异步队列

> 旧版单文件参考：[core.md](core.md)

---

## plugin/ — 插件系统

插件基类与扩展体系：

- **BasePlugin** — 插件抽象基类
- **NcatBotPlugin** — 标准插件基类（包含全部 Mixin）
- **Mixin 体系** — ConfigMixin / DataMixin / RBACMixin / TimeTaskMixin / ...
- **Manifest** — 插件描述文件解析
- **Loader** — 插件加载器与热重载

> 旧版单文件参考：[plugin.md](plugin.md)

---

## services/ — 服务层

可注入的服务组件：

- **ServiceManager** — 服务容器与生命周期
- **RBAC** — 角色权限访问控制
- **TimeTask** — 定时任务调度
- **FileWatcher** — 文件监听（热重载）

> 旧版单文件参考：[services.md](services.md)

---

## adapter/ — 适配器

协议适配层：

- **BaseAdapter** — 适配器抽象基类
- **NapCatAdapter** — NapCat WebSocket 适配器
- **MockAdapter** — 测试用模拟适配器

> 旧版单文件参考：[adapter.md](adapter.md)

---

## utils/ — 工具模块

通用工具集：

- **ConfigManager** — 配置文件读写
- **Logger** — 日志系统
- **Network** — 网络请求封装
- **IO** — 文件 IO 工具
- **Decorators** — 通用装饰器

> 旧版单文件参考：[utils.md](utils.md)

---

## testing/ — 测试框架

插件测试工具集：

- **TestHarness** — 测试编排器（BotClient + MockAdapter）
- **PluginTestHarness** — 插件选择性加载测试
- **Scenario** — 链式场景构建器
- **Factory** — 事件工厂（8 种事件类型）
- **MockBotAPI** — API 调用记录与响应配置

---

## 交叉引用

| 如果你在找… | 去这里 |
|------------|--------|
| 插件开发教程 | [guide/plugin/](../guide/plugin/) |
| 消息发送教程 | [guide/send_message/](../guide/send_message/) |
| 插件测试教程 | [guide/testing/](../guide/testing/) |
| 设计决策（为什么这样设计） | [contributing/design_decisions/](../contributing/design_decisions/) |
| 模块内部实现细节 | [contributing/module_internals/](../contributing/module_internals/) |
