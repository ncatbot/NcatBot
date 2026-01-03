"""
消息预上传工具函数测试
"""

from ncatbot.core.service.builtin.preupload.utils import (
    is_local_file,
    is_base64_data,
    is_remote_url,
    needs_upload,
    get_local_path,
    extract_base64_data,
    generate_filename_from_type,
)


class TestIsLocalFile:
    """测试 is_local_file 函数"""

    def test_absolute_path_unix(self):
        """测试 Unix 绝对路径"""
        assert is_local_file("/path/to/file.jpg") is True
        assert is_local_file("/home/user/image.png") is True

    def test_file_protocol(self):
        """测试 file:// 协议"""
        assert is_local_file("file:///path/to/file.jpg") is True
        assert is_local_file("file://localhost/path") is True

    def test_relative_path(self):
        """测试相对路径"""
        assert is_local_file("./image.jpg") is True
        assert is_local_file("images/photo.png") is True
        assert is_local_file("../data/file.txt") is True

    def test_filename_with_extension(self):
        """测试带扩展名的文件名"""
        assert is_local_file("image.jpg") is True
        assert is_local_file("video.mp4") is True

    def test_not_local_file(self):
        """测试非本地文件"""
        assert is_local_file("http://example.com/image.jpg") is False
        assert is_local_file("https://example.com/image.jpg") is False
        assert is_local_file("base64://SGVsbG8=") is False

    def test_empty_or_none(self):
        """测试空值"""
        assert is_local_file("") is False
        assert is_local_file(None) is False


class TestIsBase64Data:
    """测试 is_base64_data 函数"""

    def test_valid_base64(self):
        """测试有效的 Base64 前缀"""
        assert is_base64_data("base64://SGVsbG8gV29ybGQ=") is True
        assert is_base64_data("base64://") is True

    def test_not_base64(self):
        """测试非 Base64 数据"""
        assert is_base64_data("http://example.com") is False
        assert is_base64_data("/path/to/file.jpg") is False
        assert is_base64_data("SGVsbG8=") is False  # 无前缀

    def test_empty_or_none(self):
        """测试空值"""
        assert is_base64_data("") is False
        assert is_base64_data(None) is False


class TestIsRemoteUrl:
    """测试 is_remote_url 函数"""

    def test_http_url(self):
        """测试 HTTP URL"""
        assert is_remote_url("http://example.com/image.jpg") is True
        assert is_remote_url("HTTP://EXAMPLE.COM/IMAGE.JPG") is True

    def test_https_url(self):
        """测试 HTTPS URL"""
        assert is_remote_url("https://example.com/image.jpg") is True
        assert is_remote_url("HTTPS://example.com/") is True

    def test_not_remote_url(self):
        """测试非远程 URL"""
        assert is_remote_url("/path/to/file.jpg") is False
        assert is_remote_url("base64://SGVsbG8=") is False
        assert is_remote_url("file:///path/to/file") is False

    def test_empty_or_none(self):
        """测试空值"""
        assert is_remote_url("") is False
        assert is_remote_url(None) is False


class TestNeedsUpload:
    """测试 needs_upload 函数"""

    def test_local_file_needs_upload(self):
        """测试本地文件需要上传"""
        assert needs_upload("/path/to/file.jpg") is True
        assert needs_upload("file:///path/to/file.jpg") is True
        assert needs_upload("image.jpg") is True

    def test_base64_needs_upload(self):
        """测试 Base64 数据需要上传"""
        assert needs_upload("base64://SGVsbG8=") is True

    def test_remote_url_no_upload(self):
        """测试远程 URL 不需要上传"""
        assert needs_upload("http://example.com/image.jpg") is False
        assert needs_upload("https://example.com/image.jpg") is False


class TestGetLocalPath:
    """测试 get_local_path 函数"""

    def test_file_protocol(self):
        """测试 file:// 协议路径提取"""
        assert get_local_path("file:///path/to/file.jpg") == "/path/to/file.jpg"

    def test_absolute_path(self):
        """测试绝对路径"""
        assert get_local_path("/path/to/file.jpg") == "/path/to/file.jpg"

    def test_relative_path(self):
        """测试相对路径"""
        assert get_local_path("images/photo.png") == "images/photo.png"

    def test_not_local_file(self):
        """测试非本地文件返回 None"""
        assert get_local_path("http://example.com/image.jpg") is None
        assert get_local_path("base64://SGVsbG8=") is None


class TestExtractBase64Data:
    """测试 extract_base64_data 函数"""

    def test_valid_base64(self):
        """测试有效 Base64 解码"""
        result = extract_base64_data("base64://SGVsbG8gV29ybGQ=")
        assert result == b"Hello World"

    def test_not_base64(self):
        """测试非 Base64 返回 None"""
        assert extract_base64_data("http://example.com") is None
        assert extract_base64_data("/path/to/file") is None


class TestGenerateFilenameFromType:
    """测试 generate_filename_from_type 函数"""

    def test_image_extension(self):
        """测试图片扩展名"""
        name = generate_filename_from_type("image")
        assert name.endswith(".jpg")

    def test_video_extension(self):
        """测试视频扩展名"""
        name = generate_filename_from_type("video")
        assert name.endswith(".mp4")

    def test_record_extension(self):
        """测试音频扩展名"""
        name = generate_filename_from_type("record")
        assert name.endswith(".mp3")

    def test_unknown_type(self):
        """测试未知类型"""
        name = generate_filename_from_type("unknown")
        assert name.endswith(".bin")
