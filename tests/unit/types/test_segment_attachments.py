"""
消息段附件桥接测试 — DownloadableSegment.to_attachment() + MessageArray.get_attachments()

规范:
  SEG-01: Image.to_attachment() 返回 ImageAttachment
  SEG-02: Video.to_attachment() 返回 VideoAttachment
  SEG-03: Record.to_attachment() 返回 AudioAttachment
  SEG-04: File.to_attachment() 返回 FileAttachment
  SEG-05: MessageArray.get_attachments() 收集所有可下载段
  SEG-06: MessageArray.get_attachments() 返回 AttachmentList 带过滤能力
  SEG-07: 纯文本消息 get_attachments() 返回空 AttachmentList
"""

from __future__ import annotations

from ncatbot.types.common.attachment import (
    AttachmentKind,
    AudioAttachment,
    FileAttachment,
    ImageAttachment,
    VideoAttachment,
)
from ncatbot.types.common.attachment_list import AttachmentList
from ncatbot.types.common.segment.array import MessageArray
from ncatbot.types.common.segment.media import File, Image, Record, Video
from ncatbot.types.common.segment.text import PlainText


# ---- SEG-01 ~ SEG-04: to_attachment() ----


class TestSegmentToAttachment:
    def test_seg01_image_to_attachment(self):
        """SEG-01: Image.to_attachment() → ImageAttachment"""
        seg = Image(file="photo.jpg", url="http://cdn/photo.jpg", file_size=2048)
        att = seg.to_attachment()
        assert isinstance(att, ImageAttachment)
        assert att.kind == AttachmentKind.IMAGE
        assert att.url == "http://cdn/photo.jpg"
        assert att.name == "photo.jpg"
        assert att.size == 2048

    def test_seg01_image_with_file_name(self):
        """SEG-01: Image 有 file_name 时优先用 file_name"""
        seg = Image(
            file="abc123.image",
            url="http://cdn/abc123",
            file_name="cat.png",
            file_size=100,
        )
        att = seg.to_attachment()
        assert att.name == "cat.png"

    def test_seg01_image_file_id_in_extra(self):
        """SEG-01: file_id 传入 extra"""
        seg = Image(
            file="x.jpg", url="http://cdn/x.jpg", file_id="fid_123", file_size=50
        )
        att = seg.to_attachment()
        assert att.extra["file_id"] == "fid_123"

    def test_seg02_video_to_attachment(self):
        """SEG-02: Video.to_attachment() → VideoAttachment"""
        seg = Video(file="clip.mp4", url="http://cdn/clip.mp4", file_size=5000)
        att = seg.to_attachment()
        assert isinstance(att, VideoAttachment)
        assert att.kind == AttachmentKind.VIDEO

    def test_seg03_record_to_attachment(self):
        """SEG-03: Record.to_attachment() → AudioAttachment"""
        seg = Record(file="voice.silk", url="http://cdn/voice.silk")
        att = seg.to_attachment()
        assert isinstance(att, AudioAttachment)
        assert att.kind == AttachmentKind.AUDIO

    def test_seg04_file_to_attachment(self):
        """SEG-04: File.to_attachment() → FileAttachment"""
        seg = File(file="doc.pdf", url="http://cdn/doc.pdf", file_size=1024)
        att = seg.to_attachment()
        assert isinstance(att, FileAttachment)
        assert att.kind == AttachmentKind.FILE

    def test_seg_no_file_id_no_extra(self):
        """to_attachment() 无 file_id 时 extra 为空"""
        seg = Image(file="x.jpg", url="http://x")
        att = seg.to_attachment()
        assert att.extra == {}


# ---- SEG-05 ~ SEG-07: MessageArray.get_attachments() ----


class TestMessageArrayGetAttachments:
    def test_seg05_collects_all_downloadable(self):
        """SEG-05: get_attachments() 收集所有可下载段"""
        ma = MessageArray(
            [
                PlainText(text="看看这些"),
                Image(file="a.jpg", url="http://a"),
                Video(file="b.mp4", url="http://b"),
                PlainText(text="over"),
                File(file="c.zip", url="http://c"),
                Record(file="d.silk", url="http://d"),
            ]
        )
        atts = ma.get_attachments()
        assert len(atts) == 4
        assert isinstance(atts[0], ImageAttachment)
        assert isinstance(atts[1], VideoAttachment)
        assert isinstance(atts[2], FileAttachment)
        assert isinstance(atts[3], AudioAttachment)

    def test_seg06_returns_attachment_list(self):
        """SEG-06: get_attachments() 返回 AttachmentList"""
        ma = MessageArray(
            [
                Image(file="a.jpg", url="http://a"),
                Image(file="b.png", url="http://b"),
                Video(file="c.mp4", url="http://c"),
            ]
        )
        atts = ma.get_attachments()
        assert isinstance(atts, AttachmentList)
        assert len(atts.images()) == 2
        assert len(atts.videos()) == 1

    def test_seg07_text_only_empty(self):
        """SEG-07: 纯文本消息返回空 AttachmentList"""
        ma = MessageArray([PlainText(text="hello")])
        atts = ma.get_attachments()
        assert isinstance(atts, AttachmentList)
        assert len(atts) == 0
