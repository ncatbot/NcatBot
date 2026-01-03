"""
PermissionTrie 单元测试
"""

import pytest
from ncatbot.core.service.builtin.rbac.trie import PermissionTrie


class TestPermissionTrieBasic:
    """基础功能测试"""

    def test_add_and_exists(self):
        """测试添加和检查存在"""
        trie = PermissionTrie()
        trie.add("plugin.admin.kick")

        assert trie.exists("plugin.admin.kick", exact=True)
        assert trie.exists("plugin.admin", exact=False)
        assert not trie.exists("plugin.admin", exact=True)

    def test_add_multiple(self):
        """测试添加多个路径"""
        trie = PermissionTrie()
        trie.add("plugin.admin.kick")
        trie.add("plugin.admin.ban")
        trie.add("plugin.user.profile")

        assert trie.exists("plugin.admin.kick", exact=True)
        assert trie.exists("plugin.admin.ban", exact=True)
        assert trie.exists("plugin.user.profile", exact=True)

    def test_add_with_wildcard_error(self):
        """测试添加包含通配符的路径报错"""
        trie = PermissionTrie()

        with pytest.raises(ValueError, match="不能包含通配符"):
            trie.add("plugin.*.kick")

        with pytest.raises(ValueError, match="不能包含通配符"):
            trie.add("plugin.**")

    def test_remove(self):
        """测试删除路径"""
        trie = PermissionTrie()
        trie.add("plugin.admin.kick")
        trie.add("plugin.admin.ban")

        trie.remove("plugin.admin.kick")

        assert not trie.exists("plugin.admin.kick", exact=True)
        assert trie.exists("plugin.admin.ban", exact=True)

    def test_remove_nonexistent(self):
        """测试删除不存在的路径"""
        trie = PermissionTrie()
        trie.add("plugin.admin.kick")

        # 不应该抛出异常
        trie.remove("plugin.admin.ban")

        assert trie.exists("plugin.admin.kick", exact=True)

    def test_remove_cleans_empty_nodes(self):
        """测试删除后清理空节点"""
        trie = PermissionTrie()
        trie.add("plugin.admin.kick")
        trie.remove("plugin.admin.kick")

        # 整个分支应该被清理
        assert not trie.exists("plugin", exact=False)


class TestPermissionTrieWildcard:
    """通配符检查测试"""

    def test_exists_with_single_wildcard(self):
        """测试单层通配符检查"""
        trie = PermissionTrie()
        trie.add("plugin.admin.kick")
        trie.add("plugin.user.kick")

        assert trie.exists("plugin.*.kick", exact=False)
        assert not trie.exists("plugin.*.ban", exact=False)

    def test_exists_with_double_wildcard(self):
        """测试多层通配符检查"""
        trie = PermissionTrie()
        trie.add("plugin.admin.kick")
        trie.add("plugin.admin.ban")

        assert trie.exists("plugin.**", exact=False)
        assert trie.exists("plugin.admin.**", exact=False)


class TestPermissionTrieCaseSensitivity:
    """大小写敏感性测试"""

    def test_case_sensitive(self):
        """测试大小写敏感"""
        trie = PermissionTrie(case_sensitive=True)
        trie.add("Plugin.Admin.Kick")

        assert trie.exists("Plugin.Admin.Kick", exact=True)
        assert not trie.exists("plugin.admin.kick", exact=True)

    def test_case_insensitive(self):
        """测试大小写不敏感"""
        trie = PermissionTrie(case_sensitive=False)
        trie.add("Plugin.Admin.Kick")

        assert trie.exists("Plugin.Admin.Kick", exact=True)
        assert trie.exists("plugin.admin.kick", exact=True)
        assert trie.exists("PLUGIN.ADMIN.KICK", exact=True)


class TestPermissionTrieSerialization:
    """序列化测试"""

    def test_to_dict(self):
        """测试导出为字典"""
        trie = PermissionTrie()
        trie.add("plugin.admin.kick")
        trie.add("plugin.admin.ban")

        data = trie.to_dict()

        assert "plugin" in data
        assert "admin" in data["plugin"]
        assert "kick" in data["plugin"]["admin"]
        assert "ban" in data["plugin"]["admin"]

    def test_from_dict(self):
        """测试从字典恢复"""
        trie = PermissionTrie()
        data = {"plugin": {"admin": {"kick": {}, "ban": {}}}}

        trie.from_dict(data)

        assert trie.exists("plugin.admin.kick", exact=True)
        assert trie.exists("plugin.admin.ban", exact=True)

    def test_from_dict_empty(self):
        """测试从空字典恢复"""
        trie = PermissionTrie()
        trie.add("plugin.admin.kick")

        trie.from_dict({})

        assert not trie.exists("plugin.admin.kick", exact=True)

    def test_roundtrip(self):
        """测试序列化往返"""
        trie1 = PermissionTrie()
        trie1.add("plugin.admin.kick")
        trie1.add("plugin.admin.ban")
        trie1.add("plugin.user.profile")

        data = trie1.to_dict()

        trie2 = PermissionTrie()
        trie2.from_dict(data)

        assert trie2.exists("plugin.admin.kick", exact=True)
        assert trie2.exists("plugin.admin.ban", exact=True)
        assert trie2.exists("plugin.user.profile", exact=True)


class TestPermissionTrieGetAllPaths:
    """获取所有路径测试"""

    def test_get_all_paths(self):
        """测试获取所有路径"""
        trie = PermissionTrie()
        trie.add("plugin.admin.kick")
        trie.add("plugin.admin.ban")
        trie.add("plugin.user.profile")

        paths = trie.get_all_paths()

        assert len(paths) == 3
        assert "plugin.admin.kick" in paths
        assert "plugin.admin.ban" in paths
        assert "plugin.user.profile" in paths

    def test_get_all_paths_empty(self):
        """测试空树获取所有路径"""
        trie = PermissionTrie()
        paths = trie.get_all_paths()
        # 空树返回包含空字符串的列表（表示根节点为空）
        assert paths == [""]

    def test_list_all_alias(self):
        """测试 list_all 别名"""
        trie = PermissionTrie()
        trie.add("plugin.admin.kick")

        # list_all 应该与 get_all_paths 相同
        assert trie.list_all() == trie.get_all_paths()
