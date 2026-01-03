"""
测试配置加载器

从 JSON 文件加载测试配置和数据。
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional


class TestConfig:
    """测试配置管理器"""

    def __init__(self, config_dir: Path = None):
        """
        Args:
            config_dir: 配置目录路径，默认为 data 目录
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / "data"
        self.config_dir = config_dir
        self._config: Dict[str, Any] = {}
        self._data: Dict[str, Dict[str, Any]] = {}

    def load(self, config_file: str = "config.json") -> "TestConfig":
        """
        加载主配置文件

        Args:
            config_file: 配置文件名

        Returns:
            self，支持链式调用
        """
        config_path = self.config_dir / config_file
        if not config_path.exists():
            example_path = self.config_dir / "config.example.json"
            raise FileNotFoundError(
                f"配置文件 {config_path} 不存在。\n"
                f"请复制 {example_path} 为 {config_path} 并填写实际值。"
            )

        with open(config_path, "r", encoding="utf-8") as f:
            self._config = json.load(f)

        # 加载关联的数据文件
        data_files = self._config.get("test_data_files", {})
        for key, filename in data_files.items():
            self._load_data_file(key, filename)

        return self

    def _load_data_file(self, key: str, filename: str) -> None:
        """加载单个数据文件"""
        data_path = self.config_dir / filename
        if data_path.exists():
            with open(data_path, "r", encoding="utf-8") as f:
                self._data[key] = json.load(f)

    @property
    def targets(self) -> Dict[str, Any]:
        """获取测试目标配置"""
        return self._config.get("targets", {})

    @property
    def test_group(self) -> Optional[int]:
        """获取测试群号"""
        return self.targets.get("111222333")

    @property
    def test_user(self) -> Optional[int]:
        """获取测试用户 QQ 号"""
        return self.targets.get("444444444")

    @property
    def test_admin_group(self) -> Optional[int]:
        """获取测试管理员群号"""
        return self.targets.get("test_admin_group")

    @property
    def options(self) -> Dict[str, Any]:
        """获取测试选项"""
        return self._config.get("options", {})

    def get_data(self, category: str, *keys: str, default: Any = None) -> Any:
        """
        获取测试数据

        Args:
            category: 数据类别 (messages, friends, groups, files)
            keys: 嵌套的键路径
            default: 默认值

        Returns:
            数据值

        Example:
            config.get_data("messages", "text_messages", "private", "simple")
        """
        data = self._data.get(category, {})
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key, default)
            else:
                return default
        return data

    def to_legacy_config(self) -> Dict[str, Any]:
        """
        转换为旧版配置格式（兼容现有测试）

        Returns:
            旧版配置字典
        """
        return {
            "target_group": self.test_group,
            "target_user": self.test_user,
            "last_message_id": None,
            **self._data,
        }


def load_test_config(config_dir: Path = None) -> TestConfig:
    """
    便捷函数：加载测试配置

    Args:
        config_dir: 配置目录

    Returns:
        TestConfig 实例
    """
    config = TestConfig(config_dir)
    return config.load()
