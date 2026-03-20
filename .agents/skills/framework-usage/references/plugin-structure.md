# 插件结构与验证参考

## 目录结构

```python
plugins/my_plugin/
├── manifest.toml    # 必须
├── main.py          # 入口文件
├── config.yaml      # 可选：默认配置
└── ...              # 其他辅助模块
```

## manifest.toml 完整格式

> 参考文档：`guide/3. 插件开发/2. 插件结构.md`、`reference/5. 插件系统/1. 基类.md` § 3-pluginmanifest

```toml
# ⚠️ 必填字段必须放在 TOML 顶层，不能放在任何 [section] 下
name = "my_plugin"          # 唯一标识符，小写+下划线
version = "1.0.0"           # SemVer 版本号
main = "main.py"            # 入口文件名
entry_class = "MyPlugin"    # 入口类名（可省略，自动发现）
author = "Author"
description = "插件说明"

[dependencies]
# other_plugin = ">=1.0.0"

[pip_dependencies]
# aiohttp = ">=3.8.0"
```

**规则**：
- `name` 须为合法 Python 标识符（小写字母+下划线）
- `version` 须为合法 SemVer
- `main` 指定的文件必须存在于同目录下
- `[dependencies]` 版本约束符合 PEP 440
- `[pip_dependencies]` 包名不可用 URL 或本地路径

## 基类选择

> 参考文档：`reference/5. 插件系统/1. 基类.md`

| 基类 | 适用场景 | 继承链 |
|------|---------|--------|
| `NcatBotPlugin` | **推荐**，含全部 Mixin | BasePlugin + 5 Mixin |
| `BasePlugin` | 极简插件 | 仅生命周期 |

## 生命周期

> 参考文档：`guide/3. 插件开发/3. 生命周期.md`

```python
async def on_load(self):
    """加载时：初始化配置、数据、定时任务"""
    if self.get_config("welcome_msg") is None:
        self.set_config("welcome_msg", "欢迎！")
    self.data.setdefault("counter", 0)
    self.add_permission("my_plugin.admin")
    self.add_scheduled_task("daily_report", "08:00")

async def on_close(self):
    """卸载时：清理资源、取消后台 task"""
    pass
```

**顺序**：加载 `_init_()` → Mixin `_mixin_load()` → `on_load()` | 卸载 `_close_()` → `on_close()` → Mixin `_mixin_unload()`

## 验证清单

### manifest.toml
- [ ] `name` 存在且为合法 Python 标识符
- [ ] `version` 存在且为合法 SemVer
- [ ] `main` 指定的文件存在于同目录
- [ ] `entry_class`（如指定）在 main 文件中存在

### 入口类
- [ ] 继承 `NcatBotPlugin` 或 `BasePlugin`
- [ ] `name`/`version` 类属性与 manifest 一致
- [ ] 如省略 `entry_class`，模块中只能有一个 BasePlugin 子类

### Handler
- [ ] 所有 handler 是 `async def`
- [ ] 第一个参数 `self`，第二个参数事件对象
- [ ] import `registrar`：`from ncatbot.core import registrar`
- [ ] `@registrar.on_group_command()` 命令参数非空

### 生命周期
- [ ] `on_load()`/`on_close()` 是 `async def`
- [ ] `on_load()` 不阻塞（不用 `time.sleep()`）
- [ ] `on_close()` 取消所有后台 task

### Mixin 使用
- [ ] `self.data` 用 `setdefault()` 初始化
- [ ] `check_permission(uid, path)` 的 `uid` 为 string
- [ ] 使用 RBAC 前检查 `self.rbac is not None`
- [ ] `add_scheduled_task(name)` 的 name 与回调方法名一致

## 冒烟测试

```python
from pathlib import Path
from ncatbot.testing import PluginTestHarness

async with PluginTestHarness(
    plugin_names=["my_plugin"],
    plugin_dir=Path("plugins"),
) as h:
    assert "my_plugin" in h.loaded_plugins
    plugin = h.get_plugin("my_plugin")
    assert plugin is not None
```
