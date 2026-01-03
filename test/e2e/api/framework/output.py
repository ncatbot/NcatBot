"""
终端颜色和格式化输出
"""


class Colors:
    """终端颜色"""

    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    DIM = "\033[2m"


def print_header(text: str) -> None:
    """打印标题"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_section(title: str, content: str) -> None:
    """打印章节"""
    print(f"{Colors.CYAN}{Colors.BOLD}[{title}]{Colors.ENDC}")
    print(f"  {content}")


def print_success(text: str) -> None:
    """打印成功信息"""
    print(f"{Colors.GREEN}{text}{Colors.ENDC}")


def print_error(text: str) -> None:
    """打印错误信息"""
    print(f"{Colors.RED}{text}{Colors.ENDC}")


def print_warning(text: str) -> None:
    """打印警告信息"""
    print(f"{Colors.YELLOW}{text}{Colors.ENDC}")


def print_info(text: str) -> None:
    """打印信息"""
    print(f"{Colors.BLUE}{text}{Colors.ENDC}")
