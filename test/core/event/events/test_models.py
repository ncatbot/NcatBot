"""
models.py 模块测试 - 测试数据模型
"""

import pytest

from ncatbot.core import (
    BaseSender,
    GroupSender,
    Anonymous,
    FileInfo,
    Status,
)


class TestBaseSender:
    """测试 BaseSender 数据模型"""

    def test_create_with_defaults(self):
        """测试使用默认值创建"""
        sender = BaseSender()
        assert sender.user_id is None
        assert sender.nickname == "QQ用户"
        assert sender.sex == "unknown"
        assert sender.age == 0

    def test_create_with_values(self):
        """测试使用指定值创建"""
        sender = BaseSender(user_id="12345678", nickname="测试用户", sex="male", age=25)
        assert sender.user_id == "12345678"
        assert sender.nickname == "测试用户"
        assert sender.sex == "male"
        assert sender.age == 25

    def test_user_id_auto_convert_from_int(self):
        """测试 user_id 自动从整数转为字符串"""
        sender = BaseSender(user_id=12345678)
        assert sender.user_id == "12345678"
        assert isinstance(sender.user_id, str)

    def test_serialization_roundtrip(self):
        """测试序列化往返一致性"""
        original = BaseSender(
            user_id="12345678", nickname="测试用户", sex="female", age=20
        )
        data = original.model_dump()
        restored = BaseSender(**data)

        assert restored.user_id == original.user_id
        assert restored.nickname == original.nickname
        assert restored.sex == original.sex
        assert restored.age == original.age


class TestGroupSender:
    """测试 GroupSender 数据模型"""

    def test_create_with_defaults(self):
        """测试使用默认值创建"""
        sender = GroupSender()
        assert sender.card is None
        assert sender.area is None
        assert sender.level is None
        assert sender.role is None
        assert sender.title is None

    def test_create_with_group_fields(self):
        """测试创建带群组字段的发送者"""
        sender = GroupSender(
            user_id="12345678",
            nickname="测试用户",
            card="群名片",
            role="admin",
            level="10",
        )
        assert sender.user_id == "12345678"
        assert sender.card == "群名片"
        assert sender.role == "admin"
        assert sender.level == "10"

    def test_inherits_from_base_sender(self):
        """测试继承自 BaseSender"""
        sender = GroupSender(user_id="12345678", nickname="测试", sex="male", age=20)
        assert sender.nickname == "测试"
        assert sender.sex == "male"


class TestAnonymous:
    """测试 Anonymous 数据模型"""

    def test_create(self):
        """测试创建匿名用户模型"""
        anon = Anonymous(id=123456, name="匿名用户", flag="anon_flag_123")
        assert anon.id == 123456
        assert anon.name == "匿名用户"
        assert anon.flag == "anon_flag_123"

    def test_required_fields(self):
        """测试必填字段"""
        with pytest.raises(Exception):  # ValidationError
            Anonymous()


class TestFileInfo:
    """测试 FileInfo 数据模型"""

    def test_create(self):
        """测试创建文件信息模型"""
        file_info = FileInfo(id="file_123", name="test.txt", size=1024, busid=101)
        assert file_info.id == "file_123"
        assert file_info.name == "test.txt"
        assert file_info.size == 1024
        assert file_info.busid == 101

    def test_id_must_be_string(self):
        """测试 id 必须是字符串类型（不会自动转换，因为字段名不是 _id 结尾）"""
        # FileInfo.id 字段类型是 str，不会自动从 int 转换
        # 这与 user_id 等 _id 结尾的字段行为不同
        with pytest.raises(Exception):  # ValidationError
            FileInfo(
                id=123456,  # 整数会导致验证失败
                name="test.txt",
                size=1024,
                busid=101,
            )


class TestStatus:
    """测试 Status 数据模型"""

    def test_create_with_defaults(self):
        """测试使用默认值创建"""
        status = Status()
        assert status.online is True
        assert status.good is True

    def test_create_with_values(self):
        """测试使用指定值创建"""
        status = Status(online=False, good=False)
        assert status.online is False
        assert status.good is False

    def test_serialization_roundtrip(self):
        """测试序列化往返一致性"""
        original = Status(online=True, good=True)
        data = original.model_dump()
        restored = Status(**data)

        assert restored.online == original.online
        assert restored.good == original.good


class TestModelsWithRealData:
    """使用真实日志数据测试模型"""

    def test_base_sender_from_real_data(self, data_provider):
        """测试从真实数据解析 BaseSender"""
        if not data_provider.has_data:
            pytest.skip("测试数据不可用")

        for event in data_provider.message_events[:5]:
            sender_data = event.get("sender", {})
            if sender_data:
                sender = BaseSender(**sender_data)
                assert sender.user_id is not None or sender.nickname is not None

    def test_group_sender_from_real_data(self, data_provider):
        """测试从真实群消息数据解析 GroupSender"""
        if not data_provider.has_data:
            pytest.skip("测试数据不可用")

        group_events = data_provider.get_events_by_type("message", "group")
        for event in group_events[:5]:
            sender_data = event.get("sender", {})
            if sender_data:
                sender = GroupSender(**sender_data)
                assert sender.user_id is not None
                # 群消息的 sender 可能有 role 字段
                if "role" in sender_data:
                    assert sender.role in ["owner", "admin", "member", None]

    def test_status_from_heartbeat(self, data_provider):
        """测试从心跳事件解析 Status"""
        if not data_provider.has_data:
            pytest.skip("测试数据不可用")

        heartbeat_events = data_provider.get_events_by_type("meta_event", "heartbeat")
        for event in heartbeat_events[:3]:
            status_data = event.get("status", {})
            if status_data:
                status = Status(**status_data)
                assert isinstance(status.online, bool)
                assert isinstance(status.good, bool)
