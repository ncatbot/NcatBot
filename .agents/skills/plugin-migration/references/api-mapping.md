# API 变更映射

## 1. 命令与事件注册

### 4.4 → 5.0

| 4.4 方式 | 5.0 等价 | 说明 |
|---------|---------|------|
| `self.register_user_func(name="cmd", handler=fn, prefix="/cmd")` | `@registrar.on_command("cmd")` 装饰器 | 移除命令式注册，改用装饰器 |
| `self.register_admin_func(name="cmd", handler=fn, prefix="/cmd")` | `@registrar.on_command("cmd")` + RBACMixin 权限检查 | admin 过滤改为 RBAC |
| `self.register_handler("ncatbot.group_message_event", handler)` | `@registrar.on_group_message()` 或 `@registrar.on("message")` | |
| `self.register_handler("ncatbot.private_message_event", handler)` | `@registrar.on_private_message()` | |
| `self.register_handler("ncatbot.notice_event", handler)` | `@registrar.on_notice()` | |
| `self.register_handler("ncatbot.request_event", handler)` | `@registrar.on_request()` | |
| `self.register_handler("re:test\.", handler)` | `@registrar.on("message")` + Hook 或 handler 内判断 | 正则事件匹配需手动实现 |
| `self.event_bus.publish_async(Event("type", data))` | 5.0 无直接等价，可用 service 层实现跨插件通信 | 见注 |
| `self.event_bus.unregister_handler(hid)` | 自动管理，无需手动取消 | handler 随插件卸载自动清理 |
| `self.unregister_all_handler()` | 无需调用 | 插件卸载时自动清理 |
| `@command_registry.command("cmd")` | `@registrar.on_command("cmd")` | 装饰器名不同 |
| `@filter_registry.group_filter` | `@registrar.on_group_message()` 或 `@registrar.on_group_command()` | 内置到 registrar |
| `@filter_registry.private_filter` | `@registrar.on_private_message()` 或 `@registrar.on_private_command()` | |
| `@admin_filter` | Handler 内使用 `self.check_permission(event.user_id, "path")` | RBAC 替代 |
| `@group_filter` | `@registrar.on_group_command()` / `@registrar.on_group_message()` | |
| `@CustomFilter(lambda e: ...)` | `@add_hooks(hook)` 或 handler 内 if 判断 | Hook 系统替代；`from ncatbot.core import add_hooks` |
| `@option(short_name="v", long_name="verbose")` | 5.0 通过函数签名自动解析参数 | 类型注解替代显式声明 |

### 4.5 → 5.0

| 4.5 方式 | 5.0 等价 | 说明 |
|---------|---------|------|
| 方法名即命令名（隐式注册） | `@registrar.on_command("method_name")` | **必须**显式添加装饰器 |

### 5.0 registrar 装饰器速查

**装饰器通用参数**：

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `*names` | `str` | — | 命令名（仅 `on_command` 系列） |
| `priority` | `int` | `0` | 执行优先级，数值越大越先执行 |
| `ignore_case` | `bool` | `False` | 命令名是否忽略大小写（仅 `on_command` 系列） |
| `platform` | `str|None` | `None` | 限制特定平台（仅跨平台装饰器） |
| `**metadata` | `Any` | — | 附加元数据，透传给 Hook |

```python
from ncatbot.core import registrar

# 命令（最常用）
@registrar.on_command("cmd")                    # 所有消息类型
@registrar.on_command("cmd1", "cmd2")           # 多个命令名
@registrar.on_command("hi", ignore_case=True)   # 忽略大小写
@registrar.on_group_command("cmd")              # 仅群消息
@registrar.on_private_command("cmd")            # 仅私聊

# 消息（无命令匹配，接收所有消息）
@registrar.on_message()                         # 所有消息
@registrar.on_group_message()                   # 仅群消息
@registrar.on_group_message(priority=200)       # 高优先级（用于统计等场景）
@registrar.on_private_message()                 # 仅私聊

# 通知/请求
@registrar.on_notice()                          # 所有通知
@registrar.on_request()                         # 所有请求

# 通用
@registrar.on(event_type, priority=0)           # 监听任意事件类型

# QQ 平台子注册器（完整列表）
@registrar.qq.on_command("cmd")                 # QQ 平台命令（群+私聊）
@registrar.qq.on_group_command("cmd")           # QQ 群命令
@registrar.qq.on_private_command("cmd")         # QQ 私聊命令
@registrar.qq.on_group_message()                # QQ 群消息
@registrar.qq.on_private_message()              # QQ 私聊消息
@registrar.qq.on_group_increase()               # 群成员增加
@registrar.qq.on_group_decrease()               # 群成员减少
@registrar.qq.on_group_recall()                 # 群消息撤回
@registrar.qq.on_group_admin()                  # 群管理员变动
@registrar.qq.on_group_ban()                    # 群禁言
@registrar.qq.on_friend_add()                   # 好友添加
@registrar.qq.on_poke()                         # 戳一戳
@registrar.qq.on_friend_request()               # 好友请求
@registrar.qq.on_group_request()                # 加群请求
@registrar.qq.on_meta()                         # 元事件
@registrar.qq.on_message_sent()                 # 消息发送（自身消息）
```

