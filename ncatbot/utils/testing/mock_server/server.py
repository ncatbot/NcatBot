"""
NapCat Mock 服务器

提供模拟 NapCat WebSocket 服务器的功能。
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable, Dict, List, Optional, Set, Union
from pathlib import Path

HAS_WEBSOCKETS = False
websockets = None  # type: ignore
try:
    import websockets as _websockets  # type: ignore
    import websockets.server  # type: ignore
    import websockets.exceptions  # type: ignore

    websockets = _websockets
    HAS_WEBSOCKETS = True
except ImportError:
    pass

from .database import MockDatabase  # noqa: E402
from .handlers import MockApiHandler  # noqa: E402


class NapCatMockServer:
    """
    NapCat Mock 服务器

    模拟 NapCat 的 WebSocket 服务端，响应 API 请求。
    支持状态保持和测试后重置。

    用法:
        ```python
        async with NapCatMockServer(port=6700) as server:
            # 服务器会在 ws://localhost:6700 监听
            pass

        # 手动管理
        server = NapCatMockServer(port=6700)
        await server.start()
        # ... 测试代码 ...
        await server.stop()
        server.reset()  # 重置到初始状态
        ```
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6700,
        token: Optional[str] = None,
        initial_data: Optional[dict] = None,
        data_file: Optional[Union[str, Path]] = None,
    ):
        """
        初始化 Mock 服务器

        Args:
            host: 监听主机
            port: 监听端口
            token: 访问令牌（可选）
            initial_data: 初始数据（可选）
            data_file: 数据文件路径（可选）
        """
        if not HAS_WEBSOCKETS:
            raise ImportError("需要安装 websockets 库: pip install websockets")

        self.host = host
        self.port = port
        self.token = token

        # 初始化数据库
        if data_file:
            self.database = MockDatabase()
            self.database.load_from_json(data_file)
        else:
            self.database = MockDatabase(initial_data)

        # 初始化 API 处理器
        self.api_handler = MockApiHandler(self.database)

        # 服务器状态
        self._server: Any = None
        self._clients: Set[Any] = set()
        self._running = False

        # 调用历史记录
        self._call_history: List[Dict[str, Any]] = []

        # 自定义响应
        self._custom_responses: Dict[str, Union[dict, Callable[..., dict]]] = {}

    @property
    def uri(self) -> str:
        """获取服务器 URI"""
        if self.token:
            return f"ws://{self.host}:{self.port}?access_token={self.token}"
        return f"ws://{self.host}:{self.port}"

    @property
    def is_running(self) -> bool:
        """服务器是否正在运行"""
        return self._running

    # =========================================================================
    # 服务器生命周期
    # =========================================================================

    async def start(self) -> None:
        """启动服务器"""
        if self._running:
            return

        if websockets is None:
            raise ImportError("需要安装 websockets 库: pip install websockets")

        self._server = await websockets.serve(
            self._handle_connection,
            self.host,
            self.port,
        )
        self._running = True

    async def stop(self) -> None:
        """停止服务器"""
        if not self._running:
            return

        self._running = False

        for client in list(self._clients):
            await client.close()
        self._clients.clear()

        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    def reset(self) -> None:
        """重置数据库和调用历史"""
        self.database.reset()
        self._call_history.clear()
        self._custom_responses.clear()

    async def __aenter__(self) -> "NapCatMockServer":
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.stop()
        self.reset()

    # =========================================================================
    # 连接处理
    # =========================================================================

    async def _handle_connection(self, websocket: Any, path: str = "") -> None:
        """处理 WebSocket 连接"""
        # 验证 token
        if self.token:
            import urllib.parse

            parsed = urllib.parse.urlparse(path)
            params = urllib.parse.parse_qs(parsed.query)
            client_token = params.get("access_token", [None])[0]

            if client_token != self.token:
                await websocket.send(
                    json.dumps(
                        {
                            "status": "failed",
                            "retcode": 1403,
                            "message": "Token 验证失败",
                        }
                    )
                )
                await websocket.close()
                return

        self._clients.add(websocket)

        # 发送连接成功的 lifecycle 事件
        await websocket.send(
            json.dumps(
                {
                    "post_type": "meta_event",
                    "meta_event_type": "lifecycle",
                    "sub_type": "connect",
                    "time": int(asyncio.get_event_loop().time()),
                    "self_id": int(self.database.get_login_info().get("user_id", 0)),
                }
            )
        )

        try:
            async for message in websocket:
                await self._handle_message(websocket, message)
        except Exception as e:
            if websockets and isinstance(e, websockets.exceptions.ConnectionClosed):
                pass
            else:
                raise
        finally:
            self._clients.discard(websocket)

    async def _handle_message(self, websocket: Any, message: str) -> None:
        """处理收到的消息"""
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            return

        action = data.get("action", "")
        params = data.get("params", {})
        echo = data.get("echo")

        self._call_history.append(
            {
                "action": action,
                "params": params,
                "echo": echo,
            }
        )

        response = self._get_response(action, params)

        if echo is not None:
            response["echo"] = echo

        await websocket.send(json.dumps(response))

    def _get_response(self, action: str, params: dict) -> dict:
        """获取 API 响应"""
        action = action.lstrip("/")

        if action in self._custom_responses:
            custom = self._custom_responses[action]
            if callable(custom):
                return custom(action, params)
            return custom.copy() if isinstance(custom, dict) else custom

        return self.api_handler.handle_request(action, params)

    # =========================================================================
    # 测试辅助方法
    # =========================================================================

    def set_response(
        self,
        action: str,
        response: Union[dict, Callable[[str, dict], dict]],
    ) -> None:
        """设置自定义响应"""
        self._custom_responses[action.lstrip("/")] = response

    def get_call_history(self) -> List[Dict[str, Any]]:
        """获取调用历史"""
        return self._call_history.copy()

    def get_calls_for_action(self, action: str) -> List[dict]:
        """获取特定 API 的调用记录"""
        action = action.lstrip("/")
        return [
            call["params"] for call in self._call_history if call["action"] == action
        ]

    def clear_call_history(self) -> None:
        """清空调用历史"""
        self._call_history.clear()

    def get_call_count(self, action: str) -> int:
        """获取特定 API 的调用次数"""
        return len(self.get_calls_for_action(action.lstrip("/")))

    def assert_called(self, action: str) -> None:
        """断言 API 被调用过"""
        if not self.get_calls_for_action(action):
            raise AssertionError(f"API {action} 未被调用")

    def assert_not_called(self, action: str) -> None:
        """断言 API 未被调用"""
        calls = self.get_calls_for_action(action)
        if calls:
            raise AssertionError(f"API {action} 被调用了 {len(calls)} 次")

    def assert_called_with(self, action: str, **expected_params: Any) -> None:
        """断言 API 使用特定参数被调用"""
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
            f"API {action} 未使用预期参数调用。预期: {expected_params}, 实际: {calls}"
        )

    # =========================================================================
    # 事件注入
    # =========================================================================

    async def inject_event(self, event_data: dict) -> None:
        """向所有连接的客户端注入事件"""
        if not self._clients:
            return

        message = json.dumps(event_data)
        await asyncio.gather(*[client.send(message) for client in self._clients])
        await asyncio.sleep(0.005)  # 等 5ms 让回调处理

    async def inject_group_message(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        message: Union[str, List[dict]],
        message_id: Optional[str] = None,
    ) -> None:
        """注入群消息事件"""
        import time

        if isinstance(message, str):
            message_array = [{"type": "text", "data": {"text": message}}]
            raw_message = message
        else:
            message_array = message
            raw_message = self.database._message_to_raw(message)

        sender_info = self.database.get_group_member_info(
            str(group_id), str(user_id)
        ) or {"user_id": str(user_id), "nickname": "Unknown"}

        event = {
            "post_type": "message",
            "message_type": "group",
            "sub_type": "normal",
            "message_id": message_id or str(int(time.time() * 1000)),
            "group_id": int(group_id),
            "user_id": int(user_id),
            "message": message_array,
            "raw_message": raw_message,
            "font": 0,
            "sender": sender_info,
            "time": int(time.time()),
            "self_id": int(self.database.get_login_info().get("user_id", 0)),
        }

        await self.inject_event(event)

    async def inject_private_message(
        self,
        user_id: Union[str, int],
        message: Union[str, List[dict]],
        message_id: Optional[str] = None,
    ) -> None:
        """注入私聊消息事件"""
        import time

        if isinstance(message, str):
            message_array = [{"type": "text", "data": {"text": message}}]
            raw_message = message
        else:
            message_array = message
            raw_message = self.database._message_to_raw(message)

        sender_info = self.database.get_stranger_info(str(user_id)) or {
            "user_id": str(user_id),
            "nickname": "Unknown",
        }

        event = {
            "post_type": "message",
            "message_type": "private",
            "sub_type": "friend",
            "message_id": message_id or str(int(time.time() * 1000)),
            "user_id": int(user_id),
            "message": message_array,
            "raw_message": raw_message,
            "font": 0,
            "sender": sender_info,
            "time": int(time.time()),
            "self_id": int(self.database.get_login_info().get("user_id", 0)),
        }

        await self.inject_event(event)
