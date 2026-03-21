"""Bilibili 平台事件数据模型"""

from __future__ import annotations


from typing import Optional

from pydantic import Field

from ncatbot.types.common.base import BaseEventData
from ncatbot.types.common.segment.array import MessageArray
from .enums import BiliPostType, BiliLiveEventType, BiliCommentEventType
from .models import LiveRoomInfo
from .sender import BiliSender

__all__ = [
    # live
    "BiliLiveEventData",
    "DanmuMsgEventData",
    "SuperChatEventData",
    "GiftEventData",
    "GuardBuyEventData",
    "InteractEventData",
    "LikeEventData",
    "ViewEventData",
    "LiveStatusEventData",
    "RoomChangeEventData",
    "RoomBlockEventData",
    "RoomSilentEventData",
    "WatchedChangeEventData",
    "LikeUpdateEventData",
    "OnlineRankCountEventData",
    "OnlineRankV3EventData",
    "DanmuAggregationEventData",
    "DmInteractionEventData",
    "EntryEffectEventData",
    # session
    "BiliPrivateMessageEventData",
    "BiliPrivateMessageWithdrawEventData",
    # comment
    "BiliCommentEventData",
    # system
    "BiliConnectionEventData",
]


# ==================== 直播间事件 ====================


class BiliLiveEventData(BaseEventData):
    """直播间事件基类"""

    post_type: str = Field(default=BiliPostType.LIVE)
    live_event_type: str = ""
    room_id: str = ""


class DanmuMsgEventData(BiliLiveEventData):
    """弹幕消息"""

    live_event_type: str = Field(default=BiliLiveEventType.DANMU_MSG)
    user_id: str = ""
    user_name: str = ""
    message: MessageArray = Field(default_factory=MessageArray)
    sender: BiliSender = Field(default_factory=BiliSender)


class SuperChatEventData(BiliLiveEventData):
    """醒目留言 (SC)"""

    live_event_type: str = Field(default=BiliLiveEventType.SUPER_CHAT_MESSAGE)
    user_id: str = ""
    user_name: str = ""
    content: str = ""
    price: int = 0
    duration: int = 0
    sender: BiliSender = Field(default_factory=BiliSender)


class GiftEventData(BiliLiveEventData):
    """礼物"""

    live_event_type: str = Field(default=BiliLiveEventType.SEND_GIFT)
    user_id: str = ""
    user_name: str = ""
    gift_name: str = ""
    gift_id: str = ""
    num: int = 0
    price: int = 0
    coin_type: str = ""
    sender: BiliSender = Field(default_factory=BiliSender)


class GuardBuyEventData(BiliLiveEventData):
    """大航海"""

    live_event_type: str = Field(default=BiliLiveEventType.GUARD_BUY)
    user_id: str = ""
    user_name: str = ""
    guard_level: int = 0
    price: int = 0
    sender: BiliSender = Field(default_factory=BiliSender)


class InteractEventData(BiliLiveEventData):
    """用户进入/关注/分享"""

    live_event_type: str = Field(default=BiliLiveEventType.INTERACT_WORD_V2)
    user_id: str = ""
    user_name: str = ""
    interact_type: int = 0
    sender: BiliSender = Field(default_factory=BiliSender)


class LikeEventData(BiliLiveEventData):
    """点赞"""

    live_event_type: str = Field(default=BiliLiveEventType.LIKE_INFO_V3_CLICK)
    user_id: str = ""
    user_name: str = ""
    like_count: int = 0
    sender: BiliSender = Field(default_factory=BiliSender)


class ViewEventData(BiliLiveEventData):
    """人气值更新"""

    live_event_type: str = Field(default=BiliLiveEventType.VIEW)
    view: int = 0


class LiveStatusEventData(BiliLiveEventData):
    """开播/下播"""

    status: str = ""
    room_info: Optional[LiveRoomInfo] = None