### `registrar.*` vs `registrar.qq.*` 选择指南

| 场景 | 使用 | 示例 |
|------|------|------|
| 插件仅针对 QQ 平台 | `registrar.qq.*` | `@registrar.qq.on_group_command("hello")` |
| 插件跨平台（QQ + Bilibili 等） | `registrar.*` | `@registrar.on_command("help")` |
| QQ 特有事件（戳一戳、群成员增加等） | `registrar.qq.*` | `@registrar.qq.on_poke()` |
| 既要群又要私聊响应 | `registrar.on_command()` 或分别注册 | `@registrar.on_command("status")` |

> **迁移建议**：4.4/4.5 插件默认都是 QQ 平台，迁移时推荐用 `registrar.qq.*` 系列，语义更明确。

---

## 2. Config API

| 4.4/4.5 方式 | 5.0 等价 | 说明 |
|-------------|---------|------|
| `self.register_config("key", default, description=..., value_type=..., metadata=...)` | `if self.get_config("key") is None: self.set_config("key", default)` | register_config 不存在于 5.0 |
| `self.config["key"]` | `self.get_config("key")` 或 `self.config["key"]` | 两者皆可，推荐 get_config |
| `self.data['config']['key']` | `self.get_config("key")` | 4.5 data 嵌套 config，5.0 分离 |
| `on_change_xxx` 配置回调 | 无等价 | 5.0 无配置变更回调 |
| `/set_config plugin key value` 用户命令 | 视具体实现 | 5.0 需自行实现 |

### 5.0 ConfigMixin 完整 API

```python
# 在 on_load() 中初始化
async def on_load(self):
    if self.get_config("key") is None:
        self.set_config("key", "default_value")

# 读取
val = self.get_config("key")
val = self.get_config("key", default="fallback")

# 写入（立即持久化到 config.yaml）
self.set_config("key", "new_value")

# 删除
self.remove_config("key")

# 批量更新
self.update_config({"k1": "v1", "k2": "v2"})
```

---

## 3. 数据持久化

| 4.4/4.5 | 5.0 | 说明 |
|---------|-----|------|
| `self.data` 无标准接口 | `self.data` 字典（DataMixin） | 5.0 新增，自动持久化到 data.json |

### 5.0 DataMixin 用法

```python
async def on_load(self):
    self.data.setdefault("counter", 0)    # 用 setdefault 避免覆盖

self.data["counter"] += 1                 # 直接操作
self._save_data()                         # 手动持久化（通常不需要，卸载时自动保存）
```

---

## 4. 消息段构造

| 4.4/4.5 | 5.0 | 说明 |
|---------|-----|------|
| `Image(path)` | `Image(file=path)` | **Pydantic model，必须关键字参数** |
| `Image(file="url")` | `Image(file="url")` | 不变 |
| `Text("hello")` | `PlainText("hello")` 或 `MessageArray().add_text("hello")` | 类名变更 |
| `At("123")` | `At(user_id="123")` | 必须关键字参数；`qq` 也可作为别名 |
| `Record(file="path")` | `Record(file="path")` | 不变 |
| `Video(file="path")` | `Video(file="path")` | 不变 |
| `Node(user_id, nickname, content)` | `ForwardNode(...)` | 类名变更；从 `ncatbot.types.qq` 导入 |
| `ForwardConstructor.to_forward()` | `ForwardConstructor.build()` 或 `.to_forward()` | `.build()` 是新别名，两者等价 |
| `Message().append(segment)` | `MessageArray().add_text(...)` 链式构造 | Message → MessageArray |
| `MessageArray(seg1, seg2, ...)` | `MessageArray(seg1, seg2, ...)` | 不变 |
| `MessageArray(generator)` | `MessageArray(generator)` | 不变 |

### 5.0 消息构造模式

```python
from ncatbot.types import MessageArray, Image, PlainText, At

# 链式构造
msg = MessageArray().add_text("Hello ").add_at(user_id).add_image("pic.jpg")

# 直接构造
msg = MessageArray(PlainText("Hello"), Image(file="pic.jpg"))

# 生成器
msg = MessageArray(Image(file=path) for path in image_paths)
```

---

## 5. 事件类型

