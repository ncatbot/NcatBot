"""
测试助手类

提供便捷的测试工具方法，简化事件注入和断言操作。
"""

from typing import Literal, Optional, Dict, List, Union, TYPE_CHECKING
from .event_factory import EventFactory
from ncatbot.utils import get_log
from ncatbot.utils import run_coroutine

if TYPE_CHECKING:
    from ncatbot.core import BotClient, MessageArray
else:
    MessageArray = "MessageArray"

LOG = get_log("E2ETestHelper")


class E2ETestHelper:
    """
    测试助手类
    
    为 BotClient（Mock 模式）提供便捷的测试工具方法。
    
    使用示例：
    ```python
    client = BotClient()
    client.start(mock=True, bt_uin="123456")
    
    helper = E2ETestHelper(client)
    await helper.send_group_message("/hello")
    helper.assert_reply_sent("world")
    ```
    """

    def __init__(self, client: "BotClient"):
        """
        初始化测试助手
        
        Args:
            client: 已启动的 BotClient 实例（需要 Mock 模式）
        """
        self.client = client

    @property
    def mock_router(self):
        """获取 MockMessageRouter"""
        return self.client.services.message_router

    # ==================== 事件注入 ====================

    async def send_group_message(
        self,
        message: Union[str, "MessageArray"],
        group_id: str = "123456789",
        user_id: str = "987654321",
        nickname: str = "TestUser",
        **kwargs,
    ):
        """发送群聊消息事件"""
        event = EventFactory.create_group_message(
            message=message,
            group_id=group_id,
            user_id=user_id,
            nickname=nickname,
            **kwargs,
        )
        LOG.debug(f"注入群聊消息事件: {message[:50] if isinstance(message, str) else message}")
        await self.client.inject_event(event)

    async def send_private_message(
        self,
        message: Union[str, "MessageArray"],
        user_id: str = "987654321",
        nickname: str = "TestUser",
        **kwargs,
    ):
        """发送私聊消息事件"""
        event = EventFactory.create_private_message(
            message=message, user_id=user_id, nickname=nickname, **kwargs
        )
        LOG.debug(f"注入私聊消息事件: {message[:50] if isinstance(message, str) else message}")
        await self.client.inject_event(event)

    def send_group_message_sync(
        self,
        message: Union[str, "MessageArray"],
        group_id: str = "123456789",
        user_id: str = "987654321",
        nickname: str = "TestUser",
        **kwargs,
    ):
        """同步发送群聊消息事件"""
        run_coroutine(
            self.send_group_message, message, group_id, user_id, nickname, **kwargs
        )

    def send_private_message_sync(
        self,
        message: Union[str, "MessageArray"],
        user_id: str = "987654321",
        nickname: str = "TestUser",
        **kwargs,
    ):
        """同步发送私聊消息事件"""
        run_coroutine(self.send_private_message, message, user_id, nickname, **kwargs)

    async def on_friend_request(self, user_id: str = "987654321", comment: str = " "):
        """创建添加好友请求事件"""
        event = EventFactory.create_friend_request_event(
            user_id=user_id, comment=comment
        )
        LOG.debug(f"注入好友请求事件: user_id={user_id}")
        await self.client.inject_event(event)

    async def on_group_add_request(
        self,
        user_id: str = "987654321",
        group_id: str = "123456789",
        comment: str = " ",
    ):
        """创建加入群聊请求事件"""
        event = EventFactory.create_group_add_request_event(
            user_id=user_id, group_id=group_id, comment=comment
        )
        LOG.debug(f"注入加群请求事件: user_id={user_id}, group_id={group_id}")
        await self.client.inject_event(event)

    async def on_group_increase_notice(
        self,
        user_id: str = "987654321",
        group_id: str = "123456789",
        operator_id: str = "88888888",
        sub_type: Literal["approve", "invite"] = "approve",
    ):
        """创建群成员增加通知事件"""
        if sub_type not in ["approve", "invite"]:
            raise ValueError("sub_type must be 'approve' or 'invite'")
        event = EventFactory.create_group_increase_notice_event(
            user_id=user_id,
            group_id=group_id,
            operator_id=operator_id,
            subtype=sub_type,
        )
        LOG.debug(f"注入群成员增加事件: user_id={user_id}, sub_type={sub_type}")
        await self.client.inject_event(event)

    async def on_group_decrease_notice(
        self,
        user_id: str = "987654321",
        group_id: str = "123456789",
        operator_id: str = "88888888",
        sub_type: Literal["leave", "kick"] = "leave",
    ):
        """创建群成员减少通知事件"""
        if sub_type not in ["leave", "kick"]:
            raise ValueError("sub_type must be 'leave' or 'kick'")
        if sub_type == "leave":
            operator_id = "0"
        event = EventFactory.create_group_decrease_notice_event(
            user_id=user_id,
            group_id=group_id,
            operator_id=operator_id,
            subtype=sub_type,
        )
        LOG.debug(f"注入群成员减少事件: user_id={user_id}, sub_type={sub_type}")
        await self.client.inject_event(event)

    async def on_group_poke_notice(
        self,
        user_id: str = "987654321",
        group_id: str = "123456789",
        target_id: str = "77777777",
        raw_info: Optional[list] = None,
    ):
        """创建群戳一戳通知事件"""
        event = EventFactory.create_group_poke_notice_event(
            user_id=user_id, group_id=group_id, target_id=target_id, raw_info=raw_info
        )
        LOG.debug(f"注入戳一戳事件: user_id={user_id} -> target_id={target_id}")
        await self.client.inject_event(event)

    # ==================== 断言方法 ====================

    def assert_reply_sent(self, expected_text: Optional[str] = None):
        """
        断言发送了回复
        
        Args:
            expected_text: 回复中应包含的文本（可选）
        """
        group_calls = self.mock_router.get_calls_for_action("send_group_msg")
        private_calls = self.mock_router.get_calls_for_action("send_private_msg")
        all_calls = group_calls + private_calls

        assert all_calls, "没有发送任何回复"

        if expected_text:
            for params in all_calls:
                if params and "message" in params:
                    message = params["message"]
                    # 检查消息段中是否包含预期文本
                    if isinstance(message, list):
                        for segment in message:
                            if isinstance(segment, dict) and segment.get("type") == "text":
                                if expected_text in segment.get("data", {}).get("text", ""):
                                    return
                    # 也检查消息的字符串表示
                    if expected_text in str(message):
                        return
            raise AssertionError(f"回复中未包含预期文本: {expected_text}")

    def assert_no_reply(self):
        """断言没有发送回复"""
        group_calls = self.mock_router.get_calls_for_action("send_group_msg")
        private_calls = self.mock_router.get_calls_for_action("send_private_msg")
        all_calls = group_calls + private_calls

        assert not all_calls, f"意外发送了 {len(all_calls)} 条回复"

    def assert_api_called(self, action: str):
        """断言 API 被调用过"""
        self.mock_router.assert_called(action)

    def assert_api_not_called(self, action: str):
        """断言 API 未被调用"""
        self.mock_router.assert_not_called(action)

    def assert_api_called_with(self, action: str, **expected_params):
        """断言 API 使用特定参数被调用"""
        self.mock_router.assert_called_with(action, **expected_params)

    # ==================== 工具方法 ====================

    def get_api_calls(self, action: Optional[str] = None) -> List:
        """
        获取 API 调用记录
        
        Args:
            action: 指定 API，为 None 则返回所有调用
        """
        if action:
            return self.mock_router.get_calls_for_action(action)
        return self.mock_router.get_call_history()

    def get_latest_reply(self, index: int = -1) -> Optional[Dict]:
        """获取最新的回复"""
        group_calls = self.mock_router.get_calls_for_action("send_group_msg")
        private_calls = self.mock_router.get_calls_for_action("send_private_msg")
        all_calls = group_calls + private_calls
        return all_calls[index] if all_calls else None

    def clear_history(self):
        """清空所有历史记录"""
        self.mock_router.clear_call_history()

    def set_api_response(self, action: str, response: Dict):
        """设置 API 响应"""
        self.mock_router.set_api_response(action, response)
