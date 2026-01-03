"""
API 测试套件模块（基于场景整合）

包含按场景组织的 API 测试用例：
1. 基础信息场景 - 账号、好友、群组信息查询
2. 群消息场景 - 消息发送、操作、转发
3. 群文件场景 - 文件上传、查询、相册
4. 好友互动场景 - 私聊消息、好友操作
5. 群管理场景 - 精华消息、管理操作

场景化测试的优势：
- 减少重复的用户输入
- 相关 API 串联测试，更接近真实使用场景
- 自动化程度更高，易于 CI/CD 集成
"""

from pathlib import Path

# 场景化测试套件
try:
    # 尝试相对导入（当作为模块使用时）
    from .test_scenario_basic import BasicInfoScenarioTests
    from .test_scenario_group_msg import GroupMessageScenarioTests
    from .test_scenario_group_file import (
        GroupFileScenarioTests,
        GroupAlbumScenarioTests,
    )
    from .test_scenario_friend import FriendInteractionScenarioTests
    from .test_scenario_admin import (
        GroupAdminScenarioTests,
        GroupAdminActionTests,
        DangerousAdminTests,
    )
except ImportError:
    # 回退到绝对导入（当直接运行时）
    from test_scenario_basic import BasicInfoScenarioTests
    from test_scenario_group_msg import GroupMessageScenarioTests
    from test_scenario_group_file import GroupFileScenarioTests, GroupAlbumScenarioTests
    from test_scenario_friend import FriendInteractionScenarioTests
    from test_scenario_admin import (
        GroupAdminScenarioTests,
        GroupAdminActionTests,
        DangerousAdminTests,
    )

# 路径定义
E2E_ROOT = Path(__file__).parent
DATA_DIR = E2E_ROOT / "data"

# 所有场景化测试套件
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

# 自动化测试套件（无需用户输入）
AUTO_TEST_SUITES = [
    BasicInfoScenarioTests,
    GroupMessageScenarioTests,
    GroupFileScenarioTests,
    GroupAlbumScenarioTests,
    FriendInteractionScenarioTests,
    GroupAdminScenarioTests,
    GroupAdminActionTests,
]

# 危险操作测试套件（需要用户确认）
DANGEROUS_TEST_SUITES = [
    DangerousAdminTests,
]

__all__ = [
    # 场景化测试套件
    "BasicInfoScenarioTests",
    "GroupMessageScenarioTests",
    "GroupFileScenarioTests",
    "GroupAlbumScenarioTests",
    "FriendInteractionScenarioTests",
    "GroupAdminScenarioTests",
    "GroupAdminActionTests",
    "DangerousAdminTests",
    # 套件列表
    "ALL_TEST_SUITES",
    "AUTO_TEST_SUITES",
    "DANGEROUS_TEST_SUITES",
    # 路径
    "E2E_ROOT",
    "DATA_DIR",
]
