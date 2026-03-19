# NcatBot

`NcatBot` 是一个通用的异步机器人框架。

它的核心只关心两件事：`Adapter` 和事件流。只要把某个平台接成 `BaseAdapter`，就能复用统一的事件分发、事件等待、运行期观测事件以及适配器重启策略。

这意味着它不局限于 QQ。理论上你可以接入微博、B 站、Telegram、Discord，或者任何能被抽象成异步事件源的平台。

当前仓库内置的第一个官方 adapter 是 `NapCatAdapter`，所以现阶段对 QQ/NapCat 的接入体验最好；但框架本身的设计目标是平台无关。

## 目前提供的能力

- 平台无关的 adapter 边界
- 基于类型注解注册事件处理函数
- 内置 `NapCatAdapter`，作为现成可用的参考实现
- 支持一个处理函数同时监听多个事件类型
- 提供 `wait_event()`，方便实现多轮交互
- 适配器退出后自动重启，异常退出时会额外发出失败事件
- 暴露框架内部事件，便于做日志、监控与调试
- 运行中可动态追加新的 adapter

## 环境要求

- Python `3.12+`
- 对应平台可用的连接方式或 SDK

如果你要直接使用仓库里现成的 `NapCatAdapter`，还需要：

- 已经可用的 NapCat 实例
- NapCat 已开启 OneBot WebSocket

## 安装

这个仓库当前更适合以源码方式使用：

```bash
uv sync
```

如果你希望把它安装到当前环境中：

```bash
uv pip install -e .
```

说明：当前项目依赖里包含 `napcat-sdk`，这是因为仓库内置了 `NapCatAdapter`。这不影响你把 `NcatBot` 当成通用框架去实现其他平台的 adapter。

## 快速开始

框架本身是通用的，但当前仓库里开箱即用的是 `NapCatAdapter`，所以下面的第一个例子先以 NapCat 为例。

### 以 NapCat 为例

下面是一个最小可运行示例。它会连接到 NapCat，并在群里收到 `/ping` 时回复 `pong`。

```python
import os

from napcat import GroupMessageEvent

from ncatbot import NcatBotApp
from ncatbot.adapters import NapCatAdapter


app = NcatBotApp()

app.add_adapter(
    NapCatAdapter(
        ws_url="ws://127.0.0.1:3001",
        token=os.getenv("NAPCAT_TOKEN"),
    )
)


@app.on_event
async def handle_group_message(event: GroupMessageEvent) -> None:
    if event.raw_message == "/ping":
        await event.reply("pong")


if __name__ == "__main__":
    app.run()
```

运行：

```bash
uv run python bot.py
```

如果你的 NapCat WebSocket 没有开启鉴权，可以把 `token` 设为 `None` 或空字符串。

### 以自定义平台为例

如果你想接微博、B 站、Telegram、Discord，或者别的自有系统，核心用法其实都是一样的：

```python
from ncatbot import NcatBotApp


app = NcatBotApp()
app.add_adapter(MyAdapter())


@app.on_event
async def handle(event: MyEvent) -> None:
    ...


app.run()
```

变化的只有 `MyAdapter` 如何把目标平台的事件转换成 Python 对象并持续产出。

## 核心概念

### 1. `NcatBotApp`

应用主对象，负责：

- 管理 adapter 生命周期
- 接收并广播事件
- 把事件分发给匹配的 handler
- 暴露 `wait_event()` 等高层能力

如果你在读源码，可以把它理解成一个很薄的总控层。当前内部大致拆成 3 个私有组件：

- `HandlerRegistry`: 负责 `@app.on_event(...)` 注册和 handler 解析
- `EventBroadcaster`: 负责 `events()`/`wait_event()` 背后的广播流
- `AdapterRuntime`: 负责 adapter 任务、重启策略和运行中动态添加 adapter

推荐阅读顺序：

1. 先看 `src/ncatbot/app.py`，理解总流程
2. 再看 `src/ncatbot/_handler_registry.py`，理解 handler 是怎么登记和匹配的
3. 再看 `src/ncatbot/_event_broadcaster.py`，理解 `events()` / `wait_event()` 为什么能工作
4. 最后看 `src/ncatbot/_adapter_runtime.py`，理解 adapter 生命周期和重启逻辑

### 2. `Adapter`

adapter 是平台接入层，也是这个框架最核心的扩展点。一个 adapter 需要实现：

- `platform_name`
- `adapter_name`
- `adapter_version`
- `base_event_type`
- `async with` 生命周期
- `__aiter__()` 异步事件流

只要满足这个接口，你就可以把任何平台接进来。

比如：

