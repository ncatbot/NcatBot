"""
文件操作

Mock 数据库的文件相关操作。
"""
# pyright: reportAttributeAccessIssue=false

import time
from typing import Optional


class FileOperationsMixin:
    """文件操作混入类"""

    # 以下属性/方法由 MockDatabase 提供（类型声明仅供参考）
    _data: dict

    def _get_group_root_folder(self, group_id: str) -> dict:
        """获取群根目录文件夹"""
        group_key = str(group_id)
        if group_key not in self._data["group_files"]:
            self._data["group_files"][group_key] = {
                "folder_id": "/",
                "folder_name": "/",
                "files": [],
                "folders": [],
            }
        return self._data["group_files"][group_key]

    def _find_folder(self, group_id: str, folder_id: str) -> Optional[dict]:
        """查找文件夹"""
        if folder_id in ("/", "", None):
            return self._get_group_root_folder(group_id)

        root = self._get_group_root_folder(group_id)
        return self._find_folder_recursive(root, folder_id)

    def _find_folder_recursive(self, folder: dict, folder_id: str) -> Optional[dict]:
        """递归查找文件夹"""
        if folder.get("folder_id") == folder_id:
            return folder

        for subfolder in folder.get("folders", []):
            result = self._find_folder_recursive(subfolder, folder_id)
            if result:
                return result

        return None

    def _find_file(self, group_id: str, file_id: str) -> Optional[tuple]:
        """查找文件，返回 (file, parent_folder)"""
        root = self._get_group_root_folder(group_id)
        return self._find_file_recursive(root, file_id)

    def _find_file_recursive(self, folder: dict, file_id: str) -> Optional[tuple]:
        """递归查找文件"""
        for f in folder.get("files", []):
            if f.get("file_id") == file_id:
                return (f, folder)

        for subfolder in folder.get("folders", []):
            result = self._find_file_recursive(subfolder, file_id)
            if result:
                return result

        return None

    def get_group_root_files(self, group_id: str, file_count: int = 50) -> dict:
        """获取群根目录文件"""
        root = self._get_group_root_folder(group_id)
        return {
            "files": root.get("files", [])[:file_count],
            "folders": root.get("folders", [])[:file_count],
        }

    def get_group_files_by_folder(
        self,
        group_id: str,
        folder_id: str,
        file_count: int = 50,
    ) -> dict:
        """获取文件夹内文件"""
        folder = self._find_folder(group_id, folder_id)
        if not folder:
            return {"files": [], "folders": []}

        return {
            "files": folder.get("files", [])[:file_count],
            "folders": folder.get("folders", [])[:file_count],
        }

    def create_group_file_folder(
        self,
        group_id: str,
        folder_name: str,
        parent_id: str = "/",
    ) -> str:
        """创建群文件夹"""
        parent = self._find_folder(group_id, parent_id)
        if not parent:
            parent = self._get_group_root_folder(group_id)

        folder_id = self._generate_folder_id()
        bot = self.get_login_info()

        new_folder = {
            "folder_id": folder_id,
            "folder_name": folder_name,
            "create_time": int(time.time()),
            "creator": bot.get("user_id"),
            "creator_name": bot.get("nickname"),
            "total_file_count": 0,
            "files": [],
            "folders": [],
        }

        if "folders" not in parent:
            parent["folders"] = []
        parent["folders"].append(new_folder)

        return folder_id

    def upload_group_file(
        self,
        group_id: str,
        file_name: str,
        file_size: int = 0,
        folder_id: str = "/",
    ) -> str:
        """上传群文件"""
        folder = self._find_folder(group_id, folder_id)
        if not folder:
            folder = self._get_group_root_folder(group_id)

        file_id = self._generate_file_id()
        bot = self.get_login_info()

        new_file = {
            "file_id": file_id,
            "file_name": file_name,
            "file_size": file_size,
            "busid": 0,
            "upload_time": int(time.time()),
            "dead_time": 0,
            "modify_time": int(time.time()),
            "download_times": 0,
            "uploader": bot.get("user_id"),
            "uploader_name": bot.get("nickname"),
        }

        if "files" not in folder:
            folder["files"] = []
        folder["files"].append(new_file)

        return file_id

    def delete_group_file(self, group_id: str, file_id: str) -> bool:
        """删除群文件"""
        result = self._find_file(group_id, file_id)
        if not result:
            return False

        file_data, parent_folder = result
        parent_folder["files"].remove(file_data)
        return True

    def delete_group_folder(self, group_id: str, folder_id: str) -> bool:
        """删除群文件夹"""
        if folder_id in ("/", "", None):
            return False

        root = self._get_group_root_folder(group_id)
        return self._delete_folder_recursive(root, folder_id)

    def _delete_folder_recursive(self, parent: dict, folder_id: str) -> bool:
        """递归删除文件夹"""
        folders = parent.get("folders", [])
        for i, folder in enumerate(folders):
            if folder.get("folder_id") == folder_id:
                folders.pop(i)
                return True

            if self._delete_folder_recursive(folder, folder_id):
                return True

        return False

    def rename_group_file(
        self,
        group_id: str,
        file_id: str,
        new_name: str,
    ) -> bool:
        """重命名群文件"""
        result = self._find_file(group_id, file_id)
        if not result:
            return False

        file_data, _ = result
        file_data["file_name"] = new_name
        file_data["modify_time"] = int(time.time())
        return True

    def move_group_file(
        self,
        group_id: str,
        file_id: str,
        target_folder_id: str,
    ) -> bool:
        """移动群文件"""
        result = self._find_file(group_id, file_id)
        if not result:
            return False

        file_data, source_folder = result

        target_folder = self._find_folder(group_id, target_folder_id)
        if not target_folder:
            return False

        source_folder["files"].remove(file_data)
        if "files" not in target_folder:
            target_folder["files"] = []
        target_folder["files"].append(file_data)

        return True

    def get_group_file_url(self, group_id: str, file_id: str) -> Optional[str]:
        """获取群文件下载链接"""
        result = self._find_file(group_id, file_id)
        if not result:
            return None

        file_data, _ = result
        return f"https://mock.file.url/{group_id}/{file_id}/{file_data.get('file_name', 'file')}"
