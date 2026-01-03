"""
权限路径类

用于表示和匹配权限路径，支持通配符 * 和 **。
"""

from typing import Iterator, Union


class PermissionPath:
    """
    权限路径表示类

    支持点分隔的路径格式，如 "plugin.admin.kick"
    支持通配符：
    - * : 匹配单层任意节点
    - ** : 匹配任意深度的节点
    """

    SEPARATOR = "."

    def __init__(self, path: Union[str, "PermissionPath", list, tuple]):
        if isinstance(path, PermissionPath):
            self.raw = path.raw
            self.parts = path.parts
        elif isinstance(path, (list, tuple)):
            self.raw = self.SEPARATOR.join(path)
            self.parts = tuple(path)
        elif isinstance(path, str):
            self.raw = path
            self.parts = tuple(path.split(self.SEPARATOR))
        else:
            raise TypeError(f"不支持的类型: {type(path)}")

    def __repr__(self) -> str:
        return f"PermissionPath({self.raw!r})"

    def __str__(self) -> str:
        return self.raw

    def __eq__(self, other) -> bool:
        if isinstance(other, PermissionPath):
            return self.parts == other.parts
        elif isinstance(other, (list, tuple)):
            return self.parts == tuple(other)
        elif isinstance(other, str):
            return self.raw == other
        return False

    def __len__(self) -> int:
        return len(self.parts)

    def __getitem__(self, index: int) -> str:
        return self.parts[index]

    def __iter__(self) -> Iterator[str]:
        return iter(self.parts)

    def __contains__(self, node: str) -> bool:
        return node in self.parts

    def __hash__(self) -> int:
        return hash(self.parts)

    def get(self, index: int, default=None) -> str:
        """安全获取指定位置的节点"""
        try:
            return self.parts[index]
        except IndexError:
            return default

    def join(self, *paths: str) -> "PermissionPath":
        """连接路径"""
        new_path = self.raw
        for p in paths:
            if p:
                new_path = f"{new_path}{self.SEPARATOR}{p}"
        return PermissionPath(new_path)

    def matches(self, target: str) -> bool:
        """
        检查本路径（作为模式）是否匹配目标路径

        支持通配符：
        - * : 匹配单层
        - ** : 匹配任意深度
        """
        if self.raw == target:
            return True

        target_path = PermissionPath(target)

        # 不允许两边都有通配符
        if ("*" in self.raw or "**" in self.raw) and ("*" in target or "**" in target):
            raise ValueError("模式和目标不能同时使用通配符")

        # 确定哪个是模式，哪个是目标
        if "*" in self.raw or "**" in self.raw:
            pattern, target_p = self, target_path
        else:
            pattern, target_p = target_path, self

        return self._match_pattern(pattern.parts, target_p.parts, 0, 0)

    @staticmethod
    def _match_pattern(pattern: tuple, target: tuple, pi: int, ti: int) -> bool:
        """递归匹配模式"""
        while pi < len(pattern):
            if pattern[pi] == "**":
                # ** 匹配剩余所有
                return True
            elif pattern[pi] == "*":
                # * 匹配单个节点
                if ti >= len(target):
                    return False
                pi += 1
                ti += 1
            else:
                # 精确匹配
                if ti >= len(target) or pattern[pi] != target[ti]:
                    return False
                pi += 1
                ti += 1

        # 模式消耗完，检查目标是否也消耗完
        return ti >= len(target)
