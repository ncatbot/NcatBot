"""系统/杂项 API 响应类型"""

from __future__ import annotations

from typing import List, Optional

from ._base import NapCatModel


class VersionInfo(NapCatModel):
    """版本信息

    对应: ``get_version_info``
    """

    app_name: Optional[str] = None
    protocol_version: Optional[str] = None
    app_version: Optional[str] = None


class BotStatus(NapCatModel):
    """运行状态

    对应: ``get_status``
    """

    online: bool = False
    good: bool = False


class EmojiLikeUser(NapCatModel):
    """表情回应的用户条目

    对应: ``fetch_emoji_like`` 返回的 emojiLikesList 中的每一项
    """

    tinyId: Optional[str] = None
    nickName: Optional[str] = None
    headUrl: Optional[str] = None


class EmojiLikeInfo(NapCatModel):
    """表情回应详情

    对应: ``fetch_emoji_like``
    """

    emojiLikesList: Optional[List[EmojiLikeUser]] = None
    cookie: Optional[str] = None
    isLastPage: Optional[bool] = None
    isFirstPage: Optional[bool] = None
    result: Optional[int] = None
    errMsg: Optional[str] = None


class EmojiLikesUser(NapCatModel):
    """表情点赞列表中的用户条目

    对应: ``get_emoji_likes`` 返回的 emoji_like_list 中的每一项
    """

    user_id: str = ""
    nick_name: Optional[str] = None


class EmojiLikesResult(NapCatModel):
    """消息表情点赞列表

    对应: ``get_emoji_likes``
    """

    emoji_like_list: Optional[List[EmojiLikesUser]] = None


class OcrText(NapCatModel):
    """OCR 识别的单条文本

    对应: ``ocr_image`` 返回的 texts 列表中的每一项
    """

    text: Optional[str] = None
    confidence: Optional[float] = None
    coordinates: Optional[list] = None


class OcrResult(NapCatModel):
    """图片 OCR 结果

    对应: ``ocr_image``
    """

    texts: Optional[List[OcrText]] = None


class PttTextResult(NapCatModel):
    """语音转文字结果

    对应: ``fetch_ptt_text``
    """

    text: str = ""


class RecentContactMessage(NapCatModel):
    """最近联系人中的最新消息（内嵌结构）"""

    self_id: str = ""
    user_id: str = ""
    time: Optional[int] = None
    real_seq: Optional[str] = None
    message_type: Optional[str] = None
    raw_message: Optional[str] = None
    message_format: Optional[str] = None
    post_type: Optional[str] = None
    group_id: Optional[str] = None
    group_name: Optional[str] = None


class RecentContact(NapCatModel):
    """最近联系人条目

    对应: ``get_recent_contact`` 中的每一项
    """

    peerUin: Optional[str] = None
    remark: Optional[str] = None
    msgTime: Optional[str] = None
    chatType: Optional[int] = None
    msgId: Optional[str] = None
    sendNickName: Optional[str] = None
    sendMemberName: Optional[str] = None
    peerName: Optional[str] = None
    lastestMsg: Optional[RecentContactMessage] = None