- QQ: `NapCatAdapter`
- 微博: 轮询或流式 API adapter
- B 站: 直播间 / 动态 / 消息 adapter
- Telegram: Bot API / MTProto adapter
- Discord: Gateway adapter

当前仓库内置：

- `NapCatAdapter`: 对 NapCat 的封装，直接继承 `napcat.NapCatClient`
- `InternalEventAdapter`: 框架内部使用，用来发布框架事件

### 3. 事件处理函数

你可以显式指定要监听的事件类型：

```python
from napcat import GroupMessageEvent


@app.on_event(GroupMessageEvent)
async def handle_group_message(event: GroupMessageEvent) -> None:
    ...
```

也可以直接依靠第一个参数的类型注解推断：

```python
from napcat import GroupMessageEvent, PrivateMessageEvent


@app.on_event
async def handle_message(
    event: GroupMessageEvent | PrivateMessageEvent,
) -> None:
    ...
```

## 等待后续事件

`wait_event()` 很适合处理“先发命令，再等用户下一条消息”的交互。

```python
from napcat import GroupMessageEvent


@app.on_event
async def handle_bind(event: GroupMessageEvent) -> None:
    if event.raw_message != "/bind":
        return

    await event.reply("请在 30 秒内回复你的昵称")

    try:
        reply = await app.wait_event(
            lambda item: isinstance(item, GroupMessageEvent)
            and item.group_id == event.group_id
            and item.user_id == event.user_id,
            timeout=30,
        )
    except TimeoutError:
        await event.reply("等待超时，已取消")
        return

    await event.reply(f"收到昵称：{reply.raw_message}")
```

## 观测框架内部事件

除了业务事件，`NcatBot` 还会分发自己的框架事件。常见用途有：

- 打印生命周期日志
- 统计 handler 执行耗时
- 监控 adapter 异常与重连
- 追踪 `wait_event()` 的注册、命中、超时和取消

示例：

```python
from ncatbot.events import AdapterRunFailed, HandlerFailed, WaitMatched


@app.on_event
async def observe_framework_events(
    event: AdapterRunFailed | HandlerFailed | WaitMatched,
) -> None:
    print(type(event).__name__, event)
```

当前公开的框架事件包括：

- 应用生命周期：`AppStarting`、`AppStarted`、`AppStopping`
- adapter 生命周期：`AdapterAdded`、`AdapterRunStarting`、`AdapterRunFailed`、`AdapterRunExited`、`AdapterRestartScheduled`
- 事件分发观测：`EventReceived`、`HandlersResolved`、`HandlerScheduled`、`HandlerCompleted`、`HandlerFailed`
- 等待流程：`WaitRegistered`、`WaitMatched`、`WaitTimedOut`、`WaitCancelled`

## 自定义 Adapter

如果你想把它接到任何新平台上，实现一个 adapter 即可。最小接口如下：

```python
from collections.abc import AsyncIterator
from types import TracebackType
from typing import Self

from ncatbot.adapters import BaseAdapter


class MyEvent:
    pass


class MyAdapter(BaseAdapter):
    @property
    def platform_name(self) -> str:
        return "my-platform"

    @property
    def adapter_name(self) -> str:
        return "example.MyAdapter"

    @property
    def adapter_version(self) -> str:
        return "0.1.0"

    @property
    def base_event_type(self) -> type[MyEvent]:
        return MyEvent

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        return None

    def __aiter__(self) -> AsyncIterator[object]:
        async def iterator() -> AsyncIterator[object]:
            while True:
                yield ...

        return iterator()
```

然后：

```python
app.add_adapter(MyAdapter())
```

## 运行行为说明

- handler 是通过 `asyncio.create_task()` 调度的，不会串行阻塞整个事件循环
- handler 抛出的异常不会让应用退出，但会打印错误，并发出 `HandlerFailed`
- 只要 adapter 结束且应用仍在运行，框架就会按重启策略再次拉起它
- adapter 异常退出时会额外发出失败事件，便于监控与告警
- 调用 `app.stop()` 后，应用会取消所有 adapter 任务并关闭事件流

## 测试

运行测试：

```bash
uv run pytest
```

说明：这里会同时跑单元测试、`ruff` 和 `pyright`。静态检查被写成了 pytest 测试文件，所以执行这一条命令就会把三类检查都覆盖到。

## 当前状态

当前项目已经具备一个可用的通用 bot kernel，但还比较偏底层，暂时没有：

- 命令路由
- 插件系统
- 配置加载
- 日志封装
- 中间件体系

如果你想做的是跨平台机器人框架，或者想先把某个平台快速接进来验证事件模型，现在已经可以直接在这个基础上开始写了。
