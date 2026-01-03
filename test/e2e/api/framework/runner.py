"""
测试运行器

支持交互式和自动化两种模式运行测试。
"""

import json
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

from .types import TestCase, TestResult, TestStatus
from .output import Colors, print_header, print_section


def format_result(result: Any, indent: int = 2, max_depth: int = 3) -> str:
    """格式化结果输出"""
    prefix = " " * indent

    if result is None:
        return f"{prefix}{Colors.DIM}(None){Colors.ENDC}"

    # 处理模型对象
    if hasattr(result, "__dict__") and not isinstance(result, (str, int, float, bool)):
        result = {k: v for k, v in vars(result).items() if not k.startswith("_")}

    if isinstance(result, dict):
        lines = []
        for key, value in result.items():
            if isinstance(value, (dict, list)):
                if max_depth > 0:
                    try:
                        formatted = json.dumps(
                            value, ensure_ascii=False, indent=2, default=str
                        )
                        formatted = "\n".join(
                            prefix + "  " + line for line in formatted.split("\n")
                        )
                        lines.append(
                            f"{prefix}{Colors.CYAN}{key}{Colors.ENDC}:\n{formatted}"
                        )
                    except Exception:
                        lines.append(
                            f"{prefix}{Colors.CYAN}{key}{Colors.ENDC}: {value}"
                        )
                else:
                    lines.append(f"{prefix}{Colors.CYAN}{key}{Colors.ENDC}: ...")
            elif hasattr(value, "__dict__") and not isinstance(
                value, (str, int, float, bool)
            ):
                # 嵌套模型对象
                nested = {k: v for k, v in vars(value).items() if not k.startswith("_")}
                lines.append(f"{prefix}{Colors.CYAN}{key}{Colors.ENDC}: {nested}")
            else:
                lines.append(f"{prefix}{Colors.CYAN}{key}{Colors.ENDC}: {value}")
        return "\n".join(lines)

    if isinstance(result, list):
        if len(result) == 0:
            return f"{prefix}{Colors.DIM}(空列表){Colors.ENDC}"
        # 处理列表中的模型对象
        processed = []
        for item in result[:5]:
            if hasattr(item, "__dict__") and not isinstance(
                item, (str, int, float, bool)
            ):
                processed.append(
                    {k: v for k, v in vars(item).items() if not k.startswith("_")}
                )
            else:
                processed.append(item)
        try:
            formatted = json.dumps(processed, ensure_ascii=False, indent=2, default=str)
            formatted = "\n".join(prefix + line for line in formatted.split("\n"))
            if len(result) > 5:
                formatted += (
                    f"\n{prefix}{Colors.DIM}... 共 {len(result)} 项{Colors.ENDC}"
                )
            return formatted
        except Exception:
            return f"{prefix}{result}"

    return f"{prefix}{result}"


