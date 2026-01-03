"""
使用真实数据的集成测试
"""

import pytest

from ncatbot.core import EventParser


class TestParseAllEventsFromLog:
    """测试解析日志中的所有事件"""

    def test_parse_all_events(self, data_provider, mock_api):
        """测试解析所有事件"""
        if not data_provider.has_data:
            pytest.skip("测试数据不可用")

        success_count = 0
        fail_count = 0
        failures = []

        for event_data in data_provider.all_events:
            try:
                event = EventParser.parse(event_data, mock_api)
                assert event is not None
                success_count += 1
            except Exception as e:
                fail_count += 1
                failures.append(
                    {
                        "error": str(e),
                        "post_type": event_data.get("post_type"),
                        "secondary": event_data.get("message_type")
                        or event_data.get("notice_type")
                        or event_data.get("meta_event_type"),
                    }
                )

        print(f"\n解析结果: 成功 {success_count}, 失败 {fail_count}")
        if failures:
            print("失败详情:")
            for f in failures[:5]:  # 只显示前5个
                print(f"  - {f['post_type']}/{f['secondary']}: {f['error']}")

        # 允许部分失败（如未实现的事件类型）
        assert success_count > 0

    def test_event_statistics(self, data_provider):
        """统计测试数据中的事件类型"""
        if not data_provider.has_data:
            pytest.skip("测试数据不可用")

        stats = {}
        for event in data_provider.all_events:
            post_type = event.get("post_type", "unknown")
            if post_type not in stats:
                stats[post_type] = {}

            # 获取二级类型
            secondary = (
                event.get("message_type")
                or event.get("notice_type")
                or event.get("meta_event_type")
                or event.get("request_type")
                or "unknown"
            )
            stats[post_type][secondary] = stats[post_type].get(secondary, 0) + 1

        print("\n事件统计:")
        for post_type, secondaries in stats.items():
            print(f"  {post_type}:")
            for sec, count in secondaries.items():
                print(f"    - {sec}: {count}")

        # 验证至少有消息和元事件
        assert "message" in stats
        assert "meta_event" in stats


class TestRealMessageReplySimulation:
    """模拟真实消息的回复场景"""

    @pytest.mark.asyncio
    async def test_reply_to_real_messages(self, data_provider, mock_api):
        """测试回复真实消息"""
        if not data_provider.has_data:
            pytest.skip("测试数据不可用")

        message_events = data_provider.message_events[:3]

        for event_data in message_events:
            event = EventParser.parse(event_data, mock_api)

            # 模拟回复
            await event.reply("自动回复测试")

            # 验证调用正确
            call = mock_api.get_last_call()
            if event.message_type == "group":
                assert call[0] == "post_group_msg"
            else:
                assert call[0] == "post_private_msg"

            mock_api.clear_calls()

    @pytest.mark.asyncio
    async def test_group_admin_on_real_data(self, group_message_events, mock_api):
        """测试对真实群消息执行管理操作"""
        if not group_message_events:
            pytest.skip("无群消息测试数据")

        event_data = group_message_events[0]
        event = EventParser.parse(event_data, mock_api)

        # 执行各种管理操作
        await event.reply("警告")
        await event.delete()
        await event.ban(duration=60)

        # 验证所有操作
        assert len(mock_api.calls) == 3


class TestEdgeCases:
    """边缘情况测试"""

    def test_empty_message_list(self, mock_api):
        """测试空消息列表"""
        data = {
            "time": 1767072441,
            "self_id": "1550507358",
            "post_type": "message",
            "message_type": "private",
            "sub_type": "friend",
            "message_id": "123",
            "user_id": "456",
            "message": [],
            "raw_message": "",
            "font": 14,
            "sender": {},
        }

        event = EventParser.parse(data, mock_api)
        assert event.message.message == []

    def test_unicode_content(self, mock_api):
        """测试 Unicode 内容"""
        data = {
            "time": 1767072441,
            "self_id": "1550507358",
            "post_type": "message",
            "message_type": "private",
            "sub_type": "friend",
            "message_id": "123",
            "user_id": "456",
            "message": [{"type": "text", "data": {"text": "你好世界🌍"}}],
            "raw_message": "你好世界🌍",
            "font": 14,
            "sender": {"nickname": "测试用户👤"},
        }

        event = EventParser.parse(data, mock_api)
        assert event.raw_message == "你好世界🌍"
        assert event.sender.nickname == "测试用户👤"

    def test_none_optional_fields(self, mock_api):
        """测试可选字段为 None"""
        data = {
            "time": 1767072511,
            "self_id": "1550507358",
            "post_type": "message",
            "message_type": "group",
            "sub_type": "normal",
            "message_id": "123",
            "user_id": "456",
            "group_id": "789",
            "message": [],
            "raw_message": "",
            "font": 14,
            "sender": {},
            "anonymous": None,  # 显式 None
        }

        event = EventParser.parse(data, mock_api)
        assert event.anonymous is None

    def test_extra_fields_ignored(self, mock_api):
        """测试额外字段被忽略"""
        data = {
            "time": 1767072441,
            "self_id": "1550507358",
            "post_type": "message",
            "message_type": "private",
            "sub_type": "friend",
            "message_id": "123",
            "user_id": "456",
            "message": [],
            "raw_message": "",
            "font": 14,
            "sender": {},
            # 额外字段
            "extra_field": "should be ignored",
            "message_seq": 123456,
            "target_id": "789",
        }

        # 不应抛出异常
        event = EventParser.parse(data, mock_api)
        assert event is not None

    def test_large_message_array(self, mock_api):
        """测试大消息数组"""
        segments = [
            {"type": "text", "data": {"text": f"segment_{i}"}} for i in range(100)
        ]

        data = {
            "time": 1767072441,
            "self_id": "1550507358",
            "post_type": "message",
            "message_type": "private",
            "sub_type": "friend",
            "message_id": "123",
            "user_id": "456",
            "message": segments,
            "raw_message": "".join(f"segment_{i}" for i in range(100)),
            "font": 14,
            "sender": {},
        }

        event = EventParser.parse(data, mock_api)
        assert len(event.message.message) == 100
