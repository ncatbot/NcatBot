"""
API 工具类和基础组件

提供 API 调用的核心工具、错误处理、状态管理和依赖注入支持。
"""

from __future__ import annotations

import functools
import sys
import traceback
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    TYPE_CHECKING,
    TypeVar,
)

from ncatbot.utils import get_log, ncatbot_config, NcatBotError

if TYPE_CHECKING:
    from .client import IAPIClient, APIResponse
    from ncatbot.core.service import ServiceManager

LOG = get_log("API")
T = TypeVar("T")
R = TypeVar("R")
_C = TypeVar("_C")


# =============================================================================
# 错误类型定义
# =============================================================================


class NapCatAPIError(Exception):
    """NapCat API 调用错误"""

    def __init__(self, info: str, retcode: Optional[int] = None):
        LOG.error(f"NapCatAPIError: {info}")
        if ncatbot_config.debug:
            # 检查是否有活动的异常上下文
            if sys.exc_info()[0] is not None:
                LOG.info(f"stacktrace:\n{traceback.format_exc()}")
            else:
                # 没有活动异常时，输出当前调用栈
                LOG.info(f"stacktrace:\n{''.join(traceback.format_stack()[:-1])}")
        self.info = info
        self.retcode = retcode
        super().__init__(info)


class APIValidationError(NcatBotError):
    """API 参数验证错误"""

    logger = LOG

    def __init__(self, message: str):
        super().__init__(f"参数验证失败: {message}")


# =============================================================================
# 参数验证工具
# =============================================================================


def require_at_least_one(*args: Any, names: List[str]) -> None:
    """
    要求至少提供一个参数

    Args:
        *args: 参数值列表
        names: 对应的参数名称列表

    Raises:
        APIValidationError: 如果所有参数都为 None
    """
    if all(arg is None for arg in args):
        raise APIValidationError(f"至少需要提供以下参数之一: {', '.join(names)}")


def require_exactly_one(*args: Any, names: List[str]) -> None:
    """
    要求恰好提供一个参数

    Args:
        *args: 参数值列表
        names: 对应的参数名称列表

    Raises:
        APIValidationError: 如果提供的参数数量不是 1
    """
    count = sum(1 for arg in args if arg is not None)
    if count != 1:
        raise APIValidationError(f"必须且只能提供以下参数之一: {', '.join(names)}")


def check_exclusive_argument(*args: Any, names: List[str], error: bool = False) -> bool:
    """
    检查互斥参数，确保只提供一个

    Args:
        *args: 参数值列表
        names: 对应的参数名称列表
        error: 如果为 True，在检查失败时抛出异常

    Returns:
        bool: 如果恰好提供一个参数返回 True，否则返回 False

    Raises:
        APIValidationError: 如果 error=True 且提供的参数数量不是 1
    """
    count = sum(1 for arg in args if arg is not None)
    if count != 1:
        if error:
            raise APIValidationError(f"必须且只能提供以下参数之一: {', '.join(names)}")
        return False
    return True


# =============================================================================
# API 响应状态处理
# =============================================================================


class APIReturnStatus:
    """API 返回状态封装"""

    retcode: int
    message: str
    data: Any
    _raw: Dict[str, Any]

    def __init__(self, data: Dict[str, Any]):
        """
        从响应字典构造状态对象

        Args:
            data: API 响应字典

        Raises:
            NapCatAPIError: 如果响应表示失败
        """
        self.raise_if_failed(data)
        self.retcode = data.get("retcode", -1)
        self.message = data.get("message", "")
        self.data = data.get("data")
        self._raw = data

    @classmethod
    def raise_if_failed(cls, data: Dict[str, Any]) -> None:
        """
        检查响应是否成功，失败则抛出异常

        Args:
            data: API 响应字典

        Raises:
            NapCatAPIError: 如果 retcode != 0
        """
        if data.get("retcode") != 0:
            raise NapCatAPIError(
                data.get("message", "Unknown error"),
                retcode=data.get("retcode"),
            )

    @property
    def is_success(self) -> bool:
        return self.retcode == 0

    def __bool__(self) -> bool:
        return self.is_success

    def __str__(self) -> str:
        return f"APIReturnStatus(retcode={self.retcode}, message={self.message})"


class MessageAPIReturnStatus(APIReturnStatus):
    """消息 API 返回状态，包含 message_id"""

    @property
    def message_id(self) -> str:
        """获取消息 ID"""
        if self.data and "message_id" in self.data:
            return str(self.data["message_id"])
        return ""


# =============================================================================
# 依赖注入基础设施
# =============================================================================


