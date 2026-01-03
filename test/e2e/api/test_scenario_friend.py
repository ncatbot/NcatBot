"""
好友互动场景测试

测试场景：好友消息 + 好友操作
将相关联的操作链接起来，减少用户输入

流程：
1. 发送私聊消息 → 获取消息历史
2. 好友赞 + 好友戳一戳
3. 上传私聊文件
"""

from .framework import test_case, APITestSuite
from .utils import model_to_dict, create_test_file


# ============================================================================
# 场景测试：好友互动
# ============================================================================


class FriendInteractionScenarioTests(APITestSuite):
    """
    好友互动场景测试

    测试流程：
    1. 发送私聊消息 → 获取消息历史
    2. 好友赞 + 戳一戳
    3. 上传私聊文件
    """

    suite_name = "Friend Interaction Scenario"
    suite_description = "好友互动场景测试（消息+操作链）"

    @staticmethod
    @test_case(
        name="[场景4.1] 私聊消息: 发送→查询历史",
        description="发送私聊消息，然后获取消息历史",
        category="scenario",
        api_endpoint="/post_private_msg, /get_friend_msg_history",
        expected="私聊消息发送成功并出现在历史中",
        tags=["scenario", "private", "message"],
        show_result=True,
    )
    async def test_private_message_scenario(api, data):
        """私聊消息：发送 → 查询历史"""
        target_user = data.get("target_user")
        if not target_user:
            raise ValueError("需要配置 target_user")

        # 1. 发送私聊消息
        content = "[E2E 场景测试] 私聊消息测试 📩"
        # post_private_msg 返回 str 类型的 message_id
        message_id = await api.post_private_msg(user_id=int(target_user), text=content)
        assert message_id, "发送消息失败，未获取到 message_id"

        # 2. 获取消息历史 - 返回 List[PrivateMessageEvent]
        messages = await api.get_friend_msg_history(
            user_id=int(target_user),
            message_seq=0,
            count=10,
        )

        return {
            "step1_send": {"message_id": message_id, "content": content},
            "step2_history": {
                "count": len(messages),
                "sample": [
                    # PrivateMessageEvent 对象有 message_id 和 raw_message 属性
                    {
                        "message_id": m.message_id,
                        "content": str(m.raw_message)[:50],
                    }
                    for m in messages[:3]
                ],
            },
        }

    @staticmethod
    @test_case(
        name="[场景4.2] 好友互动: 点赞+戳一戳",
        description="给好友点赞，然后戳一戳好友",
        category="scenario",
        api_endpoint="/send_like, /friend_poke",
        expected="点赞和戳一戳都成功",
        tags=["scenario", "friend", "interaction"],
        show_result=True,
    )
    async def test_friend_interaction_scenario(api, data):
        """好友互动：点赞 + 戳一戳"""
        target_user = data.get("target_user")
        if not target_user:
            raise ValueError("需要配置 target_user")

        friends_data = data.get("friends", {})
        like_count = friends_data.get("friend_operations", {}).get(
            "send_like_count", 10
        )

        # 1. 好友点赞
        await api.send_like(user_id=int(target_user), times=like_count)

        # 2. 好友戳一戳
        await api.friend_poke(user_id=int(target_user))

        return {
            "step1_like": {
                "user_id": target_user,
                "times": like_count,
                "status": "success",
            },
            "step2_poke": {"user_id": target_user, "status": "success"},
        }

    @staticmethod
    @test_case(
        name="[场景4.3] 私聊文件上传",
        description="上传文件到私聊",
        category="scenario",
        api_endpoint="/upload_private_file, /post_private_file",
        expected="文件上传成功",
        tags=["scenario", "private", "file"],
        show_result=True,
    )
    async def test_private_file_upload_scenario(api, data):
        """私聊文件上传"""
        target_user = data.get("target_user")
        if not target_user:
            raise ValueError("需要配置 target_user")

        result = {"upload_private_file": None, "post_private_file": None}

        # 1. 使用 upload_private_file 上传
        file_path1 = "/tmp/e2e_private_upload.txt"
        file_name1 = "e2e_private_test.txt"
        create_test_file(file_path1, "E2E 场景测试 - 私聊文件上传测试")

        try:
            await api.upload_private_file(
                user_id=int(target_user),
                file=file_path1,
                name=file_name1,
            )
            result["upload_private_file"] = {
                "status": "success",
                "file_path": file_path1,
                "file_name": file_name1,
            }
        except Exception as e:
            result["upload_private_file"] = {"error": str(e)}

        # 2. 使用 post_private_file 上传
        file_path2 = "/tmp/e2e_private_post.txt"
        create_test_file(file_path2, "E2E 场景测试 - POST方式私聊文件上传")

        try:
            post_result = await api.post_private_file(
                user_id=int(target_user),
                file=file_path2,
            )
            result["post_private_file"] = {
                "status": "success",
                "file_path": file_path2,
                "result": model_to_dict(post_result),
            }
        except Exception as e:
            result["post_private_file"] = {"error": str(e)}

        return result

    @staticmethod
    @test_case(
        name="[场景4.4] 戳一戳",
        description="发送戳一戳消息",
        category="scenario",
        api_endpoint="/send_poke",
        expected="戳一戳成功",
        tags=["scenario", "private", "poke"],
        show_result=True,
    )
    async def test_send_poke_scenario(api, data):
        """发送戳一戳"""
        target_user = data.get("target_user")
        if not target_user:
            raise ValueError("需要配置 target_user")

        await api.send_poke(user_id=int(target_user))

        return {
            "target_user": target_user,
            "action": "send_poke",
            "status": "success",
        }


# 导出测试类
ALL_TEST_SUITES = [FriendInteractionScenarioTests]
