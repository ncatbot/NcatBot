"""
misc.py 模块测试 - 测试杂项消息类型 (Share, Location, Music, Json, Markdown)
"""

from ncatbot.core import (
    Share,
    Location,
    Music,
    Json,
    Markdown,
)
from ncatbot.core import parse_message_segment


class TestShare:
    """测试 Share 类"""

    def test_create_share_basic(self):
        """测试创建基本 Share 实例"""
        share = Share(url="https://example.com", title="Example")

        assert share.url == "https://example.com"
        assert share.title == "Example"
        assert share.type == "share"

    def test_create_share_with_all_fields(self):
        """测试创建完整 Share 实例"""
        share = Share(
            url="https://example.com",
            title="Example Title",
            content="This is the content",
            image="https://example.com/image.jpg",
        )

        assert share.url == "https://example.com"
        assert share.title == "Example Title"
        assert share.content == "This is the content"
        assert share.image == "https://example.com/image.jpg"

    def test_share_optional_fields_default(self):
        """测试可选字段默认值"""
        share = Share(url="https://example.com", title="Test")

        assert share.content is None
        assert share.image is None

    def test_share_from_dict(self):
        """测试从字典创建"""
        data = {
            "type": "share",
            "data": {
                "url": "https://example.com",
                "title": "Example",
                "content": "Some content",
            },
        }
        share = Share.from_dict(data)

        assert share.url == "https://example.com"
        assert share.title == "Example"
        assert share.content == "Some content"

    def test_share_to_dict(self):
        """测试序列化"""
        share = Share(url="https://example.com", title="Test")
        result = share.to_dict()

        assert result["type"] == "share"
        assert result["data"]["url"] == "https://example.com"
        assert result["data"]["title"] == "Test"

    def test_share_roundtrip(self):
        """测试序列化往返"""
        original = Share(url="https://example.com", title="Test", content="Content")
        serialized = original.to_dict()
        restored = parse_message_segment(serialized)

        assert isinstance(restored, Share)
        assert restored.url == original.url
        assert restored.title == original.title
        assert restored.content == original.content


class TestLocation:
    """测试 Location 类"""

    def test_create_location_basic(self):
        """测试创建基本 Location 实例"""
        loc = Location(lat=39.9042, lon=116.4074)

        assert loc.lat == 39.9042
        assert loc.lon == 116.4074
        assert loc.type == "location"

    def test_create_location_with_all_fields(self):
        """测试创建完整 Location 实例"""
        loc = Location(lat=39.9042, lon=116.4074, title="北京", content="中国北京市")

        assert loc.title == "北京"
        assert loc.content == "中国北京市"

    def test_location_optional_fields_default(self):
        """测试可选字段默认值"""
        loc = Location(lat=0.0, lon=0.0)

        assert loc.title is None
        assert loc.content is None

    def test_location_from_dict(self):
        """测试从字典创建"""
        data = {
            "type": "location",
            "data": {"lat": 31.2304, "lon": 121.4737, "title": "上海"},
        }
        loc = Location.from_dict(data)

        assert loc.lat == 31.2304
        assert loc.lon == 121.4737
        assert loc.title == "上海"

    def test_location_to_dict(self):
        """测试序列化"""
        loc = Location(lat=39.9042, lon=116.4074)
        result = loc.to_dict()

        assert result["type"] == "location"
        assert result["data"]["lat"] == 39.9042
        assert result["data"]["lon"] == 116.4074

    def test_location_roundtrip(self):
        """测试序列化往返"""
        original = Location(lat=39.9042, lon=116.4074, title="Test")
        serialized = original.to_dict()
        restored = parse_message_segment(serialized)

        assert isinstance(restored, Location)
        assert restored.lat == original.lat
        assert restored.lon == original.lon

    def test_location_negative_coordinates(self):
        """测试负坐标值"""
        loc = Location(lat=-33.8688, lon=151.2093)  # Sydney
        assert loc.lat == -33.8688
        assert loc.lon == 151.2093


