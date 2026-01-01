"""
Mock 服务

提供用于测试的 Mock 服务实现，替代需要网络连接的真实服务。
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Union, Awaitable
from ncatbot.core.service import BaseService
from ncatbot.utils import get_log

LOG = get_log("MockServices")


class MockWebSocket:
    """Mock WebSocket 连接，用于测试"""
    
    def __init__(self):
        self.connected = False
    
    async def connect(self):
        """模拟连接"""
        self.connected = True
    
    async def disconnect(self):
        """模拟断开连接"""
        self.connected = False
    
    async def listen(self):
        """模拟监听（什么都不做）"""
        LOG.info("Mock WebSocket: listen() 被调用（Mock 模式下不执行实际监听）")
    
    async def send(self, data: dict):
        """模拟发送数据"""
        pass
    
    def start_listening(self):
        """启动监听（Mock 模式下不执行）"""
        pass


class MockMessageRouter(BaseService):
    """
    Mock 消息路由服务
    
    不建立真实的 WebSocket 连接，用于测试环境。
    
    功能：
    - 模拟 API 调用并记录调用历史
    - 支持注入事件数据
    - 支持预设 API 响应
    """
    
    name = "message_router"
    description = "Mock 消息路由服务（测试用）"
    
    def __init__(self, **config):
        super().__init__(**config)
        self._event_callback: Optional[Callable[[dict], Awaitable[None]]] = None
        self._api_responses: Dict[str, Union[dict, Callable]] = {}
        self._call_history: List[Tuple[str, Optional[dict]]] = []
        self._mock_websocket = MockWebSocket()  # Mock WebSocket 对象
        self._default_responses = {
            "send_group_msg": lambda action, params: {
                "retcode": 0,
                "data": {"message_id": self._generate_message_id()},
            },
            "send_private_msg": lambda action, params: {
                "retcode": 0,
                "data": {"message_id": self._generate_message_id()},
            },
            "delete_msg": {"retcode": 0, "data": {}},
            "get_login_info": {
                "retcode": 0,
                "data": {"user_id": "123456789", "nickname": "TestBot"},
            },
            "get_group_info": {
                "retcode": 0,
                "data": {
                    "group_id": "123456789",
                    "group_name": "测试群",
                    "member_count": 10,
                },
            },
            "get_group_member_info": {
                "retcode": 0,
                "data": {
                    "user_id": "987654321",
                    "nickname": "TestUser",
                    "role": "member",
                },
            },
        }
        self._message_id_counter = 1000000
    
    def _generate_message_id(self) -> str:
        """生成消息 ID"""
        self._message_id_counter += 1
        return str(self._message_id_counter)
    
    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------
    
    async def on_load(self) -> None:
        """加载服务 - Mock 模式下不建立连接"""
        LOG.info("Mock 消息路由服务已加载（无网络连接）")
    
    async def on_close(self) -> None:
        """关闭服务"""
        self._call_history.clear()
        self._api_responses.clear()
        LOG.info("Mock 消息路由服务已关闭")
    
    # ------------------------------------------------------------------
    # 公开接口（兼容真实 MessageRouter）
    # ------------------------------------------------------------------
    
    @property
    def connected(self) -> bool:
        """Mock 模式始终返回 True"""
        return True
    
    @property
    def websocket(self) -> MockWebSocket:
        """返回 Mock WebSocket 对象"""
        return self._mock_websocket
    
    def set_event_callback(self, callback: Callable[[dict], Awaitable[None]]) -> None:
        """设置事件回调"""
        self._event_callback = callback
    
    async def send(
        self,
        action: str,
        params: Optional[dict] = None,
        timeout: float = 300.0
    ) -> dict:
        """
        模拟 API 调用
        
        Args:
            action: API 动作名
            params: 请求参数
            timeout: 超时时间（忽略）
            
        Returns:
            预设响应或默认响应
        """
        # 规范化 action 名称（移除开头的 /）
        action = action.lstrip("/")
        
        # 记录调用历史
        self._call_history.append((action, params.copy() if params else None))
        LOG.debug(f"Mock API 调用: {action}, 参数: {params}")
        
        # 返回预设响应
        if action in self._api_responses:
            response = self._api_responses[action]
            if callable(response):
                return response(action, params)
            return response.copy() if isinstance(response, dict) else response
        
        # 返回默认响应
        default = self._default_responses.get(action, {"retcode": 0, "data": {}})
        if callable(default):
            return default(action, params)
        return default.copy() if isinstance(default, dict) else default
    
    def start_listening(self):
        """Mock 模式下不需要监听"""
        pass
    
    # ------------------------------------------------------------------
    # 测试专用接口
    # ------------------------------------------------------------------
    
    async def inject_event(self, data: dict) -> None:
        """
        注入事件数据
        
        将事件数据直接发送到事件回调，模拟从 WebSocket 收到事件。
        
        Args:
            data: 原始事件数据（OneBot 格式）
        """
        if self._event_callback:
            await self._event_callback(data)
        else:
            LOG.warning("事件回调未设置，无法注入事件")
    
    def set_api_response(
        self,
        action: str,
        response: Union[dict, Callable[[str, Optional[dict]], dict]]
    ) -> None:
        """
        设置特定 API 的响应
        
        Args:
            action: API 动作名
            response: 响应数据或生成响应的函数
        """
        action = action.lstrip("/")
        self._api_responses[action] = response
    
    def get_call_history(self) -> List[Tuple[str, Optional[dict]]]:
        """获取 API 调用历史"""
        return self._call_history.copy()
    
    def get_calls_for_action(self, action: str) -> List[Optional[dict]]:
        """获取特定 API 的调用记录"""
        action = action.lstrip("/")
        return [params for a, params in self._call_history if a == action]
    
    def clear_call_history(self) -> None:
        """清空调用历史"""
        self._call_history.clear()
    
    def get_call_count(self, action: str) -> int:
        """获取特定 API 的调用次数"""
        action = action.lstrip("/")
        return len(self.get_calls_for_action(action))
    
    def assert_called(self, action: str) -> None:
        """断言 API 被调用过"""
        action = action.lstrip("/")
        if not self.get_calls_for_action(action):
            raise AssertionError(f"API {action} 未被调用")
    
    def assert_not_called(self, action: str) -> None:
        """断言 API 未被调用"""
        action = action.lstrip("/")
        calls = self.get_calls_for_action(action)
        if calls:
            raise AssertionError(f"API {action} 被调用了 {len(calls)} 次")
    
    def assert_called_with(self, action: str, **expected_params) -> None:
        """断言 API 使用特定参数被调用"""
        action = action.lstrip("/")
        calls = self.get_calls_for_action(action)
        if not calls:
            raise AssertionError(f"API {action} 未被调用")
        
        for params in calls:
            if params and all(
                key in params and params[key] == value
                for key, value in expected_params.items()
            ):
                return
        
        raise AssertionError(
            f"API {action} 未使用预期参数调用。"
            f"预期: {expected_params}, 实际调用: {calls}"
        )


class MockPreUploadService(BaseService):
    """
    Mock 预上传服务
    
    测试环境下不执行真实的文件上传。
    """
    
    name = "preupload"
    description = "Mock 预上传服务（测试用）"
    
    def __init__(self, **config):
        super().__init__(**config)
        self._upload_history: List[dict] = []
    
    async def on_load(self) -> None:
        LOG.info("Mock 预上传服务已加载")
    
    async def on_close(self) -> None:
        self._upload_history.clear()
        LOG.info("Mock 预上传服务已关闭")
    
    async def preupload_group_image(
        self,
        group_id: str,
        image_path: str,
        **kwargs
    ) -> dict:
        """模拟群图片预上传"""
        result = {
            "md5": "mock_md5_" + str(len(self._upload_history)),
            "fileSize": 1024,
            "url": f"https://mock.url/image/{len(self._upload_history)}.jpg",
        }
        self._upload_history.append({
            "type": "group_image",
            "group_id": group_id,
            "path": image_path,
            "result": result,
        })
        return result
    
    async def preupload_private_image(
        self,
        user_id: str,
        image_path: str,
        **kwargs
    ) -> dict:
        """模拟私聊图片预上传"""
        result = {
            "md5": "mock_md5_" + str(len(self._upload_history)),
            "fileSize": 1024,
            "url": f"https://mock.url/image/{len(self._upload_history)}.jpg",
        }
        self._upload_history.append({
            "type": "private_image",
            "user_id": user_id,
            "path": image_path,
            "result": result,
        })
        return result
    
    def get_upload_history(self) -> List[dict]:
        """获取上传历史"""
        return self._upload_history.copy()
    
    def clear_upload_history(self) -> None:
        """清空上传历史"""
        self._upload_history.clear()
