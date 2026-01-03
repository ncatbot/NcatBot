"""
NapCat Mock 服务器模块

提供模拟 NapCat WebSocket 服务器的功能，用于测试。

使用方式:
```python
from ncatbot.utils.testing import NapCatMockServer, get_standard_data

async with NapCatMockServer(port=6700, initial_data=get_standard_data()) as server:
    # 服务器在 ws://localhost:6700 监听
    pass
```
"""

from .server import NapCatMockServer
from .client import MockServerClient
from .database import MockDatabase
from .handlers import MockApiHandler
from .templates import (
    # 数据创建函数
    create_bot_data,
    create_user_data,
    create_group_member_data,
    create_group_data,
    create_file_data,
    create_folder_data,
    # 预定义数据模板
    get_minimal_data,
    get_standard_data,
    get_rich_data,
    # 场景构建器
    ScenarioBuilder,
)

__all__ = [
    # 核心组件
    "NapCatMockServer",
    "MockServerClient",
    "MockDatabase",
    "MockApiHandler",
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