class RoomChangeEventData(BiliLiveEventData):
    """直播间信息变更"""

    live_event_type: str = Field(default=BiliLiveEventType.ROOM_CHANGE)
    title: str = ""
    area_name: str = ""


class RoomBlockEventData(BiliLiveEventData):
    """用户被禁言"""

    live_event_type: str = Field(default=BiliLiveEventType.ROOM_BLOCK_MSG)
    user_id: str = ""
    user_name: str = ""


class RoomSilentEventData(BiliLiveEventData):
    """全员禁言"""

    silent_type: str = ""
    level: int = 0
    second: int = 0


class WatchedChangeEventData(BiliLiveEventData):
    """观看人数变化"""

    live_event_type: str = Field(default=BiliLiveEventType.WATCHED_CHANGE)
    num: int = 0
    text_small: str = ""
    text_large: str = ""


class LikeUpdateEventData(BiliLiveEventData):
    """点赞数更新 (全局累计)"""

    live_event_type: str = Field(default=BiliLiveEventType.LIKE_INFO_V3_UPDATE)
    click_count: int = 0


class OnlineRankCountEventData(BiliLiveEventData):
    """在线排名人数"""

    live_event_type: str = Field(default=BiliLiveEventType.ONLINE_RANK_COUNT)
    count: int = 0


class OnlineRankV3EventData(BiliLiveEventData):
    """在线排名列表"""

    live_event_type: str = Field(default=BiliLiveEventType.ONLINE_RANK_V3)
    online_list: list = Field(default_factory=list)


class DanmuAggregationEventData(BiliLiveEventData):
    """弹幕聚合 (节日/活动弹幕)"""

    live_event_type: str = Field(default=BiliLiveEventType.DANMU_AGGREGATION)
    activity_identity: str = ""
    msg: str = ""
    aggregation_num: int = 0


class DmInteractionEventData(BiliLiveEventData):
    """互动消息 (分享直播间等)"""

    live_event_type: str = Field(default=BiliLiveEventType.DM_INTERACTION)
    interaction_type: int = 0
    suffix_text: str = ""


class EntryEffectEventData(BiliLiveEventData):
    """进场特效"""

    live_event_type: str = Field(default=BiliLiveEventType.ENTRY_EFFECT)
    user_id: str = ""
    user_name: str = ""
    sender: BiliSender = Field(default_factory=BiliSender)


# ==================== 私信事件 ====================


class BiliPrivateMessageEventData(BaseEventData):
    """B 站私信消息"""

    post_type: str = Field(default=BiliPostType.MESSAGE)
    message_type: str = "private"
    user_id: str = ""
    user_name: str = ""
    message: MessageArray = Field(default_factory=MessageArray)
    msg_type: str = ""
    msg_key: str = ""
    msg_seqno: int = 0
    receiver_id: str = ""
    sender: BiliSender = Field(default_factory=BiliSender)


class BiliPrivateMessageWithdrawEventData(BaseEventData):
    """B 站私信撤回"""

    post_type: str = Field(default=BiliPostType.MESSAGE)
    message_type: str = "withdraw"
    user_id: str = ""
    msg_key: str = ""


# ==================== 评论事件 ====================


class BiliCommentEventData(BaseEventData):
    """B 站评论"""

    post_type: str = Field(default=BiliPostType.COMMENT)
    comment_event_type: str = Field(default=BiliCommentEventType.NEW_REPLY)
    resource_id: str = ""
    resource_type: str = ""
    comment_id: str = ""
    user_id: str = ""
    user_name: str = ""
    content: str = ""
    root_id: str = ""
    parent_id: str = ""
    like_count: int = 0
    ctime: int = 0
    sender: BiliSender = Field(default_factory=BiliSender)


# ==================== 系统事件 ====================


class BiliConnectionEventData(BaseEventData):
    """连接状态事件"""

    post_type: str = Field(default=BiliPostType.SYSTEM)
    event_type: str = ""
    room_id: str = ""
