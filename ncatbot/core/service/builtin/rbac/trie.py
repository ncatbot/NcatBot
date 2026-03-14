"""
权限 Trie 树

用于高效存储和检索权限路径。
"""

from typing import Dict, List
from .path import PermissionPath


class PermissionTrie:
    """
    权限路径的 Trie 树实现

    用于高效存储和检索权限路径。
    """

    def __init__(self, case_sensitive: bool = True):
        self.root: Dict = {}
        self.case_sensitive = case_sensitive

    def _normalize(self, path: str) -> PermissionPath:
        """标准化路径"""
        if not self.case_sensitive:
            path = path.lower()
        return PermissionPath(path)

    def add(self, path: str) -> None:
        """添加权限路径"""
        ppath = self._normalize(path)

        if "*" in ppath.raw or "**" in ppath.raw:
            raise ValueError("添加的路径不能包含通配符 * 或 **")

        node = self.root
        for part in ppath:
            if part not in node:
                node[part] = {}
            node = node[part]

    def remove(self, path: str) -> None:
        """删除权限路径"""
        ppath = self._normalize(path)

        nodes = [(None, None, self.root)]
        node = self.root

        for part in ppath:
            if part not in node:
                return
            nodes.append((node, part, node[part]))
            node = node[part]

        for i in range(len(nodes) - 1, 0, -1):
            parent, key, current = nodes[i]
            if not current:
                del parent[key]
            else:
                break

    def exists(self, path: str, exact: bool = False) -> bool:
        """
        检查路径是否存在

        Args:
            path: 权限路径（支持通配符）
            exact: 是否精确匹配（路径必须是叶子节点）
        """
        ppath = self._normalize(path)
        return self._check(self.root, ppath.parts, 0, exact)

    def _check(self, node: dict, parts: tuple, index: int, exact: bool) -> bool:
        """递归检查路径"""
        if index >= len(parts):
            return not exact or not node

        part = parts[index]

        if part == "**":
            return True
        elif part == "*":
            return any(
                self._check(node[child], parts, index + 1, exact) for child in node
            )
        elif part in node:
            return self._check(node[part], parts, index + 1, exact)

        return False

    def to_dict(self) -> Dict:
        """导出为字典"""
        return self.root.copy()

    def from_dict(self, data: Dict) -> None:
        """从字典恢复"""
        self.root = data.copy() if data else {}

    def get_all_paths(self) -> List[str]:
        """获取所有路径"""
        paths = []
        self._collect_paths(self.root, [], paths)
        return paths

    list_all = get_all_paths

    def _collect_paths(self, node: dict, current: list, result: list) -> None:
        """递归收集所有路径"""
        if not node:
            result.append(".".join(current))
            return

        for key, child in node.items():
            self._collect_paths(child, current + [key], result)
