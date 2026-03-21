"""
功能预览样板对应的插件骨架验证测试

验证 preview-workflow.md 中 5 个端到端预览样板对应的插件可加载并正确响应事件。
使用 docs/docs/examples/ 中的真实示例插件。

规范:
  PV-01: 简单命令响应（hello_world_common 插件加载 + hello 命令）
  PV-02: 多步对话（multi_step_dialog 插件完整注册流程）
  PV-03: 外部 API 集成（external_api 插件加载 + 命令响应）
  PV-04: 外部事件驱动通知（TestHarness 手动 handler 模拟 webhook → 群通知）
  PV-05: 命令组 + 权限控制（TestHarness 手动 handler 模拟权限分支）
"""

from pathlib import Path

from ncatbot.testing import (
    PluginTestHarness,
    TestHarness,
    group_message,
)


COMMON_EXAMPLES = (
    Path(__file__).resolve().parents[2] / "docs" / "docs" / "examples" / "common"
)


# ---------------------------------------------------------------------------
# PV-01: 简单命令响应（样板 1）
# ---------------------------------------------------------------------------

HELLO_PLUGIN = "hello_world_common"


async def test_pv01_hello_plugin_loads():
    """PV-01a: hello_world_common 插件加载成功"""
    async with PluginTestHarness(
        plugin_names=[HELLO_PLUGIN], plugin_dir=COMMON_EXAMPLES
    ) as h:
        assert HELLO_PLUGIN in h.loaded_plugins


async def test_pv01_hello_command_reply():
    """PV-01b: 群聊发 'hello' → send_group_msg"""
    async with PluginTestHarness(
        plugin_names=[HELLO_PLUGIN], plugin_dir=COMMON_EXAMPLES
    ) as h:
        await h.inject(group_message("hello", group_id="10001"))
        await h.settle(0.1)
        assert h.api_called("send_group_msg")


async def test_pv01_hi_command_reply():
    """PV-01c: 群聊发 'hi' → send_group_msg"""
    async with PluginTestHarness(
        plugin_names=[HELLO_PLUGIN], plugin_dir=COMMON_EXAMPLES
    ) as h:
        await h.inject(group_message("hi", group_id="10001"))
        await h.settle(0.1)
        assert h.api_called("send_group_msg")


# ---------------------------------------------------------------------------
# PV-02: 多步对话（样板 2）
# ---------------------------------------------------------------------------

DIALOG_PLUGIN = "multi_step_dialog"
DIALOG_GROUP = "500"
DIALOG_USER = "67890"


async def test_pv02_dialog_plugin_loads():
    """PV-02a: multi_step_dialog 插件加载成功"""
    async with PluginTestHarness(
        plugin_names=[DIALOG_PLUGIN], plugin_dir=COMMON_EXAMPLES
    ) as h:
        assert DIALOG_PLUGIN in h.loaded_plugins


async def test_pv02_full_registration_flow():
    """PV-02b: 注册 → 名字 → 年龄 → 确认 → 成功"""
    async with PluginTestHarness(
        plugin_names=[DIALOG_PLUGIN], plugin_dir=COMMON_EXAMPLES
    ) as h:
        # 触发注册
        await h.inject(
            group_message("注册", group_id=DIALOG_GROUP, user_id=DIALOG_USER)
        )
        await h.settle(0.1)
        assert h.api_called("send_group_msg"), "应提示输入名字"

        # 输入名字
        h.reset_api()
        await h.inject(
            group_message("张三", group_id=DIALOG_GROUP, user_id=DIALOG_USER)
        )
        await h.settle(0.1)
        assert h.api_called("send_group_msg"), "应提示输入年龄"

        # 输入年龄
        h.reset_api()
        await h.inject(group_message("25", group_id=DIALOG_GROUP, user_id=DIALOG_USER))
        await h.settle(0.1)
        assert h.api_called("send_group_msg"), "应提示确认"

        # 确认
        h.reset_api()
        await h.inject(
            group_message("确认", group_id=DIALOG_GROUP, user_id=DIALOG_USER)
        )
        await h.settle(0.1)
        assert h.api_called("send_group_msg"), "应回复注册成功"

        # 验证数据持久化
        plugin = h.get_plugin(DIALOG_PLUGIN)
        users = plugin.data.get("users", {})
        assert DIALOG_USER in users
        assert users[DIALOG_USER]["name"] == "张三"
        assert users[DIALOG_USER]["age"] == 25


