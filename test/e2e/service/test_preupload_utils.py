"""
预上传工具函数和客户端测试

测试内容：
- 工具函数（文件类型识别、路径解析）
- StreamUploadClient（文件分析、分片）

这些测试不需要完整 E2E 环境，运行速度快。
"""

import pytest
import base64

from ncatbot.core.service.builtin.preupload.utils import (
    is_local_file,
    is_base64_data,
    is_remote_url,
    needs_upload,
    get_local_path,
    extract_base64_data,
    generate_filename_from_type,
    DOWNLOADABLE_TYPES,
)
from ncatbot.core.service.builtin.preupload.client import StreamUploadClient


class TestPreUploadUtils:
    """工具函数测试（不需要 E2E 环境，快速运行）"""

    def test_file_type_identification_complete(self):
        """文件类型识别复合测试

        测试内容：
        - 本地文件路径识别（绝对/相对/file://）
        - Base64 数据识别
        - 远程 URL 识别
        - 需要上传判断
        """
        # 1. 本地文件路径识别
        # 绝对路径
        assert is_local_file("/home/user/test.jpg") is True
        assert is_local_file("/tmp/image.png") is True
        # 相对路径
        assert is_local_file("./images/test.jpg") is True
        assert is_local_file("data/file.bin") is True
        # file:// 协议
        assert is_local_file("file:///home/user/test.jpg") is True
        # 带扩展名的文件名
        assert is_local_file("test.jpg") is True

        # 2. 非本地文件
        assert is_local_file("base64://abc123") is False
        assert is_local_file("https://example.com/img.jpg") is False
        assert is_local_file("http://example.com/img.jpg") is False
        assert is_local_file("") is False
        assert is_local_file(None) is False  # type: ignore

        # 3. Base64 数据识别
        assert is_base64_data("base64://SGVsbG8gV29ybGQ=") is True
        assert is_base64_data("base64://") is True  # 空数据也是 base64 格式
        assert is_base64_data("/path/to/file.jpg") is False
        assert is_base64_data("https://example.com/img.jpg") is False

        # 4. 远程 URL 识别
        assert is_remote_url("https://example.com/image.jpg") is True
        assert is_remote_url("http://example.com/image.jpg") is True
        assert is_remote_url("HTTP://EXAMPLE.COM/IMAGE.JPG") is True  # 不区分大小写
        assert is_remote_url("file:///home/user/test.jpg") is False
        assert is_remote_url("/home/user/test.jpg") is False
        assert is_remote_url("base64://abc") is False

        # 5. 需要上传判断
        assert needs_upload("/home/user/test.jpg") is True
        assert needs_upload("file:///home/user/test.jpg") is True
        assert needs_upload("base64://SGVsbG8gV29ybGQ=") is True
        assert needs_upload("https://example.com/img.jpg") is False
        assert needs_upload("") is False

    def test_path_extraction_and_generation_complete(self):
        """路径提取和文件名生成复合测试

        测试内容：
        - 从 file:// 协议提取本地路径
        - 从普通路径提取
        - Base64 数据提取和解码
        - 文件名生成
        """
        # 1. 从 file:// 协议提取路径
        assert get_local_path("file:///home/user/test.jpg") == "/home/user/test.jpg"
        assert get_local_path("file:///tmp/data.bin") == "/tmp/data.bin"

        # 2. 普通路径直接返回
        assert get_local_path("/home/user/test.jpg") == "/home/user/test.jpg"
        assert get_local_path("./data/file.bin") == "./data/file.bin"

        # 3. 非本地文件返回 None
        assert get_local_path("https://example.com/img.jpg") is None
        assert get_local_path("base64://abc") is None

        # 4. Base64 数据提取和解码
        test_data = b"Hello World"
        encoded = "base64://" + base64.b64encode(test_data).decode()
        extracted = extract_base64_data(encoded)
        assert extracted == test_data

        # 无效 Base64 返回 None
        assert extract_base64_data("not_base64") is None
        assert extract_base64_data("base64://!!!invalid!!!") is None

        # 5. 文件名生成
        image_name = generate_filename_from_type("image")
        assert image_name.endswith(".jpg")
        assert len(image_name) > 4  # uuid + extension

        video_name = generate_filename_from_type("video")
        assert video_name.endswith(".mp4")

        record_name = generate_filename_from_type("record")
        assert record_name.endswith(".mp3")

        file_name = generate_filename_from_type("file")
        assert file_name.endswith(".bin")

        # 未知类型使用默认扩展名
        unknown_name = generate_filename_from_type("unknown_type")
        assert unknown_name.endswith(".bin")

    def test_downloadable_types_and_edge_cases(self):
        """可下载类型和边界情况复合测试

        测试内容：
        - 可下载消息类型常量
        - 空值和异常输入处理
        """
        # 1. 可下载消息类型
        assert "image" in DOWNLOADABLE_TYPES
        assert "video" in DOWNLOADABLE_TYPES
        assert "record" in DOWNLOADABLE_TYPES
        assert "file" in DOWNLOADABLE_TYPES
        assert "text" not in DOWNLOADABLE_TYPES
        assert "at" not in DOWNLOADABLE_TYPES

        # 2. 边界情况 - 空值
        assert is_local_file("") is False
        assert is_base64_data("") is False
        assert is_remote_url("") is False
        assert needs_upload("") is False
        assert get_local_path("") is None

        # 3. 边界情况 - 类型错误（应该安全处理）
        assert is_local_file(None) is False  # type: ignore
        assert is_base64_data(None) is False  # type: ignore
        assert is_remote_url(None) is False  # type: ignore


