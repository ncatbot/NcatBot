"""QQ 平台专用类型"""

from .enums import (
    PostType,
    EventType,
    MessageType,
    MetaEventType,
    NoticeType,
    NoticeNotifySubType,
    GroupAdminSubType,
    GroupDecreaseSubType,
    GroupIncreaseSubType,
    GroupBanSubType,
    RequestType,
)
from .sender import QQSender, GroupSender
from .misc import Anonymous, FileInfo, Status
from .message import (
    GroupMessageEventData,
    MessageEventData,
    PrivateMessageEventData,
)
from .notice import (
    EmojiLike,
    FriendAddNoticeEventData,
    FriendRecallNoticeEventData,
    GroupAdminNoticeEventData,
    GroupBanNoticeEventData,
    GroupDecreaseNoticeEventData,
    GroupIncreaseNoticeEventData,
    GroupRecallNoticeEventData,
    GroupMsgEmojiLikeNoticeEventData,
    GroupUploadNoticeEventData,
    HonorNotifyEventData,
    LuckyKingNotifyEventData,
    NoticeEventData,
    NotifyEventData,
    PokeNotifyEventData,
)
from .request import (
    FriendRequestEventData,
    GroupRequestEventData,
    RequestEventData,
)
from .meta import (
    HeartbeatMetaEventData,
    HeartbeatTimeoutMetaEventData,
    LifecycleMetaEventData,
    MetaEventData,
)
from .segment import (
    Face,
    Forward,
    ForwardNode,
    Json,
    Location,
    Markdown,
    Music,
    QQImage,
    QQRecord,
    Share,
    parse_cq_code_to_onebot11,
)
from .helper import ForwardConstructor

__all__ = [
    # enums
    "PostType",
    "MessageType",
    "NoticeType",
    "NoticeNotifySubType",
    "GroupAdminSubType",
    "GroupDecreaseSubType",
    "GroupIncreaseSubType",
    "GroupBanSubType",
    "RequestType",
    "MetaEventType",
    "EventType",
    # sender
    "QQSender",
    "GroupSender",
    # misc
    "Anonymous",
    "FileInfo",
    "Status",
    # message
    "MessageEventData",
    "PrivateMessageEventData",
    "GroupMessageEventData",
    # notice
    "EmojiLike",
    "NoticeEventData",
    "GroupUploadNoticeEventData",
    "GroupAdminNoticeEventData",
    "GroupDecreaseNoticeEventData",
    "GroupIncreaseNoticeEventData",
    "GroupBanNoticeEventData",
    "FriendAddNoticeEventData",
    "GroupRecallNoticeEventData",
    "FriendRecallNoticeEventData",
    "GroupMsgEmojiLikeNoticeEventData",
    "NotifyEventData",
    "PokeNotifyEventData",
    "LuckyKingNotifyEventData",
    "HonorNotifyEventData",
    # request
    "RequestEventData",
    "FriendRequestEventData",
    "GroupRequestEventData",
    # meta
    "MetaEventData",
    "LifecycleMetaEventData",
    "HeartbeatMetaEventData",
    "HeartbeatTimeoutMetaEventData",
    # segments
    "Face",
    "Share",
    "Location",
    "Music",
    "Json",
    "Markdown",
    "ForwardNode",
    "Forward",
    "QQImage",
    "QQRecord",
    "parse_cq_code_to_onebot11",
    # helper
    "ForwardConstructor",
]
