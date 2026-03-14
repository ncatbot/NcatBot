"""配置管理器 — 对外暴露的主要接口。"""

import os
from typing import List, Optional

from ncatbot.utils.logger import get_early_logger

from .models import Config, NapCatConfig, PluginConfig, DEFAULT_BOT_UIN, DEFAULT_ROOT
from .storage import ConfigStorage
from .security import strong_password_check, generate_strong_token

_log = get_early_logger("config")


class ConfigValueError(Exception):
    def __init__(self, msg: str):
        super().__init__(f"配置项错误: {msg}")


class ConfigManager:
    """配置管理器。

    职责：
    - 配置的懒加载、重载、保存
    - 嵌套键的读写（支持 'napcat.ws_uri' 形式）
    - 安全检查与修复
    - 目录创建等副作用操作
    """

    def __init__(self, path: Optional[str] = None):
        self._storage = ConfigStorage(path)
        self._config: Optional[Config] = None

    @property
    def config(self) -> Config:
        if self._config is None:
            self._config = self._storage.load()
            _log.info("配置加载完成")
        return self._config

    def reload(self) -> Config:
        self._config = self._storage.load()
        _log.info("配置已重新加载")
        return self._config

    def save(self) -> None:
        if self._config is not None:
            self._storage.save(self._config)

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

    # ---- 子配置访问 ----

    @property
    def napcat(self) -> NapCatConfig:
        return self.config.napcat

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
        return self.config.debug

    @debug.setter
    def debug(self, value: bool) -> None:
        self.config.debug = value

    def update_napcat(self, **kwargs) -> None:
        """从键值对批量更新 napcat 子配置。

        用法：ncatbot_config.update_napcat(ws_uri="ws://...", ws_token="...")
        通过 Pydantic validate_assignment 自动验证每个字段。
        """
        for key, value in kwargs.items():
            if not hasattr(self.napcat, key):
                raise ConfigValueError(f"NapCatConfig 不存在字段: {key}")
            setattr(self.napcat, key, value)

    # ---- 便捷方法 ----

    def get_uri_with_token(self) -> str:
        return f"{self.napcat.ws_uri}?access_token={self.napcat.ws_token}"

    def is_local(self) -> bool:
        return self.napcat.ws_host in ("localhost", "127.0.0.1")

    def is_default_uin(self) -> bool:
        return self.config.bot_uin == DEFAULT_BOT_UIN

    def is_default_root(self) -> bool:
        return self.config.root == DEFAULT_ROOT

    # ---- 安全检查 ----

    def get_security_issues(self, auto_fix: bool = True) -> List[str]:
        """检查安全性问题。auto_fix=True 时自动修复弱 token。"""
        issues = []

        if self.napcat.ws_listen_ip == "0.0.0.0":
            if not strong_password_check(self.napcat.ws_token):
                if auto_fix:
                    self.napcat.ws_token = generate_strong_token()
                    _log.warning("WS 令牌强度不足, 已自动生成新令牌")
                else:
                    issues.append("WS 令牌强度不足")

        if self.napcat.enable_webui:
            if not strong_password_check(self.napcat.webui_token):
                if auto_fix:
                    self.napcat.webui_token = generate_strong_token()
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
        d = self.plugin.plugins_dir
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
