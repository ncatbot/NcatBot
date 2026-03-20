# 导入规范

NcatBot 框架按 **一级 layer** 划分模块边界，5.2 多平台架构引入了 **平台子模块** 作为合法的第二级导入层。

## 一级 Layer 列表

`adapter` / `api` / `app` / `cli` / `core` / `event` / `plugin` / `service` / `testing` / `types` / `utils`

## 规则 1：跨 layer — 绝对导入，最多到二级（平台子模块）

不同 layer 之间互相引用时，使用 `from ncatbot.<layer> import ...`。当需要平台特定类型时，允许到 **平台子模块**（`<layer>.<platform>`），但 **禁止** 更深层导入。

```python
# ✅ 一级导入 — 平台无关
from ncatbot.core import registrar, AsyncEventDispatcher
from ncatbot.utils import get_log
from ncatbot.types import MessageArray, PlainText, At, Image

# ✅ 二级导入 — 平台特定（event / types / api 的平台子模块）
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent
from ncatbot.types.qq import ForwardConstructor, Face
from ncatbot.api.qq import QQAPIClient

# ❌ 三级及更深 — 禁止
from ncatbot.core.registry import registrar
from ncatbot.types.common.segment import PlainText
from ncatbot.event.qq.message import GroupMessageEvent
```

**允许二级导入的平台子模块**（白名单）：

| Layer | 允许的二级子模块 | 典型导入 |
|-------|-----------------|---------|
| `event` | `event.qq`, `event.bilibili`, `event.common` | `GroupMessageEvent`, `NoticeEvent` |
| `types` | `types.qq`, `types.bilibili`, `types.common`, `types.napcat` | `ForwardConstructor`, `Face`, `SendMessageResult` |
| `api` | `api.qq`, `api.bilibili`, `api.traits` | `QQAPIClient`, `IMessaging` |
| `adapter` | `adapter.napcat`, `adapter.mock`, `adapter.bilibili` | `NapCatAdapter`, `MockAdapter` |

其他 layer（`core`、`plugin`、`utils`、`app`、`service`、`cli`、`testing`）**只允许一级导入**。

## 规则 2：同 layer 内部 — 相对导入

同一个一级 layer 内部的模块互相引用时，**必须**使用相对导入。

```python
# ✅ 正确（在 utils/config/manager.py 中）
from ..logger import get_early_logger
from .models import Config

# ❌ 错误 — 同 layer 内用了绝对导入
from ncatbot.utils.logger import get_early_logger
```

## 规则 3：外部示例 — 遵循规则 1

`docs/docs/examples/`、`.agents/skills/` 中的代码与用户代码一样，遵循规则 1：一级 + 白名单内的二级。

```python
# ✅ 用户代码 / 示例代码
from ncatbot.core import registrar, from_event, Hook
from ncatbot.plugin import NcatBotPlugin
from ncatbot.event.qq import GroupMessageEvent, FriendRequestEvent
from ncatbot.types import MessageArray, PlainText, At
from ncatbot.types.qq import ForwardConstructor
from ncatbot.utils import get_log

# ❌ 三级导入 — 禁止
from ncatbot.core.registry import registrar
from ncatbot.event.qq.message import GroupMessageEvent
```

## 规则 4：TYPE_CHECKING 守护

框架内部在类型注解中引用其他 layer 的类时，使用 `TYPE_CHECKING` 块避免循环导入：

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ncatbot.core import AsyncEventDispatcher, Event
    from ncatbot.types.qq import EventType
```

## 唯一例外

访问 layer 内部的 **私有实现** (以 `_` 开头)，允许框架内部代码使用深层绝对导入：

```python
# 允许：框架内部访问私有上下文变量
from ncatbot.core.registry.context import _current_plugin_ctx
```

## 新增导出检查

新增公共 API 导出时，必须在对应 layer 的 `__init__.py` 中注册。如果 `__init__.py` 中没有某个符号，说明它不是公共 API。
