"""
Scenario — 链式测试场景构建器

以声明式 API 描述测试流程，然后一次性执行并断言::

    await (
        Scenario("群消息回复")
        .inject(qq.group_message("hello"))
        .settle()
        .assert_api_called("send_group_msg")
        .assert_api_text("send_group_msg", "hello")
        .run(harness)
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .harness import TestHarness
    from ncatbot.types import BaseEventData


class _StepKind(Enum):
    INJECT = auto()
    SETTLE = auto()
    ASSERT_API_CALLED = auto()
    ASSERT_API_NOT_CALLED = auto()
    ASSERT_API_COUNT = auto()
    ASSERT_API_PARAMS = auto()
    ASSERT_API_TEXT = auto()
    ASSERT_API_WHERE = auto()
    ASSERT_CUSTOM = auto()
    RESET_API = auto()


@dataclass
class _Step:
    kind: _StepKind
    kwargs: Dict[str, Any] = field(default_factory=dict)
    platform: Optional[str] = None


class Scenario:
    """链式测试场景构建器。

    所有链式方法返回 self 以支持流式调用。
    调用 ``await scenario.run(harness)`` 执行全部步骤。
    """

    def __init__(self, name: str = "") -> None:
        self._name = name
        self._steps: List[_Step] = []
        self._current_platform: Optional[str] = None

    # ---- 平台作用域 ----

    def on(self, platform: str) -> "Scenario":
        """切换后续断言步骤的平台作用域"""
        self._current_platform = platform
        return self

    # ---- 事件注入 ----

    def inject(self, event_data: "BaseEventData") -> "Scenario":
        """注入一个事件"""
        self._steps.append(_Step(kind=_StepKind.INJECT, kwargs={"event": event_data}))
        self._current_platform = None
        return self

    def inject_many(self, events: List["BaseEventData"]) -> "Scenario":
        """注入多个事件"""
        for ev in events:
            self.inject(ev)
        return self

    # ---- 同步/等待 ----

    def settle(self, delay: float = 0.05) -> "Scenario":
        """等待 handler 处理完成"""
        self._steps.append(_Step(kind=_StepKind.SETTLE, kwargs={"delay": delay}))
        return self

    # ---- 断言 ----

    def assert_api_called(self, action: str, **match: Any) -> "Scenario":
        """断言某 API 被调用（可选 params 子集匹配）"""
        self._steps.append(
            _Step(
                kind=_StepKind.ASSERT_API_CALLED,
                kwargs={"action": action, "match": match},
                platform=self._current_platform,
            )
        )
        return self

    def assert_api_not_called(self, action: str) -> "Scenario":
        """断言某 API 未被调用"""
        self._steps.append(
            _Step(
                kind=_StepKind.ASSERT_API_NOT_CALLED,
                kwargs={"action": action},
                platform=self._current_platform,
            )
        )
        return self

    def assert_api_count(self, action: str, count: int) -> "Scenario":
        """断言某 API 被调用了指定次数"""
        self._steps.append(
            _Step(
                kind=_StepKind.ASSERT_API_COUNT,
                kwargs={"action": action, "count": count},
                platform=self._current_platform,
            )
        )
        return self

    def assert_api_params(self, action: str, **params: Any) -> "Scenario":
        """断言某 API 被调用且 params 包含指定子集"""
        self._steps.append(
            _Step(
                kind=_StepKind.ASSERT_API_PARAMS,
                kwargs={"action": action, "params": params},
                platform=self._current_platform,
            )
        )
        return self

    def assert_api_text(self, action: str, *fragments: str) -> "Scenario":
        """断言某 API 的文本内容包含所有 fragment"""
        self._steps.append(
            _Step(
                kind=_StepKind.ASSERT_API_TEXT,
                kwargs={"action": action, "fragments": fragments},
                platform=self._current_platform,
            )
        )
        return self

    def assert_api_where(
        self,
        action: str,
        predicate: Callable,
        desc: str = "",
    ) -> "Scenario":
        """断言某 API 的任一调用满足 predicate"""
        self._steps.append(
            _Step(
                kind=_StepKind.ASSERT_API_WHERE,
                kwargs={"action": action, "predicate": predicate, "desc": desc},
                platform=self._current_platform,
            )
        )
        return self

    def assert_that(
        self,
        predicate: Callable[["TestHarness"], None],
        desc: str = "",
    ) -> "Scenario":
        """自定义断言：predicate 接收 harness，可抛出 AssertionError"""
        self._steps.append(
            _Step(
                kind=_StepKind.ASSERT_CUSTOM,
                kwargs={"predicate": predicate, "desc": desc},
            )
        )
        return self

    # ---- 重置 ----

    def reset_api(self) -> "Scenario":
        """清空 API 调用记录"""
        self._steps.append(_Step(kind=_StepKind.RESET_API))
        return self

    # ---- 执行 ----

    async def run(self, harness: "TestHarness") -> None:
        """按步骤执行全部场景"""
        for i, step in enumerate(self._steps):
            step_desc = f"[{self._name}] step {i + 1}: {step.kind.name}"
            try:
                await self._execute_step(harness, step)
            except AssertionError as e:
                raise AssertionError(f"{step_desc} 失败: {e}") from e

    def _get_assertion(
        self, harness: "TestHarness", action: str, platform: Optional[str]
    ):
        """根据 platform 获取 APICallAssertion"""
        if platform:
            return harness.on(platform).assert_api(action)
        return harness.assert_api(action)

    async def _execute_step(self, harness: "TestHarness", step: _Step) -> None:
        kw = step.kwargs

        if step.kind == _StepKind.INJECT:
            await harness.inject(kw["event"])

        elif step.kind == _StepKind.SETTLE:
            await harness.settle(kw["delay"])

        elif step.kind == _StepKind.ASSERT_API_CALLED:
            a = self._get_assertion(harness, kw["action"], step.platform)
            a.called()
            match = kw.get("match", {})
            if match:
                a.with_params(**match)

        elif step.kind == _StepKind.ASSERT_API_NOT_CALLED:
            self._get_assertion(harness, kw["action"], step.platform).not_called()

        elif step.kind == _StepKind.ASSERT_API_COUNT:
            self._get_assertion(harness, kw["action"], step.platform).times(kw["count"])

        elif step.kind == _StepKind.ASSERT_API_PARAMS:
            a = self._get_assertion(harness, kw["action"], step.platform)
            a.called().with_params(**kw["params"])

        elif step.kind == _StepKind.ASSERT_API_TEXT:
            a = self._get_assertion(harness, kw["action"], step.platform)
            a.called().with_text(*kw["fragments"])

        elif step.kind == _StepKind.ASSERT_API_WHERE:
            a = self._get_assertion(harness, kw["action"], step.platform)
            a.called().where(kw["predicate"])

        elif step.kind == _StepKind.ASSERT_CUSTOM:
            kw["predicate"](harness)

        elif step.kind == _StepKind.RESET_API:
            harness.reset_api()
