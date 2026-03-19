"""
QQFile sugar 方法单元测试

FL-01 ~ FL-06：覆盖 get_or_create_group_folder 的各种场景。
"""

import pytest

from ncatbot.adapter.mock.api import MockBotAPI
from ncatbot.api.qq.file import QQFile
from ncatbot.types.napcat import (
    CreateFolderResult,
    CreateFolderResultGroupItem,
    CreateFolderResultItem,
    GroupFileList,
    GroupFolderInfo,
)


@pytest.fixture
def api() -> MockBotAPI:
    return MockBotAPI()


@pytest.fixture
def file(api: MockBotAPI) -> QQFile:
    return QQFile(api)


def _make_folder_list(*folders: tuple[str, str]) -> GroupFileList:
    """构造 GroupFileList，每个 tuple 为 (folder_id, folder_name)"""
    return GroupFileList(
        folders=[
            GroupFolderInfo(folder_id=fid, folder_name=fname) for fid, fname in folders
        ],
        files=[],
    )


def _make_create_result(folder_id: str) -> CreateFolderResult:
    """构造 create_group_file_folder 的返回结果"""
    return CreateFolderResult(
        groupItem=CreateFolderResultGroupItem(
            folderInfo=CreateFolderResultItem(folderId=folder_id)
        )
    )


class TestGetOrCreateGroupFolder:
    """FL-01: 根目录已存在文件夹 → 直接返回"""

    @pytest.mark.asyncio
    async def test_fl01_existing_root_folder(self, file, api):
        """FL-01: 根目录中已存在目标文件夹，直接返回其 folder_id"""
        api.set_response("get_group_root_files", _make_folder_list(("abc123", "备份")))

        result = await file.get_or_create_group_folder(12345, "备份")

        assert result == "abc123"
        assert api.called("get_group_root_files")
        assert not api.called("create_group_file_folder")

    @pytest.mark.asyncio
    async def test_fl02_create_root_folder(self, file, api):
        """FL-02: 根目录中不存在，创建并返回 folder_id"""
        api.set_response("get_group_root_files", _make_folder_list())
        api.set_response("create_group_file_folder", _make_create_result("new-id-1"))

        result = await file.get_or_create_group_folder(12345, "备份")

        assert result == "new-id-1"
        assert api.called("get_group_root_files")
        assert api.called("create_group_file_folder")

    @pytest.mark.asyncio
    async def test_fl03_subfolder_with_parent_id(self, file, api):
        """FL-03: 使用 parent_id 在子目录中查找已存在的文件夹"""
        api.set_response(
            "get_group_files_by_folder", _make_folder_list(("child-1", "daily"))
        )

        result = await file.get_or_create_group_folder(
            12345, "daily", parent_id="parent-id"
        )

        assert result == "child-1"
        assert api.called("get_group_files_by_folder")
        assert not api.called("get_group_root_files")

    @pytest.mark.asyncio
    async def test_fl04_path_format(self, file, api):
        """FL-04: 使用路径格式 'parent/child' 自动拆分为两级查找/创建"""
        # 第一次调用：查找根目录中的 "备份"
        root_list = _make_folder_list(("parent-id-1", "备份"))
        # 第二次调用：在 parent-id-1 下查找 "daily"
        child_list = _make_folder_list(("child-id-1", "daily"))

        call_count = {"root": 0, "folder": 0}
        original_record = api._record

        def _patched_record(action, *args, **kwargs):
            if action == "get_group_root_files":
                call_count["root"] += 1
                return root_list
            elif action == "get_group_files_by_folder":
                call_count["folder"] += 1
                return child_list
            return original_record(action, *args, **kwargs)

        api._record = _patched_record

        result = await file.get_or_create_group_folder(12345, "备份/daily")

        assert result == "child-id-1"
        assert call_count["root"] == 1
        assert call_count["folder"] == 1

    @pytest.mark.asyncio
    async def test_fl05_query_failure(self, file, api):
        """FL-05: 查询失败返回空字符串"""

        # set_response 不设置 → MockBotAPI 返回空 dict，无 folders 属性
        # 直接 mock 抛出异常
        async def _raise(*a, **kw):
            raise RuntimeError("network error")

        api.get_group_root_files = _raise

        result = await file.get_or_create_group_folder(12345, "备份")

        assert result == ""

    @pytest.mark.asyncio
    async def test_fl06_create_failure(self, file, api):
        """FL-06: 查询成功但创建失败返回空字符串"""
        api.set_response("get_group_root_files", _make_folder_list())

        async def _raise(*a, **kw):
            raise RuntimeError("permission denied")

        api.create_group_file_folder = _raise

        result = await file.get_or_create_group_folder(12345, "备份")

        assert result == ""