| 4.4/4.5 | 5.0 | 说明 |
|---------|-----|------|
| `BaseMessageEvent` | `MessageEvent` | 名称变更 |
| `GroupMessageEvent` | `GroupMessageEvent` | 不变 |
| `PrivateMessageEvent` | `PrivateMessageEvent` | 不变 |
| `RequestEvent` | `RequestEvent` | 不变 |
| `NoticeEvent` | `NoticeEvent` | 不变 |
| `event.post_type` | `event.post_type` | 不变 |
| `event.message_type` | `event.message_type` | 不变 |
| `event.is_group_event()` | `isinstance(event, GroupMessageEvent)` | 方法 → isinstance |
| `hasattr(event, "group_id")` | `isinstance(event, GroupMessageEvent)` | 推荐 isinstance |

### 事件属性（不变）

```python
# 通用
event.message_id    # str
event.user_id       # str
event.raw_message   # str
event.sender        # BaseSender / GroupSender
event.self_id       # Bot QQ

# GroupMessageEvent
event.group_id      # str
```

### event.reply() 完整签名（5.2.0+）

```python
await event.reply(
    text: Optional[str] = None,
    *,
    at: Optional[Union[str, int]] = None,       # @某人
    image: Optional[Union[str, Image]] = None,  # 图片
    video: Optional[Union[str, Video]] = None,  # 视频（5.2.0+ 新增）
    rtf: Optional[MessageArray] = None,         # 富文本消息
    at_sender: bool = True,                     # 自动 @ 发送者（5.2.0+ 新增）
)

# 示例
await event.reply(text="Hello")
await event.reply(rtf=msg_array)
await event.reply(text="看图", image="url")
await event.reply(text="看视频", video="path.mp4")
```

---

## 6. BotAPI 方法

### 5.2.0+ API 访问架构

5.2.0+ 采用多平台架构，`self.api` 是 `BotAPIClient`（纯路由器），QQ API 必须通过 `self.api.qq` 访问：

```python
# ❗ 4.4/4.5 旧用法（不再有效）
await self.api.post_group_msg(...)       # ❌ AttributeError

# ✅ 5.2.0+ 新用法
await self.api.qq.post_group_msg(...)    # 通过 QQ 平台子对象
```

### QQ API 子对象结构

| 子对象 | 职责 | 示例 |
|---------|------|------|
| `self.api.qq` | Sugar 方法（便捷消息发送） | `post_group_msg()`, `post_group_forward_msg()` |
| `self.api.qq.manage` | 群管理 | `set_group_ban()`, `set_group_kick()` |
| `self.api.qq.query` | 信息查询 | `get_group_member_info()`, `get_group_list()` |
| `self.api.qq.file` | 文件上传 | `upload_attachment()` |
| `self.api.qq.messaging` | 底层消息发送 | `send_group_msg()` |

### Sugar 方法（最常用）

```python
# 发送消息（关键字参数自动组装 MessageArray）
await self.api.qq.post_group_msg(group_id, text=..., at=..., reply=..., image=..., video=..., rtf=...)
await self.api.qq.post_private_msg(user_id, text=..., image=...)

# 发送已构造的 MessageArray（不再自动组装）
await self.api.qq.post_group_array_msg(group_id, msg_array)
await self.api.qq.post_private_array_msg(user_id, msg_array)

# 转发消息
await self.api.qq.post_group_forward_msg(group_id=..., forward=...)
await self.api.qq.post_private_forward_msg(user_id=..., forward=...)
```

### 管理/查询/文件 API 示例

```python
# 群管理
await self.api.qq.manage.set_group_ban(group_id, user_id, duration=60)
await self.api.qq.manage.set_group_kick(group_id, user_id)

# 信息查询
info = await self.api.qq.query.get_group_member_info(group_id, user_id)
groups = await self.api.qq.query.get_group_list()

# 文件上传
await self.api.qq.file.upload_attachment(group_id, attachment, folder=folder_name)
```

### ForwardConstructor（仅导入路径变更）

```python
from ncatbot.types.qq import ForwardConstructor  # 仅导入路径变更

fcr = ForwardConstructor(self_id, "昵称")
fcr.attach_image(image_path)
fcr.attach_text("文本")
fcr.attach_message(msg_array)       # 附加 MessageArray
fcr.attach_file(file_path)          # 附加文件
fcr.attach_video(video_path)        # 附加视频
forward = fcr.build()               # 推荐用 .build()（.to_forward() 亦可，互为别名）
await self.api.qq.post_group_forward_msg(group_id=gid, forward=forward)
```

完整方法列表：`attach_image()`, `attach_text()`, `attach_file()`, `attach_video()`, `attach_forward()`, `attach_message()`, `attach()`, `set_author()`, `to_forward()` / `build()`

---

## 7. 参数绑定（5.0+ 新增）

5.0+ 命令 handler 支持通过**类型注解**自动提取消息中的参数：