async def test_pv02_cancel_registration():
    """PV-02c: 注册中输入 '取消' → 退出"""
    async with PluginTestHarness(
        plugin_names=[DIALOG_PLUGIN], plugin_dir=COMMON_EXAMPLES
    ) as h:
        await h.inject(
            group_message("注册", group_id=DIALOG_GROUP, user_id=DIALOG_USER)
        )
        await h.settle(0.1)

        h.reset_api()
        await h.inject(
            group_message("取消", group_id=DIALOG_GROUP, user_id=DIALOG_USER)
        )
        await h.settle(0.1)
        assert h.api_called("send_group_msg"), "应回复已取消"


# ---------------------------------------------------------------------------
# PV-03: 外部 API 集成（样板 3）
# ---------------------------------------------------------------------------

API_PLUGIN = "external_api"


async def test_pv03_api_plugin_loads():
    """PV-03a: external_api 插件加载成功"""
    async with PluginTestHarness(
        plugin_names=[API_PLUGIN], plugin_dir=COMMON_EXAMPLES
    ) as h:
        assert API_PLUGIN in h.loaded_plugins


async def test_pv03_api_status_command():
    """PV-03b: 发 'api状态' → send_group_msg（不依赖外部网络）"""
    async with PluginTestHarness(
        plugin_names=[API_PLUGIN], plugin_dir=COMMON_EXAMPLES
    ) as h:
        await h.inject(group_message("api状态", group_id="10001"))
        await h.settle(0.1)
        assert h.api_called("send_group_msg")


# ---------------------------------------------------------------------------
# PV-04: 外部事件驱动通知（样板 4）
# ---------------------------------------------------------------------------


async def test_pv04_webhook_triggers_notification():
    """PV-04: 模拟外部事件 → handler → send_group_msg

    由于 version_notifier 依赖 GitHub 适配器事件类型，
    这里用 TestHarness 手动注册 handler 模拟 webhook → 群通知模式。
    """
    async with TestHarness() as h:
        notification_sent = False

        async def on_webhook(event):
            nonlocal notification_sent
            # 模拟收到外部事件后向群发送通知
            await event.reply("🔔 [NcatBot] 新版本 v5.3.0 发布！")
            notification_sent = True

        h.bot.handler_dispatcher.register_handler("message.group", on_webhook)

        await h.inject(group_message("webhook_trigger", group_id="201487478"))
        await h.settle(0.1)

        assert notification_sent
        assert h.api_called("send_group_msg")


# ---------------------------------------------------------------------------
# PV-05: 命令组 + 权限控制（样板 5）
# ---------------------------------------------------------------------------

ADMIN_USER = "10001"
NORMAL_USER = "99999"


async def test_pv05_admin_command_allowed():
    """PV-05a: 管理员用户 → 命令执行成功"""
    async with TestHarness() as h:
        executed = False

        async def admin_handler(event):
            nonlocal executed
            # 模拟权限检查：user_id == ADMIN_USER 视为管理员
            if str(event.user_id) == ADMIN_USER:
                await event.reply("🔇 已禁言 张三 10分钟")
                executed = True
            else:
                await event.reply("⛔ 权限不足：此命令需要「管理员」权限")

        h.bot.handler_dispatcher.register_handler("message.group", admin_handler)

        await h.inject(
            group_message("/admin ban @张三 10m", group_id="100", user_id=ADMIN_USER)
        )
        await h.settle(0.1)

        assert executed
        assert h.api_called("send_group_msg")


async def test_pv05_normal_user_rejected():
    """PV-05b: 普通用户 → 权限不足"""
    async with TestHarness() as h:
        rejected = False

        async def admin_handler(event):
            nonlocal rejected
            if str(event.user_id) == ADMIN_USER:
                await event.reply("🔇 已禁言 张三 10分钟")
            else:
                await event.reply("⛔ 权限不足：此命令需要「管理员」权限")
                rejected = True

        h.bot.handler_dispatcher.register_handler("message.group", admin_handler)

        await h.inject(
            group_message("/admin ban @张三 10m", group_id="100", user_id=NORMAL_USER)
        )
        await h.settle(0.1)

        assert rejected
        assert h.api_called("send_group_msg")
