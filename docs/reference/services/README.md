# 服务层参考

> RBAC / 定时任务 / 文件监控等服务组件参考。服务层位于 `ncatbot/service/`，与插件系统解耦，由 `ServiceManager` 统一编排。

---

## Quick Reference

```python
from ncatbot.service import ServiceManager, BaseService
```

### BaseService 接口

| 属性/方法 | 签名 | 说明 |
|-----------|------|------|
| `name` | `str` | 服务名称（子类必须定义） |
| `description` | `str` | 服务描述 |
| `dependencies` | `list` | 依赖的其他服务名称 |
| `on_load` | `async () → None` | *abstract* — 加载回调 |
| `on_close` | `async () → None` | *abstract* — 关闭回调 |
| `is_loaded` | `@property → bool` | 是否已加载 |
| `emit_event` | `Optional[EventCallback]` | 事件发布回调（框架注入） |

### ServiceManager 方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `register_builtin` | `(*, debug=False) → None` | 注册所有内置服务 |
| `register` | `(service_class, **config) → None` | 注册自定义服务类 |
| `load` | `async (service_name) → BaseService` | 加载单个服务（含依赖注入） |
| `load_all` | `async () → None` | 按拓扑排序加载所有服务 |
| `unload` | `async (service_name) → None` | 卸载指定服务 |
| `close_all` | `async () → None` | 关闭所有已加载服务 |
| `get` | `(service_name) → Optional[BaseService]` | 获取已加载的服务实例 |
| `has` | `(service_name) → bool` | 检查服务是否已加载 |
| `list_services` | `() → List[str]` | 列出已加载服务名称 |
| `set_event_callback` | `(callback) → None` | 注入事件发布回调 |

### 快捷属性（ServiceManager）

| 属性 | 类型 | 说明 |
|------|------|------|
| `manager.rbac` | `RBACService` | RBAC 权限服务 |
| `manager.time_task` | `TimeTaskService` | 定时任务服务 |
| `manager.file_watcher` | `FileWatcherService` | 文件监控服务 |

### RBACService 核心方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `check` | `(user, permission, create_user=True) → bool` | 检查用户权限 |
| `grant` | `(target_type, target, permission, mode="white") → None` | 授予权限 |
| `revoke` | `(target_type, target, permission) → None` | 撤销权限 |
| `add_role` | `(role, exist_ok=False) → None` | 创建角色 |
| `assign_role` | `("user", user, role) → None` | 分配角色 |
| `add_permission` | `(path) → None` | 注册权限路径 |
| `save` | `(path=None) → None` | 持久化 RBAC 数据 |

### TimeTaskService 核心方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `add_job` | `(name, interval, callback, conditions=None, max_runs=None) → bool` | 添加定时任务 |
| `remove_job` | `(name) → bool` | 移除任务 |
| `get_job_status` | `(name) → Optional[Dict]` | 获取任务状态 |
| `list_jobs` | `() → List[str]` | 列出所有任务 |
| `is_running` | `@property → bool` | 调度器运行状态 |
| `job_count` | `@property → int` | 当前任务数量 |

---

## 本目录索引

| 文件 | 说明 |
|------|------|
| [1_rbac_service.md](1_rbac_service.md) | RBACService — 权限路径、角色管理、权限分配与检查、持久化 |
| [2_config_task_service.md](2_config_task_service.md) | TimeTaskService / FileWatcherService 详解 + 服务交互流程 |
