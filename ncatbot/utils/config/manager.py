"""配置管理器 — 对外暴露的主要接口。"""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass
from typing import Any, List, Optional

from ..logger import get_early_logger

from .models import (
    AdapterEntry,
    Config,
    NapCatConfig,
    PluginConfig,
    DEFAULT_BOT_UIN,
    DEFAULT_ROOT,
)
from .storage import ConfigStorage
from .security import strong_password_check, generate_strong_token

_log = get_early_logger("config")


class ConfigValueError(Exception):
    def __init__(self, msg: str):
        super().__init__(f"配置项错误: {msg}")


class _MissingType:
    """apply_runtime_overrides 未传入某参数时使用。"""

    __slots__ = ()


MISSING = _MissingType()


@dataclass
class RuntimeOverrides:
    debug: Optional[bool] = None
    plugins_dir: Optional[str] = None
    hot_reload: Optional[bool] = None


def _truthy_env(name: str) -> bool:
    v = os.getenv(name)
    if v is None:
        return False
    return v.strip().lower() in ("1", "true", "yes", "on")


class ConfigManager:
    """配置管理器。

    职责：
    - 配置的懒加载、重载、保存
    - 嵌套键的读写（支持 'napcat.ws_uri' 形式）
    - 运行时覆盖（debug / plugins_dir / hot_reload）：不写回 yaml
    - 安全检查与修复
    - 旧格式迁移时自动回写配置文件
    """

    def __init__(self, path: Optional[str] = None):
        self._storage = ConfigStorage(path)
        self._config: Optional[Config] = None
        self._runtime = RuntimeOverrides()

    @property
    def config(self) -> Config:
        if self._config is None:
            self._config = self._storage.load()
            _log.info("配置加载完成")
            # 旧格式迁移后自动回写
            if getattr(self._config, "_migrated", False):
                _log.info("检测到旧版 napcat 配置格式，自动回写为 adapters 格式")
                self._config._migrated = False
                self.save()
        return self._config

    def reload(self) -> Config:
        self._config = self._storage.load()
        _log.info("配置已重新加载")
        if getattr(self._config, "_migrated", False):
            self._config._migrated = False
            self.save()
        return self._config

    def save(self) -> None:
        if self._config is not None:
            self._storage.save(
                self._config,
                env_only_bot_uin=self._storage._env_only_bot_uin,
                env_only_root=self._storage._env_only_root,
            )

    def apply_runtime_overrides(
        self,
        *,
        debug: Any = MISSING,
        plugins_dir: Any = MISSING,
        hot_reload: Any = MISSING,
    ) -> None:
        """进程内覆盖（CLI / BotClient 传参），不写入 config.yaml。"""
        if debug is not MISSING:
            self._runtime.debug = debug
        if plugins_dir is not MISSING:
            self._runtime.plugins_dir = plugins_dir
        if hot_reload is not MISSING:
            self._runtime.hot_reload = hot_reload

    def clear_runtime_overrides(self) -> None:
        self._runtime = RuntimeOverrides()

    @property
    def effective_debug(self) -> bool:
        if self._runtime.debug is not None:
            return self._runtime.debug
        return self.config.debug

    def effective_plugins_dir(self) -> str:
        if self._runtime.plugins_dir:
            return self._runtime.plugins_dir
        return self.plugin.plugins_dir

    def effective_hot_reload(self) -> bool:
        if self._runtime.hot_reload is not None:
            return self._runtime.hot_reload
        return self.config.plugin.hot_reload

    def effective_skip_napcat_install_confirm(self) -> bool:
        return self.config.skip_napcat_install_confirm or _truthy_env(
            "NCATBOT_SKIP_NAPCAT_INSTALL_CONFIRM"
        )

    def effective_skip_pip_install_confirm(self) -> bool:
        return self.config.plugin.skip_pip_install_confirm or _truthy_env(
            "NCATBOT_SKIP_PIP_INSTALL_CONFIRM"
        )

    # ---- 通用读写 ----

    def update_value(self, key: str, value) -> None:
        """更新配置项。支持直接键 ('debug') 和嵌套键 ('napcat.ws_uri')。"""
        full_key = self.config.get_field_paths().get(key, key)
        parts = full_key.split(".")
        obj = self.config
        for part in parts[:-1]:
            if not hasattr(obj, part):
                raise ConfigValueError(f"未知的配置项: {key}")
            obj = getattr(obj, part)
        final = parts[-1]
        if not hasattr(obj, final):
            raise ConfigValueError(f"未知的配置项: {key}")
        setattr(obj, final, value)
        if final == "bot_uin":
            self._storage._env_only_bot_uin = False
        if final == "root":
            self._storage._env_only_root = False

    # ---- 适配器配置访问 ----

    def get_adapter_configs(self) -> List[AdapterEntry]:
        """返回所有已启用的适配器配置条目。"""
        return [e for e in self.config.adapters if e.enabled]

    def get_adapter_config(self, adapter_type: str) -> Optional[AdapterEntry]:
        """返回指定类型的第一个适配器配置条目。"""
        for e in self.config.adapters:
            if e.type == adapter_type:
                return e
        return None

    # ---- 子配置访问 ----

    @property
    def napcat(self) -> NapCatConfig:
        """(deprecated) 返回第一个 napcat 适配器的配置。请使用 get_adapter_config('napcat')。"""
        warnings.warn(
            "ConfigManager.napcat 已弃用，请使用 get_adapter_config('napcat')",
            DeprecationWarning,
            stacklevel=2,
        )
        entry = self.get_adapter_config("napcat")
        if entry:
            return NapCatConfig.model_validate(entry.config)
        return NapCatConfig()

    @property
    def plugin(self) -> PluginConfig:
        return self.config.plugin

    @property
    def bot_uin(self) -> str:
        return self.config.bot_uin

    @property
    def root(self) -> str:
        return self.config.root

    @property
    def debug(self) -> bool:
        return self.effective_debug

    @debug.setter
    def debug(self, value: bool) -> None:
        self.config.debug = value
        self._runtime.debug = None

    @property
    def websocket_timeout(self) -> int:
        return self.config.websocket_timeout

    def update_napcat(self, **kwargs) -> None:
        """(deprecated) 批量更新 napcat 子配置。请直接修改 adapters 配置。"""
        warnings.warn(
            "ConfigManager.update_napcat() 已弃用",
            DeprecationWarning,
            stacklevel=2,
        )
        entry = self.get_adapter_config("napcat")
        if entry is None:
            raise ConfigValueError("配置中未找到 napcat 适配器")
        for key, value in kwargs.items():
            entry.config[key] = value

    # ---- 便捷方法 ----

    def get_uri_with_token(self) -> str:
        """(deprecated) 请通过适配器实例访问。"""
        warnings.warn(
            "ConfigManager.get_uri_with_token() 已弃用",
            DeprecationWarning,
            stacklevel=2,
        )
        nc = self.napcat
        return nc.get_uri_with_token()

    def is_local(self) -> bool:
        entry = self.get_adapter_config("napcat")
        if entry:
            nc = NapCatConfig.model_validate(entry.config)
            return nc.ws_host in ("localhost", "127.0.0.1")
        return True

    def is_default_uin(self) -> bool:
        return self.config.bot_uin == DEFAULT_BOT_UIN

    def is_default_root(self) -> bool:
        return self.config.root == DEFAULT_ROOT

    # ---- 安全检查 ----

    def get_security_issues(self, auto_fix: bool = True) -> List[str]:
        """检查安全性问题。auto_fix=True 时自动修复弱 token。"""
        issues = []

        for entry in self.config.adapters:
            if entry.type != "napcat":
                continue
            nc = NapCatConfig.model_validate(entry.config)
            if nc.ws_listen_ip == "0.0.0.0":
                if not strong_password_check(nc.ws_token):
                    if auto_fix:
                        entry.config["ws_token"] = generate_strong_token()
                        _log.warning("WS 令牌强度不足, 已自动生成新令牌")
                    else:
                        issues.append("WS 令牌强度不足")

            if nc.enable_webui:
                if not strong_password_check(nc.webui_token):
                    if auto_fix:
                        entry.config["webui_token"] = generate_strong_token()
                        _log.warning("WebUI 令牌强度不足, 已自动生成新令牌")
                    else:
                        issues.append("WebUI 令牌强度不足")

        return issues

    def get_issues(self) -> List[str]:
        """返回所有配置问题（安全 + 必填项）。"""
        issues = self.get_security_issues()
        if self.is_default_uin():
            issues.append("机器人 QQ 号未配置")
        if self.is_default_root():
            issues.append("管理员 QQ 号未配置")
        return issues

    def ensure_plugins_dir(self) -> None:
        """确保插件目录存在。"""
        d = self.effective_plugins_dir()
        if not os.path.exists(d):
            os.makedirs(d)


# ---- 单例 ----

_default_manager: Optional[ConfigManager] = None


def get_config_manager(path: Optional[str] = None) -> ConfigManager:
    """获取配置管理器单例。"""
    global _default_manager
    if _default_manager is None or path is not None:
        _default_manager = ConfigManager(path)
    return _default_manager
