"""配置文件存储 — YAML 读写。"""

import os
from typing import Any, Dict, Optional

import yaml

from ncatbot.utils.logger import get_early_logger

from .models import Config

_log = get_early_logger("config.storage")

CONFIG_PATH = os.getenv(
    "NCATBOT_CONFIG_PATH",
    os.path.join(os.getcwd(), "config.yaml"),
)


class ConfigStorage:
    """配置文件的读写。"""

    def __init__(self, path: Optional[str] = None):
        self.path = path or CONFIG_PATH

    def load(self) -> Config:
        _log.debug("加载配置文件: %s", self.path)
        data = self._load_raw()
        return Config.model_validate(data)

    def save(self, config: Config) -> None:
        self._save_raw(config.to_dict())

    def exists(self) -> bool:
        return os.path.exists(self.path)

    def _load_raw(self) -> Dict[str, Any]:
        if not os.path.exists(self.path):
            _log.info("配置文件不存在, 使用默认配置: %s", self.path)
            return {}
        with open(self.path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _save_raw(self, data: Dict[str, Any]) -> None:
        dir_path = os.path.dirname(self.path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        tmp_path = f"{self.path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        os.replace(tmp_path, self.path)
        _log.debug("配置文件已保存: %s", self.path)
