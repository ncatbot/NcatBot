# Event 模块测试方案

本目录包含对 `ncatbot.core.event` 模块的完整测试套件。

## 测试结构

```
test/core/event/
├── conftest.py                    # 通用 pytest 配置和数据加载器
├── README.md                      # 本文件
├── message_segments/              # 消息段测试
│   ├── __init__.py
│   ├── conftest.py               # message_segments 专用 fixtures
│   ├── test_base.py              # MessageSegment 基类测试
│   ├── test_primitives.py        # 基础消息段测试 (PlainText, Face, At, Reply)
│   ├── test_media.py             # 媒体消息段测试 (Image, Record, Video)
│   ├── test_misc.py              # 其他消息段测试
│   ├── test_forward.py           # 转发消息测试
│   ├── test_integration.py       # 消息段集成测试
│   └── test_conftest.py          # conftest 测试
└── events/                        # 事件系统测试
    ├── __init__.py
    ├── conftest.py               # events 专用 fixtures (MockBotAPI)
    ├── test_enums.py             # 枚举测试
    ├── test_models.py            # 数据模型测试 (Sender, Status 等)
    ├── test_context.py           # 上下文/依赖注入测试
    ├── test_mixins.py            # Mixin 功能测试
    ├── test_events.py            # 事件类测试
    ├── test_parser.py            # EventParser 测试
    └── test_integration.py       # 事件系统集成测试
```

## 测试数据管理

### 数据源配置

测试框架按以下优先级查找数据文件：

1. **环境变量** `NCATBOT_TEST_DATA_FILE` - 可指定自定义数据文件路径
2. **默认路径** `dev/data.txt` - 项目根目录的 dev 文件夹

**如果找不到数据文件**：依赖真实数据的测试将自动跳过（不会导致测试失败）

```bash
# 使用自定义数据文件路径
NCATBOT_TEST_DATA_FILE=/path/to/your/data.txt pytest test/core/event/ -v

# 使用相对路径（相对于项目根目录）
NCATBOT_TEST_DATA_FILE=logs/my_events.txt pytest test/core/event/ -v
```

### 数据格式

测试数据存储在 `.txt` 文件中，支持两种格式：

1. **日志格式** - 从应用日志中提取的事件数据：
   ```
   [时间戳] DEBUG Adapter ... | 收到事件: {'type': 'message', ...}
   ```

2. **纯 JSON/Python 格式** - 直接的事件数据（支持单引号和双引号）

### 添加新测试数据

只需将新的测试数据添加到 `dev/data.txt` 文件中，测试框架会自动加载并解析。

## 测试数据提供器

`conftest.py` 中的 `TestDataProvider` 类提供以下功能：

### 消息段相关

| 方法/属性 | 描述 |
|---------|------|
| `get_segments_by_type("text")` | 获取指定类型的消息段 |
| `get_all_segments()` | 获取所有消息段 |
| `available_segment_types` | 获取所有可用的消息段类型 |

### 事件相关

| 方法/属性 | 描述 |
|---------|------|
| `all_events` | 获取所有事件 |
| `message_events` | 获取所有消息事件 |
| `meta_events` | 获取所有元事件 |
| `notice_events` | 获取所有通知事件 |
| `request_events` | 获取所有请求事件 |
| `get_events_by_post_type("message")` | 按一级类型获取事件 |
| `get_events_by_type("message", "private")` | 按一级+二级类型获取事件 |
| `get_notice_events_by_subtype("poke")` | 获取特定子类型的 notify 事件 |

### 可用的 Fixtures

#### 通用 Fixtures

| Fixture | 描述 |
|---------|------|
| `data_provider` | TestDataProvider 实例 |
| `message_events` | 所有消息事件 |

#### message_segments 专用 Fixtures

| Fixture | 描述 |
|---------|------|
| `text_segments` | 所有文本消息段 |
| `image_segments` | 所有图片消息段 |
| `face_segments` | 所有表情消息段 |
| `at_segments` | 所有@消息段 |
| `reply_segments` | 所有回复消息段 |
| `forward_segments` | 所有转发消息段 |

#### events 专用 Fixtures

| Fixture | 描述 |
|---------|------|
| `mock_api` | MockBotAPI 实例，用于测试 API 调用 |
| `private_message_events` | 私聊消息事件 |
| `group_message_events` | 群消息事件 |
| `heartbeat_events` | 心跳元事件 |
| `lifecycle_events` | 生命周期元事件 |
| `poke_events` | 戳一戳通知事件 |
| `notice_events` | 所有通知事件 |

## 运行测试

```bash
# 运行所有事件模块测试
uv run pytest test/core/event/ -v

# 只运行消息段测试
uv run pytest test/core/event/message_segments/ -v

# 只运行事件系统测试
uv run pytest test/core/event/events/ -v

# 运行特定测试文件
uv run pytest test/core/event/events/test_parser.py -v

# 运行特定测试类
uv run pytest test/core/event/events/test_events.py::TestPrivateMessageEvent -v

# 运行带覆盖率的测试
uv run pytest test/core/event/ --cov=ncatbot.core.event

# 运行异步测试（需要 pytest-asyncio）
uv run pytest test/core/event/events/test_mixins.py -v
```