class APIComponent:
    """
    API 组件基类（使用依赖注入）

    所有 API 模块应继承此类，通过构造函数注入 IAPIClient 依赖。
    """

    def __init__(
        self, client: "IAPIClient", service_manager: Optional["ServiceManager"] = None
    ):
        """
        Args:
            client: API 客户端实例，实现 IAPIClient 接口
            service_manager: 服务管理器实例（可选）
        """
        self._client = client
        self._service_manager = service_manager

    @property
    def services(self) -> Optional["ServiceManager"]:
        """获取服务管理器实例"""
        return self._service_manager

    @property
    def _preupload_available(self) -> bool:
        """预上传服务是否可用"""
        if not self._service_manager:
            return False
        preupload = self._service_manager.preupload
        return preupload is not None and preupload.available

    async def _preupload_message(
        self, message: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        预上传消息中的文件资源

        Args:
            message: 消息段列表

        Returns:
            处理后的消息段列表
        """
        if not self._preupload_available:
            return message

        preupload = self._service_manager.preupload
        result = await preupload.process_message_array(message)

        if result.success and result.data:
            return result.data.get("message", message)

        LOG.warning(f"消息预上传处理失败: {result.errors}")
        return message

    async def _preupload_file(
        self, file_value: str, file_type: str = "file", require_preupload: bool = False
    ) -> str:
        """
        预上传单个文件

        Args:
            file_value: 文件路径/URL/Base64
            file_type: 文件类型
            require_preupload: 是否必须使用预上传服务（为 True 时，服务不可用将报错）

        Returns:
            处理后的文件路径

        Raises:
            NapCatAPIError: 如果 require_preupload=True 且预上传服务不可用
        """
        import os

        if not self._preupload_available:
            if require_preupload:
                raise NapCatAPIError(
                    "预上传服务不可用。请确保：\n"
                    "1. PreUploadService 已注册\n"
                    "2. ServiceManager 已传入 BotAPI\n"
                    "3. 预上传服务已正确启动"
                )
            # 预上传服务不可用时，将本地路径转换为 file:// URL
            # NapCat 需要 file:// 协议的 URL 格式
            if file_value and not file_value.startswith(
                ("http://", "https://", "base64://", "file://")
            ):
                # 可能是本地路径
                if os.path.isabs(file_value) or os.path.exists(file_value):
                    abs_path = os.path.abspath(file_value)
                    return f"file://{abs_path}"
            return file_value

        try:
            preupload = self._service_manager.preupload
            return await preupload.preupload_file_if_needed(file_value, file_type)
        except Exception as e:
            if require_preupload:
                raise NapCatAPIError(f"文件预上传失败: {e}") from e
            LOG.warning(f"文件预上传失败: {e}，使用原始路径")
            # 失败时也尝试转换为 file:// URL
            if file_value and not file_value.startswith(
                ("http://", "https://", "base64://", "file://")
            ):
                if os.path.isabs(file_value) or os.path.exists(file_value):
                    abs_path = os.path.abspath(file_value)
                    return f"file://{abs_path}"
            return file_value

    async def _request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> "APIResponse":
        """
        发送 API 请求

        Args:
            endpoint: API 端点
            params: 请求参数

        Returns:
            APIResponse 对象
        """
        return await self._client.request(endpoint, params)

    async def _request_raw(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        发送 API 请求并返回原始字典

        为了兼容现有代码，返回原始响应字典。

        Args:
            endpoint: API 端点
            params: 请求参数

        Returns:
            原始响应字典
        """
        response = await self._client.request(endpoint, params)
        return response.raw


# =============================================================================
# 同步方法生成器
# =============================================================================


def sync_wrapper(async_method: Callable[..., T]) -> Callable[..., T]:
    """
    将异步方法包装为同步方法的装饰器

    ⚠️ 警告：此方法会阻塞线程，仅用于向后兼容。
    新代码应直接使用异步方法。

    Args:
        async_method: 异步方法

    Returns:
        同步包装方法
    """
    from ncatbot.utils import run_coroutine

    @functools.wraps(async_method)
    def wrapper(self, *args, **kwargs):
        return run_coroutine(async_method, self, *args, **kwargs)  # type: ignore

    # 标记为同步包装方法
    wrapper._is_sync_wrapper = True  # type: ignore
    wrapper._async_method = async_method  # type: ignore

    return wrapper  # type: ignore


def generate_sync_methods(cls: type[_C]) -> type[_C]:
    """
    类装饰器：为所有异步方法自动生成同步版本

    同步方法命名规则：{method_name}_sync

    使用 Type[_C] 泛型保持原始类的类型信息，确保装饰后的类仍然具有
    正确的类型注解，IDE 可以正常提供异步方法的类型提示。

    Note:
        动态生成的同步方法（*_sync）无法在静态分析中被识别。

    Args:
        cls: 要处理的类

    Returns:
        添加了同步方法的类（保持原始类型）
    """
    import inspect

    for name, method in inspect.getmembers(cls, predicate=inspect.iscoroutinefunction):
        # 跳过私有方法和已有同步版本的方法
        if name.startswith("_"):
            continue
        sync_name = f"{name}_sync"
        if hasattr(cls, sync_name):
            continue

        # 生成同步包装方法
        setattr(cls, sync_name, sync_wrapper(method))

    return cls
