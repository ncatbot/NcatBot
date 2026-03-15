"""配置数据模型 - 纯 Pydantic 结构定义，不含业务逻辑。"""

import os
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ==================== 常量 ====================

DEFAULT_BOT_UIN = "123456"
DEFAULT_ROOT = "123456"


# ==================== 基础配置类 ====================


class BaseConfig(BaseModel):
    """配置基类。"""

    model_config = ConfigDict(validate_assignment=True, extra="allow")

    def get_field_paths(self, prefix: str = "") -> Dict[str, str]:
        """递归获取所有字段的点分路径映射。"""
        paths = {}
        for field_name in type(self).model_fields:
            current = f"{prefix}.{field_name}" if prefix else field_name
            paths[field_name] = current
            value = getattr(self, field_name)
            if isinstance(value, BaseConfig):
                paths.update(value.get_field_paths(current))
        return paths

    def to_dict(self) -> dict:
        return self.model_dump()


# ==================== 子配置模型 ====================


class PluginConfig(BaseConfig):
    """插件相关配置。"""

    plugins_dir: str = Field(default="plugins")
    plugin_whitelist: List[str] = Field(default_factory=list)
    plugin_blacklist: List[str] = Field(default_factory=list)
    load_plugin: bool = False
    auto_install_pip_deps: bool = True
    """是否允许自动安装插件声明的 pip 依赖（仍会先询问用户确认）。"""
    plugin_configs: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    """全局配置文件中的插件配置覆盖。键为插件名，值为配置字典。"""

    @field_validator("plugins_dir")
    @classmethod
    def _validate_plugins_dir(cls, v: str) -> str:
        return v if v else "plugins"


class NapCatConfig(BaseConfig):
    """NapCat 客户端连接配置。"""

    ws_uri: str = "ws://localhost:3001"
    ws_token: str = "napcat_ws"
    ws_listen_ip: str = "localhost"
    webui_uri: str = "http://localhost:6099"
    webui_token: str = "napcat_webui"
    enable_webui: bool = True
    enable_update_check: bool = False
    stop_napcat: bool = False
    skip_setup: bool = False

    @field_validator("ws_uri")
    @classmethod
    def _validate_ws_uri(cls, v: str) -> str:
        if not v:
            return "ws://localhost:3001"
        if not (v.startswith("ws://") or v.startswith("wss://")):
            return f"ws://{v}"
        return v

    @field_validator("webui_uri")
    @classmethod
    def _validate_webui_uri(cls, v: str) -> str:
        if not v:
            return "http://localhost:6099"
        if not (v.startswith("http://") or v.startswith("https://")):
            return f"http://{v}"
        return v

    @property
    def ws_host(self) -> Optional[str]:
        import urllib.parse

        return urllib.parse.urlparse(self.ws_uri).hostname

    @property
    def ws_port(self) -> Optional[int]:
        import urllib.parse

        return urllib.parse.urlparse(self.ws_uri).port

    @property
    def webui_host(self) -> Optional[str]:
        import urllib.parse

        return urllib.parse.urlparse(self.webui_uri).hostname

    @property
    def webui_port(self) -> Optional[int]:
        import urllib.parse

        return urllib.parse.urlparse(self.webui_uri).port


class Config(BaseConfig):
    """主配置模型 — 聚合所有子配置。"""

    napcat: NapCatConfig = Field(default_factory=NapCatConfig)
    plugin: PluginConfig = Field(default_factory=PluginConfig)
    bot_uin: str = DEFAULT_BOT_UIN
    root: str = DEFAULT_ROOT
    debug: bool = False
    enable_webui_interaction: bool = True
    github_proxy: Optional[str] = Field(
        default_factory=lambda: os.getenv("GITHUB_PROXY")
    )
    check_ncatbot_update: bool = True
    skip_ncatbot_install_check: bool = False
    websocket_timeout: int = 15

    @field_validator("bot_uin", "root", mode="before")
    @classmethod
    def _coerce_to_str(cls, v) -> str:
        return str(v)

    @field_validator("websocket_timeout")
    @classmethod
    def _validate_timeout(cls, v: int) -> int:
        return max(1, v)

    def to_dict(self) -> dict:
        return self.model_dump(exclude_none=True)
