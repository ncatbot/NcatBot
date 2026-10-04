# 集成测试

跨模块协作的集成测试，验证多个组件协同工作。

## AI 视频生成 (`test_ai_video.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| AI-37 | 视频任务完整流程 | AIAdapter → BotAPIClient → 真实 LiteLLM → 模拟 HTTP；生成、查询、下载，ID 路由、认证和失败状态 |

## 公共 fixtures (`conftest.py`)

| Fixture | 说明 |
|---------|------|
| `harness` | 异步 fixture，提供 `TestHarness()` 实例；在 `async with` 生命周期内 yield，供依赖真实 harness 的用例使用 |

## 验证规范

### 事件管线 (`test_event_pipeline.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| I-01 | 全链路事件管线 | `Dispatcher` → `HandlerDispatcher` → handler 收到 `GroupMessageEvent` |
| I-01 补充 | handler 与 API | handler 内 `event.reply()` → `MockBotAPI` 记录 `post_group_array_msg` 调用 |
| I-22 | reply 经 sugar 层全链路 | `event.reply()` 经 `QQAPIClient` sugar 层 → `send_group_msg` 到 `MockBotAPI` |
| I-02 | 混合事件过滤 | 多类型事件混发；`message.group` handler 仅群消息；`message` handler 收到群+私聊 |
| I-03 | Hook 过滤 + 执行 | `MessageTypeFilter("group")` + `add_hooks` 在全链路中过滤私聊，仅群消息进入 handler |

### 插件生命周期 (`test_plugin_lifecycle.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| I-10 | Registrar → flush → HandlerDispatcher | `on()` 收集 → `flush_pending` → handler 可收事件 |
| I-11 | `revoke_plugin` 阻断 | 撤销后同插件 handler 不再触发 |
| I-12 | 多插件隔离 | 多插件 handler 各自触发；撤销一插件不影响另一插件 |
| I-13 | ContextVar 隔离 | 不同 `set_current_plugin` 上下文下 pending 分组独立 |

### 服务集成 (`test_service_integration.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| I-20 | 多服务加载顺序 | `ServiceManager.load_all()` 按依赖拓扑（如 `db` → `cache` → `app`） |
| I-21 | 服务关闭 | `close_all()` 关闭已加载服务，`has()` 为假 |


### 预览样板插件 (`test_preview_skeletons.py`)

对应文档中的端到端预览样板；插件目录为 `docs/docs/examples/common`（`COMMON_EXAMPLES`）。

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| PV-01a | `hello_world_common` 加载 | 插件出现在 `loaded_plugins` |
| PV-01b | `hello` 命令 | 群聊发 `hello` → 触发 `send_group_msg` |
| PV-01c | `hi` 命令 | 群聊发 `hi` → 触发 `send_group_msg` |
| PV-02a | `multi_step_dialog` 加载 | 插件出现在 `loaded_plugins` |
| PV-02b | 多步注册流 | `注册` → 名字 → 年龄 → `确认`；`data` 持久化姓名与年龄 |
| PV-02c | 注册中取消 | 注册流程中发 `取消` → 有回复 |
| PV-03a | `external_api` 加载 | 插件出现在 `loaded_plugins` |
| PV-03b | `api状态` 命令 | 发 `api状态` → `send_group_msg`（不依赖外网） |
| PV-04 | 外部事件 → 群通知 | `TestHarness` 手动注册 handler 模拟 webhook → `reply` → `send_group_msg` |
| PV-05a | 权限分支（允许） | 模拟管理员 `user_id` → 执行成功回复 |
| PV-05b | 权限分支（拒绝） | 普通用户 → 权限不足回复 |

### 在线状态 API (`test_online_status.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| I-23 | NapCat 必填参数 | 整数调用经 QQManage → NapCatBotAPI → OB11Protocol 自动携带 battery_status=0 |
| I-24 | 参数兼容 | 第三位置参数仍为 custom_status，battery_status 通过关键字指定 |
| I-25 | 枚举与整数兼容 | 六种基础状态序列化为协议整数，未枚举整数原样发送 |
| I-26 | Mock 契约一致 | Mock API 接受枚举、整数及关键字电量参数 |
