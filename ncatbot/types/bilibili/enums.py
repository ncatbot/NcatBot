"""Bilibili 平台专用枚举"""

from enum import Enum

__all__ = [
    "BiliPostType",
    "BiliLiveEventType",
    "BiliSessionEventType",
    "BiliCommentEventType",
    "BiliDynamicEventType",
]


class BiliPostType(str, Enum):
    LIVE = "live"
    MESSAGE = "message"
    COMMENT = "comment"
    DYNAMIC = "dynamic"
    SYSTEM = "system"


class BiliLiveEventType(str, Enum):
    """直播间事件类型 — 值与 bilibili-api cmd 一致"""

    DANMU_MSG = "DANMU_MSG"
    SEND_GIFT = "SEND_GIFT"
    COMBO_SEND = "COMBO_SEND"
    GUARD_BUY = "GUARD_BUY"
    SUPER_CHAT_MESSAGE = "SUPER_CHAT_MESSAGE"
    SUPER_CHAT_MESSAGE_JPN = "SUPER_CHAT_MESSAGE_JPN"
    SUPER_CHAT_MESSAGE_DELETE = "SUPER_CHAT_MESSAGE_DELETE"
    INTERACT_WORD_V2 = "INTERACT_WORD_V2"
    ENTRY_EFFECT = "ENTRY_EFFECT"
    LIKE_INFO_V3_CLICK = "LIKE_INFO_V3_CLICK"
    LIKE_INFO_V3_UPDATE = "LIKE_INFO_V3_UPDATE"
    VIEW = "VIEW"
    WATCHED_CHANGE = "WATCHED_CHANGE"
    ROOM_CHANGE = "ROOM_CHANGE"
    LIVE = "LIVE"
    PREPARING = "PREPARING"
    ROOM_BLOCK_MSG = "ROOM_BLOCK_MSG"
    ROOM_SILENT_ON = "ROOM_SILENT_ON"
    ROOM_SILENT_OFF = "ROOM_SILENT_OFF"
    ROOM_REAL_TIME_MESSAGE_UPDATE = "ROOM_REAL_TIME_MESSAGE_UPDATE"
    WARNING = "WARNING"
    CUT_OFF = "CUT_OFF"
    CUT_OFF_V2 = "CUT_OFF_V2"
    ANCHOR_LOT_START = "ANCHOR_LOT_START"
    ANCHOR_LOT_END = "ANCHOR_LOT_END"
    ANCHOR_LOT_AWARD = "ANCHOR_LOT_AWARD"
    DANMU_AGGREGATION = "DANMU_AGGREGATION"
    DM_INTERACTION = "DM_INTERACTION"
    ONLINE_RANK_COUNT = "ONLINE_RANK_COUNT"
    ONLINE_RANK_V3 = "ONLINE_RANK_V3"
    STOP_LIVE_ROOM_LIST = "STOP_LIVE_ROOM_LIST"


class BiliSessionEventType(str, Enum):
    """私信消息类型 — 值与 bilibili-api EventType.value 一致"""

    TEXT = "1"
    PICTURE = "2"
    WITHDRAW = "5"
    GROUPS_PICTURE = "6"
    SHARE_VIDEO = "7"
    NOTICE = "10"
    PUSHED_VIDEO = "11"


class BiliCommentEventType(str, Enum):
    """评论事件类型"""

    NEW_REPLY = "new_reply"
    NEW_SUB_REPLY = "new_sub_reply"


class BiliDynamicEventType(str, Enum):
    """动态事件类型"""

    NEW_DYNAMIC = "new_dynamic"
    DELETED_DYNAMIC = "deleted_dynamic"
