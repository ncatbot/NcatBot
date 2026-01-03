"""
基础信息场景测试

测试场景：账号信息 + 好友信息 + 群组信息
这些都是只读查询操作，无需用户输入，可以自动化完成

流程：
1. 获取登录信息、状态、版本信息
2. 获取好友列表及分类信息
3. 获取群列表和群信息
4. 获取群成员列表和成员信息
"""

from .framework import test_case, APITestSuite
from .utils import model_to_dict


# ============================================================================
# 场景测试：基础信息
# ============================================================================


class BasicInfoScenarioTests(APITestSuite):
    """
    基础信息场景测试

    测试无需用户输入的只读 API，包括：
    - 账号信息：登录信息、状态、版本
    - 好友信息：好友列表、分类、最近联系人
    - 群组信息：群列表、群信息、成员列表
    """

    suite_name = "Basic Info Scenario"
    suite_description = "基础信息场景测试（只读，自动化）"

    # ========== 账号信息部分 ==========

    @staticmethod
    @test_case(
        name="[场景1.1] 获取账号信息",
        description="获取登录信息、运行状态、版本信息",
        category="scenario",
        api_endpoint="/get_login_info, /get_status, /get_version_info",
        expected="返回完整的账号和系统信息",
        tags=["scenario", "account", "basic"],
        show_result=True,
    )
    async def test_account_info_scenario(api, data):
        """获取账号相关所有信息"""
        # 1. 获取登录信息
        login_info = await api.get_login_info()
        assert login_info is not None, "登录信息不能为空"
        assert hasattr(login_info, "user_id"), "登录信息应包含 user_id"
        assert hasattr(login_info, "nickname"), "登录信息应包含 nickname"

        # 2. 获取运行状态
        status = await api.get_status()
        assert status is not None, "状态信息不能为空"

        # 3. 获取版本信息
        version = await api.get_version_info()
        assert version is not None, "版本信息不能为空"

        return {
            "login_info": {
                "user_id": login_info.user_id,
                "nickname": login_info.nickname,
            },
            "status": model_to_dict(status),
            "version": model_to_dict(version),
        }

    # ========== 好友信息部分 ==========

    @staticmethod
    @test_case(
        name="[场景1.2] 获取好友信息",
        description="获取好友列表、分类好友、最近联系人",
        category="scenario",
        api_endpoint="/get_friend_list, /get_friends_with_category, /get_recent_contact",
        expected="返回好友相关的完整信息",
        tags=["scenario", "friend", "basic"],
        show_result=True,
    )
    async def test_friend_info_scenario(api, data):
        """获取好友相关所有信息"""
        # 1. 获取好友列表 - 返回 List[dict]
        friend_list = await api.get_friend_list()
        assert friend_list is not None, "好友列表不能为空"
        assert isinstance(friend_list, list), "好友列表应为列表类型"

        # 2. 获取带分类的好友列表
        friends_with_cat = await api.get_friends_with_cat()

        # 3. 获取最近联系人
        recent_contact = await api.get_recent_contact()

        return {
            "friend_count": len(friend_list),
            "friend_sample": [
                # friend_list 中的元素是 dict 类型
                {"user_id": f["user_id"], "nickname": f["nickname"]}
                for f in friend_list[:3]
            ],
            "friends_with_category": (
                {"count": len(friends_with_cat), "sample": friends_with_cat[:2]}
                if isinstance(friends_with_cat, list)
                else str(friends_with_cat)[:100]
            ),
            "recent_contact": (
                {"count": len(recent_contact), "sample": recent_contact[:2]}
                if isinstance(recent_contact, list)
                else str(recent_contact)[:100]
            ),
        }

    @staticmethod
    @test_case(
        name="[场景1.3] 获取陌生人信息",
        description="使用配置的 target_user 获取陌生人信息",
        category="scenario",
        api_endpoint="/get_stranger_info",
        expected="返回用户的基本信息",
        tags=["scenario", "friend"],
        show_result=True,
    )
    async def test_stranger_info_scenario(api, data):
        """获取陌生人信息"""
        target_user = data.get("target_user")
        if not target_user:
            raise ValueError("需要配置 target_user")

        result = await api.get_stranger_info(user_id=int(target_user))
        assert result is not None, "返回结果不能为空"

        return model_to_dict(result)

    # ========== 群组信息部分 ==========

    @staticmethod
    @test_case(
        name="[场景1.4] 获取群组信息",
        description="获取群列表、群详情、群成员列表、群成员详情",
        category="scenario",
        api_endpoint="/get_group_list, /get_group_info, /get_group_member_list, /get_group_member_info",
        expected="返回群组相关的完整信息",
        tags=["scenario", "group", "basic"],
        show_result=True,
    )
    async def test_group_info_scenario(api, data):
        """获取群组相关所有信息"""
        target_group = data.get("target_group")
        target_user = data.get("target_user")
        if not target_group:
            raise ValueError("需要配置 target_group")

        # 1. 获取群列表 - 返回 List[str]（默认）或 List[dict]（info=True）
        # 使用 info=True 获取详细信息
        group_list = await api.get_group_list(info=True)
        assert group_list is not None, "群列表不能为空"
        # group_list 是 List[dict] 类型
        groups = group_list if isinstance(group_list, list) else []

        # 2. 获取指定群信息 - 返回 GroupInfo 对象
        group_info = await api.get_group_info(group_id=int(target_group))
        assert group_info is not None, "群信息不能为空"

        # 3. 获取群成员列表 - 返回 GroupMemberList 对象
        member_list = await api.get_group_member_list(group_id=int(target_group))
        # GroupMemberList 有 members 属性
        members = member_list.members if hasattr(member_list, "members") else []

        # 4. 获取指定群成员信息 - 返回 GroupMemberInfo 对象
        member_info = None
        if target_user:
            member_info = await api.get_group_member_info(
                group_id=int(target_group), user_id=int(target_user)
            )

        return {
            "group_count": len(groups),
            "group_sample": [
                # groups 中的元素是 dict 类型（因为 info=True）
                {
                    "group_id": g["group_id"],
                    "group_name": g.get("group_name", ""),
                }
                for g in groups[:3]
            ],
            "target_group_info": model_to_dict(group_info),
            "member_count": len(members),
            "member_sample": [
                # members 中的元素是 GroupMemberInfo 对象
                {
                    "user_id": m.user_id,
                    "nickname": m.nickname,
                    "card": m.card,
                }
                for m in members[:3]
            ],
            "target_member_info": model_to_dict(member_info) if member_info else None,
        }

    @staticmethod
    @test_case(
        name="[场景1.5] 获取群禁言列表",
        description="获取群内被禁言的成员列表",
        category="scenario",
        api_endpoint="/get_group_shut_list",
        expected="返回禁言成员列表",
        tags=["scenario", "group"],
        show_result=True,
    )
    async def test_group_shut_list_scenario(api, data):
        """获取群禁言列表"""
        target_group = data.get("target_group")
        if not target_group:
            raise ValueError("需要配置 target_group")

        # get_group_shut_list 返回 GroupMemberList 对象
        result = await api.get_group_shut_list(group_id=int(target_group))
        # GroupMemberList 有 members 属性
        members = result.members if hasattr(result, "members") else []

        return {
            "shut_count": len(members),
            "shut_list": [
                # members 中的元素是 GroupMemberInfo 对象
                {"user_id": m.user_id, "nickname": m.nickname}
                for m in members[:5]
            ]
            if members
            else [],
        }


# 导出测试类
ALL_TEST_SUITES = [BasicInfoScenarioTests]
