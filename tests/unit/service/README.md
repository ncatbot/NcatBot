# Service 模块测试

源码模块: `ncatbot.service`

## 测试文件对应

| 测试文件 | 覆盖范围 |
|----------|----------|
| `test_service_manager.py` | `ServiceManager`（SM-01～SM-08 及补充） |
| `test_file_watcher.py` | `FileWatcherService`（FW-01） |
| `test_rbac.py` | RBAC 子系统（SC-01～SC-12） |
| `test_schedule_parser.py` | `TimeTaskParser`（TS-01～TS-06） |
| `test_time_task_service.py` | `TimeTaskService`（TT-01） |

## 验证规范

### ServiceManager (`test_service_manager.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| SM-01 | `register()` | 注册服务类到管理器 |
| SM-02 | `load()` | 加载并返回服务实例 |
| SM-02 补充 | `load()` 边界 | 未注册服务抛出 `KeyError`；已加载则幂等返回同一实例 |
| SM-03 | `load_all()` | 按拓扑排序加载所有已注册服务 |
| SM-04 | 循环依赖检测 | 循环依赖抛出 `ValueError` |
| SM-05 | `close_all()` | 关闭所有已加载服务 |
| SM-06 | `get()` | 返回已加载的服务实例 |
| SM-06 补充 | `get()` 边界 | 未加载的服务返回 `None` |
| SM-07 | `has()` | 判断服务是否已加载 |
| SM-08 | `register_builtin()` | 注册内置服务（含 `rbac`、`file_watcher`、`time_task`） |

### FileWatcherService (`test_file_watcher.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| FW-01 | 插件目录变更与热重载 | `effective_hot_reload()` 为真时，即使 `debug` 为假仍对待处理插件目录计数；`hot_reload` 为假时不记录变更 |

### RBAC (`test_rbac.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| SC-01 | `PermissionTrie` | `add` 多段路径后 `exists` 精确匹配 |
| SC-02 | 通配符 | `*` 匹配单层，`**` 匹配任意深度 |
| SC-03 | `remove` | 移除路径后 `exists` 为假 |
| SC-04 | 路径约束 | `add` 时拒绝含通配符的路径（`ValueError`） |
| SC-05 | 角色继承链 | `set_role_inheritance` 链式继承后 `user_has_role` 递归成立 |
| SC-06 | 循环检测 | 角色继承形成环时抛出 `ValueError`（循环继承） |
| SC-07 | `remove_role` 级联 | 删除角色时清理用户角色列表与继承关系 |
| SC-08 | 分配一致性 | `assign_role` / `unassign_role` 与用户、角色双向索引一致 |
| SC-09 | 白名单授权 | `grant` 白名单后 `check` 通过 |
| SC-10 | 黑名单授权 | `grant` 黑名单后 `check` 拒绝 |
| SC-11 | 黑白名单互斥 | 黑名单授权时从白名单移除同一权限 |
| SC-12 | 继承传递权限 | 用户通过继承链获得下游角色的授权 |

### TimeTaskParser (`test_schedule_parser.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| TS-01 | 一次性时间 | `YYYY-MM-DD HH:MM:SS` → `type=once`，`value` 为正浮点 |
| TS-02 | 每日时间 | `HH:MM` → `type=daily`，`value` 为时间字符串 |
| TS-03 | 秒间隔 | `Ns`（如 `120s`）→ `type=interval`，`value` 为秒数 |
| TS-04 | 冒号间隔 | `HH:MM:SS` 样式 → 换算为总秒数（如 `00:02:30` → 9000） |
| TS-05 | 中文间隔 | 如 `2天3小时5秒` → 总秒数 |
| TS-06 | 无效格式 | 无法解析时抛出 `ValueError`（匹配「无效的时间格式」） |

### TimeTaskService (`test_time_task_service.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| TT-01 | 同时到期任务派发 | 不同插件在同一时间点触发时，慢任务不会阻塞快任务启动 |
