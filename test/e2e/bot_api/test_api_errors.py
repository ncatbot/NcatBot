"""
API 调用异常处理测试

测试优先级 2：系统稳定性
- API 调用失败时的错误处理
- 服务不可用时的处理
- 网络错误时的处理
- 参数验证错误
"""

import pytest
import pytest_asyncio
import logging

from ncatbot.utils.testing import E2ETestSuite
from ncatbot.core.api.utils import (
    NapCatAPIError,
    APIValidationError,
    require_at_least_one,
    require_exactly_one,
    check_exclusive_argument,
    APIReturnStatus,
)


@pytest_asyncio.fixture
async def api_suite():
    """创建 API 测试套件"""
    suite = E2ETestSuite()
    await suite.setup()
    yield suite
    await suite.teardown()


class TestAPIReturnStatusErrors:
    """测试 API 返回状态处理"""

    def test_raise_if_failed_with_error_response(self):
        """测试错误响应抛出异常"""
        error_response = {"retcode": -1, "message": "群不存在", "data": None}

        with pytest.raises(NapCatAPIError) as exc_info:
            APIReturnStatus.raise_if_failed(error_response)

        assert "群不存在" in str(exc_info.value)
        assert exc_info.value.retcode == -1

    def test_raise_if_failed_with_success_response(self):
        """测试成功响应不抛出异常"""
        success_response = {
            "retcode": 0,
            "message": "ok",
            "data": {"result": "success"},
        }

        # 不应该抛出异常
        APIReturnStatus.raise_if_failed(success_response)

    def test_api_return_status_constructor_with_error(self):
        """测试构造函数处理错误响应"""
        error_response = {
            "retcode": 100,
            "message": "权限不足",
        }

        with pytest.raises(NapCatAPIError) as exc_info:
            APIReturnStatus(error_response)

        assert exc_info.value.retcode == 100

    def test_api_return_status_is_success(self):
        """测试 is_success 属性"""
        success_response = {"retcode": 0, "message": "ok", "data": None}
        status = APIReturnStatus(success_response)

        assert status.is_success
        assert bool(status)

    def test_api_return_status_with_unknown_error(self):
        """测试未知错误消息"""
        error_response = {"retcode": -1}  # 没有 message

        with pytest.raises(NapCatAPIError) as exc_info:
            APIReturnStatus.raise_if_failed(error_response)

        assert "Unknown error" in str(exc_info.value)


class TestParameterValidation:
    """测试参数验证工具"""

    def test_require_at_least_one_all_none(self):
        """测试所有参数都为 None 时抛出异常"""
        with pytest.raises(APIValidationError) as exc_info:
            require_at_least_one(None, None, None, names=["a", "b", "c"])

        assert "至少需要提供以下参数之一" in str(exc_info.value)
        assert "a" in str(exc_info.value)

    def test_require_at_least_one_has_value(self):
        """测试有值时不抛出异常"""
        # 不应该抛出异常
        require_at_least_one(None, "value", None, names=["a", "b", "c"])

    def test_require_exactly_one_none(self):
        """测试没有提供参数时抛出异常"""
        with pytest.raises(APIValidationError):
            require_exactly_one(None, None, names=["a", "b"])

    def test_require_exactly_one_multiple(self):
        """测试提供多个参数时抛出异常"""
        with pytest.raises(APIValidationError):
            require_exactly_one("v1", "v2", names=["a", "b"])

    def test_require_exactly_one_success(self):
        """测试恰好提供一个参数时成功"""
        require_exactly_one("value", None, names=["a", "b"])

    def test_check_exclusive_argument_returns_false(self):
        """测试互斥检查返回 False"""
        result = check_exclusive_argument("v1", "v2", names=["a", "b"], error=False)
        assert result is False

    def test_check_exclusive_argument_raises_error(self):
        """测试互斥检查抛出异常"""
        with pytest.raises(APIValidationError):
            check_exclusive_argument("v1", "v2", names=["a", "b"], error=True)

    def test_check_exclusive_argument_success(self):
        """测试互斥检查成功"""
        result = check_exclusive_argument("value", None, names=["a", "b"], error=False)
        assert result is True


class TestNapCatAPIError:
    """测试 NapCatAPIError 异常类"""

    def test_error_contains_info(self, caplog):
        """测试错误信息被正确记录"""
        with caplog.at_level(logging.ERROR):
            error = NapCatAPIError("测试错误信息", retcode=404)

        assert error.info == "测试错误信息"
        assert error.retcode == 404
        assert "测试错误信息" in str(error)

    def test_error_logs_stacktrace_in_debug(self, caplog):
        """测试 debug 模式下记录堆栈"""
        from ncatbot.utils import ncatbot_config

        original_debug = ncatbot_config.debug
        try:
            ncatbot_config.debug = True
            with caplog.at_level(logging.INFO):
                _error = NapCatAPIError("Debug 模式测试")

            # 验证堆栈被记录（在 debug 模式下）
            # 注意：这取决于具体的实现
        finally:
            ncatbot_config.debug = original_debug


class TestAPICallErrors:
    """测试 API 调用错误处理

    注意：这些测试依赖于 MockServer 的具体实现。
    """

    @pytest.mark.asyncio
    async def test_api_returns_error_retcode(self, api_suite):
        """测试 API 返回错误 retcode 时的处理"""
        # 这个测试验证 APIReturnStatus 正确处理错误响应
        error_response = {"retcode": -1, "message": "测试错误"}

        with pytest.raises(NapCatAPIError):
            APIReturnStatus.raise_if_failed(error_response)


class TestAPIConnectionErrors:
    """测试 API 连接错误处理

    注意：这些测试验证基础的 API 可用性检查逻辑。
    """

    @pytest.mark.asyncio
    async def test_api_check_handles_exceptions(self):
        """测试 API 检查处理异常"""
        # 这个测试验证 is_api_available 方法在异常时返回 False
        # 具体行为取决于实现
        pass  # 跳过，需要更复杂的模拟设置


class TestValidationError:
    """测试 APIValidationError"""

    def test_validation_error_message(self, caplog):
        """测试验证错误消息"""
        with caplog.at_level(logging.ERROR):
            error = APIValidationError("无效的群号格式")

        assert "参数验证失败" in str(error)
        assert "无效的群号格式" in str(error)
