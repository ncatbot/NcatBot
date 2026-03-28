"""飞书事件解析器 — 将 lark-oapi SDK 事件转换为 NcatBot 数据模型。"""

from __future__ import annotations

import json
import time
from typing import Optional

from ncatbot.types import BaseEventData, MessageArray
from ncatbot.types.lark import (
    LarkGroupMessageEventData,
    LarkPrivateMessageEventData,
    LarkMessageReadEventData,
    LarkMessageRecalledEventData,
    LarkSender,
)
from ncatbot.utils import get_log

LOG = get_log("LarkEventParser")


class LarkEventParser:
    """飞书事件解析器"""

    def __init__(self, self_id: str = "") -> None:
        self._self_id = self_id

    def parse_message(self, data) -> Optional[BaseEventData]:
        """解析飞书 P2ImMessageReceiveV1 消息事件

        Args:
            data: lark_oapi.api.im.v1.P2ImMessageReceiveV1 事件对象
        """
        try:
            event = data.event
            message = event.message
            sender_info = event.sender

            # 提取消息文本
            content_str = message.content or "{}"
            try:
                content_obj = json.loads(content_str)
                text = content_obj.get("text", content_str)
            except (json.JSONDecodeError, TypeError):
                text = content_str

            msg_array = MessageArray()
            msg_array.add_text(text)

            sender = LarkSender(
                user_id=getattr(sender_info, "sender_id", None)
                and sender_info.sender_id.open_id
                or "",
                nickname="",
                open_id=getattr(sender_info, "sender_id", None)
                and sender_info.sender_id.open_id
                or "",
                union_id=getattr(sender_info, "sender_id", None)
                and sender_info.sender_id.union_id
                or "",
                tenant_key=getattr(sender_info, "tenant_key", None) or "",
            )

            chat_id = message.chat_id or ""
            chat_type = message.chat_type or ""
            message_id = message.message_id or ""
            user_id = sender.open_id or ""

            if chat_type == "group":
                return LarkGroupMessageEventData(  # type: ignore[arg-type]
                    time=int(time.time()),
                    self_id=self._self_id,
                    platform="lark",
                    message_id=message_id,
                    chat_id=chat_id,
                    chat_type=chat_type,
                    content=text,
                    message=msg_array,
                    sender=sender,
                    user_id=user_id,
                    group_id=chat_id,
                )
            else:
                return LarkPrivateMessageEventData(  # type: ignore[arg-type]
                    time=int(time.time()),
                    self_id=self._self_id,
                    platform="lark",
                    message_id=message_id,
                    chat_id=chat_id,
                    chat_type=chat_type,
                    content=text,
                    message=msg_array,
                    sender=sender,
                    user_id=user_id,
                )

        except Exception:
            LOG.exception("飞书消息解析失败")
            return None

    def parse_message_read(self, data) -> Optional[BaseEventData]:
        """解析飞书 P2ImMessageMessageReadV1 消息已读事件"""
        try:
            event = data.event
            reader = event.reader

            reader_id = getattr(reader, "reader_id", None)
            return LarkMessageReadEventData(  # type: ignore[arg-type]
                time=int(time.time()),
                self_id=self._self_id,
                platform="lark",
                message_id_list=event.message_id_list or [],
                reader_open_id=(reader_id.open_id if reader_id else "") or "",
                reader_union_id=(reader_id.union_id if reader_id else "") or "",
                reader_user_id=(reader_id.user_id if reader_id else "") or "",
                read_time=getattr(reader, "read_time", None) or "",
                tenant_key=getattr(reader, "tenant_key", None) or "",
            )
        except Exception:
            LOG.exception("飞书消息已读事件解析失败")
            return None

    def parse_message_recalled(self, data) -> Optional[BaseEventData]:
        """解析飞书 P2ImMessageRecalledV1 消息撤回事件"""
        try:
            event = data.event
            return LarkMessageRecalledEventData(  # type: ignore[arg-type]
                time=int(time.time()),
                self_id=self._self_id,
                platform="lark",
                message_id=event.message_id or "",
                chat_id=event.chat_id or "",
                recall_time=event.recall_time or "",
                recall_type=event.recall_type or "",
            )
        except Exception:
            LOG.exception("飞书消息撤回事件解析失败")
            return None