| 类型注解 | 提取方式 | 说明 |
|---------|---------|------|
| `target: At` | 从消息中的 @mention 按顺序提取 | 多个 At 参数按出现顺序绑定 |
| `count: int` | 从文本 token 中解析整数 | `float` 同理 |
| `name: str` | 单个文本 token（最后一个 `str` 参数获取剩余文本） | |
| 有默认值的参数 | 可选，缺失时用默认值 | 必填参数缺失则 handler **不触发** |

### 4.4/4.5 → 5.0 迁移

```python
# 4.4：显式解析
@command_registry.command("kick")
@option(short_name="t", long_name="target")
@option(short_name="d", long_name="duration", default=60)
async def kick(self, msg, target, duration):
    ...

# 5.0：类型注解自动绑定
@registrar.qq.on_group_command("kick")
async def kick(self, event: GroupMessageEvent, target: At, duration: int = 60):
    await self.api.qq.manage.set_group_ban(event.group_id, target.user_id, duration)
```

---

## 8. 事件流与 wait_event（5.0+ 新增）

替代旧版 `event_bus.publish_async()` 和手动状态管理的多步对话方案。

### wait_event（单次等待）

```python
@registrar.qq.on_group_command("确认测试")
async def on_confirm(self, event: GroupMessageEvent):
    await event.reply(text="请在 15 秒内回复「确认」...")
    try:
        confirm_event = await self.wait_event(
            predicate=lambda e: (
                str(e.data.user_id) == str(event.user_id)
                and e.data.raw_message.strip() == "确认"
            ),
            timeout=15.0,
        )
        await event.reply(text="操作已确认 ✅")
    except asyncio.TimeoutError:
        await event.reply(text="操作超时 ⏰")
```

### 事件流（持续监听）

```python
async def _stream_listener(self):
    async with self.events("message") as stream:
        async for event in stream:
            if event.data.message_type.value == "private":
                LOG.info("[Event Stream] %s", event.data.raw_message)
```

### 4.4 → 5.0 迁移

| 4.4 方式 | 5.0 等价 | 说明 |
|---------|---------|------|
| `self.event_bus.publish_async(Event("type", data))` | 无直接等价，可用 service 层 | 跨插件通信 |
| 手动状态机 + `register_handler` | `self.wait_event(predicate, timeout)` | 多步对话 |
| 轮询检查 + 状态变量 | `async with self.events("type") as stream` | 持续监听 |

---

## 9. 定时任务

| 4.4/4.5 | 5.0 | 说明 |
|---------|-----|------|
| `self.add_scheduled_task(job_func, name, interval, ...)` | `self.add_scheduled_task(name, interval, ..., callback=fn)` | **参数顺序变更**，见下 |
| `conditions=[fn]` | `conditions=[fn]` | 不变 |
| `max_runs=N` | `max_runs=N` | 不变 |
| 时间格式 `"1h"` / `"09:30"` / `"2025-12-31"` | 同上 | 不变 |

### 5.0 签名变更重点

```python
# 4.x 签名
self.add_scheduled_task(job_func, name, interval, conditions=None, max_runs=None)

# 5.0 签名
self.add_scheduled_task(name, interval, conditions=None, max_runs=None, callback=None)
#                       ^^^^ ^^^^^^^^                                  ^^^^^^^^
#                       1st   2nd（原 job_func 移到末尾并改名 callback）
```

- `callback` 可省略：省略时自动查找 `self.{name}()` 方法作为回调
- 因此可以直接定义 `async def my_task(self)` 然后 `self.add_scheduled_task("my_task", "1h")`

---

## 10. RBAC 权限

| 4.4/4.5 | 5.0 | 说明 |
|---------|-----|------|
| `self.rbac_manager.check_permission(uid, path)` | `self.check_permission(uid, path)` | 直接调用 Mixin 方法 |
| `self.rbac_manager.assign_permissions_to_user(...)` | `self.add_permission(path)` 注册 + RBAC service 管理 | 简化 API |
| `self.rbac_manager.assign_role_to_user(uid, role)` | 通过 RBAC service 管理 | |

---

## 11. 其它变更

| 项目 | 4.4/4.5 | 5.0 |
|------|---------|-----|
| 参数命名惯例 | `msg: MessageEvent` | `event: MessageEvent` |
| 日志 | `print()` 混用 | `LOG = get_log("name"); LOG.info(...)` |
| `__init__.py` 中的 `__all__` | 必需（多插件文件） | 非必需（manifest.toml 指定 entry_class）|
| `dependencies = {}` 类属性 | 必需 | 移至 manifest.toml `[dependencies]` |
| 插件间通信 | `self.event_bus.publish_async()` | 无直接等价，可通过 service 层 |
| sync API | `method_sync()` 后缀 | 不推荐，统一 async |
