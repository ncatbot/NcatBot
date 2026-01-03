"""
HTTP 客户端协议和实现

使用依赖注入模式，定义 API 客户端的抽象接口和具体实现。
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine, Dict, Optional, TypeVar
from dataclasses import dataclass, field

T = TypeVar("T")


@dataclass
class APIResponse:
    """API 响应的统一数据结构"""

    retcode: int
    message: str
    data: Any = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "APIResponse":
        return cls(
            retcode=data.get("retcode", -1),
            message=data.get("message", ""),
            data=data.get("data"),
            raw=data,
        )

    @property
    def is_success(self) -> bool:
        return self.retcode == 0

    def __bool__(self) -> bool:
        return self.is_success


class IAPIClient(ABC):
    """
    API 客户端接口协议

    定义所有 API 客户端必须实现的方法，支持依赖注入。
    """

    @abstractmethod
    async def request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> APIResponse:
        """
        发送 API 请求

        Args:
            endpoint: API 端点路径，如 "/get_login_info"
            params: 请求参数字典

        Returns:
            APIResponse: 统一的响应对象
        """
        ...


class CallbackAPIClient(IAPIClient):
    """
    基于回调函数的 API 客户端实现

    将现有的 async_callback 模式封装为 IAPIClient 接口
    """

    def __init__(
        self,
        callback: Callable[[str, Optional[Dict[str, Any]]], Coroutine[Any, Any, Dict]],
    ):
        """
        Args:
            callback: 异步回调函数，接受 (endpoint, params) 返回响应字典
        """
        self._callback = callback

    async def request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> APIResponse:
        result = await self._callback(endpoint, params or {})
        return APIResponse.from_dict(result)


class MockAPIClient(IAPIClient):
    """
    模拟 API 客户端，用于测试

    可以预设响应或自定义响应逻辑
    """

    def __init__(self):
        self._responses: Dict[str, APIResponse] = {}
        self._default_response = APIResponse(retcode=0, message="ok", data={})
        self._request_history: list = []

    def set_response(self, endpoint: str, response: APIResponse) -> None:
        """设置特定端点的模拟响应"""
        self._responses[endpoint] = response

    def set_default_response(self, response: APIResponse) -> None:
        """设置默认响应"""
        self._default_response = response

    def get_request_history(self) -> list:
        """获取请求历史"""
        return self._request_history.copy()

    def clear_history(self) -> None:
        """清除请求历史"""
        self._request_history.clear()

    async def request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> APIResponse:
        self._request_history.append({"endpoint": endpoint, "params": params})
        return self._responses.get(endpoint, self._default_response)
