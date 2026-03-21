"""Bilibili 平台数据模型 — 非事件类结构化数据"""

from __future__ import annotations

from typing import Optional, Tuple

from pydantic import BaseModel, Field


__all__ = [
    "LiveRoomInfo",
    "RoomInfo",
    "AnchorInfo",
    "WatchedShow",
    "DynamicStatInfo",
    "DynamicVideoInfo",
    "DynamicMusicInfo",
    "DynamicArticleInfo",
    "DynamicLiveRcmdInfo",
]


class RoomInfo(BaseModel):
    """直播间信息"""

    uid: int = 0
    room_id: int = 0
    title: str = ""
    cover_url: str = ""
    background_url: str = ""
    description: str = ""
    tags: Tuple[str, ...] = ()
    live_status: int = 0
    live_start_time: int = 0
    parent_area_name: str = ""
    parent_area_id: int = 0
    area_name: str = ""
    area_id: int = 0
    keyframe_url: str = ""
    online: int = 0


class AnchorInfo(BaseModel):
    """主播信息"""

    name: str = ""
    face_url: str = ""
    gender: str = ""
    official_info: str = ""
    fanclub_name: str = ""
    fanclub_num: int = 0
    live_level: int = 0
    live_score: int = 0
    live_upgrade_score: int = 0


class WatchedShow(BaseModel):
    """观看榜信息"""

    num: int = 0
    text_small: str = ""
    text_large: str = ""


class LiveRoomInfo(BaseModel):
    """直播间完整信息"""

    room_info: RoomInfo = Field(default_factory=RoomInfo)
    anchor_info: AnchorInfo = Field(default_factory=AnchorInfo)
    watched_show: WatchedShow = Field(default_factory=WatchedShow)

    @classmethod
    def from_raw(cls, data: dict) -> Optional["LiveRoomInfo"]:
        """从 bilibili-api ``LiveRoom.get_room_info()`` 原始数据构造模型。"""
        try:
            ri = data.get("room_info", {})
            tags_str: str = ri.get("tags", "")
            tags = tuple(tags_str.split(",")) if tags_str else ()

            room_info = RoomInfo(
                uid=ri.get("uid", 0),
                room_id=ri.get("room_id", 0),
                title=ri.get("title", ""),
                cover_url=ri.get("cover", ""),
                background_url=ri.get("background", ""),
                description=ri.get("description", ""),
                tags=tags,
                live_status=ri.get("live_status", 0),
                live_start_time=ri.get("live_start_time", 0),
                parent_area_name=ri.get("parent_area_name", ""),
                parent_area_id=ri.get("parent_area_id", 0),
                area_name=ri.get("area_name", ""),
                area_id=ri.get("area_id", 0),
                keyframe_url=ri.get("keyframe", ""),
                online=ri.get("online", 0),
            )

            ai = data.get("anchor_info", {})
            base = ai.get("base_info", {})
            medal = ai.get("medal_info", {})
            live_info = ai.get("live_info", {})
            official = base.get("official_info", {})

            anchor_info = AnchorInfo(
                name=base.get("uname", ""),
                face_url=base.get("face", ""),
                gender=base.get("gender", ""),
                official_info=official.get("title", ""),
                fanclub_name=medal.get("medal_name", ""),
                fanclub_num=medal.get("fansclub", 0),
                live_level=live_info.get("level", 0),
                live_score=live_info.get("score", 0),
                live_upgrade_score=live_info.get("upgrade_score", 0),
            )

            ws = data.get("watched_show", {})
            watched_show = WatchedShow(
                num=ws.get("num", 0),
                text_small=ws.get("text_small", ""),
                text_large=ws.get("text_large", ""),
            )

            return cls(
                room_info=room_info,
                anchor_info=anchor_info,
                watched_show=watched_show,
            )
        except Exception:
            return None


# ==================== 动态相关模型 ====================


class DynamicStatInfo(BaseModel):
    """动态统计信息"""

    comment_count: int = 0
    like_count: int = 0
    forward_count: int = 0


class DynamicVideoInfo(BaseModel):
    """动态中的视频信息"""

    av_id: str = ""
    bv_id: str = ""
    title: str = ""
    cover: str = ""
    desc: str = ""
    duration_text: str = ""
    play_count: str = ""
    danmaku_count: str = ""
    dynamic_text: str = ""


class DynamicMusicInfo(BaseModel):
    """动态中的音乐信息"""

    music_id: str = ""
    title: str = ""
    cover: str = ""
    label: str = ""
    dynamic_text: str = ""


class DynamicArticleInfo(BaseModel):
    """动态中的专栏信息"""

    title: str = ""
    summary: str = ""
    has_more: bool = False
    article_id: int = 0


class DynamicLiveRcmdInfo(BaseModel):
    """动态中的直播推荐信息"""

    room_id: int = 0
    live_status: int = 0
    title: str = ""
    cover: str = ""
    online: int = 0
    area_id: int = 0
    area_name: str = ""
    parent_area_id: int = 0
    parent_area_name: str = ""
    live_start_time: int = 0
