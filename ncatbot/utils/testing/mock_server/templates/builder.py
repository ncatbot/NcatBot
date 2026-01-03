"""
场景构建器

用于构建自定义测试场景。
"""

from typing import Any, Dict, Optional

from .creators import (
    create_bot_data,
    create_user_data,
    create_group_member_data,
    create_group_data,
    create_file_data,
    create_folder_data,
)


class ScenarioBuilder:
    """
    场景构建器

    用于构建自定义测试场景。

    示例:
        ```python
        data = (
            ScenarioBuilder(bot_id="999999", bot_name="MyBot")
            .add_friend("111111", "Alice")
            .add_group("222222", "测试群", bot_role="owner")
            .add_group_member("222222", "111111", "Alice")
            .add_group_file("222222", "test.txt")
            .build()
        )
        ```
    """

    def __init__(self, bot_id: str = "123456789", bot_name: str = "TestBot"):
        """
        初始化场景构建器

        Args:
            bot_id: Bot QQ 号
            bot_name: Bot 昵称
        """
        self._data: Dict[str, Any] = {
            "bot": create_bot_data(bot_id, bot_name),
            "friends": [],
            "groups": [],
            "group_messages": {},
            "private_messages": {},
            "group_files": {},
        }
        self._bot_id = bot_id
        self._bot_name = bot_name

    def add_friend(
        self,
        user_id: str,
        nickname: str,
        remark: str = "",
    ) -> "ScenarioBuilder":
        """添加好友"""
        self._data["friends"].append(create_user_data(user_id, nickname, remark))
        return self

    def add_group(
        self,
        group_id: str,
        group_name: str,
        owner_id: Optional[str] = None,
        bot_role: str = "member",
    ) -> "ScenarioBuilder":
        """
        添加群

        Args:
            group_id: 群号
            group_name: 群名
            owner_id: 群主 ID，不提供则为 Bot
            bot_role: Bot 在群中的角色
        """
        owner_id = owner_id or self._bot_id
        members = [
            create_group_member_data(self._bot_id, self._bot_name, role=bot_role),
        ]
        if owner_id != self._bot_id:
            members.insert(
                0, create_group_member_data(owner_id, f"群主{owner_id}", role="owner")
            )

        self._data["groups"].append(
            create_group_data(group_id, group_name, owner_id, members)
        )
        return self

    def add_group_member(
        self,
        group_id: str,
        user_id: str,
        nickname: str,
        role: str = "member",
    ) -> "ScenarioBuilder":
        """添加群成员"""
        for group in self._data["groups"]:
            if group["group_id"] == group_id:
                group["members"].append(
                    create_group_member_data(user_id, nickname, role=role)
                )
                break
        return self

    def add_group_message(
        self,
        group_id: str,
        user_id: str,
        text: str,
        message_id: Optional[str] = None,
    ) -> "ScenarioBuilder":
        """添加群消息"""
        import time

        if group_id not in self._data["group_messages"]:
            self._data["group_messages"][group_id] = []

        messages = self._data["group_messages"][group_id]
        msg_id = message_id or f"msg_{len(messages) + 1}"

        messages.append(
            {
                "message_id": msg_id,
                "message_type": "group",
                "group_id": group_id,
                "user_id": user_id,
                "message": [{"type": "text", "data": {"text": text}}],
                "raw_message": text,
                "time": int(time.time()),
                "sender": {"user_id": user_id, "nickname": f"User{user_id}"},
                "message_seq": len(messages) + 1,
            }
        )
        return self

    def add_group_file(
        self,
        group_id: str,
        file_name: str,
        file_id: Optional[str] = None,
        folder_id: str = "/",
    ) -> "ScenarioBuilder":
        """添加群文件"""
        if group_id not in self._data["group_files"]:
            self._data["group_files"][group_id] = {
                "folder_id": "/",
                "folder_name": "/",
                "files": [],
                "folders": [],
            }

        root = self._data["group_files"][group_id]

        file_data = create_file_data(
            file_id or f"file_{len(root['files']) + 1}",
            file_name,
            1024,
            self._bot_id,
            self._bot_name,
        )

        if folder_id == "/" or not folder_id:
            root["files"].append(file_data)
        else:

            def find_and_add(folder: dict, target_id: str) -> bool:
                if folder.get("folder_id") == target_id:
                    folder.setdefault("files", []).append(file_data)
                    return True
                for sf in folder.get("folders", []):
                    if find_and_add(sf, target_id):
                        return True
                return False

            find_and_add(root, folder_id)

        return self

    def add_group_folder(
        self,
        group_id: str,
        folder_name: str,
        folder_id: Optional[str] = None,
        parent_id: str = "/",
    ) -> "ScenarioBuilder":
        """添加群文件夹"""
        if group_id not in self._data["group_files"]:
            self._data["group_files"][group_id] = {
                "folder_id": "/",
                "folder_name": "/",
                "files": [],
                "folders": [],
            }

        root = self._data["group_files"][group_id]

        folder_data = create_folder_data(
            folder_id or f"folder_{len(root['folders']) + 1}",
            folder_name,
            self._bot_id,
            self._bot_name,
        )

        if parent_id == "/" or not parent_id:
            root["folders"].append(folder_data)
        else:

            def find_and_add(folder: dict, target_id: str) -> bool:
                if folder.get("folder_id") == target_id:
                    folder.setdefault("folders", []).append(folder_data)
                    return True
                for sf in folder.get("folders", []):
                    if find_and_add(sf, target_id):
                        return True
                return False

            find_and_add(root, parent_id)

        return self

    def build(self) -> dict:
        """构建并返回数据"""
        return self._data
