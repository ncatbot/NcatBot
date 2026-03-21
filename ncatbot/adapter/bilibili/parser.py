"""Bilibili 事件解析器

将三类数据源 (live / session / comment) 的原始数据转换为 BaseEventData 数据模型。
只产出纯数据模型，不创建实体。
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, Optional

from ncatbot.types.bilibili.events import (
    BiliCommentEventData,
    BiliConnectionEventData,
    BiliDynamicEventData,
    BiliPrivateMessageEventData,
    BiliPrivateMessageWithdrawEventData,
    DanmuAggregationEventData,
    DanmuMsgEventData,
    DmInteractionEventData,
    EntryEffectEventData,
    GiftEventData,
    GuardBuyEventData,
    InteractEventData,
    LikeEventData,
    LikeUpdateEventData,
    LiveStatusEventData,
    OnlineRankCountEventData,
    OnlineRankV3EventData,
    RoomBlockEventData,
    RoomChangeEventData,
    RoomSilentEventData,
    SuperChatEventData,
    ViewEventData,
    WatchedChangeEventData,
)
from ncatbot.types.bilibili.enums import BiliLiveEventType, BiliSessionEventType
from ncatbot.types.bilibili.models import (
    LiveRoomInfo,
    DynamicStatInfo,
    DynamicVideoInfo,
    DynamicMusicInfo,
    DynamicArticleInfo,
    DynamicLiveRcmdInfo,
)
from ncatbot.types.bilibili.sender import BiliSender
from ncatbot.types.common.base import BaseEventData
from ncatbot.types.common.segment.array import MessageArray
from ncatbot.utils import get_log

LOG = get_log("BiliEventParser")


class BiliEventParser:
    """统一事件解析器 — 按 source_type 三路由"""

    def __init__(self, self_id: str = "0") -> None:
        self._self_id = self_id

    def parse(self, source_type: str, raw_data: dict) -> Optional[BaseEventData]:
        try:
            if source_type == "live":
                return self._parse_live(raw_data)
            if source_type == "session":
                return self._parse_session(raw_data)
            if source_type == "comment":
                return self._parse_comment(raw_data)
            if source_type == "dynamic":
                return self._parse_dynamic(raw_data)
        except Exception:
            LOG.debug(
                "解析 %s 事件失败: %s",
                source_type,
                str(raw_data)[:200],
                exc_info=True,
            )
        return None

    # ==================== 直播解析 ====================

    def _parse_live(self, callback_info: dict) -> Optional[BaseEventData]:
        cmd = callback_info.get("type", "")
        room_id = str(
            callback_info.get("room_real_id", callback_info.get("room_display_id", ""))
        )
        data = callback_info.get("data")
        now = int(time.time())

        common = dict(
            time=now,
            self_id=self._self_id,
            platform="bilibili",
            room_id=room_id,
        )

        parser = _LIVE_PARSERS.get(cmd)
        if parser is not None:
            result = parser(data, common)
            # 开播事件：附加直播间信息
            if isinstance(result, LiveStatusEventData) and result.status == "live":
                raw_room_info = callback_info.get("room_info")
                if raw_room_info is not None:
                    result.room_info = LiveRoomInfo.from_raw(raw_room_info)
            return result

        # 系统事件
        if cmd in ("VERIFICATION_SUCCESSFUL", "DISCONNECT", "TIMEOUT"):
            return BiliConnectionEventData(
                **common,
                event_type=cmd.lower(),
            )

        if cmd in _SILENT_IGNORE:
            return None

        LOG.warning("跳过未注册直播事件: %s, 原始数据: %s", cmd, data)
        return None

    # ==================== 私信解析 ====================

    def _parse_session(self, raw: dict) -> Optional[BaseEventData]:
        now = int(time.time())
        common = dict(
            time=raw.get("timestamp", now),
            self_id=self._self_id,
            platform="bilibili",
        )
        msg_type = str(raw.get("msg_type", ""))

        if msg_type == BiliSessionEventType.WITHDRAW:
            return BiliPrivateMessageWithdrawEventData(
                **common,
                user_id=str(raw.get("sender_uid", "")),
                msg_key=str(raw.get("msg_key", "")),
            )

        # 普通消息
        content = raw.get("content", "")
        msg_array = MessageArray()
        if content:
            msg_array.add_text(str(content))

        sender = BiliSender(
            user_id=str(raw.get("sender_uid", "")),
            nickname=str(raw.get("sender_uid", "")),
        )

        return BiliPrivateMessageEventData(
            **common,
            user_id=str(raw.get("sender_uid", "")),
            user_name=str(raw.get("sender_uid", "")),
            message=msg_array,
            msg_type=msg_type,
            msg_key=str(raw.get("msg_key", "")),
            msg_seqno=raw.get("msg_seqno", 0),
            receiver_id=str(raw.get("receiver_id", "")),
            sender=sender,
        )

    # ==================== 评论解析 ====================

    def _parse_comment(self, raw: dict) -> Optional[BaseEventData]:
        reply = raw.get("reply", {})
        member = reply.get("member", {})
        content_obj = reply.get("content", {})

        sender = BiliSender(
            user_id=str(member.get("mid", "")),
            nickname=member.get("uname", ""),
            face_url=member.get("avatar", ""),
        )

        return BiliCommentEventData(
            time=reply.get("ctime", int(time.time())),
            self_id=self._self_id,
            platform="bilibili",
            resource_id=str(raw.get("resource_id", "")),
            resource_type=str(raw.get("resource_type", "")),
            comment_id=str(reply.get("rpid", "")),
            user_id=str(member.get("mid", "")),
            user_name=member.get("uname", ""),
            content=content_obj.get("message", ""),
            root_id=str(reply.get("root", "0")),
            parent_id=str(reply.get("parent", "0")),
            like_count=reply.get("like", 0),
            ctime=reply.get("ctime", 0),
            sender=sender,
        )

    # ==================== 动态解析 ====================

    def _parse_dynamic(self, raw: dict) -> Optional[BaseEventData]:
        import json as _json
        from ncatbot.types.bilibili.enums import BiliDynamicEventType

        item = raw.get("dynamic") or {}
        dynamic_status = raw.get("status", "new")  # "new" | "deleted"
        now = int(time.time())

        # 基础信息 — 与 DTO.from_raw 保持一致
        dynamic_id = item.get("id_str", "")
        dynamic_type = item.get("type", "")
        modules = item.get("modules") or {}
        author_info = modules.get("module_author") or {}
        pub_ts = author_info.get("pub_ts", 0)
        pub_time = author_info.get("pub_time", "")

        uid = str(author_info.get("mid", raw.get("uid", "")))
        uname = author_info.get("name", "")
        face = author_info.get("face", "")

        # 解析动态内容
        text = None
        pics_url = None
        video = None
        music = None
        article = None
        live_rcmd = None
        tag = None
        stat = None

        module_dynamic = modules.get("module_dynamic") or {}
        major = module_dynamic.get("major") or {}

        # 统计信息
        stat_info = modules.get("module_stat")
        if stat_info:
            stat = DynamicStatInfo(
                comment_count=(stat_info.get("comment") or {}).get("count", 0),
                like_count=(stat_info.get("like") or {}).get("count", 0),
                forward_count=(stat_info.get("forward") or {}).get("count", 0),
            )

        # 标签（如置顶）
        if modules.get("module_tag"):
            tag = modules["module_tag"].get("text")

        # 文字/图片动态
        if dynamic_type in ("DYNAMIC_TYPE_WORD", "DYNAMIC_TYPE_DRAW"):
            opus = major.get("opus") or {}
            summary = opus.get("summary") or {}
            text = summary.get("text", "")
            pics = opus.get("pics") or []
            if pics:
                pics_url = [pic.get("url", "") for pic in pics]

        # 视频动态
        elif dynamic_type == "DYNAMIC_TYPE_AV":
            archive = major.get("archive") or {}
            desc_info = module_dynamic.get("desc")
            stat_v = archive.get("stat") or {}
            video = DynamicVideoInfo(
                av_id=str(archive.get("aid", "")),
                bv_id=archive.get("bvid", ""),
                title=archive.get("title", ""),
                cover=archive.get("cover", ""),
                desc=archive.get("desc", ""),
                duration_text=archive.get("duration_text", ""),
                dynamic_text=desc_info.get("text", "") if desc_info else "",
                play_count=str(stat_v.get("play", "")),
                danmaku_count=str(stat_v.get("danmaku", "")),
            )

        # 音乐动态
        elif dynamic_type == "DYNAMIC_TYPE_MUSIC":
            music_info = major.get("music") or {}
            desc_info = module_dynamic.get("desc")
            music = DynamicMusicInfo(
                music_id=str(music_info.get("id", "")),
                title=music_info.get("title", ""),
                cover=music_info.get("cover", ""),
                label=music_info.get("label", ""),
                dynamic_text=desc_info.get("text", "") if desc_info else "",
            )

        # 专栏动态
        elif dynamic_type == "DYNAMIC_TYPE_ARTICLE":
            opus = major.get("opus") or {}
            summary_info = opus.get("summary") or {}
            article = DynamicArticleInfo(
                title=opus.get("title", ""),
                summary=summary_info.get("text", ""),
                has_more=summary_info.get("has_more", False),
                article_id=int(dynamic_id) if dynamic_id.isdigit() else 0,
            )

        # 直播推荐动态
        elif dynamic_type == "DYNAMIC_TYPE_LIVE_RCMD":
            live_rcmd_obj = major.get("live_rcmd") or {}
            live_rcmd_content = live_rcmd_obj.get("content", "{}")
            try:
                live_data = _json.loads(live_rcmd_content)
            except Exception:
                live_data = {}
            live_play_info = live_data.get("live_play_info") or {}
            live_rcmd = DynamicLiveRcmdInfo(
                room_id=live_play_info.get("room_id", 0),
                live_status=live_play_info.get("live_status", 0),
                title=live_play_info.get("title", ""),
                cover=live_play_info.get("cover", ""),
                online=live_play_info.get("online", 0),
                area_id=live_play_info.get("area_id", 0),
                area_name=live_play_info.get("area_name", ""),
                parent_area_id=live_play_info.get("parent_area_id", 0),
                parent_area_name=live_play_info.get("parent_area_name", ""),
                live_start_time=live_play_info.get("live_start_time", 0),
            )

        # 转发动态
        forward_dynamic_id = None
        if dynamic_type == "DYNAMIC_TYPE_FORWARD":
            desc_info = module_dynamic.get("desc")
            text = desc_info.get("text", "") if desc_info else ""
            orig = item.get("orig") or {}
            forward_dynamic_id = orig.get("id_str", "")

        # 映射 status → dynamic_event_type
        if dynamic_status == "deleted":
            dyn_event_type = BiliDynamicEventType.DELETED_DYNAMIC
        else:
            dyn_event_type = BiliDynamicEventType.NEW_DYNAMIC

        sender = BiliSender(
            user_id=uid,
            nickname=uname,
            face_url=face,
        )

        return BiliDynamicEventData(
            time=pub_ts or now,
            self_id=self._self_id,
            platform="bilibili",
            dynamic_event_type=dyn_event_type,
            dynamic_status=dynamic_status,
            dynamic_id=dynamic_id,
            dynamic_type=dynamic_type,
            uid=uid,
            user_name=uname,
            face_url=face,
            pub_ts=pub_ts,
            pub_time=pub_time,
            text=text,
            pics_url=pics_url,
            tag=tag,
            stat=stat,
            video=video,
            music=music,
            article=article,
            live_rcmd=live_rcmd,
            forward_dynamic_id=forward_dynamic_id,
            sender=sender,
        )


# ==================== 直播事件解析器注册表 ====================


def _parse_danmu(data: dict, common: dict) -> DanmuMsgEventData:
    info = data.get("info", [])
    text = info[1] if len(info) > 1 else ""
    user_info = info[2] if len(info) > 2 else []
    medal_info = info[3] if len(info) > 3 else []

    uid = str(user_info[0]) if len(user_info) > 0 else ""
    uname = str(user_info[1]) if len(user_info) > 1 else ""
    is_admin = bool(user_info[2]) if len(user_info) > 2 else False

    medal_name = str(medal_info[1]) if len(medal_info) > 1 else ""
    medal_level = int(medal_info[0]) if len(medal_info) > 0 else 0

    msg_array = MessageArray()
    msg_array.add_text(str(text))

    sender = BiliSender(
        user_id=uid,
        nickname=uname,
        medal_name=medal_name,
        medal_level=medal_level,
        admin=is_admin,
    )

    return DanmuMsgEventData(
        **common,
        user_id=uid,
        user_name=uname,
        message=msg_array,
        sender=sender,
    )


def _parse_gift(data: dict, common: dict) -> GiftEventData:
    d = data.get("data", data)
    sender = BiliSender(
        user_id=str(d.get("uid", "")),
        nickname=d.get("uname", ""),
        face_url=d.get("face", ""),
    )
    return GiftEventData(
        **common,
        user_id=str(d.get("uid", "")),
        user_name=d.get("uname", ""),
        gift_name=d.get("giftName", ""),
        gift_id=str(d.get("giftId", "")),
        num=d.get("num", 0),
        price=d.get("price", 0),
        coin_type=d.get("coin_type", ""),
        sender=sender,
    )


def _parse_sc(data: dict, common: dict) -> SuperChatEventData:
    d = data.get("data", data)
    user_info = d.get("user_info", {})
    sender = BiliSender(
        user_id=str(d.get("uid", "")),
        nickname=user_info.get("uname", ""),
        face_url=user_info.get("face", ""),
    )
    return SuperChatEventData(
        **common,
        user_id=str(d.get("uid", "")),
        user_name=user_info.get("uname", ""),
        content=d.get("message", ""),
        price=d.get("price", 0),
        duration=d.get("time", 0),
        sender=sender,
    )


def _parse_guard(data: dict, common: dict) -> GuardBuyEventData:
    d = data.get("data", data)
    sender = BiliSender(
        user_id=str(d.get("uid", "")),
        nickname=d.get("username", ""),
        guard_level=d.get("guard_level", 0),
    )
    return GuardBuyEventData(
        **common,
        user_id=str(d.get("uid", "")),
        user_name=d.get("username", ""),
        guard_level=d.get("guard_level", 0),
        price=d.get("price", 0),
        sender=sender,
    )


def _parse_interact(data: dict, common: dict) -> InteractEventData:
    d = data.get("data", data)
    # INTERACT_WORD_V2 的 pb_decoded 如果可用则使用
    pb = d.get("pb_decoded", {})
    uname = pb.get("uname", d.get("uname", ""))
    uid = str(pb.get("uid", d.get("uid", "")))
    interact_type = pb.get("msg_type", d.get("msg_type", 0))

    sender = BiliSender(user_id=uid, nickname=uname)
    return InteractEventData(
        **common,
        user_id=uid,
        user_name=uname,
        interact_type=int(interact_type),
        sender=sender,
    )


def _parse_like(data: dict, common: dict) -> LikeEventData:
    d = data.get("data", data)
    sender = BiliSender(
        user_id=str(d.get("uid", "")),
        nickname=d.get("uname", ""),
    )
    return LikeEventData(
        **common,
        user_id=str(d.get("uid", "")),
        user_name=d.get("uname", ""),
        like_count=d.get("like_count", 0),
        sender=sender,
    )


def _parse_view(data: Any, common: dict) -> ViewEventData:
    view = data if isinstance(data, int) else 0
    return ViewEventData(**common, view=view)


def _parse_live_status(data: dict, common: dict, status: str) -> LiveStatusEventData:
    live_event_type = (
        BiliLiveEventType.LIVE if status == "live" else BiliLiveEventType.PREPARING
    )
    return LiveStatusEventData(**common, live_event_type=live_event_type, status=status)


def _parse_room_change(data: dict, common: dict) -> RoomChangeEventData:
    d = data.get("data", data)
    return RoomChangeEventData(
        **common,
        title=d.get("title", ""),
        area_name=d.get("area_name", ""),
    )


def _parse_room_block(data: dict, common: dict) -> RoomBlockEventData:
    d = data.get("data", data)
    return RoomBlockEventData(
        **common,
        user_id=str(d.get("uid", "")),
        user_name=d.get("uname", ""),
    )


def _parse_room_silent(data: dict, common: dict, on: bool) -> RoomSilentEventData:
    d = data.get("data", data)
    return RoomSilentEventData(
        **common,
        live_event_type=BiliLiveEventType.ROOM_SILENT_ON
        if on
        else BiliLiveEventType.ROOM_SILENT_OFF,
        silent_type=d.get("type", ""),
        level=d.get("level", 0),
        second=d.get("second", 0),
    )


def _parse_watched_change(data: dict, common: dict) -> WatchedChangeEventData:
    d = data.get("data", data)
    return WatchedChangeEventData(
        **common,
        num=d.get("num", 0),
        text_small=d.get("text_small", ""),
        text_large=d.get("text_large", ""),
    )


def _parse_like_update(data: dict, common: dict) -> LikeUpdateEventData:
    d = data.get("data", data)
    return LikeUpdateEventData(**common, click_count=d.get("click_count", 0))


def _parse_online_rank_count(data: dict, common: dict) -> OnlineRankCountEventData:
    d = data.get("data", data)
    return OnlineRankCountEventData(**common, count=d.get("count", 0))


def _parse_online_rank_v3(data: dict, common: dict) -> OnlineRankV3EventData:
    d = data.get("data", data)
    pb = d.get("pb_decoded", {})
    online_list = pb.get("online_list", []) if pb else []
    return OnlineRankV3EventData(**common, online_list=online_list)


def _parse_danmu_aggregation(data: dict, common: dict) -> DanmuAggregationEventData:
    d = data.get("data", data)
    return DanmuAggregationEventData(
        **common,
        activity_identity=str(d.get("activity_identity", "")),
        msg=d.get("msg", ""),
        aggregation_num=d.get("aggregation_num", 0),
    )


def _parse_dm_interaction(data: dict, common: dict) -> DmInteractionEventData:
    d = data.get("data", data)
    import json

    inner = d.get("data", "{}")
    if isinstance(inner, str):
        try:
            inner = json.loads(inner)
        except (json.JSONDecodeError, TypeError):
            inner = {}
    return DmInteractionEventData(
        **common,
        interaction_type=d.get("type", 0),
        suffix_text=inner.get("suffix_text", ""),
    )


def _parse_entry_effect(data: dict, common: dict) -> EntryEffectEventData:
    d = data.get("data", data)
    uid = str(d.get("uid", ""))
    uname = d.get("copy_writing_v2", d.get("copy_writing", ""))
    # 提取 <% ... %> 中的用户名
    if "<%" in uname and "%>" in uname:
        uname = uname.split("<%")[1].split("%>")[0]
    sender = BiliSender(user_id=uid, nickname=uname)
    return EntryEffectEventData(
        **common,
        user_id=uid,
        user_name=uname,
        sender=sender,
    )


# 静默忽略的事件 — 无业务价值
_SILENT_IGNORE: set = {
    "STOP_LIVE_ROOM_LIST",
    "ROOM_REAL_TIME_MESSAGE_UPDATE",
    "NOTICE_MSG",
}


_LIVE_PARSERS: Dict[str, Callable[..., BaseEventData]] = {
    "DANMU_MSG": _parse_danmu,
    "SEND_GIFT": _parse_gift,
    "COMBO_SEND": _parse_gift,
    "SUPER_CHAT_MESSAGE": _parse_sc,
    "SUPER_CHAT_MESSAGE_JPN": _parse_sc,
    "GUARD_BUY": _parse_guard,
    "INTERACT_WORD_V2": _parse_interact,
    "LIKE_INFO_V3_CLICK": _parse_like,
    "VIEW": _parse_view,
    "ROOM_CHANGE": _parse_room_change,
    "ROOM_BLOCK_MSG": _parse_room_block,
    "LIVE": lambda data, common: _parse_live_status(data, common, "live"),
    "PREPARING": lambda data, common: _parse_live_status(data, common, "preparing"),
    "ROOM_SILENT_ON": lambda data, common: _parse_room_silent(data, common, True),
    "ROOM_SILENT_OFF": lambda data, common: _parse_room_silent(data, common, False),
    # — 新增事件 —
    "WATCHED_CHANGE": _parse_watched_change,
    "LIKE_INFO_V3_UPDATE": _parse_like_update,
    "ONLINE_RANK_COUNT": _parse_online_rank_count,
    "ONLINE_RANK_V3": _parse_online_rank_v3,
    "DANMU_AGGREGATION": _parse_danmu_aggregation,
    "DM_INTERACTION": _parse_dm_interaction,
    "ENTRY_EFFECT": _parse_entry_effect,
}