## 测试分类

### 单元测试

#### 枚举测试 (`test_enums.py`)

- 枚举值存在性验证
- 枚举类型检查 (`str, Enum`)
- JSON 序列化兼容性
- 字符串比较兼容性

#### 模型测试 (`test_models.py`)

- 模型创建（默认值、指定值）
- ID 字段自动转换 (int → str)
- 序列化/反序列化往返一致性
- 真实数据解析验证

#### 上下文测试 (`test_context.py`)

- API 绑定/解绑
- 未初始化异常
- Protocol 兼容性验证

#### Mixin 测试 (`test_mixins.py`)

- `MessageActionMixin.reply()` - 群/私聊回复
- `MessageActionMixin.delete()` - 消息删除
- `GroupAdminMixin.kick()` - 踢人
- `GroupAdminMixin.ban()` - 禁言
- `RequestActionMixin.approve()/reject()` - 请求处理

#### 事件测试 (`test_events.py`)

- 各类事件创建和字段验证
- ID 字段自动转换
- 嵌套模型解析
- 序列化测试

#### Parser 测试 (`test_parser.py`)

- 注册表初始化验证
- 各类事件正确路由
- API 注入验证
- 错误处理

### 集成测试

#### 消息段集成测试 (`message_segments/test_integration.py`)

- 完整消息解析 - 测试解析包含多种类型的完整消息
- 类型注册 - 验证所有类型都正确注册到 `TYPE_MAP`
- 边缘情况 - 空消息、Unicode、特殊字符等

#### 事件系统集成测试 (`events/test_integration.py`)

- 完整消息处理流程（解析→回复→删除）
- 事件序列化往返
- 真实日志数据解析
- 边缘情况处理

## Mock API

`events/conftest.py` 提供了 `MockBotAPI` 类：

```python
class MockBotAPI:
    """用于测试的 Mock Bot API"""

    # 记录所有 API 调用
    calls: List[tuple]

    # 获取最后一次调用
    def get_last_call() -> tuple

    # 清空调用记录
    def clear_calls() -> None

    # 实现的 API 方法
    async def post_group_msg(group_id, text, **kwargs)
    async def post_private_msg(user_id, text, **kwargs)
    async def delete_msg(message_id)
    async def set_group_kick(group_id, user_id, reject_add_request)
    async def set_group_ban(group_id, user_id, duration)
    async def set_friend_add_request(flag, approve, remark)
    async def set_group_add_request(flag, sub_type, approve, reason)
```

## 扩展测试

### 添加新的消息类型测试

1. 在 `message_segments/` 对应的测试文件中添加新的测试类
2. 参考现有测试结构编写测试用例
3. 如果需要，在 `message_segments/conftest.py` 中添加新的 fixture

### 添加新的事件类型测试

1. 在 `events/test_events.py` 中添加新的测试类
2. 如果是新的事件类别，在 `events/conftest.py` 中添加对应的 fixture
3. 在 `events/test_parser.py` 中添加路由测试

### 添加新的测试数据

1. 将新的日志行或事件数据添加到 `dev/data.txt`
2. 运行测试验证数据能正确解析

## 注意事项

1. **异步测试**：使用 `@pytest.mark.asyncio` 装饰器标记异步测试
2. **数据不可用**：依赖真实数据的测试会自动跳过，不影响其他测试
3. **Pydantic 版本**：测试基于 Pydantic v2，使用 `model_dump()` 而非 `dict()`
4. **额外字段**：事件类默认忽略未知字段，以兼容不同版本的数据格式
5. **测试数据中的省略内容**（如 `[...]`）会被自动处理
6. 支持 Python 格式（单引号）和 JSON 格式（双引号）的数据
## 测试过程中发现的源码问题及修复

### Mixin 中可选字段设计问题

**问题描述**：

在编写测试过程中发现 `ncatbot/core/event/mixins.py` 中的 Mixin 类定义了一些字段作为必需字段（使用 `Any` 类型），但实际业务场景中这些字段并非总是存在：

1. `MessageActionMixin.group_id` - 私聊消息没有 `group_id`
2. `RequestActionMixin.sub_type` - 好友请求没有 `sub_type`

这导致使用真实日志数据测试时，`PrivateMessageEvent` 和 `FriendRequestEvent` 无法正确解析。

**修复方案**：

将这些字段改为可选字段：

```python
# Before (mixins.py)
class MessageActionMixin(ContextMixin):
    message_type: Any
    group_id: Any  # 必需
    user_id: Any
    message_id: Any

class RequestActionMixin(ContextMixin):
    request_type: Any
    flag: Any
    sub_type: Any  # 必需

# After (mixins.py)
class MessageActionMixin(ContextMixin):
    message_type: Any
    group_id: Optional[Any] = None  # 可选，私聊消息无此字段
    user_id: Any
    message_id: Any

class RequestActionMixin(ContextMixin):
    request_type: Any
    flag: Any
    sub_type: Optional[Any] = None  # 可选，好友请求无此字段
```

**影响范围**：

此修复使得所有继承这些 Mixin 的事件类能够正确处理真实数据，同时保持向后兼容（已有的代码如果提供了这些字段仍然正常工作）。
