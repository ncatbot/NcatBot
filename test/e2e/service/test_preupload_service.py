"""
预上传服务端到端测试

测试内容：
- PreUploadService（服务生命周期、接口）
- MessagePreUploadProcessor（消息预处理）
- API 集成

这些测试需要完整 E2E 环境（MockServer + BotClient）。
"""

import pytest
import base64


class TestPreUploadServiceE2E:
    """PreUploadService 端到端测试（需要完整 E2E 环境）"""

    @pytest.mark.asyncio
    async def test_service_lifecycle_and_upload_complete(
        self, preupload_suite, temp_test_files
    ):
        """服务生命周期与上传流程复合测试

        测试内容：
        - 服务加载和初始化验证
        - 文件上传功能
        - 字节数据上传
        - 服务可用性检查
        """
        services = preupload_suite.services
        preupload = services.preupload

        # 1. 验证服务已加载
        assert preupload is not None
        assert preupload.available is True
        assert preupload.client is not None
        assert preupload.message_processor is not None

        # 2. 测试本地文件上传
        result = await preupload.upload_file(temp_test_files["small"])
        assert result.success is True
        assert result.file_path is not None
        assert "/mock/uploads/" in result.file_path
        assert result.file_size == 100

        # 3. 测试字节数据上传
        test_data = b"Hello from preupload test!"
        result = await preupload.upload_bytes(test_data, "test.txt")
        assert result.success is True
        assert result.file_path is not None

        # 4. 测试较大文件上传（多分片）
        result = await preupload.upload_file(temp_test_files["medium"])
        assert result.success is True
        assert result.file_size == 1024 * 1024

    @pytest.mark.asyncio
    async def test_preupload_file_interface_complete(
        self, preupload_suite, temp_test_files
    ):
        """preupload_file 接口复合测试

        测试内容：
        - 本地文件预上传
        - Base64 数据预上传
        - 远程 URL 跳过上传
        - 错误处理
        """
        preupload = preupload_suite.services.preupload

        # 1. 本地文件预上传
        result = await preupload.preupload_file(temp_test_files["image"], "image")
        assert result.success is True
        assert result.uploaded is True  # 路径变化
        assert result.file_path != result.original_path

        # 2. file:// 协议路径
        file_uri = f"file://{temp_test_files['small']}"
        result = await preupload.preupload_file(file_uri, "file")
        assert result.success is True
        assert result.uploaded is True

        # 3. Base64 数据预上传
        test_data = b"Test image data"
        b64_data = "base64://" + base64.b64encode(test_data).decode()
        result = await preupload.preupload_file(b64_data, "image")
        assert result.success is True
        assert result.uploaded is True

        # 4. 远程 URL 不需要上传
        url = "https://example.com/image.jpg"
        result = await preupload.preupload_file(url, "image")
        assert result.success is True
        assert result.uploaded is False  # 路径未变化
        assert result.file_path == url

        # 5. 空路径错误处理
        result = await preupload.preupload_file("", "file")
        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_message_processing_complete(self, preupload_suite, temp_test_files):
        """消息预处理复合测试

        测试内容：
        - 处理包含本地文件的消息
        - 处理包含 Base64 的消息
        - 处理消息数组
        - URL 类型跳过上传
        - 嵌套消息结构
        """
        preupload = preupload_suite.services.preupload

        # 1. 处理包含本地文件的消息
        message = {"type": "image", "data": {"file": temp_test_files["image"]}}
        result = await preupload.process_message(message)
        assert result.success is True
        assert result.uploaded_count == 1
        assert "/mock/uploads/" in result.data["data"]["file"]

        # 2. 处理包含 Base64 的消息
        b64_data = "base64://" + base64.b64encode(b"test").decode()
        message = {"type": "image", "data": {"file": b64_data}}
        result = await preupload.process_message(message)
        assert result.success is True
        assert result.uploaded_count == 1

        # 3. URL 类型不需要上传
        message = {"type": "image", "data": {"file": "https://example.com/img.jpg"}}
        result = await preupload.process_message(message)
        assert result.success is True
        assert result.uploaded_count == 0
        assert result.data["data"]["file"] == "https://example.com/img.jpg"

        # 4. 处理消息数组
        messages = [
            {"type": "text", "data": {"text": "Hello"}},
            {"type": "image", "data": {"file": temp_test_files["small"]}},
            {"type": "image", "data": {"file": "https://example.com/img.jpg"}},
        ]
        result = await preupload.process_message_array(messages)
        assert result.success is True
        assert result.uploaded_count == 1  # 只有一个本地文件被上传

        # 5. 嵌套 Forward 消息结构
        forward_message = {
            "type": "forward",
            "data": {
                "content": [
                    {
                        "type": "node",
                        "data": {
                            "content": [
                                {"type": "text", "data": {"text": "嵌套文本"}},
                                {
                                    "type": "image",
                                    "data": {"file": temp_test_files["image"]},
                                },
                            ]
                        },
                    }
                ]
            },
        }
        result = await preupload.process_message(forward_message)
        assert result.success is True
        assert result.uploaded_count == 1
        # 验证嵌套的文件路径已被替换
        nested_content = result.data["data"]["content"][0]["data"]["content"]
        image_segment = next(s for s in nested_content if s["type"] == "image")
        assert "/mock/uploads/" in image_segment["data"]["file"]

    @pytest.mark.asyncio
    async def test_error_handling_and_edge_cases(self, preupload_suite):
        """错误处理和边界情况复合测试

        测试内容：
        - 不存在的文件处理
        - 无效 Base64 数据处理
        - preupload_file_if_needed 异常抛出
        - 非可下载类型消息处理
        """
        preupload = preupload_suite.services.preupload

        # 1. 不存在的文件
        result = await preupload.preupload_file("/nonexistent/file.jpg", "image")
        assert result.success is False
        assert result.error is not None

        # 2. 无效 Base64 数据
        result = await preupload.preupload_file("base64://!!!invalid!!!", "image")
        assert result.success is False

        # 3. preupload_file_if_needed 在失败时抛出异常
        with pytest.raises(RuntimeError):
            await preupload.preupload_file_if_needed("/nonexistent/file.jpg", "image")

        # 4. 非可下载类型消息不处理文件字段
        message = {
            "type": "text",
            "data": {"text": "Hello", "file": "/some/path.jpg"},  # text 类型不处理 file
        }
        result = await preupload.process_message(message)
        assert result.success is True
        assert result.uploaded_count == 0


class TestPreUploadAPIIntegration:
    """预上传与 API 调用集成测试"""

    @pytest.mark.asyncio
    async def test_api_preupload_check(self, preupload_suite):
        """API 预上传检查测试

        测试内容：
        - 验证 API 层可以访问预上传服务
        - 验证服务状态标识正确
        """
        preupload = preupload_suite.services.preupload

        # 验证服务可用
        assert preupload.available is True

        # 验证 API 可以通过 services 访问预上传服务
        assert preupload_suite.services.preupload is preupload
