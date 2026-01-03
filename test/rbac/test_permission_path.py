"""
PermissionPath 单元测试
"""

import pytest
from ncatbot.core.service.builtin.rbac.path import PermissionPath


class TestPermissionPathInit:
    """初始化测试"""

    def test_init_from_string(self):
        """测试从字符串初始化"""
        path = PermissionPath("plugin.admin.kick")
        assert path.raw == "plugin.admin.kick"
        assert path.parts == ("plugin", "admin", "kick")

    def test_init_from_list(self):
        """测试从列表初始化"""
        path = PermissionPath(["plugin", "admin", "kick"])
        assert path.raw == "plugin.admin.kick"
        assert path.parts == ("plugin", "admin", "kick")

    def test_init_from_tuple(self):
        """测试从元组初始化"""
        path = PermissionPath(("plugin", "admin", "kick"))
        assert path.raw == "plugin.admin.kick"
        assert path.parts == ("plugin", "admin", "kick")

    def test_init_from_permission_path(self):
        """测试从 PermissionPath 初始化"""
        original = PermissionPath("plugin.admin.kick")
        path = PermissionPath(original)
        assert path.raw == "plugin.admin.kick"
        assert path.parts == ("plugin", "admin", "kick")

    def test_init_invalid_type(self):
        """测试无效类型"""
        with pytest.raises(TypeError):
            PermissionPath(123)


class TestPermissionPathOperators:
    """运算符测试"""

    def test_equality_with_permission_path(self):
        """测试与 PermissionPath 相等"""
        path1 = PermissionPath("plugin.admin")
        path2 = PermissionPath("plugin.admin")
        assert path1 == path2

    def test_equality_with_string(self):
        """测试与字符串相等"""
        path = PermissionPath("plugin.admin")
        assert path == "plugin.admin"

    def test_equality_with_list(self):
        """测试与列表相等"""
        path = PermissionPath("plugin.admin")
        assert path == ["plugin", "admin"]

    def test_equality_with_tuple(self):
        """测试与元组相等"""
        path = PermissionPath("plugin.admin")
        assert path == ("plugin", "admin")

    def test_inequality(self):
        """测试不相等"""
        path1 = PermissionPath("plugin.admin")
        path2 = PermissionPath("plugin.user")
        assert path1 != path2

    def test_len(self):
        """测试长度"""
        path = PermissionPath("plugin.admin.kick")
        assert len(path) == 3

    def test_getitem(self):
        """测试索引访问"""
        path = PermissionPath("plugin.admin.kick")
        assert path[0] == "plugin"
        assert path[1] == "admin"
        assert path[2] == "kick"

    def test_iter(self):
        """测试迭代"""
        path = PermissionPath("plugin.admin.kick")
        parts = list(path)
        assert parts == ["plugin", "admin", "kick"]

    def test_contains(self):
        """测试 in 运算符"""
        path = PermissionPath("plugin.admin.kick")
        assert "admin" in path
        assert "user" not in path

    def test_hash(self):
        """测试哈希"""
        path1 = PermissionPath("plugin.admin")
        path2 = PermissionPath("plugin.admin")
        assert hash(path1) == hash(path2)

        # 可以作为字典键
        d = {path1: "value"}
        assert d[path2] == "value"

    def test_str(self):
        """测试字符串表示"""
        path = PermissionPath("plugin.admin")
        assert str(path) == "plugin.admin"

    def test_repr(self):
        """测试 repr"""
        path = PermissionPath("plugin.admin")
        assert repr(path) == "PermissionPath('plugin.admin')"


class TestPermissionPathMethods:
    """方法测试"""

    def test_get(self):
        """测试 get 方法"""
        path = PermissionPath("plugin.admin.kick")
        assert path.get(0) == "plugin"
        assert path.get(1) == "admin"
        assert path.get(10) is None
        assert path.get(10, "default") == "default"

    def test_join(self):
        """测试 join 方法"""
        path = PermissionPath("plugin")
        new_path = path.join("admin", "kick")
        assert new_path.raw == "plugin.admin.kick"

    def test_join_empty(self):
        """测试 join 空字符串"""
        path = PermissionPath("plugin")
        new_path = path.join("", "admin")
        assert new_path.raw == "plugin.admin"


class TestPermissionPathMatching:
    """路径匹配测试"""

    def test_exact_match(self):
        """测试精确匹配"""
        path = PermissionPath("plugin.admin.kick")
        assert path.matches("plugin.admin.kick")
        assert not path.matches("plugin.admin.ban")

    def test_single_wildcard(self):
        """测试单层通配符 *"""
        pattern = PermissionPath("plugin.*.kick")
        assert pattern.matches("plugin.admin.kick")
        assert pattern.matches("plugin.user.kick")
        assert not pattern.matches("plugin.admin.ban")
        assert not pattern.matches("plugin.kick")  # 缺少中间层

    def test_double_wildcard(self):
        """测试多层通配符 **"""
        pattern = PermissionPath("plugin.**")
        assert pattern.matches("plugin.admin")
        assert pattern.matches("plugin.admin.kick")
        assert pattern.matches("plugin.admin.kick.all")

    def test_wildcard_in_target(self):
        """测试目标包含通配符"""
        path = PermissionPath("plugin.admin.kick")
        assert path.matches("plugin.*.kick")
        assert path.matches("plugin.**")

    def test_both_wildcard_error(self):
        """测试两边都有通配符时报错"""
        pattern = PermissionPath("plugin.*")
        # 当两个不同的通配符路径比较时抛出异常
        with pytest.raises(ValueError, match="不能同时使用通配符"):
            pattern.matches("*.admin")

    def test_same_wildcard_exact_match(self):
        """测试相同通配符路径精确匹配"""
        pattern = PermissionPath("plugin.*")
        # 完全相同的路径直接返回 True（不检查通配符冲突）
        assert pattern.matches("plugin.*")

    def test_wildcard_no_match(self):
        """测试通配符不匹配"""
        pattern = PermissionPath("plugin.admin.*")
        assert not pattern.matches("plugin.user.kick")

    def test_wildcard_at_start(self):
        """测试通配符在开头"""
        pattern = PermissionPath("*.admin.kick")
        assert pattern.matches("plugin.admin.kick")
        assert pattern.matches("system.admin.kick")

    def test_multiple_single_wildcards(self):
        """测试多个单层通配符"""
        pattern = PermissionPath("*.*.kick")
        assert pattern.matches("plugin.admin.kick")
        assert not pattern.matches("plugin.kick")
