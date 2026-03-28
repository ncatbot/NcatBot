"""飞书适配器配置模型"""

from __future__ import annotations

from pydantic import BaseModel

__all__ = [
    "LarkConfig",
]


class LarkConfig(BaseModel):
    """飞书适配器专属配置"""

    app_id: str = ""
    app_secret: str = ""
    verification_token: str = ""
    encrypt_key: str = ""
