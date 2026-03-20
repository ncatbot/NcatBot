# 问题症状 → 文档速查表

根据用户描述的**症状或关键词**，快速定位应首先查阅的文档。

## 症状速查表

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

## 多症状并发

按事件处理链路（adapter → event → dispatcher → registry → handler）逐步排查，找到第一个偏离预期的环节。
