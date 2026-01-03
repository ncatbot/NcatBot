"""
群管理场景测试

测试场景：群管理操作 + 精华消息
将需要管理员权限的操作整合在一起

流程：
1. 精华消息：发送消息 → 设为精华 → 获取精华列表 → 取消精华
2. 群管理操作（需要用户确认的危险操作单独分组）

注意：部分测试需要管理员权限
"""

from .framework import test_case, APITestSuite


# ============================================================================
# 场景测试：群管理
# ============================================================================


class GroupAdminScenarioTests(APITestSuite):
    """
    群管理场景测试

    测试流程：
    1. 精华消息生命周期
    2. 群管理基础操作（需要管理员权限）
    """

    suite_name = "Group Admin Scenario"
    suite_description = "群管理场景测试（需要管理员权限）"

    @staticmethod
    @test_case(
        name="[场景5.1] 精华消息生命周期",
        description="发送消息 → 设为精华 → 获取精华列表 → 取消精华",
        category="scenario",
        api_endpoint="/post_group_msg, /set_essence_msg, /get_essence_msg_list, /delete_essence_msg",
        expected="精华消息全流程操作成功",
        tags=["scenario", "admin", "essence"],
        show_result=True,
    )
    async def test_essence_lifecycle_scenario(api, data):
        """精华消息生命周期测试"""
        target_group = data.get("target_group")
        if not target_group:
            raise ValueError("需要配置 target_group")

        result = {
            "step1_send": None,
            "step2_set_essence": None,
            "step3_get_list": None,
            "step4_delete_essence": None,
        }

        # 1. 发送测试消息
        content = "[E2E 场景测试] 精华消息测试 ⭐"
        # post_group_msg 返回 str 类型的 message_id
        message_id = await api.post_group_msg(group_id=int(target_group), text=content)
        assert message_id, "发送消息失败，未获取到 message_id"
        result["step1_send"] = {"message_id": message_id, "content": content}

        # 2. 设为精华消息
        try:
            await api.set_essence_msg(message_id=int(message_id))
            result["step2_set_essence"] = {
                "status": "success",
                "message_id": message_id,
            }
        except Exception as e:
            result["step2_set_essence"] = {
                "error": str(e),
                "note": "可能需要管理员权限",
            }

        # 3. 获取精华消息列表
        try:
            essence_list = await api.get_essence_msg_list(group_id=int(target_group))
            essences = essence_list if isinstance(essence_list, list) else []
            result["step3_get_list"] = {
                "count": len(essences),
                "sample": essences[:3] if essences else [],
            }
        except Exception as e:
            result["step3_get_list"] = {"error": str(e)}

        # 4. 取消精华消息
        if (
            result["step2_set_essence"]
            and result["step2_set_essence"].get("status") == "success"
        ):
            try:
                await api.delete_essence_msg(message_id=int(message_id))
                result["step4_delete_essence"] = {
                    "status": "success",
                    "message_id": message_id,
                }
            except Exception as e:
                result["step4_delete_essence"] = {"error": str(e)}
        else:
            result["step4_delete_essence"] = {
                "skipped": True,
                "reason": "设为精华失败，跳过取消",
            }

        return result


class GroupAdminActionTests(APITestSuite):
    """
    群管理操作测试（危险操作）

    这些操作需要管理员权限，并且部分操作有实际影响
    - 设置群名片（安全）
    - 禁言/解禁（可恢复）
    - 全员禁言（可恢复）
    """

    suite_name = "Group Admin Actions"
    suite_description = "群管理操作测试（危险操作，需要确认）"

    @staticmethod
    @test_case(
        name="[场景5.2] 设置群名片",
        description="设置目标用户的群名片",
        category="scenario",
        api_endpoint="/set_group_card",
        expected="群名片设置成功",
        tags=["scenario", "admin", "card"],
        show_result=True,
    )
    async def test_set_group_card_scenario(api, data):
        """设置群名片"""
        target_group = data.get("target_group")
        target_user = data.get("target_user")
        if not target_group or not target_user:
            raise ValueError("需要配置 target_group 和 target_user")

        groups_data = data.get("groups", {})
        card = groups_data.get("member_operations", {}).get("card", "E2E测试名片")

        await api.set_group_card(
            group_id=int(target_group),
            user_id=int(target_user),
            card=card,
        )

        return {
            "group_id": target_group,
            "user_id": target_user,
            "new_card": card,
            "status": "success",
        }

    @staticmethod
    @test_case(
        name="[场景5.3] 禁言流程: 禁言→解禁",
        description="禁言目标用户60秒，然后立即解除禁言",
        category="scenario",
        api_endpoint="/set_group_ban",
        expected="禁言和解禁都成功",
        tags=["scenario", "admin", "ban"],
        show_result=True,
    )
    async def test_ban_unban_scenario(api, data):
        """禁言流程：禁言 → 解禁"""
        target_group = data.get("target_group")
        target_user = data.get("target_user")
        if not target_group or not target_user:
            raise ValueError("需要配置 target_group 和 target_user")

        result = {"step1_ban": None, "step2_unban": None}

        # 1. 禁言60秒
        try:
            await api.set_group_ban(
                group_id=int(target_group),
                user_id=int(target_user),
                duration=60,
            )
            result["step1_ban"] = {"status": "success", "duration": 60}
        except Exception as e:
            result["step1_ban"] = {"error": str(e), "note": "可能需要管理员权限"}
            return result

        # 2. 立即解除禁言
        try:
            await api.set_group_ban(
                group_id=int(target_group),
                user_id=int(target_user),
                duration=0,
            )
            result["step2_unban"] = {"status": "success"}
        except Exception as e:
            result["step2_unban"] = {"error": str(e)}

        return result

    @staticmethod
    @test_case(
        name="[场景5.4] 设置群头衔",
        description="设置目标用户的群头衔",
        category="scenario",
        api_endpoint="/set_group_special_title",
        expected="头衔设置成功",
        tags=["scenario", "admin", "title"],
        show_result=True,
    )
    async def test_set_title_scenario(api, data):
        """设置群头衔"""
        target_group = data.get("target_group")
        target_user = data.get("target_user")
        if not target_group or not target_user:
            raise ValueError("需要配置 target_group 和 target_user")

        groups_data = data.get("groups", {})
        title = groups_data.get("member_operations", {}).get(
            "special_title", "E2E测试头衔"
        )

        await api.set_group_special_title(
            group_id=int(target_group),
            user_id=int(target_user),
            special_title=title,
        )

        return {
            "group_id": target_group,
            "user_id": target_user,
            "special_title": title,
            "status": "success",
        }


