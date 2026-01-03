"""
群文件操作复合测试

测试内容：
- 获取群文件列表
- 上传群文件
- 创建文件夹
- 重命名文件
- 删除文件/文件夹
- 获取文件下载链接
"""

import pytest


class TestGroupFileQuery:
    """群文件查询综合测试"""

    @pytest.mark.asyncio
    async def test_group_file_query_complete(self, api_suite, standard_group_id):
        """
        群文件查询综合测试

        测试内容：
        1. 获取群根目录文件列表
        2. 获取指定文件夹内文件
        3. 获取文件下载链接
        """
        api = api_suite.api

        # 1. 获取群根目录文件列表
        root_files = await api.get_group_root_files(
            group_id=int(standard_group_id), file_count=20
        )
        assert root_files is not None, "根目录文件列表不能为空"
        api_suite.assert_api_called("get_group_root_files")

        # 2. 获取指定文件夹内文件
        api_suite.clear_call_history()
        folder_files = await api.get_group_files_by_folder(
            group_id=int(standard_group_id),
            folder_id="folder_001",  # 使用标准测试数据中的文件夹
            file_count=20,
        )
        assert folder_files is not None, "文件夹内容不能为空"
        api_suite.assert_api_called("get_group_files_by_folder")

        # 3. 获取文件下载链接
        api_suite.clear_call_history()
        file_url = await api.get_group_file_url(
            group_id=int(standard_group_id),
            file_id="file_001",  # 使用标准测试数据中的文件
        )
        assert file_url is not None, "文件 URL 不能为空"
        api_suite.assert_api_called("get_group_file_url")


class TestGroupFileOperations:
    """群文件操作综合测试"""

    @pytest.mark.asyncio
    async def test_file_folder_lifecycle(self, api_suite, standard_group_id):
        """
        文件夹生命周期测试

        测试内容：
        1. 创建文件夹
        2. 上传文件到群
        3. 重命名文件
        4. 删除文件
        5. 删除文件夹
        """
        api = api_suite.api

        # 1. 创建文件夹
        await api.create_group_file_folder(
            group_id=int(standard_group_id), folder_name="测试文件夹"
        )
        api_suite.assert_api_called("create_group_file_folder")
        api_suite.assert_api_called_with(
            "create_group_file_folder", folder_name="测试文件夹"
        )

        # 2. 上传文件（使用 URL 形式）
        api_suite.clear_call_history()
        await api.upload_group_file(
            group_id=int(standard_group_id),
            file="https://example.com/test.txt",
            name="test_upload.txt",
            folder="/",
        )
        api_suite.assert_api_called("upload_group_file")

        # 3. 重命名文件
        api_suite.clear_call_history()
        await api.rename_group_file(
            group_id=int(standard_group_id),
            file_id="file_001",
            new_name="renamed_file.txt",
        )
        api_suite.assert_api_called("rename_group_file")

        # 4. 删除文件
        api_suite.clear_call_history()
        await api.delete_group_file(group_id=int(standard_group_id), file_id="file_001")
        api_suite.assert_api_called("delete_group_file")

        # 5. 删除文件夹
        api_suite.clear_call_history()
        await api.delete_group_folder(
            group_id=int(standard_group_id), folder_id="folder_001"
        )
        api_suite.assert_api_called("delete_group_folder")

    @pytest.mark.asyncio
    async def test_move_file(self, api_suite, standard_group_id):
        """
        移动文件测试

        测试内容：
        1. 移动文件到不同目录
        2. 验证 API 调用参数
        """
        api = api_suite.api

        # 移动文件
        await api.move_group_file(
            group_id=int(standard_group_id),
            file_id="file_002",
            current_parent_directory="/",
            target_parent_directory="folder_001",
        )
        api_suite.assert_api_called("move_group_file")
        api_suite.assert_api_called_with(
            "move_group_file", file_id="file_002", target_parent_directory="folder_001"
        )


class TestPrivateFile:
    """私聊文件操作测试"""

    @pytest.mark.asyncio
    async def test_private_file_operations(self, api_suite, standard_user_id):
        """
        私聊文件操作测试

        测试内容：
        1. 上传私聊文件
        2. 获取私聊文件链接
        """
        api = api_suite.api

        # 1. 上传私聊文件
        await api.upload_private_file(
            user_id=int(standard_user_id),
            file="https://example.com/private_file.txt",
            name="private_upload.txt",
        )
        api_suite.assert_api_called("upload_private_file")

        # 2. 获取私聊文件链接
        api_suite.clear_call_history()
        url = await api.get_private_file_url(file_id="private_file_001")
        assert url is not None, "私聊文件 URL 不能为空"
        api_suite.assert_api_called("get_private_file_url")

    @pytest.mark.asyncio
    async def test_get_file_info(self, api_suite):
        """
        获取文件信息测试

        测试内容：
        1. 获取文件详细信息
        2. 验证返回的 File 对象
        """
        api = api_suite.api

        # 获取文件信息
        file_info = await api.get_file(file_id="test_file_id", file="test_file")
        assert file_info is not None, "文件信息不能为空"
        api_suite.assert_api_called("get_file")
