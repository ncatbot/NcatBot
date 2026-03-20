# 迁移验证清单

迁移完成后，按此清单逐项验证。

## 1. manifest.toml

- [ ] `manifest.toml` 存在于插件目录根下
- [ ] `name` 字段非空
- [ ] `version` 字段为合法 SemVer（如 `1.0.0`）
- [ ] `main` 字段指向存在的入口文件（通常 `main.py`）
- [ ] `entry_class` 字段与入口文件中的类名一致（可省略，自动发现）
- [ ] `[dependencies]` section 替代了原 `dependencies = {}` 类属性
- [ ] `pip_dependencies` 字段列出了所需的 PyPI 包（支持两种格式：数组 `pip_dependencies = ["requests"]` 或 TOML 表 `[pip_dependencies]`；推荐后者）

## 2. 导入路径

- [ ] 无 `from ncatbot.plugin_system` 的导入（→ `ncatbot.plugin`）
- [ ] 无 `from ncatbot.core import MessageEvent/Image/MessageArray`（→ `ncatbot.event` / `ncatbot.types`）
- [ ] 无 `from ncatbot.core.helper import ForwardConstructor`（→ `ncatbot.types.qq`）
- [ ] 无 `from ncatbot.core.event.message_segment import ...`（→ `ncatbot.types`）
- [ ] 已添加 `from ncatbot.core import registrar`
- [ ] 已添加需要的事件类型导入（`from ncatbot.event.qq import GroupMessageEvent` 等）
- [ ] 无 `filter_registry`、`command_registry` 导入
- [ ] 无未使用的导入（如 `asyncio`）

## 3. 命令/事件注册

- [ ] 所有命令方法都有 `@registrar.on_command("cmd")` 装饰器
- [ ] 无 `register_user_func()` / `register_admin_func()` 调用
- [ ] 无 `register_handler()` 调用
- [ ] 无 `@command_registry.command()` 装饰器
- [ ] 无 `@filter_registry.xxx` 装饰器
- [ ] 4.5 隐式注册的方法（方法名即命令名）全部加了 `@registrar` 装饰器

## 4. Config API

- [ ] 无 `self.register_config(...)` 调用
- [ ] 配置初始化改为 `if self.get_config("key") is None: self.set_config("key", default)`
- [ ] 配置读取使用 `self.get_config("key")` 或 `self.config["key"]`
- [ ] 无 `self.data['config']['key']` 形式的配置访问
- [ ] 无 `on_change_xxx` 配置回调方法

## 5. 消息段构造

- [ ] 无 `Image(path)` 位置参数调用（→ `Image(file=path)`）
- [ ] 无 `Text()` 使用（→ `PlainText()` 或 `.add_text()`）
- [ ] 无 `Node()` 使用（→ `ForwardNode()`）
- [ ] 无 `Message()` 使用（→ `MessageArray()`）

## 6. 事件类型

- [ ] 所有 handler 的事件参数有正确的类型注解
- [ ] `hasattr(x, "group_id")` 改为 `isinstance(x, GroupMessageEvent)`
- [ ] 事件参数名统一为 `event`（非必须，但推荐）
- [ ] `event.is_group_event()` 改为 `isinstance(event, GroupMessageEvent)`

## 7. 元数据与生命周期

- [ ] 移除 `dependencies = {}` 类属性
- [ ] 类的 `name`、`version` 属性与 manifest.toml 一致
- [ ] `on_load()` 是 `async def`
- [ ] `on_load()` 不阻塞（无 `time.sleep()`）
- [ ] `on_close()` 是 `async def`（如果存在）
- [ ] 日志使用 `LOG.info()` 而非 `print()`（推荐）
- [ ] `__init__.py` 导出正确的类名

## 8. BotAPI 访问（5.2.0+ 多平台架构）

- [ ] 无 `self.api.post_group_msg(...)` 等直接调用（→ `self.api.qq.post_group_msg(...)`）
- [ ] 无 `self.api.post_private_msg(...)` 等直接调用（→ `self.api.qq.post_private_msg(...)`）
- [ ] 无 `self.api.post_group_forward_msg(...)` 等直接调用（→ `self.api.qq.post_group_forward_msg(...)`）
- [ ] 所有 `self.api.xxx()` 均已改为 `self.api.qq.xxx()`

## 9. 功能验证

- [ ] `get_errors` 无语法/类型错误
- [ ] manifest.toml 可被 `PluginManifest.from_toml()` 正确解析
- [ ] 入口类可被正确导入
- [ ] 所有 `@registrar` 装饰器注册的 handler 出现在 `_pending_handlers` 中
- [ ] 如有测试环境：`ncatbot dev` 启动后插件加载成功

## 快速验证脚本

```python
# 验证 manifest 解析 + 类导入
import sys, importlib
sys.path.insert(0, "plugins/YOUR_PLUGIN")

from ncatbot.plugin.manifest import PluginManifest
manifest = PluginManifest.from_toml("plugins/YOUR_PLUGIN/manifest.toml")
print(f"Manifest: {manifest.name} v{manifest.version}")

mod = importlib.import_module(manifest.main.replace(".py", ""))
cls = getattr(mod, manifest.entry_class)
print(f"Class: {cls.__name__}, MRO: {[c.__name__ for c in cls.__mro__]}")

# 验证 handler 注册（通过 flush_pending 公开 API）
from ncatbot.core import flush_pending
handlers = flush_pending()
for name, entries in handlers.items():
    print(f"\nPlugin: {name}")
    for entry in entries:
        print(f"  {entry}")
```
