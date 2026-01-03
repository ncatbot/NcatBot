"""
NcatBot API 端到端测试入口

运行方式:
    uv run python test/e2e/run.py

可选参数:
    --category <category>   只运行指定分类的测试
    --tag <tag>             只运行带有指定标签的测试
    --skip-to <index>       从指定序号开始运行测试（跳过之前的测试）
    --report <path>         保存测试报告到指定路径
    --list                  只列出测试用例，不执行
    --auto                  自动模式（非交互），适合 CI/CD

示例:
    # 运行所有测试
    uv run python test/e2e/run.py

    # 只运行账号相关测试
    uv run python test/e2e/run.py --category account

    # 运行带有 basic 标签的测试
    uv run python test/e2e/run.py --tag basic

    # 从第 10 个测试开始运行（跳过前 9 个）
    uv run python test/e2e/run.py --skip-to 10

    # 自动模式运行测试
    uv run python test/e2e/run.py --auto --category account

    # 生成报告
    uv run python test/e2e/run.py --report ./reports/e2e_test.md
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import List, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 添加当前目录到路径，以便导入所有模块
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    # 尝试作为模块导入
    from framework import (  # noqa: E402
        TestCase,
        TestConfig,
        TestRunner,
        InteractiveTestRunner,
        TestReporter,
        collect_all_tests,
        Colors,
    )
except ImportError:
    # 直接导入文件
    from framework.types import TestCase  # noqa: E402
    from framework.config import TestConfig  # noqa: E402
    from framework.runner import TestRunner, InteractiveTestRunner  # noqa: E402
    from framework.reporter import TestReporter  # noqa: E402
    from framework.decorators import collect_all_tests  # noqa: E402
    from framework.output import Colors  # noqa: E402

# 直接导入测试套件
from test_scenario_basic import BasicInfoScenarioTests  # noqa: E402
from test_scenario_group_msg import GroupMessageScenarioTests  # noqa: E402
from test_scenario_group_file import (  # noqa: E402
    GroupFileScenarioTests,
    GroupAlbumScenarioTests,
)
from test_scenario_friend import FriendInteractionScenarioTests  # noqa: E402
from test_scenario_admin import (  # noqa: E402
    GroupAdminScenarioTests,
    GroupAdminActionTests,
    DangerousAdminTests,
)

ALL_TEST_SUITES = [
    # 场景1: 基础信息（只读，全自动）
    BasicInfoScenarioTests,
    # 场景2: 群消息操作（自动）
    GroupMessageScenarioTests,
    # 场景3: 群文件操作（自动）
    GroupFileScenarioTests,
    GroupAlbumScenarioTests,
    # 场景4: 好友互动（自动）
    FriendInteractionScenarioTests,
    # 场景5: 群管理（部分需要确认）
    GroupAdminScenarioTests,
    GroupAdminActionTests,
    DangerousAdminTests,
]


def print_banner():
    """打印启动横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     ███╗   ██╗ ██████╗ █████╗ ████████╗██████╗  ██████╗████████╗   ║
║     ████╗  ██║██╔════╝██╔══██╗╚══██╔══╝██╔══██╗██╔═══██╗╚══██╔══╝  ║
║     ██╔██╗ ██║██║     ███████║   ██║   ██████╔╝██║   ██║   ██║     ║
║     ██║╚██╗██║██║     ██╔══██║   ██║   ██╔══██╗██║   ██║   ██║     ║
║     ██║ ╚████║╚██████╗██║  ██║   ██║   ██████╔╝╚██████╔╝   ██║     ║
║     ╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═════╝  ╚═════╝    ╚═╝     ║
║                                                           ║
║              API 端到端测试工具 v2.0                        ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(f"{Colors.CYAN}{banner}{Colors.ENDC}")


def filter_tests(
    tests: List[TestCase],
    category: Optional[str] = None,
    tag: Optional[str] = None,
    skip_to: Optional[int] = None,
) -> List[TestCase]:
    """过滤测试用例"""
    filtered = tests

    if category:
        filtered = [t for t in filtered if t.category == category]

    if tag:
        filtered = [t for t in filtered if tag in t.tags]

    if skip_to is not None:
        # skip_to 是 1-based，转换为 0-based 索引
        if skip_to > 0 and skip_to <= len(tests):
            filtered = tests[skip_to - 1 :]
        elif skip_to > len(tests):
            print(
                f"{Colors.RED}错误: 指定的序号 {skip_to} 超过总测试数 {len(tests)}{Colors.ENDC}"
            )
            sys.exit(1)

    return filtered


def print_test_list(tests: List[TestCase]):
    """打印测试列表"""
    print(f"\n{Colors.BOLD}即将运行的测试用例:{Colors.ENDC}\n")

    # 按分类分组
    categories = {}
    for test in tests:
        if test.category not in categories:
            categories[test.category] = []
        categories[test.category].append(test)

    for category, category_tests in categories.items():
        print(f"{Colors.CYAN}[{category.upper()}]{Colors.ENDC}")
        for i, test in enumerate(category_tests, 1):
            tags_str = ""
            if test.tags:
                tags_str = f" {Colors.YELLOW}[{', '.join(test.tags)}]{Colors.ENDC}"
            input_mark = ""
            if test.requires_input:
                input_mark = f" {Colors.RED}*{Colors.ENDC}"
            print(f"  {i}. {test.name}{tags_str}{input_mark}")
        print()

    print(f"{Colors.RED}* 表示需要人工输入测试数据{Colors.ENDC}\n")