class TestRunner:
    """
    测试运行器基类

    提供基本的测试执行功能。
    """

    def __init__(self, api: Any, config: Dict[str, Any] = None):
        """
        Args:
            api: BotAPI 实例
            config: 测试配置
        """
        self.api = api
        self.config = config or {}
        self.results: List[TestResult] = []

    async def run_single_test(self, test_case: TestCase) -> TestResult:
        """执行单个测试"""
        result = TestResult(test_case=test_case)
        result.started_at = datetime.now()
        result.status = TestStatus.RUNNING

        try:
            actual = await test_case.func(self.api, self.config)
            result.actual_result = actual

            # 运行验证器
            passed, message = test_case.validate(actual)
            if passed:
                result.status = TestStatus.PASSED
            else:
                result.status = TestStatus.FAILED
                result.error = message or "验证失败"

            result.finished_at = datetime.now()
        except AssertionError as e:
            result.error = str(e) or "断言失败"
            result.status = TestStatus.FAILED
            result.finished_at = datetime.now()
        except Exception:
            result.error = traceback.format_exc()
            result.status = TestStatus.ERROR
            result.finished_at = datetime.now()

        return result

    async def run_tests(self, test_cases: List[TestCase]) -> List[TestResult]:
        """运行所有测试"""
        self.results = []
        total = len(test_cases)
        passed = 0
        failed = 0
        errors = 0

        print(f"\n{Colors.BOLD}开始运行 {total} 个测试...{Colors.ENDC}\n")

        for i, test_case in enumerate(test_cases, 1):
            print(f"[{i}/{total}] {test_case.name}...", end=" ", flush=True)
            result = await self.run_single_test(test_case)
            self.results.append(result)

            if result.status == TestStatus.PASSED:
                print(f"{Colors.GREEN}✓ PASSED{Colors.ENDC}")
                passed += 1
                # 显示详细结果
                if test_case.show_result and result.actual_result is not None:
                    print(f"{Colors.DIM}  结果:{Colors.ENDC}")
                    print(format_result(result.actual_result, indent=4))
            elif result.status == TestStatus.FAILED:
                print(f"{Colors.YELLOW}✗ FAILED{Colors.ENDC}")
                if result.error:
                    print(f"  {Colors.YELLOW}原因: {result.error}{Colors.ENDC}")
                failed += 1
            elif result.status == TestStatus.ERROR:
                print(f"{Colors.RED}✗ ERROR{Colors.ENDC}")
                error_line = (
                    result.error.splitlines()[-1] if result.error else "Unknown error"
                )
                print(f"  {Colors.DIM}{error_line}{Colors.ENDC}")
                errors += 1

        # 打印总结
        print(f"\n{Colors.BOLD}{'=' * 40}{Colors.ENDC}")
        print(f"{Colors.BOLD}测试结果:{Colors.ENDC}")
        print(f"  {Colors.GREEN}通过: {passed}{Colors.ENDC}")
        if failed > 0:
            print(f"  {Colors.YELLOW}失败: {failed}{Colors.ENDC}")
        if errors > 0:
            print(f"  {Colors.RED}错误: {errors}{Colors.ENDC}")
        print(f"  总计: {total}")

        # 显示失败/错误的详情
        failures = [
            r for r in self.results if r.status in (TestStatus.FAILED, TestStatus.ERROR)
        ]
        if failures:
            print(f"\n{Colors.RED}失败/错误详情:{Colors.ENDC}")
            for r in failures:
                status_color = (
                    Colors.YELLOW if r.status == TestStatus.FAILED else Colors.RED
                )
                print(f"  {status_color}• {r.test_case.name}{Colors.ENDC}")
                if r.error:
                    for line in r.error.strip().split("\n")[-3:]:
                        print(f"    {Colors.DIM}{line}{Colors.ENDC}")

        return self.results


