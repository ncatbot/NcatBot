# 导入路径映射

## 4.4 → 5.0

| 4.4 导入 | 5.0 导入 | 备注 |
|---------|---------|------|
| `from ncatbot.plugin_system import NcatBotPlugin` | `from ncatbot.plugin import NcatBotPlugin` | 基类位置变更 |
| `from ncatbot.plugin_system import filter_registry` | 移除 | 用 `@registrar` 替代 |
| `from ncatbot.plugin_system import command_registry` | 移除 | 用 `@registrar` 替代 |
| `from ncatbot.plugin_system import group_filter, admin_filter, private_filter` | 移除 | 用 `@registrar.on_group_command()` 等替代 |
| `from ncatbot.plugin_system import option, param` | 移除 | 5.0 命令参数通过类型注解自动绑定 |
| `from ncatbot.plugin_system.event import Event` | `from ncatbot.event import BaseEvent` | 事件基类变更 |
| `from ncatbot.core import MessageEvent` | `from ncatbot.event.qq import MessageEvent` | |
| `from ncatbot.core import GroupMessageEvent` | `from ncatbot.event.qq import GroupMessageEvent` | |
| `from ncatbot.core import PrivateMessageEvent` | `from ncatbot.event.qq import PrivateMessageEvent` | |
| `from ncatbot.core import BaseMessageEvent` | `from ncatbot.event.qq import MessageEvent` | 名称变更 |
| `from ncatbot.core import RequestEvent` | `from ncatbot.event.qq import RequestEvent` | |
| `from ncatbot.core import NoticeEvent` | `from ncatbot.event.qq import NoticeEvent` | |
| `from ncatbot.core.event.message_segment import MessageArray, Text, At, Image` | `from ncatbot.types import MessageArray, PlainText, At, Image` | `Text` → `PlainText` |
| `from ncatbot.core import MessageArray, Image` | `from ncatbot.types import MessageArray, Image` | |
| `from ncatbot.core import Message, PlainText, At, Image, Record` | `from ncatbot.types import MessageArray, PlainText, At, Image, Record` | `Message` → `MessageArray` |
| `from ncatbot.core.event.message_segment import Node, Forward` | `from ncatbot.types.qq import ForwardNode, Forward` | `Node` → `ForwardNode`；仅在 `ncatbot.types.qq` 中导出 |
| `from ncatbot.core.helper import ForwardConstructor` | `from ncatbot.types.qq import ForwardConstructor` | |
| `from ncatbot.utils.assets.literals import OFFICIAL_*` | 移除 | 5.0 用装饰器直接注册，不需要事件常量 |
| （无） | `from ncatbot.core import registrar` | **新增**：5.0 必需 |
| （无） | `from ncatbot.event.qq import GroupMessageEvent` | **新增**：类型细化 |
| （无） | `from ncatbot.event.qq import GroupIncreaseEvent` | **新增**：群成员增加事件 |
| （无） | `from ncatbot.event.qq import MetaEvent` | **新增**：元事件 |
| （无） | `from ncatbot.event.qq import FriendRequestEvent, GroupRequestEvent` | **新增**：细化请求事件 |
| （无） | `from ncatbot.types.qq import Face, Json, Markdown` | **新增**：QQ 特有消息段 |
| （无） | `from ncatbot.event import Kickable, Bannable, Approvable` | **新增**：事件 Trait（用于 isinstance 检查） |

| 4.5 导入 | 5.0 导入 | 备注 |
|---------|---------|------|
| `from ncatbot.plugin_system.builtin_mixin import NcatBotPlugin` | `from ncatbot.plugin import NcatBotPlugin` | |
| `from ncatbot.core import PrivateMessageEvent` | `from ncatbot.event.qq import PrivateMessageEvent` | |
| `from ncatbot.core import MessageEvent` | `from ncatbot.event.qq import MessageEvent` | |
| `from ncatbot.core import MessageArray, Image` | `from ncatbot.types import MessageArray, Image` | |
| `from ncatbot.core.helper import ForwardConstructor` | `from ncatbot.types.qq import ForwardConstructor` | |
| （无） | `from ncatbot.core import registrar` | **新增**：5.0 必需 |
| （无） | `from ncatbot.event.qq import GroupMessageEvent` | **新增**：类型细化 |
| （无） | `from ncatbot.event.qq import GroupIncreaseEvent` | **新增**：群成员增加事件 |
| （无） | `from ncatbot.event.qq import FriendRequestEvent, GroupRequestEvent` | **新增**：细化请求事件 |
| （无） | `from ncatbot.types.qq import Face, Json, Markdown` | **新增**：QQ 特有消息段 |

## 通用导入路径规则

5.0 中的包结构分工：

| 包 | 职责 | 典型导出 |
|----|------|---------|
| `ncatbot.plugin` | 插件基类 | `NcatBotPlugin`, `BasePlugin`, `PluginManifest` |
| `ncatbot.core` | 注册器、调度器、Hook | `registrar`, `Hook`, `HookStage`, `HookAction` |
| `ncatbot.event` | 事件基类与 Trait | `BaseEvent`, `Replyable`, `Deletable`, `HasSender`, `GroupScoped`, `Kickable`, `Bannable`, `Approvable`（QQ 事件需从 `ncatbot.event.qq` 导入） |
| `ncatbot.event.qq` | QQ 平台事件类 | `MessageEvent`, `GroupMessageEvent`, `PrivateMessageEvent`, `NoticeEvent`, `RequestEvent`, `GroupIncreaseEvent`, `FriendRequestEvent`, `GroupRequestEvent`, `MetaEvent` |
| `ncatbot.types` | 通用消息段、数据类型 | `MessageArray`, `Image`, `PlainText`, `At`, `Reply`, `Record`, `Video`, `File`, `Attachment`, `AttachmentList` |
| `ncatbot.types.qq` | QQ 特定类型 | `ForwardConstructor`, `Forward`, `ForwardNode`, `Face`, `Json`, `Markdown`, `QQImage`, `QQRecord` |
| `ncatbot.utils` | 工具函数 | `get_log` |
