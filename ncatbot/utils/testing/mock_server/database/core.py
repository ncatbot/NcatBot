"""
Mock 数据库核心

提供基于内存的测试数据存储，支持状态变更和重置。
"""

import json
import copy
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Union

from .messages import MessageOperationsMixin
from .files import FileOperationsMixin


class MockDatabase(MessageOperationsMixin, FileOperationsMixin):
    """
    Mock 数据库

    使用内存存储测试数据，支持从 JSON 加载初始数据。
    测试结束后可以重置到初始状态。
    """

    def __init__(self, initial_data: Optional[dict] = None):
        """
        初始化 Mock 数据库

        Args:
            initial_data: 初始数据字典，如果不提供则使用默认数据
        """
        self._initial_data = initial_data or self._get_default_data()
        self._data: dict = {}
        self.reset()

    @staticmethod
    def _get_default_data() -> dict:
        """获取默认测试数据"""
        return {
            "bot": {
                "user_id": "123456789",
                "nickname": "TestBot",
            },
            "friends": [
                {"user_id": "100001", "nickname": "好友1", "remark": "测试好友1"},
                {"user_id": "100002", "nickname": "好友2", "remark": "测试好友2"},
            ],
            "groups": [
                {
                    "group_id": "200001",
                    "group_name": "测试群1",
                    "owner_id": "123456789",
                    "members": [
                        {
                            "user_id": "123456789",
                            "nickname": "TestBot",
                            "role": "owner",
                        },
                        {"user_id": "100001", "nickname": "好友1", "role": "admin"},
                        {"user_id": "100002", "nickname": "好友2", "role": "member"},
                    ],
                },
                {
                    "group_id": "200002",
                    "group_name": "测试群2",
                    "owner_id": "100001",
                    "members": [
                        {"user_id": "100001", "nickname": "好友1", "role": "owner"},
                        {
                            "user_id": "123456789",
                            "nickname": "TestBot",
                            "role": "member",
                        },
                    ],
                },
            ],
            "group_messages": {},
            "private_messages": {},
            "group_files": {},
        }

    def reset(self) -> None:
        """重置数据库到初始状态"""
        self._data = copy.deepcopy(self._initial_data)
        self._message_id_counter = 1000000
        self._file_id_counter = 1000000
        self._folder_id_counter = 1000000
        self._message_seq_counter: Dict[str, int] = {}

        # 确保必要的字段存在
        self._data.setdefault("group_messages", {})
        self._data.setdefault("private_messages", {})
        self._data.setdefault("group_files", {})

    def load_from_json(self, path: Union[str, Path]) -> None:
        """从 JSON 文件加载初始数据"""
        with open(path, "r", encoding="utf-8") as f:
            self._initial_data = json.load(f)
        self.reset()

    def save_to_json(self, path: Union[str, Path]) -> None:
        """保存当前数据到 JSON 文件"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    # =========================================================================
    # ID 生成
    # =========================================================================

    def _generate_message_id(self) -> str:
        """生成消息 ID"""
        self._message_id_counter += 1
        return str(self._message_id_counter)

    def _generate_file_id(self) -> str:
        """生成文件 ID"""
        self._file_id_counter += 1
        return f"file_{self._file_id_counter}_{uuid.uuid4().hex[:8]}"

    def _generate_folder_id(self) -> str:
        """生成文件夹 ID"""
        self._folder_id_counter += 1
        return f"folder_{self._folder_id_counter}_{uuid.uuid4().hex[:8]}"

    def _get_message_seq(self, key: str) -> int:
        """获取下一个消息序号"""
        seq = self._message_seq_counter.get(key, 0) + 1
        self._message_seq_counter[key] = seq
        return seq

    # =========================================================================
    # Bot 信息
    # =========================================================================

    def get_login_info(self) -> dict:
        """获取登录信息"""
        return self._data.get("bot", {"user_id": "123456789", "nickname": "TestBot"})

    def get_status(self) -> dict:
        """获取状态"""
        return {"online": True, "good": True}

    # =========================================================================
    # 好友相关
    # =========================================================================

    def get_friend_list(self) -> List[dict]:
        """获取好友列表"""
        return self._data.get("friends", [])

    def get_stranger_info(self, user_id: str) -> Optional[dict]:
        """获取陌生人信息"""
        # 先从好友中查找
        for friend in self._data.get("friends", []):
            if str(friend.get("user_id")) == str(user_id):
                return friend

        # 从群成员中查找
        for group in self._data.get("groups", []):
            for member in group.get("members", []):
                if str(member.get("user_id")) == str(user_id):
                    return {
                        "user_id": member.get("user_id"),
                        "nickname": member.get("nickname"),
                    }
        return None

    # =========================================================================
    # 群相关
    # =========================================================================

    def get_group_list(self) -> List[dict]:
        """获取群列表"""
        return [
            {
                "group_id": g.get("group_id"),
                "group_name": g.get("group_name"),
                "member_count": len(g.get("members", [])),
                "max_member_count": g.get("max_member_count", 500),
            }
            for g in self._data.get("groups", [])
        ]

    def get_group_info(self, group_id: str) -> Optional[dict]:
        """获取群信息"""
        for group in self._data.get("groups", []):
            if str(group.get("group_id")) == str(group_id):
                return {
                    "group_id": group.get("group_id"),
                    "group_name": group.get("group_name"),
                    "member_count": len(group.get("members", [])),
                    "max_member_count": group.get("max_member_count", 500),
                    "owner_id": group.get("owner_id"),
                }
        return None

    def get_group_member_list(self, group_id: str) -> List[dict]:
        """获取群成员列表"""
        for group in self._data.get("groups", []):
            if str(group.get("group_id")) == str(group_id):
                return group.get("members", [])
        return []

    def get_group_member_info(self, group_id: str, user_id: str) -> Optional[dict]:
        """获取群成员信息"""
        for group in self._data.get("groups", []):
            if str(group.get("group_id")) == str(group_id):
                for member in group.get("members", []):
                    if str(member.get("user_id")) == str(user_id):
                        return member
        return None