class TestStreamUploadClient:
    """StreamUploadClient 测试（文件分析不需要网络连接）"""

    def test_file_analysis_complete(self, temp_test_files):
        """文件分析复合测试

        测试内容：
        - 小文件分析（单分片）
        - 中等文件分析（多分片）
        - 分片数量验证
        - SHA256 哈希计算
        - Base64 编码验证
        """
        from ncatbot.core.service.builtin.preupload.constants import DEFAULT_CHUNK_SIZE

        # 创建模拟的 message_router（分析不需要实际连接）
        class MockRouter:
            pass

        client = StreamUploadClient(MockRouter(), chunk_size=DEFAULT_CHUNK_SIZE)  # type: ignore

        # 1. 小文件分析（应该只有 1 个分片）
        small_analysis = client.analyze_file(temp_test_files["small"])
        assert small_analysis.total_size == 100
        assert len(small_analysis.chunks) == 1
        assert small_analysis.filename == "small.txt"
        assert len(small_analysis.sha256_hash) == 64  # SHA256 hex

        # 验证分片内容
        chunk = small_analysis.chunks[0]
        assert chunk.index == 0
        assert len(chunk.data) == 100
        assert chunk.base64_data == base64.b64encode(chunk.data).decode()

        # 2. 中等文件分析（应该有多个分片）
        medium_analysis = client.analyze_file(temp_test_files["medium"])
        assert medium_analysis.total_size == 1024 * 1024
        expected_chunks = (1024 * 1024 + DEFAULT_CHUNK_SIZE - 1) // DEFAULT_CHUNK_SIZE
        assert len(medium_analysis.chunks) == expected_chunks

        # 验证分片索引连续
        for i, chunk in enumerate(medium_analysis.chunks):
            assert chunk.index == i

        # 3. 图片文件分析
        image_analysis = client.analyze_file(temp_test_files["image"])
        assert image_analysis.filename == "test.jpg"
        assert image_analysis.total_size > 0

        # 4. 字节数据分析
        test_bytes = b"Test data for upload" * 100
        bytes_analysis = client.analyze_bytes(test_bytes, "test_data.bin")
        assert bytes_analysis.total_size == len(test_bytes)
        assert bytes_analysis.filename == "test_data.bin"

    def test_file_not_found_handling(self):
        """文件不存在处理测试"""

        class MockRouter:
            pass

        client = StreamUploadClient(MockRouter())  # type: ignore

        with pytest.raises(FileNotFoundError):
            client.analyze_file("/nonexistent/path/to/file.jpg")
