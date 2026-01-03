"""
Mock 数据模板模块

提供预定义的测试数据模板和场景构建器。
"""

from .creators import (
    create_bot_data,
    create_user_data,
    create_group_member_data,
    create_group_data,
    create_file_data,
    create_folder_data,
)
from .presets import (
    get_minimal_data,
    get_standard_data,
    get_rich_data,
)
from .builder import ScenarioBuilder

__all__ = [
    # 数据创建函数
    "create_bot_data",
    "create_user_data",
    "create_group_member_data",
    "create_group_data",
    "create_file_data",
    "create_folder_data",
    # 预定义数据模板
    "get_minimal_data",
    "get_standard_data",
    "get_rich_data",
    # 场景构建器
    "ScenarioBuilder",
]
