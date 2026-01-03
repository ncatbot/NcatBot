"""
端到端测试框架

提供交互式 API 测试能力。
"""

from .types import TestCase, TestResult, TestStatus
from .decorators import test_case, APITestSuite, collect_all_tests
from .runner import TestRunner, InteractiveTestRunner
from .reporter import TestReporter
from .config import TestConfig, load_test_config
from .output import Colors, print_header, print_section

__all__ = [
    # 类型
    "TestCase",
    "TestResult",
    "TestStatus",
    # 装饰器
    "test_case",
    "APITestSuite",
    "collect_all_tests",
    # 运行器
    "TestRunner",
    "InteractiveTestRunner",
    # 报告
    "TestReporter",
    # 配置
    "TestConfig",
    "load_test_config",
    # 输出
    "Colors",
    "print_header",
    "print_section",
]
