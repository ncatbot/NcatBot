"""
测试用例装饰器和收集器
"""

from typing import Callable, List, Type

from .types import TestCase


def test_case(
    name: str,
    description: str,
    category: str,
    api_endpoint: str,
    expected: str,
    tags: List[str] = None,
    requires_input: bool = False,
    validator: Callable = None,
    show_result: bool = False,
):
    """
    测试用例装饰器

    Args:
        name: 测试名称
        description: 测试描述
        category: 测试分类
        api_endpoint: API 端点
        expected: 预期结果描述
        tags: 标签列表
        requires_input: 是否需要人工输入
        validator: 验证函数，接受结果返回 (passed, message)
        show_result: 是否显示详细结果

    Example:
        @test_case(
            name="获取登录信息",
            description="获取当前登录的 QQ 账号信息",
            category="account",
            api_endpoint="/get_login_info",
            expected="返回包含 user_id 和 nickname 的信息",
            validator=lambda r: (r.get("user_id") is not None, "user_id 不能为空"),
            show_result=True,
        )
        async def test_get_login_info(api, data):
            return await api.get_login_info()
    """

    def decorator(func: Callable) -> TestCase:
        return TestCase(
            name=name,
            description=description,
            category=category,
            api_endpoint=api_endpoint,
            expected=expected,
            func=func,
            tags=tags or [],
            requires_input=requires_input,
            validator=validator,
            show_result=show_result,
        )

    return decorator


class APITestSuite:
    """
    API 测试套件基类

    子类通过定义 test_* 属性来添加测试用例。
    """

    suite_name: str = "API Tests"
    suite_description: str = ""

    @classmethod
    def collect_tests(cls) -> List[TestCase]:
        """收集所有测试用例"""
        tests = []
        for name in dir(cls):
            if name.startswith("test_"):
                attr = getattr(cls, name)
                if isinstance(attr, TestCase):
                    tests.append(attr)
        return tests

    @classmethod
    def get_test_count(cls) -> int:
        """获取测试用例数量"""
        return len(cls.collect_tests())


def collect_all_tests(*suites: Type[APITestSuite]) -> List[TestCase]:
    """从多个测试套件收集所有测试用例"""
    all_tests = []
    for suite in suites:
        all_tests.extend(suite.collect_tests())
    return all_tests