class DangerousAdminTests(APITestSuite):
    """
    危险操作测试（需要手动输入确认）

    这些操作具有较大影响，需要用户手动确认：
    - 全员禁言开关
    - 踢出成员
    - 设置管理员
    - 删除好友
    """

    suite_name = "Dangerous Admin Operations"
    suite_description = "危险操作测试（需要手动输入确认）"

    @staticmethod
    @test_case(
        name="[危险] 全员禁言开关",
        description="开启全员禁言，然后关闭",
        category="scenario",
        api_endpoint="/set_group_whole_ban",
        expected="全员禁言开关操作成功",
        tags=["scenario", "admin", "dangerous", "ban"],
        requires_input=True,
        show_result=True,
    )
    async def test_whole_ban_toggle(api, data):
        """全员禁言开关"""
        target_group = data.get("target_group")
        if not target_group:
            raise ValueError("需要配置 target_group")

        confirm = input(f"是否测试全员禁言开关（群 {target_group}）? (yes/no): ")
        if confirm.lower() != "yes":
            return {"status": "cancelled", "reason": "用户取消"}

        result = {"step1_enable": None, "step2_disable": None}

        # 1. 开启全员禁言
        try:
            await api.set_group_whole_ban(group_id=int(target_group), enable=True)
            result["step1_enable"] = {"status": "success", "whole_ban": True}
        except Exception as e:
            result["step1_enable"] = {"error": str(e)}
            return result

        # 2. 立即关闭全员禁言
        try:
            await api.set_group_whole_ban(group_id=int(target_group), enable=False)
            result["step2_disable"] = {"status": "success", "whole_ban": False}
        except Exception as e:
            result["step2_disable"] = {"error": str(e)}

        return result

    @staticmethod
    @test_case(
        name="[危险] 踢出群成员",
        description="将指定成员踢出群（谨慎使用）",
        category="scenario",
        api_endpoint="/set_group_kick",
        expected="成员被踢出群",
        tags=["scenario", "admin", "dangerous", "kick", "skip"],
        requires_input=True,
        show_result=True,
    )
    async def test_kick_member(api, data):
        """踢出群成员"""
        target_group = data.get("target_group")
        if not target_group:
            raise ValueError("需要配置 target_group")

        target_user = input("请输入要踢出的成员 QQ 号: ")
        confirm = input(f"确认踢出群 {target_group} 的成员 {target_user}? (yes/no): ")

        if confirm.lower() != "yes":
            return {"status": "cancelled", "reason": "用户取消"}

        reject_add = input("是否拒绝此人再次加群? (y/n): ").lower() == "y"

        await api.set_group_kick(
            group_id=int(target_group),
            user_id=int(target_user),
            reject_add_request=reject_add,
        )

        return {
            "group_id": target_group,
            "user_id": target_user,
            "reject_add": reject_add,
            "status": "kicked",
        }

    @staticmethod
    @test_case(
        name="[危险] 设置群管理员",
        description="设置或取消群管理员",
        category="scenario",
        api_endpoint="/set_group_admin",
        expected="管理员状态改变",
        tags=["scenario", "admin", "dangerous", "skip"],
        requires_input=True,
        show_result=True,
    )
    async def test_set_admin(api, data):
        """设置群管理员"""
        target_group = data.get("target_group")
        if not target_group:
            raise ValueError("需要配置 target_group")

        target_user = input("请输入目标成员 QQ 号: ")
        enable = input("设为管理员? (y/n): ").lower() == "y"
        confirm = input(
            f"确认{'设置' if enable else '取消'} 群 {target_group} 成员 {target_user} 的管理员? (yes/no): "
        )

        if confirm.lower() != "yes":
            return {"status": "cancelled", "reason": "用户取消"}

        await api.set_group_admin(
            group_id=int(target_group),
            user_id=int(target_user),
            enable=enable,
        )

        return {
            "group_id": target_group,
            "user_id": target_user,
            "admin": enable,
            "status": "success",
        }


# 导出测试类
ALL_TEST_SUITES = [
    GroupAdminScenarioTests,
    GroupAdminActionTests,
    DangerousAdminTests,
]
