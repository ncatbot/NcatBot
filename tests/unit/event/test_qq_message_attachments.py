"""
QQ 消息事件 HasAttachments 测试

规范:
  QMA-01: QQ MessageEvent isinstance HasAttachments
  QMA-02: get_attachments() 从消息段提取附件
  QMA-03: 纯文本消息返回空 AttachmentList
"""

from __future__ import annotations

import pytest

from ncatbot.adapter.mock.api import MockBotAPI
from ncatbot.event.common.factory import create_entity
from ncatbot.event.common.mixins import HasAttachments
from ncatbot.event.qq.message import GroupMessageEvent
from ncatbot.testing import factory
from ncatbot.types.common.attachment import ImageAttachment, VideoAttachment
from ncatbot.types.common.attachment_list import AttachmentList
from ncatbot.types.common.segment.media import Image, Video

pytestmark = pytest.mark.asyncio


class TestQQMessageAttachments:
    def test_qma01_isinstance_has_attachments(self):
        """QMA-01: QQ MessageEvent 实现 HasAttachments"""
        data = factory.group_message("hi", group_id="111", user_id="222")
        entity = create_entity(data, MockBotAPI())
        assert isinstance(entity, GroupMessageEvent)
        assert isinstance(entity, HasAttachments)

    async def test_qma02_get_attachments_from_segments(self):
        """QMA-02: get_attachments() 提取图片和视频附件"""
        data = factory.group_message("look", group_id="111", user_id="222")
        # 手动注入媒体段
        data.message._segments.extend(
            [
                Image(file="photo.jpg", url="http://cdn/photo.jpg", file_size=2048),
                Video(file="clip.mp4", url="http://cdn/clip.mp4", file_size=5000),
            ]
        )
        entity = create_entity(data, MockBotAPI())
        assert isinstance(entity, GroupMessageEvent)

        atts = await entity.get_attachments()
        assert isinstance(atts, AttachmentList)
        assert len(atts) == 2
        assert isinstance(atts[0], ImageAttachment)
        assert isinstance(atts[1], VideoAttachment)
        assert atts[0].url == "http://cdn/photo.jpg"

    async def test_qma03_text_only(self):
        """QMA-03: 纯文本消息 get_attachments() 返回空"""
        data = factory.group_message("hello", group_id="111", user_id="222")
        entity = create_entity(data, MockBotAPI())

        atts = await entity.get_attachments()
        assert isinstance(atts, AttachmentList)
        assert len(atts) == 0
