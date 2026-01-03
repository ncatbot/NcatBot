"""RBAC E2E 测试共享 fixtures"""

import sys
from pathlib import Path

import pytest

from ncatbot.utils import status
from ncatbot.core.service.builtin.rbac.service import RBACService


# 测试插件目录
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
PLUGINS_DIR = FIXTURES_DIR / "plugins"
RBAC_PLUGIN_DIR = PLUGINS_DIR / "rbac_test_plugin"
TEST_STORAGE = Path("data/rbac_e2e_test.json")


def cleanup_modules():
    """清理插件模块缓存"""
    modules_to_remove = [
        name
        for name in list(sys.modules.keys())
        if "rbac_test_plugin" in name or "ncatbot_plugin" in name
    ]
    for name in modules_to_remove:
        sys.modules.pop(name, None)


def cleanup_test_storage():
    """清理测试存储文件"""
    if TEST_STORAGE.exists():
        TEST_STORAGE.unlink()


@pytest.fixture
def rbac_service_for_e2e():
    """提供 E2E 测试用的 RBAC 服务"""
    Path("data").mkdir(exist_ok=True)
    cleanup_test_storage()

    service = RBACService(storage_path=str(TEST_STORAGE))

    # 设置为全局访问管理器
    old_manager = status.global_access_manager
    status.global_access_manager = service

    yield service

    # 恢复原状态
    status.global_access_manager = old_manager
    cleanup_test_storage()
