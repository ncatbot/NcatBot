"""
代码迁移框架 - 基础类型和数据结构
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class MigrationResult:
    """迁移结果"""

    file_path: Path
    original_content: str
    migrated_content: str
    changes: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return self.original_content != self.migrated_content


class MigrationRule(ABC):
    """迁移规则基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """规则名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """规则描述"""
        pass

    @abstractmethod
    def apply(self, content: str, file_path: Path) -> Tuple[str, List[str]]:
        """
        应用迁移规则

        Args:
            content: 文件内容
            file_path: 文件路径

        Returns:
            (迁移后的内容, 变更描述列表)
        """
        pass
