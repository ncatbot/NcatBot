"""
RBAC 数据序列化/反序列化

处理 RBAC 数据的持久化存储。
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


def save_rbac_data(path: Path, data: Dict[str, Any]) -> None:
    """保存 RBAC 数据到文件"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_rbac_data(path: Path) -> Optional[Dict[str, Any]]:
    """从文件加载 RBAC 数据"""
    if not path.exists():
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def serialize_rbac_state(
    users: Dict,
    roles: Dict,
    role_users: Dict,
    role_inheritance: Dict,
    permissions_trie: Dict,
    case_sensitive: bool,
    default_role: Optional[str],
) -> Dict[str, Any]:
    """序列化 RBAC 状态"""
    return {
        "case_sensitive": case_sensitive,
        "default_role": default_role,
        "roles": {
            name: {
                "whitelist": list(data.get("whitelist", [])),
                "blacklist": list(data.get("blacklist", [])),
            }
            for name, data in roles.items()
        },
        "users": {
            name: {
                "whitelist": list(data.get("whitelist", [])),
                "blacklist": list(data.get("blacklist", [])),
                "roles": list(data.get("roles", [])),
            }
            for name, data in users.items()
        },
        "role_users": {role: list(users) for role, users in role_users.items()},
        "role_inheritance": role_inheritance.copy(),
        "permissions": permissions_trie,
    }


def deserialize_rbac_state(data: Dict[str, Any]) -> Dict[str, Any]:
    """反序列化 RBAC 状态"""
    return {
        "case_sensitive": data.get("case_sensitive", True),
        "default_role": data.get("default_role"),
        "roles": {
            name: {
                "whitelist": set(role_data.get("whitelist", [])),
                "blacklist": set(role_data.get("blacklist", [])),
            }
            for name, role_data in data.get("roles", {}).items()
        },
        "users": {
            name: {
                "whitelist": set(user_data.get("whitelist", [])),
                "blacklist": set(user_data.get("blacklist", [])),
                "roles": list(user_data.get("roles", [])),
            }
            for name, user_data in data.get("users", {}).items()
        },
        "role_users": {
            role: set(users) for role, users in data.get("role_users", {}).items()
        },
        "role_inheritance": data.get("role_inheritance", {}),
        "permissions": data.get("permissions", {}),
    }
