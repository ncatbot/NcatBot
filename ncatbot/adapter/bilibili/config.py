"""Bilibili 适配器配置模型"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class CommentWatch(BaseModel):
    """评论监听条目"""

    id: str
    type: str = "video"


class DynamicWatch(BaseModel):
    """动态监听条目"""

    uid: int


class BilibiliConfig(BaseModel):
    """Bilibili 适配器专属配置"""

    # 认证
    sessdata: str = ""
    bili_jct: str = ""
    buvid3: str = ""
    dedeuserid: str = ""
    ac_time_value: str = ""

    # 初始监听源
    live_rooms: List[int] = Field(default_factory=list)
    enable_session: bool = False
    comment_watches: List[CommentWatch] = Field(default_factory=list)
    dynamic_watches: List[DynamicWatch] = Field(default_factory=list)

    # 轮询配置
    session_poll_interval: float = 6.0
    comment_poll_interval: float = 30.0
    dynamic_poll_interval: float = 600.0

    # 连接
    max_retry: int = 5
    retry_after: float = 1.0
