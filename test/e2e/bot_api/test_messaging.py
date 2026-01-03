"""
消息发送与检索复合测试

测试内容：
- 群消息发送
- 私聊消息发送
- 消息删除
- API 调用记录验证
"""

import pytest


class TestMessageSending:
    """消息发送综合测试"""

    @pytest.mark.asyncio
    async def test_group_message_complete(self, api_suite, standard_group_id):
        """
        群消息发送综合测试

        测试内容：
        1. 发送纯文本群消息
        2. 验证消息 ID 返回
        3. 验证 API 调用参数
        4. 发送多条消息验证调用计数
        """
        api = api_suite.api

        # 1. 发送纯文本群消息
        message_id = await api.post_group_msg(
            group_id=int(standard_group_id), text="测试群消息"
        )
        assert message_id is not None, "发送消息应返回 message_id"
        assert message_id, "message_id 不能为空"

        # 验证 API 调用
        api_suite.assert_api_called("send_group_msg")

        # 2. 发送第二条消息
        api_suite.clear_call_history()
        message_id_2 = await api.post_group_msg(
            group_id=int(standard_group_id), text="第二条测试消息"
        )
        assert message_id_2 is not None
        assert message_id != message_id_2, "两条消息应有不同的 ID"

        # 验证调用参数
        api_suite.assert_api_called_with(
            "send_group_msg", group_id=int(standard_group_id)
        )

    @pytest.mark.asyncio
    async def test_private_message_complete(self, api_suite, standard_user_id):
        """
        私聊消息发送综合测试

        测试内容：
        1. 发送纯文本私聊消息
        2. 验证消息 ID 返回
        3. 验证 API 调用参数
        """
        api = api_suite.api

        # 1. 发送私聊消息
        message_id = await api.post_private_msg(
            user_id=int(standard_user_id), text="测试私聊消息"
        )
        assert message_id is not None, "发送消息应返回 message_id"
        assert message_id, "message_id 不能为空"

        # 验证 API 调用
        api_suite.assert_api_called("send_private_msg")

        # 验证调用参数
        api_suite.assert_api_called_with(
            "send_private_msg", user_id=int(standard_user_id)
        )


class TestMessageOperations:
    """消息操作综合测试"""

    @pytest.mark.asyncio
    async def test_message_delete(self, api_suite, standard_group_id):
        """
        消息删除测试

        测试内容：
        1. 发送消息
        2. 删除消息
        3. 验证 API 调用参数
        """
        api = api_suite.api

        # 1. 发送消息
        message_id = await api.post_group_msg(
            group_id=int(standard_group_id), text="待删除的测试消息"
        )
        assert message_id, "发送消息应返回 message_id"

        # 2. 删除消息
        api_suite.clear_call_history()
        await api.delete_msg(message_id=int(message_id))
        api_suite.assert_api_called("delete_msg")
        api_suite.assert_api_called_with("delete_msg", message_id=int(message_id))

    @pytest.mark.asyncio
    async def test_emoji_reaction(self, api_suite, standard_group_id):
        """
        表情回应测试

        测试内容：
        1. 发送消息以获得有效消息 ID
        2. 对消息添加表情回应
        3. 验证 API 调用
        """
        api = api_suite.api

        # 1. 发送一条消息以获取有效的消息 ID
        message_id = await api.post_group_msg(
            group_id=int(standard_group_id), text="表情测试消息"
        )
        assert message_id, "需要有效的消息 ID"

        # 2. 添加表情回应
        api_suite.clear_call_history()
        await api.set_msg_emoji_like(
            message_id=int(message_id),
            emoji_id=128077,  # 👍
        )
        api_suite.assert_api_called("set_msg_emoji_like")


class TestMediaRetrieval:
    """媒体检索测试"""

    @pytest.mark.asyncio
    async def test_get_media_urls(self, api_suite):
        """
        媒体 URL 获取测试

        测试内容：
        1. 获取图片 URL
        2. 获取语音 URL
        """
        api = api_suite.api

        # 1. 获取图片信息
        mock_file_id = "test_image_file_id"
        image_info = await api.get_image(file=mock_file_id)
        assert image_info is not None, "图片信息不能为空"
        api_suite.assert_api_called("get_image")

        # 2. 获取语音信息
        api_suite.clear_call_history()
        mock_record_id = "test_record_file_id"
        record_info = await api.get_record(file=mock_record_id)
        assert record_info is not None, "语音信息不能为空"
        api_suite.assert_api_called("get_record")
