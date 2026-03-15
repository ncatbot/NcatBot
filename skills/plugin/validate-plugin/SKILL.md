# validate-plugin — 验证 NcatBot 插件规范

## 触发条件

当用户要求检查插件是否符合规范、验证插件结构、或排查插件加载问题时，使用此技能。

## 验证清单

### 1. manifest.toml 格式

> 参考文档：[guide/plugin/2.structure.md](docs/guide/plugin/2.structure.md), [reference/plugin/1_base_class.md](docs/reference/plugin/1_base_class.md#3-pluginmanifest)

```toml
# 必填字段
[plugin]
name = "my_plugin"          # 唯一标识符，小写+下划线
version = "1.0.0"           # SemVer 版本号
main = "main.py"            # 入口文件名
author = "Author"           # 作者
description = "描述"        # 插件说明

# 可选: 入口类名（省略则自动发现）
entry_class = "MyPlugin"

# 可选: 插件间依赖
[dependencies]
base_plugin = ">=1.0.0,<2.0"

# 可选: pip 依赖
[pip_dependencies]
aiohttp = ">=3.8.0"
```

**检查项**:
- [ ] `name` 存在且为合法 Python 标识符
- [ ] `version` 存在且为合法 SemVer
- [ ] `main` 指定的文件存在于同目录下
- [ ] `entry_class`（如指定）在 main 文件中存在
- [ ] `[dependencies]` 中的约束符合 PEP 440
- [ ] `[pip_dependencies]` 中包名合法（无 URL/本地路径）

### 2. 入口类验证

> 参考文档：[guide/plugin/1.quick-start.md](docs/guide/plugin/1.quick-start.md), [reference/plugin/1_base_class.md](docs/reference/plugin/1_base_class.md)

```python
# 正确: 继承 NcatBotPlugin
from ncatbot.plugin import NcatBotPlugin

class MyPlugin(NcatBotPlugin):
    name = "my_plugin"       # 应与 manifest.toml 一致
    version = "1.0.0"        # 应与 manifest.toml 一致
```

**检查项**:
- [ ] 入口类继承自 `NcatBotPlugin`（或 `BasePlugin`）
- [ ] 类属性 `name` 与 manifest 中的 `name` 一致
- [ ] 类属性 `version` 与 manifest 中的 `version` 一致

### 3. Handler 注册

> 参考文档：[guide/plugin/4a.event-registration.md](docs/guide/plugin/4a.event-registration.md)

```python
from ncatbot.core.registry import registrar

class MyPlugin(NcatBotPlugin):
    @registrar.on_group_command("hello")
    async def on_hello(self, event: GroupMessageEvent):
        ...
```

**检查项**:
- [ ] 所有 handler 都是 `async def`（同步函数会被拒绝）
- [ ] handler 的第一个参数是 `self`（需要是方法而非独立函数）
- [ ] 使用正确的事件类型注解: `GroupMessageEvent`, `PrivateMessageEvent` 等
- [ ] `@registrar.on_group_command()` 命令参数非空
- [ ] import 了正确的 `registrar` 实例: `from ncatbot.core.registry import registrar`

### 4. 生命周期方法

> 参考文档：[guide/plugin/3a.loading.md](docs/guide/plugin/3a.loading.md), [reference/plugin/1_base_class.md](docs/reference/plugin/1_base_class.md#1-3-生命周期方法)

```python
async def on_load(self):    # 可选
    ...

async def on_close(self):   # 可选
    ...
```

**检查项**:
- [ ] `on_load()` 和 `on_close()` 都是 `async def`
- [ ] `on_load()` 中不要阻塞（避免 `time.sleep()`）
- [ ] `on_close()` 中取消所有后台 task（`asyncio.Task.cancel()`）
- [ ] 使用 `self.events()` 创建的事件流需要在 `on_close()` 中关闭

### 5. Mixin 使用规范

> 参考文档：[guide/plugin/5a.config-data.md](docs/guide/plugin/5a.config-data.md), [reference/plugin/2_mixins.md](docs/reference/plugin/2_mixins.md)

**ConfigMixin**:
- [ ] `self.get_config(key)` / `self.set_config(key, value)` 使用 string key
- [ ] 在 `on_load()` 中初始化默认配置

**DataMixin**:
- [ ] `self.data` 作为 dict 使用
- [ ] 在 `on_load()` 中用 `self.data.setdefault()` 初始化

**RBACMixin**:
- [ ] `self.add_permission(path)` 在 `on_load()` 中调用
- [ ] `self.check_permission(uid, path)` 的 `uid` 为 string 类型
- [ ] 检查 `self.rbac` 是否为 None（服务可能未启动）

**TimeTaskMixin**:
- [ ] `self.add_scheduled_task(name, interval)` 的 interval 格式正确
- [ ] 任务会在 `on_close()` 中自动清理

**EventMixin**:
- [ ] `async with self.events(type)` 必须在 async 上下文中
- [ ] 后台事件流 task 需要在 `on_close()` 中取消

### 6. 目录结构

```
my_plugin/
├── manifest.toml    # 必须
├── main.py          # 入口文件（可在 manifest 中指定其他名称）
├── config.yaml      # 可选: 默认配置（ConfigMixin 自动加载）
└── ...              # 其他辅助模块
```

## 验证执行

> 参考文档：[guide/testing/1.quick-start.md](docs/guide/testing/1.quick-start.md), [reference/testing/1_harness.md](docs/reference/testing/1_harness.md#plugintestharness)

使用 PluginTestHarness 做冒烟测试:

```python
from pathlib import Path
from ncatbot.testing import PluginTestHarness

async with PluginTestHarness(
    plugin_names=["my_plugin"],
    plugin_dir=Path("..."),
) as h:
    assert "my_plugin" in h.loaded_plugins
    plugin = h.get_plugin("my_plugin")
    assert plugin is not None
```

或使用自动发现批量验证（参见 [guide/testing/3.factory-scenario.md](docs/guide/testing/3.factory-scenario.md#4-自动冒烟测试)）：

```python
from ncatbot.testing import discover_testable_plugins, generate_smoke_tests

manifests = discover_testable_plugins(Path("plugins/"))
code = generate_smoke_tests(manifests)
Path("tests/test_smoke.py").write_text(code)
```

## 参考文档

- 插件快速入门: [docs/guide/plugin/1.quick-start.md](docs/guide/plugin/1.quick-start.md)
- 插件结构: [docs/guide/plugin/2.structure.md](docs/guide/plugin/2.structure.md)
- 插件基类参考: [docs/reference/plugin/1_base_class.md](docs/reference/plugin/1_base_class.md)
- Mixin 参考: [docs/reference/plugin/2_mixins.md](docs/reference/plugin/2_mixins.md)
- 测试指南: [docs/guide/testing/](docs/guide/testing/)
- 示例插件: [examples/](examples/)
