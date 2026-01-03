"""
测试套件 Mixins

提供可复用的测试功能：断言、事件注入、插件管理。
仅提供异步方法，同步包装器由 E2ETestSuite 提供。
"""
# pyright: reportAttributeAccessIssue=false
# pyright: reportArgumentType=false

from typing import Literal, Optional, List, Union, Dict, TYPE_CHECKING

from ncatbot.utils import get_log

if TYPE_CHECKING:
    from ncatbot.plugin_system import BasePlugin
    from .mock_server import NapCatMockServer

LOG = get_log("TestMixins")


class PluginMixin:
    """插件管理 Mixin"""

    def index_plugin(self, plugin_dir: str) -> str:
        """
        索引一个外部插件文件夹

        Args:
            plugin_dir: 插件文件夹的路径

        Returns:
            插件名称
        """
        plugin_name = self.client.plugin_loader.index_external_plugin(plugin_dir)
        if plugin_name:
            LOG.info(f"已索引测试插件: {plugin_name} (路径: {plugin_dir})")
        return plugin_name or ""

    async def register_plugin(self, plugin_name: str) -> Optional["BasePlugin"]:
        """注册插件（异步）"""
        plugin = await self.client.plugin_loader.load_plugin(plugin_name)
        if plugin:
            self._registered_plugins.append(plugin_name)
            LOG.info(f"已注册测试插件: {plugin_name}")
        return plugin

    async def unregister_plugin(self, plugin_name: str) -> None:
        """卸载插件（异步）"""
        await self.client.plugin_loader.unload_plugin(plugin_name)
        if plugin_name in self._registered_plugins:
            self._registered_plugins.remove(plugin_name)
        LOG.info(f"已卸载测试插件: {plugin_name}")


class InjectorMixin:
    """事件注入 Mixin, 注入后会自动等待处理"""

    async def inject_event(self, event_data: dict) -> None:
        """
        注入原始事件数据（异步）

        通过 MockServer 向所有连接的客户端发送事件。
        """
        if not self._mock_server:
            raise RuntimeError("MockServer 未设置，无法注入事件")
        await self._mock_server.inject_event(event_data)

    async def inject_group_message(
        self,
        message: Union[str, List[dict]],
        group_id: Union[str, int] = "123456789",
        user_id: Union[str, int] = "987654321",
        **kwargs,
    ) -> None:
        """注入群消息事件（异步）"""
        if not self._mock_server:
            raise RuntimeError("MockServer 未设置，无法注入事件")
        await self._mock_server.inject_group_message(
            group_id=group_id, user_id=user_id, message=message, **kwargs
        )

    async def inject_private_message(
        self,
        message: Union[str, List[dict]],
        user_id: Union[str, int] = "987654321",
        **kwargs,
    ) -> None:
        """注入私聊消息事件（异步）"""
        if not self._mock_server:
            raise RuntimeError("MockServer 未设置，无法注入事件")
        await self._mock_server.inject_private_message(
            user_id=user_id, message=message, **kwargs
        )

    # ==================== 更多事件类型 ====================

    async def inject_friend_request(
        self, user_id: str = "987654321", comment: str = " "
    ) -> None:
        """注入好友请求事件"""
        from .event_factory import EventFactory

        event = EventFactory.create_friend_request_event(
            user_id=user_id, comment=comment
        )
        await self.inject_event(event)

    async def inject_group_add_request(
        self,
        user_id: str = "987654321",
        group_id: str = "123456789",
        comment: str = " ",
    ) -> None:
        """注入加群请求事件"""
        from .event_factory import EventFactory

        event = EventFactory.create_group_add_request_event(
            user_id=user_id, group_id=group_id, comment=comment
        )
        await self.inject_event(event)

    async def inject_group_increase_notice(
        self,
        user_id: str = "987654321",
        group_id: str = "123456789",
        operator_id: str = "88888888",
        sub_type: Literal["approve", "invite"] = "approve",
    ) -> None:
        """注入群成员增加事件"""
        from .event_factory import EventFactory

        event = EventFactory.create_group_increase_notice_event(
            user_id=user_id,
            group_id=group_id,
            operator_id=operator_id,
            subtype=sub_type,
        )
        await self.inject_event(event)

    async def inject_group_decrease_notice(
        self,
        user_id: str = "987654321",
        group_id: str = "123456789",
        operator_id: str = "88888888",
        sub_type: Literal["leave", "kick"] = "leave",
    ) -> None:
        """注入群成员减少事件"""
        from .event_factory import EventFactory

        if sub_type == "leave":
            operator_id = "0"
        event = EventFactory.create_group_decrease_notice_event(
            user_id=user_id,
            group_id=group_id,
            operator_id=operator_id,
            subtype=sub_type,
        )
        await self.inject_event(event)

    async def inject_group_poke_notice(
        self,
        user_id: str = "987654321",
        group_id: str = "123456789",
        target_id: str = "77777777",
        raw_info: Optional[list] = None,
    ) -> None:
        """注入群戳一戳事件"""
        from .event_factory import EventFactory

        event = EventFactory.create_group_poke_notice_event(
            user_id=user_id, group_id=group_id, target_id=target_id, raw_info=raw_info
        )
        await self.inject_event(event)


