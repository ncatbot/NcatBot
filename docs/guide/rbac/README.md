# RBAC 权限管理

> NcatBot 内置基于角色的访问控制（RBAC）服务，为插件提供细粒度的权限管理能力。

---

## Quick Reference

3 步为插件添加权限控制：**注册权限 → 配置角色 → 检查权限**。

### RBACMixin 方法

| 方法 | 说明 |
|------|------|
| `add_permission(path)` | 注册权限路径（如 `"my_plugin.admin"`） |
| `remove_permission(path)` | 移除权限路径 |
| `check_permission(user, permission)` | 检查用户是否有权限 → `bool` |
| `add_role(role, exist_ok=True)` | 创建角色 |
| `user_has_role(user, role)` | 检查用户角色归属 |
| `self.rbac` | 访问底层 `RBACService` 实例 |

### RBACService 底层操作

| 方法 | 说明 |
|------|------|
| `rbac.grant("role", role_name, permission)` | 给角色授权 |
| `rbac.revoke("role", role_name, permission)` | 撤销角色权限 |
| `rbac.grant("user", user_id, role=role_name)` | 给用户分配角色 |
| `rbac.check(user_id, permission)` | 检查权限 |

### 权限路径格式

- 使用点分层级：`"plugin_name.action"`，如 `"weather.query"`、`"admin.ban"`
- 通配符 `"*"` 匹配同级所有权限
- 基于 Trie 树实现，层级路径自动继承

### 典型流程

```python
async def on_load(self):
    self.add_permission("my_plugin.admin")
    self.add_role("my_plugin_admin")
    self.rbac.grant("role", "my_plugin_admin", "my_plugin.admin")

@registrar.on_group_command("管理命令")
async def on_admin_cmd(self, event: GroupMessageEvent):
    if self.check_permission(str(event.user_id), "my_plugin.admin"):
        await event.reply(text="执行成功")
```

---

## 本目录索引

| 文档 | 内容 |
|------|------|
| [RBAC 模型详解](1_model.md) | 三层模型、权限路径、Trie 树、通配符、rbac.json 格式、角色继承 |
| [RBAC 插件集成](2.integration.md) | RBACMixin API、RBACService 底层操作、层级权限与默认策略 |