class InteractiveTestRunner(TestRunner):
    """
    交互式测试运行器

    逐个执行测试，人工确认结果。
    """

    def _print_header(self, text: str) -> None:
        """打印标题"""
        print_header(text)

    def _print_section(self, title: str, content: str) -> None:
        """打印章节"""
        print_section(title, content)

    def _print_result(self, result: Any) -> None:
        """格式化打印结果"""
        print(f"{Colors.CYAN}{Colors.BOLD}[实际结果]{Colors.ENDC}")
        if isinstance(result, dict):
            for key, value in result.items():
                print(f"  {Colors.DIM}{key}:{Colors.ENDC} {value}")
        elif hasattr(result, "__dict__"):
            for key, value in vars(result).items():
                if not key.startswith("_"):
                    print(f"  {Colors.DIM}{key}:{Colors.ENDC} {value}")
        else:
            print(f"  {result}")

    def _print_status(self, status: TestStatus) -> None:
        """打印状态"""
        color_map = {
            TestStatus.PASSED: Colors.GREEN,
            TestStatus.FAILED: Colors.RED,
            TestStatus.SKIPPED: Colors.YELLOW,
            TestStatus.ERROR: Colors.RED,
            TestStatus.PENDING: Colors.DIM,
            TestStatus.RUNNING: Colors.BLUE,
        }
        color = color_map.get(status, Colors.ENDC)
        print(f"{color}{Colors.BOLD}[{status.value.upper()}]{Colors.ENDC}")

    def _get_user_action(self) -> str:
        """获取用户操作"""
        print(f"\n{Colors.YELLOW}请选择操作:{Colors.ENDC}")
        print(f"  {Colors.GREEN}[p]{Colors.ENDC} 通过 (Pass)")
        print(f"  {Colors.RED}[f]{Colors.ENDC} 失败 (Fail)")
        print(f"  {Colors.YELLOW}[s]{Colors.ENDC} 跳过 (Skip)")
        print(f"  {Colors.BLUE}[r]{Colors.ENDC} 重试 (Retry)")
        print(f"  {Colors.CYAN}[c]{Colors.ENDC} 添加评论 (Comment)")
        print(f"  {Colors.DIM}[q]{Colors.ENDC} 退出 (Quit)")

        while True:
            action = input(f"\n{Colors.BOLD}> {Colors.ENDC}").strip().lower()
            if action in ["p", "f", "s", "r", "c", "q"]:
                return action
            print(f"{Colors.RED}无效输入，请重新选择{Colors.ENDC}")

    async def _run_interactive_test(self, test_case: TestCase) -> TestResult:
        """执行单个测试（交互模式）"""
        result = TestResult(test_case=test_case)
        result.started_at = datetime.now()
        result.status = TestStatus.RUNNING

        # 打印测试信息
        self._print_header(f"测试: {test_case.name}")
        self._print_section("描述", test_case.description)
        self._print_section("API", test_case.api_endpoint)
        self._print_section("分类", test_case.category)
        self._print_section("预期结果", test_case.expected)

        if test_case.tags:
            self._print_section("标签", ", ".join(test_case.tags))

        print(f"\n{Colors.BLUE}正在执行测试...{Colors.ENDC}\n")

        try:
            actual = await test_case.func(self.api, self.config)
            result.actual_result = actual
            self._print_result(actual)
        except Exception as e:
            result.error = traceback.format_exc()
            print(f"\n{Colors.RED}{Colors.BOLD}[执行错误]{Colors.ENDC}")
            print(f"  {Colors.RED}{e}{Colors.ENDC}")
            print(f"\n{Colors.DIM}{result.error}{Colors.ENDC}")

        return result

    async def _handle_test_result(self, result: TestResult) -> Optional[bool]:
        """
        处理测试结果

        Returns:
            True: 继续下一个测试
            False: 退出测试
            None: 重试当前测试
        """
        comment = ""

        while True:
            action = self._get_user_action()

            if action == "p":
                result.mark_passed(comment)
                self._print_status(TestStatus.PASSED)
                return True
            elif action == "f":
                result.mark_failed(comment)
                self._print_status(TestStatus.FAILED)
                return True
            elif action == "s":
                result.mark_skipped(comment or "用户跳过")
                self._print_status(TestStatus.SKIPPED)
                return True
            elif action == "r":
                return None
            elif action == "c":
                comment = input(f"{Colors.CYAN}请输入评论: {Colors.ENDC}")
                print(f"{Colors.GREEN}评论已保存{Colors.ENDC}")
                continue
            elif action == "q":
                result.mark_skipped("用户退出")
                return False

    async def run_tests(self, test_cases: List[TestCase]) -> List[TestResult]:
        """运行所有测试（交互模式）"""
        self.results = []
        total = len(test_cases)

        self._print_header("交互式 API 端到端测试")
        print(f"共 {Colors.BOLD}{total}{Colors.ENDC} 个测试用例")
        print(f"\n{Colors.DIM}按 Enter 开始测试...{Colors.ENDC}")
        input()

        for i, test_case in enumerate(test_cases):
            print(f"\n{Colors.DIM}[{i + 1}/{total}]{Colors.ENDC}")

            while True:
                result = await self._run_interactive_test(test_case)
                continue_flag = await self._handle_test_result(result)

                if continue_flag is None:
                    print(f"\n{Colors.BLUE}重试测试...{Colors.ENDC}")
                    continue
                elif continue_flag:
                    self.results.append(result)
                    break
                else:
                    self.results.append(result)
                    self._print_summary()
                    return self.results

        self._print_summary()
        return self.results

    def _print_summary(self) -> None:
        """打印测试摘要"""
        self._print_header("测试摘要")

        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
        error = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        total = len(self.results)

        print(f"  {Colors.GREEN}通过: {passed}{Colors.ENDC}")
        print(f"  {Colors.RED}失败: {failed}{Colors.ENDC}")
        print(f"  {Colors.YELLOW}跳过: {skipped}{Colors.ENDC}")
        print(f"  {Colors.RED}错误: {error}{Colors.ENDC}")
        print(f"  {Colors.BOLD}总计: {total}{Colors.ENDC}")

        if failed > 0 or error > 0:
            print(f"\n{Colors.RED}{Colors.BOLD}失败的测试:{Colors.ENDC}")
            for r in self.results:
                if r.status in [TestStatus.FAILED, TestStatus.ERROR]:
                    msg = r.human_comment or r.error or "无说明"
                    print(f"  - {r.test_case.name}: {msg}")
