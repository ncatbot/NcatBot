# RBAC 权限管理

> NcatBot 内置基于角色的访问控制（RBAC）服务，为插件提供细粒度的权限管理能力。

---

## Quick Start

只需 3 步即可为你的插件添加权限控制：**注册权限 → 配置角色 → 检查权限**。

### 1. 在插件中注册权限并检查

```python
from ncatbot.core.registry import registrar
from ncatbot.event import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin


class MyPlugin(NcatBotPlugin):
    name = "my_plugin"
    version = "1.0.0"

    async def on_load(self):
        # 注册权限路径
        self.add_permission("my_plugin.admin")
        self.add_permission("my_plugin.user")

        # 创建角色并分配权限
        self.add_role("my_plugin_admin", exist_ok=True)
        self.add_role("my_plugin_user", exist_ok=True)
        if self.rbac:
            self.rbac.grant("role", "my_plugin_admin", "my_plugin.admin")
            self.rbac.grant("role", "my_plugin_admin", "my_plugin.user")
            self.rbac.grant("role", "my_plugin_user", "my_plugin.user")

    @registrar.on_group_command("管理命令")
    async def on_admin_cmd(self, event: GroupMessageEvent):
        uid = str(event.user_id)
        if self.check_permission(uid, "my_plugin.admin"):
            await event.reply("管理命令执行成功")
        else:
            await event.reply("你没有执行此命令的权限")
```

### 2. 在 `data/rbac.json` 中配置角色与用户

```json
{
  "roles": {
    "my_plugin_admin": {
      "whitelist": ["my_plugin.admin", "my_plugin.user"],
      "blacklist": []
    },
    "my_plugin_user": {
      "whitelist": ["my_plugin.user"],
      "blacklist": []
    }
  },
  "users": {
    "12345678": {
      "whitelist": [],
      "blacklist": [],
      "roles": ["my_plugin_admin"]
    }
  }
}
```

### 3. 权限判定规则

```
黑名单命中 → ❌ 拒绝
白名单命中 → ✅ 允许
都不命中   → ❌ 拒绝（默认拒绝）
```

> 黑名单优先级始终高于白名单。即使用户通过角色获得了某权限，只要该权限出现在黑名单中，检查结果仍为 `False`。

---

## 权限模型速查

### 三层模型

```
用户 ──拥有──▶ 角色 ──包含──▶ 权限
```

- **用户** 不直接绑定权限，而是关联到角色
- **角色** 持有白名单 / 黑名单两个权限集
- 角色支持 **继承**：子角色聚合所有父角色的权限

### 权限路径格式

点分隔的层级格式：`<命名空间>.<模块>.<操作>`

| 路径 | 含义 |
|---|---|
| `rbac.admin` | RBAC 系统管理权限 |
| `rbac.user` | RBAC 系统普通用户权限 |
| `my_plugin.feature.edit` | 自定义插件的编辑功能权限 |

通配符（用于权限检查，不可用于注册）：

| 通配符 | 含义 | 示例 |
|---|---|---|
| `*` | 匹配 **单层** 任意节点 | `plugin.*.read` 匹配 `plugin.foo.read` |
| `**` | 匹配 **任意深度** | `plugin.**` 匹配 `plugin.foo.bar.baz` |

### 内置角色与权限矩阵

NcatBot 默认的 `data/rbac.json` 包含以下内置角色：

| 角色 | 白名单权限 | 黑名单权限 | 说明 |
|---|---|---|---|
| `rbac_admin` | `rbac.admin`、`rbac.user` | —— | RBAC 管理员，拥有系统管理和用户权限 |
| `rbac_user` | `rbac.user` | —— | RBAC 普通用户，仅拥有用户权限 |

内置权限路径：

| 权限路径 | 说明 |
|---|---|
| `rbac.admin` | RBAC 系统管理权限 |
| `rbac.user` | RBAC 系统普通用户权限 |

### 权限检查方法签名

| 方法 | 签名 | 说明 |
|---|---|---|
| `PermissionChecker.check` | `(user: str, permission: str, create_user: bool = True) -> bool` | 核心检查方法 |
| `RBACMixin.check_permission` | `(user: str, permission: str) -> bool` | 插件高层封装，服务不可用时返回 `False` |
| `RBACService.check` | `(user: str, permission: str, create_user: bool = True) -> bool` | 服务层检查方法 |

检查流程：

1. 用户不存在 → 自动创建（`create_user=True`）或抛出 `ValueError`
2. 收集用户自身 + 所有角色（含继承）的权限
3. 黑名单匹配 → `False`
4. 白名单匹配 → `True`
5. 都不匹配 → `False`

---

## RBACMixin API

`NcatBotPlugin` 已内置 `RBACMixin`，插件可直接使用以下高层 API：

| 方法 | 签名 | 说明 |
|---|---|---|
| `rbac` | `@property → Optional[RBACService]` | 获取 RBAC 服务实例 |
| `check_permission` | `(user: str, permission: str) -> bool` | 检查用户权限，服务不可用时返回 `False` |
| `add_permission` | `(path: str) -> None` | 注册权限路径 |
| `remove_permission` | `(path: str) -> None` | 移除权限路径 |
| `add_role` | `(role: str, exist_ok: bool = True) -> None` | 创建角色 |
| `user_has_role` | `(user: str, role: str) -> bool` | 检查用户是否拥有指定角色 |

> `RBACMixin` 方法内部会检查 RBAC 服务是否可用。服务不可用时，`check_permission` 返回 `False`，其他方法静默忽略。

需要更精细的控制时，可通过 `self.rbac` 直接操作底层 `RBACService`：

```python
if self.rbac:
    # 授予权限到白名单
    self.rbac.grant("user", user_id, "my_plugin.vip", mode="white")

    # 将权限加入黑名单（显式拒绝）
    self.rbac.grant("user", user_id, "my_plugin.dangerous", mode="black")

    # 撤销权限（同时从白名单和黑名单中移除）
    self.rbac.revoke("user", user_id, "my_plugin.vip")

    # 设置角色继承
    self.rbac.set_role_inheritance("my_plugin_admin", "my_plugin_user")

    # 直接检查权限
    result = self.rbac.check(user_id, "my_plugin.admin")
```

---

## 深入阅读

| 文档 | 内容 |
|---|---|
| [RBAC 模型详解](1_model.md) | 三层模型、权限路径体系、Trie 树、通配符、rbac.json 完整格式、角色继承、权限命名规范 |
| [RBAC 核心模块与插件集成](2a_integration.md) | EntityManager / PermissionAssigner / PermissionChecker 核心模块详解与 RBACMixin 插件集成 |
| [RBACService API 与高级用法](2b_integration.md) | RBACService 完整 API、层级权限设计与默认权限策略 |
| [示例代码](../../../examples/07_rbac/main.py) | 完整 RBAC 插件示例 |

---

> **相关文档**：[架构总览](../../architecture.md) · [插件开发指南](../plugin/)
