"""
转发消息与支持功能测试

测试内容：
- 合并转发消息发送
- 版本信息查询
- 能力检查
"""

import pytest


class TestForwardMessage:
    """合并转发消息测试"""

    @pytest.mark.asyncio
    async def test_forward_msg_send(self, api_suite, standard_group_id):
        """
        合并转发消息发送测试

        测试内容：
        1. 发送群合并转发消息
        2. 验证 API 调用
        """
        api = api_suite.api

        # 发送合并转发消息
        result = await api.send_forward_msg(
            group_id=int(standard_group_id),
            messages=[],
            news=["预览文本1", "预览文本2"],
            prompt="[聊天记录]",
            summary="查看 2 条转发消息",
            source="群聊的聊天记录",
        )
        # send_forward_msg 应该返回 message_id
        assert result is not None
        api_suite.assert_api_called("send_forward_msg")


class TestSupportAPI:
    """支持功能 API 测试"""

    @pytest.mark.asyncio
    async def test_version_and_capability(self, api_suite):
        """
        版本信息与能力检查综合测试

        测试内容：
        1. 获取版本信息
        2. 检查发送图片能力
        """
        api = api_suite.api

        # 1. 获取版本信息
        version = await api.get_version_info()
        assert version is not None, "版本信息不能为空"
        assert isinstance(version, dict), "版本信息应为字典"
        api_suite.assert_api_called("get_version_info")

        # 2. 检查发送图片能力
        api_suite.clear_call_history()
        can_send = await api.can_send_image()
        # 结果应该是布尔值
        assert isinstance(can_send, bool), "can_send_image 应返回布尔值"
        api_suite.assert_api_called("can_send_image")


class TestGroupAdminExtended:
    """群管理扩展操作测试"""

    @pytest.mark.asyncio
    async def test_group_settings_operations(self, api_suite, standard_group_id):
        """
        群设置操作测试

        测试内容：
        1. 设置群备注
        2. 群签到
        """
        api = api_suite.api

        # 1. 设置群备注
        await api.set_group_remark(group_id=int(standard_group_id), remark="测试群备注")
        api_suite.assert_api_called("set_group_remark")

        # 2. 群签到
        api_suite.clear_call_history()
        await api.set_group_sign(group_id=int(standard_group_id))
        api_suite.assert_api_called("set_group_sign")

    @pytest.mark.asyncio
    async def test_whole_group_ban(self, api_suite, standard_group_id):
        """
        全群禁言测试

        测试内容：
        1. 开启全群禁言
        2. 关闭全群禁言
        """
        api = api_suite.api

        # 1. 开启全群禁言
        await api.set_group_whole_ban(group_id=int(standard_group_id), enable=True)
        api_suite.assert_api_called_with(
            "set_group_whole_ban", group_id=int(standard_group_id), enable=True
        )

        # 2. 关闭全群禁言
        api_suite.clear_call_history()
        await api.set_group_whole_ban(group_id=int(standard_group_id), enable=False)
        api_suite.assert_api_called_with("set_group_whole_ban", enable=False)


class TestAccountExtended:
    """账号扩展操作测试"""

    @pytest.mark.asyncio
    async def test_profile_operations(self, api_suite):
        """
        资料设置测试

        测试内容：
        1. 设置 QQ 资料
        2. 设置在线状态
        3. 设置个人长昵称
        """
        api = api_suite.api

        # 1. 设置 QQ 资料
        await api.set_qq_profile(
            nickname="测试昵称", personal_note="测试签名", sex="未知"
        )
        api_suite.assert_api_called("set_qq_profile")

        # 2. 设置在线状态
        api_suite.clear_call_history()
        await api.set_online_status(status=11, ext_status=0, battery_status=100)
        api_suite.assert_api_called("set_online_status")

        # 3. 设置个人长昵称
        api_suite.clear_call_history()
        await api.set_self_longnick(long_nick="这是一个很长的昵称用于测试")
        api_suite.assert_api_called("set_self_longnick")

    @pytest.mark.asyncio
    async def test_friend_management(self, api_suite, standard_user_id):
        """
        好友管理测试

        测试内容：
        1. 设置好友备注
        2. 获取用户状态
        """
        api = api_suite.api

        # 1. 设置好友备注
        await api.set_friend_remark(user_id=int(standard_user_id), remark="测试备注")
        api_suite.assert_api_called("set_friend_remark")

        # 2. 获取用户状态
        api_suite.clear_call_history()
        status = await api.nc_get_user_status(user_id=int(standard_user_id))
        assert status is not None, "用户状态不能为空"
        api_suite.assert_api_called("nc_get_user_status")
