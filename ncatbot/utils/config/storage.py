"""配置文件存储 — YAML 读写。"""

from __future__ import annotations

import copy
import os
from typing import Any, Dict, Optional

import yaml

from ..logger import get_early_logger

from .models import Config

_log = get_early_logger("config.storage")

CONFIG_PATH = os.getenv(
    "NCATBOT_CONFIG_PATH",
    os.path.join(os.getcwd(), "config.yaml"),
)


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """递归合并：override 覆盖 base 中的同名字段。"""
    out = copy.deepcopy(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


class ConfigStorage:
    """配置文件的读写。"""

    def __init__(self, path: Optional[str] = None):
        self.path = path or CONFIG_PATH
        self._raw_snapshot: Dict[str, Any] = {}
        self._env_only_bot_uin: bool = False
        self._env_only_root: bool = False

    def load(self) -> Config:
        _log.debug("加载配置文件: %s", self.path)
        raw = self._load_raw()
        self._raw_snapshot = copy.deepcopy(raw) if isinstance(raw, dict) else {}
        data, self._env_only_bot_uin, self._env_only_root = self._apply_env_layer(
            self._raw_snapshot
        )
        return Config.model_validate(data)

    def save(
        self,
        config: Config,
        *,
        env_only_bot_uin: bool = False,
        env_only_root: bool = False,
    ) -> None:
        patch = config.to_dict()
        if env_only_bot_uin:
            patch.pop("bot_uin", None)
        if env_only_root:
            patch.pop("root", None)
        merged = _deep_merge(copy.deepcopy(self._raw_snapshot), patch)
        self._save_raw(merged)
        self._raw_snapshot = copy.deepcopy(merged)

    def exists(self) -> bool:
        return os.path.exists(self.path)

    def _load_raw(self) -> Dict[str, Any]:
        if not os.path.exists(self.path):
            _log.warning("配置文件不存在: %s", self.path)
            _log.info("配置文件不存在, 使用默认配置")
            return {}
        with open(self.path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @staticmethod
    def _apply_env_layer(
        raw: Dict[str, Any],
    ) -> tuple[Dict[str, Any], bool, bool]:
        """默认 < NCATBOT_* < yaml 中显式键。

        若某键在 yaml 中已存在（含 null），以 yaml 为准；否则可用环境变量。
        """
        data = dict(raw)
        env_only_bot_uin = False
        env_only_root = False

        if "bot_uin" not in raw:
            ev = os.getenv("NCATBOT_BOT_UIN")
            if ev is not None and str(ev).strip():
                data["bot_uin"] = str(ev).strip()
                env_only_bot_uin = True

        if "root" not in raw:
            ev = os.getenv("NCATBOT_ROOT")
            if ev is not None and str(ev).strip():
                data["root"] = str(ev).strip()
                env_only_root = True

        return data, env_only_bot_uin, env_only_root

    def _save_raw(self, data: Dict[str, Any]) -> None:
        dir_path = os.path.dirname(self.path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        tmp_path = f"{self.path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        os.replace(tmp_path, self.path)
        _log.debug("配置文件已保存: %s", self.path)
