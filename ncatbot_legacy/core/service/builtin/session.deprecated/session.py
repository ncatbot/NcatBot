"""
Session 模型

支持:
- 自由状态存储 (get/set)
- FSM 状态机 (define_state/add_transition/trigger)
- 等待机制 (wait_for_event/feed)
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Callable, Coroutine, Dict, List, Optional


@dataclass
class SessionState:
    """FSM 状态"""

    name: str
    on_enter: Optional[Callable[..., Coroutine]] = None
    on_exit: Optional[Callable[..., Coroutine]] = None


@dataclass
class Transition:
    """FSM 状态转移"""

    from_state: str
    trigger: str
    to_state: str


class Session:
    """
    会话对象

    每个 Session 有:
    - session_key: 用于标识 (通常由 key_func 生成)
    - plugin_name: 所属插件
    - state: 自由存储 (dict)
    - FSM: 可选的有限状态机
    - 等待机制: wait_for_event/feed
    """

    def __init__(
        self,
        session_key: str,
        plugin_name: str,
        ttl: Optional[float] = None,
    ):
        self.session_key = session_key
        self.plugin_name = plugin_name
        self.state: Dict[str, Any] = {}
        self.ttl = ttl  # 秒, None = 不过期

        self.created_at = time.time()
        self.updated_at = time.time()

        # FSM
        self._fsm_states: Dict[str, SessionState] = {}
        self._transitions: List[Transition] = []
        self._current_state: Optional[str] = None

        # 等待机制
        self._waiting: Optional[asyncio.Future] = None

        # 是否已关闭
        self._closed = False

    # ==================== 自由存储 ====================

    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.state[key] = value
        self.touch()

    # ==================== FSM ====================

    @property
    def current_fsm_state(self) -> Optional[str]:
        return self._current_state

    def define_state(
        self,
        name: str,
        on_enter: Optional[Callable[..., Coroutine]] = None,
        on_exit: Optional[Callable[..., Coroutine]] = None,
    ) -> None:
        """定义一个 FSM 状态"""
        self._fsm_states[name] = SessionState(
            name=name, on_enter=on_enter, on_exit=on_exit
        )

    def add_transition(self, from_state: str, trigger: str, to_state: str) -> None:
        """添加状态转移"""
        self._transitions.append(
            Transition(from_state=from_state, trigger=trigger, to_state=to_state)
        )

    async def trigger(self, name: str) -> bool:
        """触发状态转移"""
        for t in self._transitions:
            if t.from_state == self._current_state and t.trigger == name:
                # 退出当前状态
                if self._current_state and self._current_state in self._fsm_states:
                    cb = self._fsm_states[self._current_state].on_exit
                    if cb:
                        await cb(self)

                # 进入新状态
                old = self._current_state
                self._current_state = t.to_state
                if t.to_state in self._fsm_states:
                    cb = self._fsm_states[t.to_state].on_enter
                    if cb:
                        await cb(self)

                self.touch()
                return True

        return False

    async def set_fsm_state(self, state_name: str) -> None:
        """直接设置 FSM 状态 (跳过转移检查)"""
        if self._current_state and self._current_state in self._fsm_states:
            cb = self._fsm_states[self._current_state].on_exit
            if cb:
                await cb(self)

        self._current_state = state_name
        if state_name in self._fsm_states:
            cb = self._fsm_states[state_name].on_enter
            if cb:
                await cb(self)

        self.touch()

    # ==================== 等待机制 ====================

    async def wait_for_event(self, timeout: Optional[float] = None) -> Any:
        """等待下一个事件 (由 SessionStepHook feed)"""
        if self._waiting is not None:
            self._waiting.cancel()

        loop = asyncio.get_running_loop()
        self._waiting = loop.create_future()

        try:
            return await asyncio.wait_for(self._waiting, timeout=timeout)
        except asyncio.TimeoutError:
            return None
        finally:
            self._waiting = None

    def feed(self, event: Any) -> bool:
        """投递事件给 wait_for_event"""
        if self._waiting is not None and not self._waiting.done():
            self._waiting.set_result(event)
            return True
        return False

    # ==================== 生命周期 ====================

    def touch(self) -> None:
        self.updated_at = time.time()

    def is_expired(self) -> bool:
        if self._closed:
            return True
        if self.ttl is None:
            return False
        return (time.time() - self.updated_at) > self.ttl

    def close(self) -> None:
        self._closed = True
        if self._waiting and not self._waiting.done():
            self._waiting.cancel()

    @property
    def closed(self) -> bool:
        return self._closed

    def __repr__(self) -> str:
        return (
            f"<Session(key={self.session_key!r}, plugin={self.plugin_name!r}, "
            f"closed={self._closed}, fsm={self._current_state})>"
        )
