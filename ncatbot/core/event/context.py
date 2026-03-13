from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from pydantic import BaseModel, PrivateAttr

if TYPE_CHECKING:
    from ncatbot.core.api.interface import IBotAPI


def _get_ibotapi():
    """延迟导入 IBotAPI 以避免循环引用"""
    from ncatbot.core.api.interface import IBotAPI

    return IBotAPI


class ContextMixin(BaseModel):
    """依赖注入混入类"""

    _api: Optional[IBotAPI] = PrivateAttr(default=None)

    def bind_api(self, api: IBotAPI):
        self._api = api

    @property
    def api(self) -> IBotAPI:
        if self._api is None:
            raise RuntimeError("API context not initialized.")
        return self._api


# 向后兼容：允许 from context import IBotAPI
def __getattr__(name):
    if name == "IBotAPI":
        return _get_ibotapi()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
