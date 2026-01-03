"""
群消息操作场景测试

测试场景：群消息发送 → 消息操作 → 消息查询
将相关联的操作链接起来，减少用户输入

流程：
1. 发送文本消息 → 获取消息详情 → 撤回消息
2. 发送消息 → 设置表情回应 → 获取表情回应
3. 发送消息 → 转发消息
4. 获取群历史消息
5. 发送合并转发消息
"""

from .framework import test_case, APITestSuite
from .utils import model_to_dict, ensure_test_image


# ============================================================================
# 场景测试：群消息操作
# ============================================================================


class GroupMessageScenarioTests(APITestSuite):
    """
    群消息操作场景测试

    将消息发送、操作、查询串联起来测试，流程如下：
    1. 发送 → 查询详情 → 撤回
    2. 发送 → 表情回应 → 查询表情
    3. 发送 → 转发
    4. 历史消息查询
    5. 合并转发消息
    """

    suite_name = "Group Message Scenario"
    suite_description = "群消息操作场景测试（发送→操作→查询链）"

    @staticmethod
    @test_case(
        name="[场景2.1] 消息生命周期: 发送→查询→撤回",
        description="发送消息，获取消息详情，然后撤回消息",
        category="scenario",
        api_endpoint="/post_group_msg, /get_msg, /delete_msg",
        expected="消息发送、查询、撤回全流程成功",
        tags=["scenario", "message", "lifecycle"],
        show_result=True,
    )
    async def test_message_lifecycle_scenario(api, data):
        """消息生命周期测试：发送 → 查询 → 撤回"""
        target_group = data.get("target_group")
        if not target_group:
            raise ValueError("需要配置 target_group")

        # 1. 发送测试消息
        content = "[E2E 场景测试] 消息生命周期测试 - 即将撤回 🔄"
        # post_group_msg 返回 str 类型的 message_id
        image_file = ensure_test_image(data)
        message_id = await api.post_group_msg(
            group_id=int(target_group), text=content, image=image_file
        )
        assert message_id, "发送消息失败，未获取到 message_id"

        # 2. 查询消息详情
        msg_detail = await api.get_msg(message_id=int(message_id))
        assert msg_detail is not None, "获取消息详情失败"

        # 3. 撤回消息
        await api.delete_msg(message_id=int(message_id))

        return {
            "step1_send": {"message_id": message_id, "content": content},
            "step2_query": model_to_dict(msg_detail),
            "step3_delete": {"status": "success", "action": "撤回成功"},
        }

    @staticmethod
    @test_case(
        name="[场景2.2] 表情回应: 发送→设置表情→获取表情",
        description="发送消息，设置表情回应，然后获取表情回应列表",
        category="scenario",
        api_endpoint="/post_group_msg, /set_msg_emoji_like, /fetch_emoji_like",
        expected="表情回应设置和获取成功",
        tags=["scenario", "message", "emoji"],
        show_result=True,
    )
    async def test_emoji_reaction_scenario(api, data):
        """表情回应测试：发送 → 设置表情 → 获取表情"""
        target_group = data.get("target_group")
        if not target_group:
            raise ValueError("需要配置 target_group")

        # 1. 发送测试消息
        content = "[E2E 场景测试] 表情回应测试 😊"
        # post_group_msg 返回 str 类型的 message_id
        message_id = await api.post_group_msg(group_id=int(target_group), text=content)
        assert message_id, "发送消息失败，未获取到 message_id"

        # 2. 设置表情回应（使用笑脸 128516）
        emoji_id = 128516
        emoji_type = 1
        await api.set_msg_emoji_like(message_id=int(message_id), emoji_id=emoji_id)

        # 3. 获取表情回应
        emoji_result = await api.fetch_emoji_like(
            message_id=int(message_id),
            emoji_id=emoji_id,
            emoji_type=emoji_type,
        )

        return {
            "step1_send": {"message_id": message_id, "content": content},
            "step2_set_emoji": {"emoji_id": emoji_id, "status": "success"},
            "step3_fetch_emoji": model_to_dict(emoji_result),
        }

    @staticmethod
    @test_case(
        name="[场景2.3] 消息转发: 发送→单条转发",
        description="发送消息，然后转发该消息",
        category="scenario",
        api_endpoint="/post_group_msg, /forward_group_single_msg",
        expected="消息转发成功",
        tags=["scenario", "message", "forward"],
        show_result=True,
    )
    async def test_message_forward_scenario(api, data):
        """消息转发测试：发送 → 转发"""
        target_group = data.get("target_group")
        if not target_group:
            raise ValueError("需要配置 target_group")

        # 1. 发送测试消息
        content = "[E2E 场景测试] 待转发的消息 ↗️"
        # post_group_msg 返回 str 类型的 message_id
        message_id = await api.post_group_msg(group_id=int(target_group), text=content)
        assert message_id, "发送消息失败，未获取到 message_id"

        # 2. 转发该消息
        forward_result = await api.forward_group_single_msg(
            group_id=int(target_group),
            message_id=int(message_id),
        )

        return {
            "step1_send": {"message_id": message_id, "content": content},
            "step2_forward": {
                "status": "success",
                "result": model_to_dict(forward_result),
            },
        }

    @staticmethod
    @test_case(
        name="[场景2.4] 获取群历史消息",
        description="获取指定群的历史消息记录",
        category="scenario",
        api_endpoint="/get_group_msg_history",
        expected="返回消息历史列表",
        tags=["scenario", "message", "history"],
        show_result=True,
    )
    async def test_group_history_scenario(api, data):
        """获取群历史消息"""
        target_group = data.get("target_group")
        if not target_group:
            raise ValueError("需要配置 target_group")

        messages_data = data.get("messages", {})
        count = messages_data.get("history_query", {}).get("count", 10)

        # get_group_msg_history 返回 List[GroupMessageEvent]
        messages = await api.get_group_msg_history(
            group_id=int(target_group), count=count
        )

        return {
            "count": len(messages),
            "sample": [
                # GroupMessageEvent 对象有 message_id, sender, raw_message 属性
                {
                    "message_id": m.message_id,
                    "sender": m.sender.nickname if m.sender else None,
                    "content": str(m.raw_message)[:50],
                }
                for m in messages[:5]
            ],
        }

    @staticmethod
    @test_case(
        name="[场景2.5] 合并转发: 复杂场景测试",
        description="构建包含多人对话、嵌套转发、图片消息的综合合并转发",
        category="scenario",
        api_endpoint="/post_group_forward_msg",
        expected="复杂合并转发消息发送成功",
        tags=["scenario", "message", "forward", "nested", "image"],
        show_result=True,
    )
    async def test_forward_comprehensive_scenario(api, data):
        """合并转发综合测试：多人对话+嵌套转发+图片消息"""
        from ncatbot.core.helper import ForwardConstructor
        from ncatbot.core.event import MessageArray, Text, Image

        target_group = data.get("target_group")
        if not target_group:
            raise ValueError("需要配置 target_group")

        image_path = ensure_test_image(data)

        # ========== 构建内层转发消息（嵌套场景） ==========
        inner_fc = ForwardConstructor(user_id="10001", nickname="内层用户A")
        inner_fc.attach_text("[E2E 场景测试] 嵌套转发内层消息 1️⃣")
        inner_fc.attach_text("[E2E 场景测试] 嵌套转发内层消息 2️⃣")
        inner_fc.attach_image(
            "https://storage.moegirl.org.cn/moegirl/commons/3/30/%E6%B4%9B%E5%A4%A9%E4%BE%9DV4%E5%AE%98%E6%96%B9%E6%B8%B2%E6%9F%932.png"
        )
        inner_forward = inner_fc.to_forward()

        # ========== 构建外层转发消息（综合场景） ==========
        outer_fc = ForwardConstructor()

        # 1. 多人对话 - 用户A
        outer_fc.set_author(user_id="10001", nickname="测试用户A")
        outer_fc.attach_text("[E2E 场景测试] 大家好！这是合并转发综合测试 👋")

        # 2. 多人对话 - 用户B
        outer_fc.set_author(user_id="10002", nickname="测试用户B")
        outer_fc.attach_text("收到！我来展示图片消息 📸")

        # 3. 带图片消息 - 用户B
        msg_with_image = MessageArray()
        msg_with_image.add_text(Text("[E2E 场景测试] 这是我的图片: "))
        msg_with_image.add_image(Image(file=image_path))
        outer_fc.attach_message(msg_with_image)

        # 4. 多人对话 - 用户C
        outer_fc.set_author(user_id="10003", nickname="测试用户C")
        outer_fc.attach_text("我来展示嵌套转发功能 🔄")

        # 5. 嵌套转发 - 用户C
        outer_fc.attach_forward(inner_forward)

        # 6. 多人对话 - 用户C
        outer_fc.attach_text("嵌套转发展示完成！✅")

        # 7. 多人对话 - 用户A总结
        outer_fc.set_author(user_id="10001", nickname="测试用户A")
        outer_fc.attach_text("综合测试完成！🎉")

        forward = outer_fc.to_forward()
        # post_group_forward_msg 返回 str 类型的 message_id
        message_id = await api.post_group_forward_msg(
            group_id=int(target_group),
            forward=forward,
        )

        return {
            "scenario": "comprehensive",
            "outer_node_count": len(forward.content) if forward.content else 0,
            "inner_node_count": len(inner_forward.content)
            if inner_forward.content
            else 0,
            "is_multi_user": True,
            "is_nested": True,
            "has_image": True,
            "image_source": image_path,
            "message_id": message_id,
            "coverage": {
                "多人对话": "✓ 4 个不同用户的对话",
                "嵌套转发": "✓ 内层转发嵌入外层转发",
                "图片消息": "✓ MessageArray 中包含图片",
            },
        }

    @staticmethod
    @test_case(
        name="[场景2.8] 群音乐分享",
        description="发送自定义音乐分享到群聊",
        category="scenario",
        api_endpoint="/send_group_custom_music",
        expected="音乐分享发送成功",
        tags=["scenario", "message", "music"],
        show_result=True,
    )
    async def test_group_music_scenario(api, data):
        """群音乐分享"""
        target_group = data.get("target_group")
        if not target_group:
            raise ValueError("需要配置 target_group")

        messages_data = data.get("messages", {})
        music_info = messages_data.get("music_messages", {}).get("custom_music", {})

        # send_group_custom_music 返回 str 类型的 message_id
        message_id = await api.send_group_custom_music(
            group_id=int(target_group),
            url=music_info.get("url", "https://music.163.com"),
            audio=music_info.get(
                "audio", "https://music.163.com/song/media/outer/url?id=1.mp3"
            ),
            title=music_info.get("title", "E2E测试音乐"),
            content=music_info.get("content", "测试歌手"),
            image=music_info.get("image", "https://via.placeholder.com/300"),
        )

        return {
            "target_group": target_group,
            "music_title": music_info.get("title", "E2E测试音乐"),
            "message_id": message_id,
        }

    @staticmethod
    @test_case(
        name="[场景2.9] 群戳一戳",
        description="在群里戳一戳指定成员",
        category="scenario",
        api_endpoint="/group_poke",
        expected="戳一戳成功",
        tags=["scenario", "message", "poke"],
        show_result=True,
    )
    async def test_group_poke_scenario(api, data):
        """群戳一戳"""
        target_group = data.get("target_group")
        target_user = data.get("target_user")
        if not target_group or not target_user:
            raise ValueError("需要配置 target_group 和 target_user")

        await api.group_poke(group_id=int(target_group), user_id=int(target_user))

        return {
            "target_group": target_group,
            "target_user": target_user,
            "action": "group_poke",
            "status": "success",
        }


# 导出测试类
ALL_TEST_SUITES = [GroupMessageScenarioTests]
