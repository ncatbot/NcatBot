"""
NapCat 适配器模块

提供 NapCat 服务的安装、配置、启动、登录等功能。
"""

from .service import (
    NapCatService,
    launch_napcat_service,
    napcat_service_ok,
    get_service,
)
from .auth import (
    AuthHandler,
    LoginStatus,
    login,
    report_login_status,
)
from .platform import (
    PlatformOps,
    WindowsOps,
    LinuxOps,
    UnsupportedPlatformError,
)
from .config_manager import (
    ConfigManager,
    config_napcat,
)
from .websocket import (
    NapCatWebSocket,
)

__all__ = [
    # 主服务
    "NapCatService",
    "launch_napcat_service",
    "napcat_service_ok",
    "get_service",
    # 认证
    "AuthHandler",
    "LoginStatus",
    "login",
    "report_login_status",
    # 平台操作
    "PlatformOps",
    "WindowsOps",
    "LinuxOps",
    "UnsupportedPlatformError",
    # 配置管理
    "ConfigManager",
    "config_napcat",
    # WebSocket
    "NapCatWebSocket",
]
