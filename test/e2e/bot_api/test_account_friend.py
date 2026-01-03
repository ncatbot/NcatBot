"""
账号与好友信息复合测试

测试内容：
- 登录信息获取
- 账号状态查询
- 好友列表获取
- 陌生人信息获取
- 点赞操作
"""

import pytest


class TestAccountInfo:
    """账号信息综合测试"""

    @pytest.mark.asyncio
    async def test_account_info_complete(self, api_suite):
        """
        账号信息综合测试

        测试内容：
        1. 获取登录信息
        2. 获取账号状态
        3. 验证返回数据结构
        """
        api = api_suite.api

        # 1. 获取登录信息
        login_info = await api.get_login_info()
        assert login_info is not None, "登录信息不能为空"
        assert hasattr(login_info, "user_id"), "登录信息应包含 user_id"
        assert hasattr(login_info, "nickname"), "登录信息应包含 nickname"
        assert login_info.user_id, "user_id 不能为空"

        # 2. 获取账号状态
        status = await api.get_status()
        assert status is not None, "状态信息不能为空"
        assert isinstance(status, dict), "状态应为字典类型"

        # 3. 验证 API 调用被正确记录
        api_suite.assert_api_called("get_login_info")
        api_suite.assert_api_called("get_status")


class TestFriendOperations:
    """好友操作综合测试"""

    @pytest.mark.asyncio
    async def test_friend_info_complete(self, api_suite):
        """
        好友信息综合测试

        测试内容：
        1. 获取好友列表
        2. 获取带分类的好友列表
        3. 获取最近联系人
        4. 获取陌生人信息
        """
        api = api_suite.api

        # 1. 获取好友列表
        friend_list = await api.get_friend_list()
        assert friend_list is not None, "好友列表不能为空"
        assert isinstance(friend_list, list), "好友列表应为列表类型"

        # 2. 获取带分类的好友列表
        friends_with_cat = await api.get_friends_with_cat()
        assert friends_with_cat is not None, "带分类好友列表不能为空"

        # 3. 获取最近联系人
        recent_contact = await api.get_recent_contact()
        assert recent_contact is not None, "最近联系人不能为空"

        # 4. 获取陌生人信息（使用标准数据中的用户）
        if friend_list:
            first_friend = friend_list[0]
            user_id = first_friend.get("user_id")
            if user_id:
                stranger_info = await api.get_stranger_info(user_id=user_id)
                assert stranger_info is not None, "陌生人信息不能为空"

        # 验证 API 调用
        api_suite.assert_api_called("get_friend_list")
        api_suite.assert_api_called("get_friends_with_category")
        api_suite.assert_api_called("get_recent_contact")

    @pytest.mark.asyncio
    async def test_send_like_operation(self, api_suite, standard_user_id):
        """
        点赞操作测试

        测试内容：
        1. 给用户点赞
        2. 验证 API 调用参数
        """
        api = api_suite.api

        # 执行点赞操作
        result = await api.send_like(user_id=standard_user_id, times=1)
        assert result is not None, "点赞操作应返回结果"

        # 验证 API 调用参数
        api_suite.assert_api_called_with("send_like", user_id=standard_user_id, times=1)

    @pytest.mark.asyncio
    async def test_message_read_status(
        self, api_suite, standard_user_id, standard_group_id
    ):
        """
        消息已读状态测试

        测试内容：
        1. 将群消息标记为已读
        2. 将私聊消息标记为已读
        """
        api = api_suite.api

        # 1. 将群消息标记为已读
        await api.mark_group_msg_as_read(group_id=standard_group_id)
        api_suite.assert_api_called("mark_group_msg_as_read")

        # 2. 将私聊消息标记为已读
        api_suite.clear_call_history()
        await api.mark_private_msg_as_read(user_id=standard_user_id)
        api_suite.assert_api_called("mark_private_msg_as_read")
