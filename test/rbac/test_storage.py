"""
RBAC 存储模块单元测试
"""

from ncatbot.core.service.builtin.rbac.storage import (
    save_rbac_data,
    load_rbac_data,
    serialize_rbac_state,
    deserialize_rbac_state,
)


class TestSaveAndLoad:
    """保存和加载测试"""

    def test_save_and_load(self, tmp_path):
        """测试保存和加载"""
        path = tmp_path / "rbac.json"
        data = {"key": "value", "nested": {"a": 1}}

        save_rbac_data(path, data)
        loaded = load_rbac_data(path)

        assert loaded == data

    def test_save_creates_directory(self, tmp_path):
        """测试保存时创建目录"""
        path = tmp_path / "nested" / "dir" / "rbac.json"
        data = {"key": "value"}

        save_rbac_data(path, data)

        assert path.exists()
        assert path.parent.exists()

    def test_load_nonexistent(self, tmp_path):
        """测试加载不存在的文件"""
        path = tmp_path / "nonexistent.json"
        result = load_rbac_data(path)
        assert result is None

    def test_save_unicode(self, tmp_path):
        """测试保存 Unicode 内容"""
        path = tmp_path / "rbac.json"
        data = {"中文": "测试", "emoji": "🎉"}

        save_rbac_data(path, data)
        loaded = load_rbac_data(path)

        assert loaded == data

    def test_save_indent(self, tmp_path):
        """测试保存格式化（带缩进）"""
        path = tmp_path / "rbac.json"
        data = {"key": "value"}

        save_rbac_data(path, data)

        content = path.read_text()
        # 应该有缩进
        assert "  " in content


class TestSerialize:
    """序列化测试"""

    def test_serialize_basic(self):
        """测试基本序列化"""
        result = serialize_rbac_state(
            users={
                "user1": {
                    "whitelist": {"perm1"},
                    "blacklist": set(),
                    "roles": ["admin"],
                }
            },
            roles={"admin": {"whitelist": {"perm1"}, "blacklist": set()}},
            role_users={"admin": {"user1"}},
            role_inheritance={"admin": ["member"]},
            permissions_trie={"plugin": {"admin": {}}},
            case_sensitive=True,
            default_role="member",
        )

        assert result["case_sensitive"] is True
        assert result["default_role"] == "member"
        assert "user1" in result["users"]
        assert "admin" in result["roles"]

    def test_serialize_converts_sets_to_lists(self):
        """测试序列化将 set 转换为 list"""
        result = serialize_rbac_state(
            users={
                "user1": {
                    "whitelist": {"perm1", "perm2"},
                    "blacklist": set(),
                    "roles": [],
                }
            },
            roles={},
            role_users={},
            role_inheritance={},
            permissions_trie={},
            case_sensitive=True,
            default_role=None,
        )

        # whitelist 应该是 list
        assert isinstance(result["users"]["user1"]["whitelist"], list)
        assert set(result["users"]["user1"]["whitelist"]) == {"perm1", "perm2"}


class TestDeserialize:
    """反序列化测试"""

    def test_deserialize_basic(self):
        """测试基本反序列化"""
        data = {
            "case_sensitive": True,
            "default_role": "member",
            "users": {
                "user1": {"whitelist": ["perm1"], "blacklist": [], "roles": ["admin"]}
            },
            "roles": {"admin": {"whitelist": ["perm1"], "blacklist": []}},
            "role_users": {"admin": ["user1"]},
            "role_inheritance": {"admin": ["member"]},
            "permissions": {"plugin": {"admin": {}}},
        }

        result = deserialize_rbac_state(data)

        assert result["case_sensitive"] is True
        assert result["default_role"] == "member"
        assert "user1" in result["users"]
        assert "admin" in result["roles"]

    def test_deserialize_converts_lists_to_sets(self):
        """测试反序列化将 list 转换为 set"""
        data = {
            "users": {
                "user1": {"whitelist": ["perm1", "perm2"], "blacklist": [], "roles": []}
            },
            "roles": {},
            "role_users": {},
            "role_inheritance": {},
            "permissions": {},
        }

        result = deserialize_rbac_state(data)

        # whitelist 应该是 set
        assert isinstance(result["users"]["user1"]["whitelist"], set)
        assert result["users"]["user1"]["whitelist"] == {"perm1", "perm2"}

    def test_deserialize_with_defaults(self):
        """测试反序列化使用默认值"""
        data = {}

        result = deserialize_rbac_state(data)

        assert result["case_sensitive"] is True
        assert result["default_role"] is None
        assert result["users"] == {}
        assert result["roles"] == {}


class TestRoundtrip:
    """序列化往返测试"""

    def test_roundtrip(self):
        """测试序列化和反序列化往返"""
        original_users = {
            "user1": {
                "whitelist": {"perm1", "perm2"},
                "blacklist": {"perm3"},
                "roles": ["admin"],
            }
        }
        original_roles = {"admin": {"whitelist": {"perm1"}, "blacklist": set()}}

        serialized = serialize_rbac_state(
            users=original_users,
            roles=original_roles,
            role_users={"admin": {"user1"}},
            role_inheritance={},
            permissions_trie={},
            case_sensitive=True,
            default_role="member",
        )

        deserialized = deserialize_rbac_state(serialized)

        assert deserialized["users"]["user1"]["whitelist"] == {"perm1", "perm2"}
        assert deserialized["users"]["user1"]["blacklist"] == {"perm3"}
        assert deserialized["roles"]["admin"]["whitelist"] == {"perm1"}
