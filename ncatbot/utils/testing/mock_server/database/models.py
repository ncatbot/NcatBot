"""
Mock 数据模型

定义测试数据的数据类。
"""

import time
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class MockUser:
    """用户数据"""

    user_id: str
    nickname: str
    sex: str = "unknown"
    age: int = 0
    remark: str = ""
    level: int = 0

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "nickname": self.nickname,
            "sex": self.sex,
            "age": self.age,
            "remark": self.remark,
            "level": self.level,
        }


@dataclass
class MockGroupMember:
    """群成员数据"""

    user_id: str
    nickname: str
    card: str = ""
    role: str = "member"  # owner, admin, member
    join_time: int = 0
    last_sent_time: int = 0
    level: str = "1"
    title: str = ""

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "nickname": self.nickname,
            "card": self.card,
            "role": self.role,
            "join_time": self.join_time,
            "last_sent_time": self.last_sent_time,
            "level": self.level,
            "title": self.title,
        }


@dataclass
class MockGroup:
    """群数据"""

    group_id: str
    group_name: str
    member_count: int = 0
    max_member_count: int = 500
    owner_id: str = ""
    members: List[MockGroupMember] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "group_id": self.group_id,
            "group_name": self.group_name,
            "member_count": self.member_count or len(self.members),
            "max_member_count": self.max_member_count,
            "owner_id": self.owner_id,
        }

    def get_member(self, user_id: str) -> Optional[MockGroupMember]:
        """获取群成员"""
        for member in self.members:
            if member.user_id == str(user_id):
                return member
        return None


@dataclass
class MockMessage:
    """消息数据"""

    message_id: str
    message_type: str  # group, private
    user_id: str
    group_id: Optional[str] = None
    target_id: Optional[str] = None  # 私聊目标
    message: List[dict] = field(default_factory=list)
    raw_message: str = ""
    time: int = 0
    sender: dict = field(default_factory=dict)
    message_seq: int = 0

    def to_dict(self) -> dict:
        data = {
            "message_id": self.message_id,
            "message_type": self.message_type,
            "user_id": self.user_id,
            "message": self.message,
            "raw_message": self.raw_message,
            "time": self.time or int(time.time()),
            "sender": self.sender,
            "message_seq": self.message_seq,
        }
        if self.group_id:
            data["group_id"] = self.group_id
        if self.target_id:
            data["target_id"] = self.target_id
        return data


@dataclass
class MockFile:
    """文件数据"""

    file_id: str
    file_name: str
    file_size: int = 0
    busid: int = 0
    upload_time: int = 0
    dead_time: int = 0
    modify_time: int = 0
    download_times: int = 0
    uploader: str = ""
    uploader_name: str = ""

    def to_dict(self) -> dict:
        return {
            "file_id": self.file_id,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "busid": self.busid,
            "upload_time": self.upload_time or int(time.time()),
            "dead_time": self.dead_time,
            "modify_time": self.modify_time or int(time.time()),
            "download_times": self.download_times,
            "uploader": self.uploader,
            "uploader_name": self.uploader_name,
        }


@dataclass
class MockFolder:
    """文件夹数据"""

    folder_id: str
    folder_name: str
    create_time: int = 0
    creator: str = ""
    creator_name: str = ""
    total_file_count: int = 0
    files: List[MockFile] = field(default_factory=list)
    subfolders: List["MockFolder"] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "folder_id": self.folder_id,
            "folder_name": self.folder_name,
            "create_time": self.create_time or int(time.time()),
            "creator": self.creator,
            "creator_name": self.creator_name,
            "total_file_count": self.total_file_count or len(self.files),
        }

    def get_file(self, file_id: str) -> Optional[MockFile]:
        """获取文件"""
        for f in self.files:
            if f.file_id == file_id:
                return f
        return None

    def get_subfolder(self, folder_id: str) -> Optional["MockFolder"]:
        """获取子文件夹"""
        for sf in self.subfolders:
            if sf.folder_id == folder_id:
                return sf
        return None
