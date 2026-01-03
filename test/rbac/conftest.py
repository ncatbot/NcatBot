"""
RBAC 测试共享 fixtures
"""

import pytest
from pathlib import Path

from ncatbot.core.service.builtin.rbac import RBACService


# 测试数据存储目录
TEST_DATA_DIR = Path(__file__).parent / "test_data"


@pytest.fixture
def temp_storage_path(tmp_path):
    """提供临时存储路径"""
    storage_path = tmp_path / "rbac_test.json"
    yield storage_path
    # 清理
    if storage_path.exists():
        storage_path.unlink()


@pytest.fixture
def rbac_service(temp_storage_path):
    """创建 RBAC 服务实例（使用临时存储）"""
    service = RBACService(storage_path=str(temp_storage_path))
    yield service
    # 清理：删除存储文件
    if temp_storage_path.exists():
        temp_storage_path.unlink()


@pytest.fixture
def rbac_service_no_storage():
    """创建不使用存储的 RBAC 服务实例"""
    service = RBACService(storage_path=None)
    yield service


@pytest.fixture
def rbac_service_with_default_role(temp_storage_path):
    """创建带默认角色的 RBAC 服务实例"""
    service = RBACService(storage_path=str(temp_storage_path), default_role="member")
    # 初始化默认角色
    service.add_role("member", exist_ok=True)
    yield service
    if temp_storage_path.exists():
        temp_storage_path.unlink()


@pytest.fixture
def populated_rbac_service(rbac_service):
    """创建预填充数据的 RBAC 服务"""
    # 添加权限
    rbac_service.add_permission("plugin.admin.kick")
    rbac_service.add_permission("plugin.admin.ban")
    rbac_service.add_permission("plugin.user.profile")
    rbac_service.add_permission("plugin.user.settings")

    # 添加角色
    rbac_service.add_role("admin")
    rbac_service.add_role("moderator")
    rbac_service.add_role("member")

    # 设置角色继承
    rbac_service.set_role_inheritance("moderator", "member")
    rbac_service.set_role_inheritance("admin", "moderator")

    # 授予角色权限
    rbac_service.grant("role", "admin", "plugin.admin.kick")
    rbac_service.grant("role", "admin", "plugin.admin.ban")
    rbac_service.grant("role", "member", "plugin.user.profile")
    rbac_service.grant("role", "member", "plugin.user.settings")

    # 添加用户
    rbac_service.add_user("user1")
    rbac_service.add_user("user2")
    rbac_service.add_user("111111111")

    # 分配角色
    rbac_service.assign_role("user", "user1", "member")
    rbac_service.assign_role("user", "user2", "moderator")
    rbac_service.assign_role("user", "111111111", "admin")

    yield rbac_service
