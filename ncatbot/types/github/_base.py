"""GitHub 平台模型基类"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

__all__ = ["GitHubModel"]


class GitHubModel(BaseModel):
    """GitHub 平台 Pydantic 模型基类

    * ``extra="allow"`` — 容忍 GitHub API 返回的未声明字段，前向兼容。
    * ``populate_by_name=True`` — 同时支持 alias 和字段原名。
    * dict 兼容层 — 支持 ``model["key"]`` / ``model.get(key)`` 下标访问,
      方便从 raw-dict 用法无痛迁移。
    """

    model_config = ConfigDict(
        extra="allow", populate_by_name=True, coerce_numbers_to_str=True
    )

    # ---- dict 兼容层 ----

    def __getitem__(self, key: str) -> Any:
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)