async def setup_connection():
    """建立连接并返回 BotAPI"""
    from ncatbot.core.api import BotAPI
    from ncatbot.core.adapter.nc import napcat_service_ok
    from ncatbot.core.service import MessageRouter, ServiceManager, PreUploadService

    print(f"{Colors.BLUE}正在连接 NapCat 服务...{Colors.ENDC}")

    if not napcat_service_ok(timeout=5):
        print(f"{Colors.RED}错误: 无法连接到 NapCat 服务{Colors.ENDC}")
        print(f"{Colors.YELLOW}请确保 NapCat 服务正在运行{Colors.ENDC}")
        sys.exit(1)

    # 创建服务管理器
    services = ServiceManager()
    services.register(MessageRouter)
    services.register(PreUploadService)

    # 加载消息路由服务
    await services.load("message_router")
    router = services.message_router

    # 启动消息监听（必须在发送请求前启动）
    router.start_listening()

    # 加载预上传服务（使用 message_router 的连接）
    await services.load("preupload")

    # 创建 API（传入 service_manager 以支持预上传）
    api = BotAPI(router.send, service_manager=services)
    print(f"{Colors.GREEN}连接成功!{Colors.ENDC}")

    # 显示预上传服务状态
    if api._preupload_available:
        print(f"{Colors.GREEN}预上传服务已启用{Colors.ENDC}")
    else:
        print(f"{Colors.YELLOW}警告: 预上传服务不可用{Colors.ENDC}")

    try:
        login_info = await api.get_login_info()
        print(
            f"{Colors.GREEN}当前登录: {login_info.nickname} ({login_info.user_id}){Colors.ENDC}"
        )
    except Exception as e:
        print(f"{Colors.YELLOW}警告: 无法获取登录信息 - {e}{Colors.ENDC}")

    return api


def load_config() -> dict:
    """加载测试配置"""
    try:
        config = TestConfig()
        config.load()
        print(f"{Colors.GREEN}已加载配置文件{Colors.ENDC}")
        return config.to_legacy_config()
    except FileNotFoundError as e:
        print(f"{Colors.YELLOW}警告: {e}{Colors.ENDC}")
        print(f"{Colors.YELLOW}将使用交互式输入模式{Colors.ENDC}")
        return {}


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="NcatBot API 端到端测试工具")
    parser.add_argument("--category", "-c", help="只运行指定分类的测试")
    parser.add_argument("--tag", "-t", help="只运行带有指定标签的测试")
    parser.add_argument(
        "--skip-to",
        "-s",
        type=int,
        help="从指定序号开始运行测试（跳过之前的测试，序号从 1 开始）",
    )
    parser.add_argument("--report", "-r", help="保存测试报告到指定路径")
    parser.add_argument("--list", "-l", action="store_true", help="只列出测试用例")
    parser.add_argument("--auto", "-a", action="store_true", help="自动模式（非交互）")

    args = parser.parse_args()

    print_banner()

    # 收集所有测试
    all_tests = collect_all_tests(*ALL_TEST_SUITES)

    # 过滤测试
    tests = filter_tests(
        all_tests, category=args.category, tag=args.tag, skip_to=args.skip_to
    )

    if not tests:
        print(f"{Colors.RED}没有匹配的测试用例{Colors.ENDC}")
        sys.exit(1)

    print(f"找到 {Colors.BOLD}{len(tests)}{Colors.ENDC} 个测试用例")

    # 打印测试列表
    print_test_list(tests)

    if args.list:
        sys.exit(0)

    # 确认开始（自动模式跳过）
    if not args.auto:
        confirm = input(f"{Colors.YELLOW}是否开始测试? (y/n): {Colors.ENDC}").lower()
        if confirm != "y":
            print("已取消")
            sys.exit(0)

    # 加载配置
    config = load_config()

    # 建立连接
    api = await setup_connection()

    # 创建运行器
    if args.auto:
        runner = TestRunner(api, config)
    else:
        runner = InteractiveTestRunner(api, config)

    # 运行测试
    results = await runner.run_tests(tests)

    # 生成报告
    if args.report:
        reporter = TestReporter(results)
        report_path = Path(args.report)

        if report_path.suffix == ".json":
            reporter.save(str(report_path), format="json")
        else:
            reporter.save(str(report_path), format="markdown")

        print(f"{Colors.GREEN}报告已保存到: {report_path}{Colors.ENDC}")

    print(f"\n{Colors.GREEN}测试完成!{Colors.ENDC}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}测试被用户中断{Colors.ENDC}")
        sys.exit(1)