class AssertionMixin:
    """断言和工具方法 Mixin"""

    def _get_mock_server(self) -> "NapCatMockServer":
        """获取 MockServer 实例"""
        if self._mock_server:
            return self._mock_server
        raise RuntimeError("MockServer 未初始化")

    def assert_api_called(self, action: str) -> None:
        """断言 API 被调用过"""
        self._get_mock_server().assert_called(action)

    def assert_api_not_called(self, action: str) -> None:
        """断言 API 未被调用"""
        self._get_mock_server().assert_not_called(action)

    def assert_api_called_with(self, action: str, **expected_params) -> None:
        """断言 API 使用特定参数被调用"""
        self._get_mock_server().assert_called_with(action, **expected_params)

    def assert_reply_sent(self, contains: Optional[str] = None) -> None:
        """
        断言发送了回复消息

        Args:
            contains: 回复中应包含的文本（可选）
        """
        server = self._get_mock_server()
        group_calls = server.get_calls_for_action("send_group_msg")
        private_calls = server.get_calls_for_action("send_private_msg")
        all_calls = group_calls + private_calls

        assert all_calls, "没有发送任何回复消息"

        if contains:
            for params in all_calls:
                if params and "message" in params:
                    message = params["message"]
                    # 检查消息段
                    if isinstance(message, list):
                        for segment in message:
                            if (
                                isinstance(segment, dict)
                                and segment.get("type") == "text"
                            ):
                                if contains in segment.get("data", {}).get("text", ""):
                                    return
                    # 检查字符串表示
                    if contains in str(message):
                        return
            raise AssertionError(f"回复中未包含预期文本: {contains}")

    def assert_no_reply(self) -> None:
        """断言没有发送回复"""
        server = self._get_mock_server()
        group_calls = server.get_calls_for_action("send_group_msg")
        private_calls = server.get_calls_for_action("send_private_msg")
        all_calls = group_calls + private_calls

        assert not all_calls, f"意外发送了 {len(all_calls)} 条回复"

    def get_api_calls(self, action: Optional[str] = None) -> list:
        """获取 API 调用记录"""
        server = self._get_mock_server()
        if action:
            return server.get_calls_for_action(action)
        return server.get_call_history()

    def get_latest_reply(self, index: int = -1) -> Optional[Dict]:
        """获取最新的回复"""
        server = self._get_mock_server()
        group_calls = server.get_calls_for_action("send_group_msg")
        private_calls = server.get_calls_for_action("send_private_msg")
        all_calls = group_calls + private_calls
        return all_calls[index] if all_calls else None

    def clear_call_history(self) -> None:
        """清空 API 调用历史"""
        self._get_mock_server().clear_call_history()
