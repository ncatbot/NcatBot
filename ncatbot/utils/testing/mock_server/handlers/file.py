"""
文件相关 API 处理器
"""
# pyright: reportAttributeAccessIssue=false

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..database import MockDatabase


class FileHandlerMixin:
    """文件相关处理器"""

    # 以下属性/方法由 MockApiHandler 提供
    db: "MockDatabase"
    _handlers: dict

    def _register_file_handlers(self) -> None:
        """注册文件相关处理器"""
        handlers = {
            "get_group_root_files": self._handle_get_group_root_files,
            "get_group_files_by_folder": self._handle_get_group_files_by_folder,
            "get_group_file_url": self._handle_get_group_file_url,
            "upload_group_file": self._handle_upload_group_file,
            "create_group_file_folder": self._handle_create_group_file_folder,
            "delete_group_file": self._handle_delete_group_file,
            "delete_group_folder": self._handle_delete_group_folder,
            "rename_group_file": self._handle_rename_group_file,
            "move_group_file": self._handle_move_group_file,
            "upload_private_file": self._handle_upload_private_file,
            "get_private_file_url": self._handle_get_private_file_url,
            "get_file": self._handle_get_file,
        }
        self._handlers.update(handlers)

    # =========================================================================
    # 文件相关处理器
    # =========================================================================

    def _handle_get_group_root_files(self, params: dict) -> dict:
        group_id = str(params.get("group_id", ""))
        file_count = int(params.get("file_count", 50))

        result = self.db.get_group_root_files(group_id, file_count)
        return self._success_response(result)

    def _handle_get_group_files_by_folder(self, params: dict) -> dict:
        group_id = str(params.get("group_id", ""))
        folder_id = str(params.get("folder_id", "/"))
        file_count = int(params.get("file_count", 50))

        result = self.db.get_group_files_by_folder(group_id, folder_id, file_count)
        return self._success_response(result)

    def _handle_get_group_file_url(self, params: dict) -> dict:
        group_id = str(params.get("group_id", ""))
        file_id = str(params.get("file_id", ""))

        url = self.db.get_group_file_url(group_id, file_id)
        if url:
            return self._success_response({"url": url})
        return self._error_response("文件不存在")

    def _handle_upload_group_file(self, params: dict) -> dict:
        group_id = str(params.get("group_id", ""))
        name = params.get("name", "file")
        folder = params.get("folder", "/")

        file_id = self.db.upload_group_file(group_id, name, 0, folder)
        return self._success_response({"file_id": file_id})

    def _handle_create_group_file_folder(self, params: dict) -> dict:
        group_id = str(params.get("group_id", ""))
        folder_name = params.get("folder_name", "")

        folder_id = self.db.create_group_file_folder(group_id, folder_name)
        return self._success_response({"folder_id": folder_id})

    def _handle_delete_group_file(self, params: dict) -> dict:
        group_id = str(params.get("group_id", ""))
        file_id = str(params.get("file_id", ""))

        if self.db.delete_group_file(group_id, file_id):
            return self._success_response({})
        return self._error_response("文件不存在")

    def _handle_delete_group_folder(self, params: dict) -> dict:
        group_id = str(params.get("group_id", ""))
        folder_id = str(params.get("folder_id", ""))

        if self.db.delete_group_folder(group_id, folder_id):
            return self._success_response({})
        return self._error_response("文件夹不存在")

    def _handle_rename_group_file(self, params: dict) -> dict:
        group_id = str(params.get("group_id", ""))
        file_id = str(params.get("file_id", ""))
        new_name = params.get("new_name", "")

        if self.db.rename_group_file(group_id, file_id, new_name):
            return self._success_response({})
        return self._error_response("文件不存在")

    def _handle_move_group_file(self, params: dict) -> dict:
        group_id = str(params.get("group_id", ""))
        file_id = str(params.get("file_id", ""))
        target_folder = str(params.get("target_parent_directory", "/"))

        if self.db.move_group_file(group_id, file_id, target_folder):
            return self._success_response({})
        return self._error_response("移动失败")

    def _handle_upload_private_file(self, params: dict) -> dict:
        return self._success_response({})

    def _handle_get_private_file_url(self, params: dict) -> dict:
        file_id = str(params.get("file_id", ""))
        return self._success_response(
            {"url": f"https://mock.file.url/private/{file_id}"}
        )

    def _handle_get_file(self, params: dict) -> dict:
        file_id = str(params.get("file_id", ""))
        file_path = str(params.get("file", ""))
        return self._success_response(
            {
                "file": file_path or f"/mock/files/{file_id}",
                "file_id": file_id,
                "file_name": "mock_file",
                "file_size": 1024,
                "url": f"https://mock.file.url/{file_id}",
            }
        )