class TestMusic:
    """测试 Music 类"""

    def test_create_music_qq(self):
        """测试创建 QQ 音乐"""
        music = Music(platform="qq", id="123456")

        assert music.platform == "qq"
        assert music.id == "123456"
        assert music.type == "music"

    def test_create_music_163(self):
        """测试创建网易云音乐"""
        music = Music(platform="163", id="789012")

        assert music.platform == "163"
        assert music.id == "789012"

    def test_create_music_custom(self):
        """测试创建自定义音乐"""
        music = Music(
            platform="custom",
            url="https://example.com/song.html",
            audio="https://example.com/song.mp3",
            title="Custom Song",
        )

        assert music.platform == "custom"
        assert music.url == "https://example.com/song.html"
        assert music.audio == "https://example.com/song.mp3"
        assert music.title == "Custom Song"

    def test_music_from_dict(self):
        """测试从字典创建"""
        data = {"type": "music", "data": {"type": "qq", "id": "123456"}}
        music = Music.from_dict(data)

        assert music.platform == "qq"
        assert music.id == "123456"

    def test_music_to_dict(self):
        """测试序列化"""
        music = Music(platform="qq", id="123456")
        result = music.to_dict()

        assert result["type"] == "music"
        # 注意: platform 会被转换为 type
        assert result["data"]["type"] == "qq"
        assert result["data"]["id"] == "123456"
        assert "platform" not in result["data"]

    def test_music_roundtrip(self):
        """测试序列化往返"""
        original = Music(platform="163", id="999888")
        serialized = original.to_dict()
        restored = parse_message_segment(serialized)

        assert isinstance(restored, Music)
        assert restored.platform == original.platform
        assert restored.id == original.id


class TestJson:
    """测试 Json 类"""

    def test_create_json(self):
        """测试创建 Json 实例"""
        json_msg = Json(data='{"key": "value"}')

        assert json_msg.data == '{"key": "value"}'
        assert json_msg.type == "json"

    def test_json_complex_data(self):
        """测试复杂 JSON 数据"""
        complex_json = '{"app":"com.tencent.miniapp_01","desc":"","view":"notification","ver":"1.0.0.11"}'
        json_msg = Json(data=complex_json)

        assert json_msg.data == complex_json

    def test_json_from_dict(self):
        """测试从字典创建"""
        data = {"type": "json", "data": {"data": '{"test": true}'}}
        json_msg = Json.from_dict(data)

        assert json_msg.data == '{"test": true}'

    def test_json_to_dict(self):
        """测试序列化"""
        json_msg = Json(data='{"hello": "world"}')
        result = json_msg.to_dict()

        assert result["type"] == "json"
        assert result["data"]["data"] == '{"hello": "world"}'

    def test_json_roundtrip(self):
        """测试序列化往返"""
        original = Json(data='{"roundtrip": true}')
        serialized = original.to_dict()
        restored = parse_message_segment(serialized)

        assert isinstance(restored, Json)
        assert restored.data == original.data


class TestMarkdown:
    """测试 Markdown 类"""

    def test_create_markdown(self):
        """测试创建 Markdown 实例"""
        md = Markdown(content="# Hello World")

        assert md.content == "# Hello World"
        assert md.type == "markdown"

    def test_markdown_complex_content(self):
        """测试复杂 Markdown 内容"""
        content = """# Title

## Subtitle

- Item 1
- Item 2

**Bold** and *italic* text.

```python
print("Hello")
```
"""
        md = Markdown(content=content)
        assert md.content == content

    def test_markdown_from_dict(self):
        """测试从字典创建"""
        data = {"type": "markdown", "data": {"content": "## Test Header"}}
        md = Markdown.from_dict(data)

        assert md.content == "## Test Header"

    def test_markdown_to_dict(self):
        """测试序列化"""
        md = Markdown(content="# Title")
        result = md.to_dict()

        assert result["type"] == "markdown"
        assert result["data"]["content"] == "# Title"

    def test_markdown_roundtrip(self):
        """测试序列化往返"""
        original = Markdown(content="**Bold Text**")
        serialized = original.to_dict()
        restored = parse_message_segment(serialized)

        assert isinstance(restored, Markdown)
        assert restored.content == original.content

    def test_markdown_empty_content(self):
        """测试空内容"""
        md = Markdown(content="")
        assert md.content == ""

    def test_markdown_unicode(self):
        """测试 Unicode 内容"""
        md = Markdown(content="# 你好世界 🌍")
        assert md.content == "# 你好世界 🌍"
