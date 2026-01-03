"""
群管理相关数据模型

包含群信息、成员信息、群活跃度等数据类型定义。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


# =============================================================================
# 用户信息
# =============================================================================


@dataclass
class UserInfo:
    """用户基本信息"""

    avatar: str = ""
    """头像 URL"""
    description: str = ""
    """个人描述"""
    nickname: str = ""
    """昵称"""
    uid: str = ""
    """用户 UID"""
    user_id: int = 0
    """QQ 号"""

    def __init__(self, data: Dict[str, Any]):
        self.avatar = data.get("avatar", "")
        self.description = data.get("description", "")
        self.nickname = data.get("nickname", "")
        self.uid = data.get("uid", "")
        self.user_id = int(data.get("user_id", 0))


# =============================================================================
# 群活跃信息
# =============================================================================


@dataclass
class GroupChatActivity:
    """群聊天活跃信息"""

    all: List[dict] = field(default_factory=list)
    """所有荣誉信息"""
    emotion: List[dict] = field(default_factory=list)
    """表情相关荣誉"""
    legend: List[dict] = field(default_factory=list)
    """传奇荣誉"""
    performer: List[dict] = field(default_factory=list)
    """表现荣誉"""
    talkative: List[dict] = field(default_factory=list)
    """龙王信息"""

    def __init__(self, data: Dict[str, Any]):
        self.all = data.get("all", [])
        self.emotion = data.get("emotion", [])
        self.legend = data.get("legend", [])
        self.performer = data.get("performer", [])
        self.talkative = data.get("talkative", [])


# =============================================================================
# 群信息
# =============================================================================


@dataclass
class GroupInfo:
    """群基本信息"""

    group_id: int = 0
    """群号"""
    group_name: str = ""
    """群名"""
    member_count: int = 0
    """成员数量"""
    max_member_count: int = 0
    """最大成员数"""
    group_desc: str = ""
    """群描述"""
    group_type: int = 0
    """群类型"""
    group_create_time: int = 0
    """创建时间戳"""
    group_level: int = 0
    """群等级"""
    master_id: int = 0
    """群主 ID"""

    def __init__(
        self,
        group_id: int = 0,
        group_name: str = "",
        member_count: int = 0,
        max_member_count: int = 0,
        group_desc: str = "",
        group_type: int = 0,
        group_create_time: int = 0,
        group_level: int = 0,
        master_id: int = 0,
        **kwargs,
    ):
        self.group_id = group_id
        self.group_name = group_name
        self.member_count = member_count
        self.max_member_count = max_member_count
        self.group_desc = group_desc
        self.group_type = group_type
        self.group_create_time = group_create_time
        self.group_level = group_level
        self.master_id = master_id


# =============================================================================
# 群成员信息
# =============================================================================


@dataclass
class GroupMemberInfo:
    """群成员详细信息"""

    card: str = ""
    """群名片"""
    card_changeable: bool = False
    """名片是否可更改"""
    group_id: int = 0
    """群号"""
    join_time: int = 0
    """入群时间戳"""
    last_sent_time: int = 0
    """最后发言时间戳"""
    level: str = ""
    """等级"""
    nickname: str = ""
    """昵称"""
    role: str = ""
    """角色（owner/admin/member）"""
    shut_up_timestamp: int = 0
    """禁言结束时间戳"""
    title: str = ""
    """头衔"""
    title_expire_time: int = 0
    """头衔过期时间戳"""
    unfriendly: bool = False
    """是否不友好"""
    user_id: int = 0
    """QQ 号"""

    def __init__(
        self,
        card: str = "",
        card_changeable: bool = False,
        group_id: int = 0,
        join_time: int = 0,
        last_sent_time: int = 0,
        level: str = "",
        nickname: str = "",
        role: str = "",
        shut_up_timestamp: int = 0,
        title: str = "",
        title_expire_time: int = 0,
        unfriendly: bool = False,
        user_id: int = 0,
        **kwargs,
    ):
        self.card = card
        self.card_changeable = card_changeable
        self.group_id = group_id
        self.join_time = join_time
        self.last_sent_time = last_sent_time
        self.level = level
        self.nickname = nickname
        self.role = role
        self.shut_up_timestamp = shut_up_timestamp
        self.title = title
        self.title_expire_time = title_expire_time
        self.unfriendly = unfriendly
        self.user_id = user_id


# =============================================================================
# 群成员列表
# =============================================================================


@dataclass
class GroupMemberList:
    """群成员列表"""

    members: List[GroupMemberInfo] = field(default_factory=list)
    """成员信息列表"""

    def __init__(self, data: List[Dict[str, Any]]):
        self.members = [GroupMemberInfo(**member) for member in data]

    @classmethod
    def from_shut_list(cls, data: List[Dict[str, Any]]) -> "GroupMemberList":
        """从禁言列表数据创建成员列表"""
        instance = cls([])
        instance.members = [GroupMemberInfo(**member) for member in data]
        return instance

    def __iter__(self):
        return iter(self.members)

    def __len__(self):
        return len(self.members)

    def __getitem__(self, index):
        return self.members[index]


# =============================================================================
# 精华消息
# =============================================================================


@dataclass
class EssenceMessage:
    """精华消息信息"""

    group_id: int = 0
    """群号"""
    message_id: int = 0
    """消息 ID"""
    message_seq: int = 0
    """消息序号"""
    sender_id: int = 0
    """发送者 QQ 号"""
    sender_nick: str = ""
    """发送者昵称"""
    sender_time: int = 0
    """发送时间戳"""
    operator_id: int = 0
    """设置者 QQ 号"""
    operator_nick: str = ""
    """设置者昵称"""
    operator_time: int = 0
    """设置时间戳"""

    def __init__(
        self,
        group_id: int = 0,
        message_id: int = 0,
        message_seq: int = 0,
        sender_id: int = 0,
        sender_nick: str = "",
        sender_time: int = 0,
        operator_id: int = 0,
        operator_nick: str = "",
        operator_time: int = 0,
        **kwargs,
    ):
        self.group_id = group_id
        self.message_id = message_id
        self.message_seq = message_seq
        self.sender_id = sender_id
        self.sender_nick = sender_nick
        self.sender_time = sender_time
        self.operator_id = operator_id
        self.operator_nick = operator_nick
        self.operator_time = operator_time
