"""飞书平台 Sender"""

from __future__ import annotations

from typing import Optional

from ..common.sender import BaseSender

__all__ = [
    "LarkSender",
]


class LarkSender(BaseSender):
    """飞书消息发送者"""

    open_id: Optional[str] = None
    union_id: Optional[str] = None
    tenant_key: Optional[str] = None
