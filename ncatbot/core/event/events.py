from typing import Literal, Optional, Union, Any
from pydantic import Field, field_validator
from .enums import *
from .models import *
from .context import ContextMixin
from .mixins import MessageActionMixin, GroupAdminMixin, RequestActionMixin

# --- 基类 ---
class BaseEvent(ContextMixin):
    time: int
    self_id: str
    post_type: PostType

    @field_validator("self_id", mode="before")
    def force_str(cls, v): return str(v)

# ==========================================
# 消息事件 (Message Events)
# ==========================================

class MessageEvent(BaseEvent, MessageActionMixin):
    post_type: PostType = Field(default=PostType.MESSAGE)
    message_type: MessageType
    sub_type: str
    message_id: str
    user_id: str
    message: Any # 建议后续定义为 List[MessageSegment]
    raw_message: str
    font: int = 0

    @field_validator("message_id", "user_id", mode="before")
    def _force_ids(cls, v): return str(v)

class PrivateMessageEvent(MessageEvent):
    message_type: MessageType = Field(default=MessageType.PRIVATE)
    sub_type: str = Field(default="friend")
    sender: BaseSender

class GroupMessageEvent(MessageEvent, GroupAdminMixin):
    message_type: MessageType = Field(default=MessageType.GROUP)
    sub_type: str = Field(default="normal")
    group_id: str
    anonymous: Optional[Anonymous] = None
    sender: GroupSender

    @field_validator("group_id", mode="before")
    def _gid(cls, v): return str(v)

# ==========================================
# 通知事件 (Notice Events)
# ==========================================

class NoticeEvent(BaseEvent):
    post_type: PostType = Field(default=PostType.NOTICE)
    notice_type: NoticeType
    # 大部分通知都有这俩
    group_id: Optional[str] = None
    user_id: Optional[str] = None

    @field_validator("group_id", "user_id", mode="before")
    def _ids(cls, v): return str(v) if v else None

class GroupUploadNoticeEvent(NoticeEvent):
    notice_type: NoticeType = Field(default=NoticeType.GROUP_UPLOAD)
    file: FileInfo

class GroupAdminNoticeEvent(NoticeEvent):
    notice_type: NoticeType = Field(default=NoticeType.GROUP_ADMIN)
    sub_type: str = Field(default="set")

class GroupDecreaseNoticeEvent(NoticeEvent):
    notice_type: NoticeType = Field(default=NoticeType.GROUP_DECREASE)
    sub_type: str = Field(default="leave")
    operator_id: str
    
    @field_validator("operator_id", mode="before")
    def _oid(cls, v): return str(v)

class GroupIncreaseNoticeEvent(NoticeEvent, GroupAdminMixin):
    notice_type: NoticeType = Field(default=NoticeType.GROUP_INCREASE)
    sub_type: str = Field(default="approve")
    operator_id: str

    @field_validator("operator_id", mode="before")
    def _oid(cls, v): return str(v)

class GroupBanNoticeEvent(NoticeEvent):
    notice_type: NoticeType = Field(default=NoticeType.GROUP_BAN)
    sub_type: str = Field(default="ban")
    operator_id: str
    duration: int # 秒

    @field_validator("operator_id", mode="before")
    def _oid(cls, v): return str(v)

class FriendAddNoticeEvent(NoticeEvent):
    notice_type: NoticeType = Field(default=NoticeType.FRIEND_ADD)

class GroupRecallNoticeEvent(NoticeEvent):
    notice_type: NoticeType = Field(default=NoticeType.GROUP_RECALL)
    operator_id: str
    message_id: str
    
    @field_validator("operator_id", "message_id", mode="before")
    def _ids(cls, v): return str(v)

class FriendRecallNoticeEvent(NoticeEvent):
    notice_type: NoticeType = Field(default=NoticeType.FRIEND_RECALL)
    message_id: str
    @field_validator("message_id", mode="before")
    def _mid(cls, v): return str(v)

# --- 具体的 Notify (Poke, Honor, etc) ---

class NotifyEvent(NoticeEvent):
    """Notify 类型的基类，通常 notice_type=notify"""
    notice_type: NoticeType = Field(default=NoticeType.NOTIFY)
    sub_type: str 

class PokeNotifyEvent(NotifyEvent):
    sub_type: str = Field(default=NotifySubType.POKE)
    target_id: str
    @field_validator("target_id", mode="before")
    def _tid(cls, v): return str(v)

class LuckyKingNotifyEvent(NotifyEvent):
    sub_type: str = Field(default=NotifySubType.LUCKY_KING)
    target_id: str
    @field_validator("target_id", mode="before")
    def _tid(cls, v): return str(v)

class HonorNotifyEvent(NotifyEvent):
    sub_type: str = Field(default=NotifySubType.HONOR)
    honor_type: Literal["talkative", "performer", "emotion"]

# ==========================================
# 请求事件 (Request Events)
# ==========================================

class RequestEvent(BaseEvent, RequestActionMixin):
    post_type: PostType = Field(default=PostType.REQUEST)
    request_type: RequestType
    user_id: str
    comment: Optional[str] = None
    flag: str

    @field_validator("user_id", mode="before")
    def _uid(cls, v): return str(v)

class FriendRequestEvent(RequestEvent):
    request_type: RequestType = Field(default=RequestType.FRIEND)

class GroupRequestEvent(RequestEvent):
    request_type: RequestType = Field(default=RequestType.GROUP)
    sub_type: str = Field(default="add")
    group_id: str

    @field_validator("group_id", mode="before")
    def _gid(cls, v): return str(v)

# ==========================================
# 元事件 (Meta Events)
# ==========================================

class MetaEvent(BaseEvent):
    post_type: PostType = Field(default=PostType.META_EVENT)
    meta_event_type: MetaEventType

class LifecycleMetaEvent(MetaEvent):
    meta_event_type: MetaEventType = Field(default=MetaEventType.LIFECYCLE)
    sub_type: str = Field(default="enable")

class HeartbeatMetaEvent(MetaEvent):
    meta_event_type: MetaEventType = Field(default=MetaEventType.HEARTBEAT)
    status: Status
    interval: int