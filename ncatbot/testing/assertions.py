"""
Fluent 断言 API — 基于 APICall.params: dict 的语义化断言

提供 APICallAssertion（fluent builder）和 PlatformScope（平台作用域）。
"""

from __future__ import annotations

from typing import Any, Callable, List, TYPE_CHECKING

from ncatbot.adapter import APICall

if TYPE_CHECKING:
    from ncatbot.adapter.mock.api_base import MockAPIBase


def extract_text(call: APICall) -> str:
    """从 APICall 中提取文本内容（跨平台感知）

    - QQ ``message`` 参数: 拼接 segment list 中 type=text 的 data.text
    - QQ ``msg`` 参数 (MessageArray): 拼接 filter_text() 内容
    - Bilibili ``text``/``content``: 直接取字符串
    - GitHub ``body``: 直接取字符串
    - 兜底: str(params)
    """
    p = call.params
    if "message" in p and isinstance(p["message"], list):
        return "".join(
            seg.get("data", {}).get("text", "")
            for seg in p["message"]
            if isinstance(seg, dict) and seg.get("type") == "text"
        )
    if "msg" in p:
        msg = p["msg"]
        if hasattr(msg, "filter_text"):
            return "".join(seg.text for seg in msg.filter_text())
        if hasattr(msg, "to_list"):
            return "".join(
                seg.get("data", {}).get("text", "")
                for seg in msg.to_list()
                if isinstance(seg, dict) and seg.get("type") == "text"
            )
    for key in ("text", "content", "body"):
        if key in p and isinstance(p[key], str):
            return p[key]
    return str(p)


class APICallAssertion:
    """Fluent API 调用断言 — 作用于 action 匹配的调用子集"""

    def __init__(self, action: str, calls: List[APICall]) -> None:
        self._action = action
        self._matching = [c for c in calls if c.action == action]

    # ---- 存在性 ----

    def called(self) -> "APICallAssertion":
        """断言至少被调用一次"""
        assert self._matching, f"期望 '{self._action}' 被调用，但无调用记录"
        return self

    def not_called(self) -> "APICallAssertion":
        """断言未被调用"""
        assert not self._matching, (
            f"期望 '{self._action}' 未被调用，实际 {len(self._matching)} 次"
        )
        return self

    def times(self, n: int) -> "APICallAssertion":
        """断言调用次数"""
        actual = len(self._matching)
        assert actual == n, f"'{self._action}' 调用次数: 期望 {n}, 实际 {actual}"
        return self

    # ---- 参数匹配 ----

    def with_params(self, **expected: Any) -> "APICallAssertion":
        """断言任一调用的 params 包含 expected 子集（精确值匹配）"""
        for call in self._matching:
            if all(call.params.get(k) == v for k, v in expected.items()):
                return self
        raise AssertionError(
            f"'{self._action}' 无匹配调用，期望 params 包含 {expected}。"
            f" 实际调用: {[c.params for c in self._matching]}"
        )

    def with_text(self, *fragments: str) -> "APICallAssertion":
        """断言任一调用的文本内容包含所有 fragment（跨平台感知）"""
        for call in self._matching:
            text = extract_text(call)
            if all(f in text for f in fragments):
                return self
        texts = [extract_text(c) for c in self._matching]
        raise AssertionError(
            f"'{self._action}' 无匹配调用，期望文本包含 {fragments}。 实际文本: {texts}"
        )

    def where(self, predicate: Callable[[APICall], bool]) -> "APICallAssertion":
        """断言任一调用满足自定义条件"""
        for call in self._matching:
            if predicate(call):
                return self
        raise AssertionError(f"'{self._action}' 无调用满足给定条件")

    # ---- 取值 ----

    @property
    def last(self) -> APICall:
        """返回最后一次匹配调用"""
        assert self._matching, f"'{self._action}' 无调用记录"
        return self._matching[-1]

    @property
    def calls(self) -> List[APICall]:
        """返回所有匹配调用"""
        return list(self._matching)


class PlatformScope:
    """限定到单个平台的断言作用域"""

    def __init__(self, harness: Any, platform: str) -> None:
        self._harness = harness
        self._platform = platform

    def assert_api(self, action: str) -> APICallAssertion:
        return APICallAssertion(
            action, self._harness.mock_api_for(self._platform).calls
        )

    @property
    def mock_api(self) -> "MockAPIBase":
        return self._harness.mock_api_for(self._platform)

    def reset(self) -> None:
        self.mock_api.reset()
