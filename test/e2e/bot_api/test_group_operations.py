"""
群组信息与操作复合测试

测试内容：
- 群列表获取
- 群信息查询
- 群成员列表
- 群成员信息
- 群管理操作（禁言、设置名片等）
"""

import pytest


class TestGroupInfo:
    """群组信息综合测试"""

    @pytest.mark.asyncio
    async def test_group_info_complete(self, api_suite, standard_group_id):
        """
        群组信息综合测试

        测试内容：
        1. 获取群列表
        2. 获取指定群信息
        3. 获取群成员列表
        4. 获取指定群成员信息
        5. 获取群禁言列表
        """
        api = api_suite.api

        # 1. 获取群列表
        group_list = await api.get_group_list()
        assert group_list is not None, "群列表不能为空"
        assert isinstance(group_list, list), "群列表应为列表类型"

        # 2. 获取指定群信息
        group_info = await api.get_group_info(group_id=int(standard_group_id))
        assert group_info is not None, "群信息不能为空"
        assert hasattr(group_info, "group_id"), "群信息应包含 group_id"

        # 3. 获取群成员列表
        member_list = await api.get_group_member_list(group_id=int(standard_group_id))
        assert member_list is not None, "群成员列表不能为空"
        # GroupMemberList 有 members 属性
        members = member_list.members if hasattr(member_list, "members") else []
        assert isinstance(members, list), "成员列表应为列表类型"

        # 4. 如果有成员，获取第一个成员的详细信息
        if members:
            first_member = members[0]
            member_info = await api.get_group_member_info(
                group_id=int(standard_group_id), user_id=int(first_member.user_id)
            )
            assert member_info is not None, "成员信息不能为空"
            api_suite.assert_api_called("get_group_member_info")

        # 5. 获取群禁言列表
        shut_list = await api.get_group_shut_list(group_id=int(standard_group_id))
        assert shut_list is not None, "禁言列表不能为空"

        # 验证关键 API 被调用
        api_suite.assert_api_called("get_group_list")
        api_suite.assert_api_called("get_group_info")
        api_suite.assert_api_called("get_group_member_list")
        api_suite.assert_api_called("get_group_shut_list")


class TestGroupAdminOperations:
    """群管理操作综合测试"""

    @pytest.mark.asyncio
    async def test_group_member_management(
        self, api_suite, standard_group_id, standard_user_id
    ):
        """
        群成员管理综合测试

        测试内容：
        1. 设置群名片
        2. 设置群头衔
        3. 设置群成员禁言（然后解禁）
        """
        api = api_suite.api

        # 1. 设置群名片
        await api.set_group_card(
            group_id=int(standard_group_id),
            user_id=int(standard_user_id),
            card="测试名片",
        )
        api_suite.assert_api_called_with(
            "set_group_card",
            group_id=int(standard_group_id),
            user_id=int(standard_user_id),
            card="测试名片",
        )

        # 2. 设置群头衔
        api_suite.clear_call_history()
        await api.set_group_special_title(
            group_id=int(standard_group_id),
            user_id=int(standard_user_id),
            special_title="测试头衔",
        )
        api_suite.assert_api_called("set_group_special_title")

        # 3. 设置禁言
        api_suite.clear_call_history()
        await api.set_group_ban(
            group_id=int(standard_group_id), user_id=int(standard_user_id), duration=60
        )
        api_suite.assert_api_called_with(
            "set_group_ban",
            group_id=int(standard_group_id),
            user_id=int(standard_user_id),
            duration=60,
        )

        # 4. 解除禁言（duration=0）
        api_suite.clear_call_history()
        await api.set_group_ban(
            group_id=int(standard_group_id), user_id=int(standard_user_id), duration=0
        )
        api_suite.assert_api_called_with("set_group_ban", duration=0)

    @pytest.mark.asyncio
    async def test_group_poke_operation(
        self, api_suite, standard_group_id, standard_user_id
    ):
        """
        群戳一戳操作测试

        测试内容：
        1. 发送群戳一戳
        2. 验证 API 调用参数
        """
        api = api_suite.api

        # 执行戳一戳操作
        await api.group_poke(
            group_id=int(standard_group_id), user_id=int(standard_user_id)
        )

        # 验证 API 调用
        api_suite.assert_api_called_with(
            "group_poke", group_id=int(standard_group_id), user_id=int(standard_user_id)
        )

    @pytest.mark.asyncio
    async def test_group_honor_info(self, api_suite, standard_group_id):
        """
        群荣誉信息测试

        测试内容：
        1. 获取群荣誉信息
        2. 验证返回数据结构
        """
        api = api_suite.api

        # 获取群荣誉信息
        honor_info = await api.get_group_honor_info(
            group_id=int(standard_group_id), type="all"
        )
        assert honor_info is not None, "群荣誉信息不能为空"

        # 验证 API 调用
        api_suite.assert_api_called("get_group_honor_info")
