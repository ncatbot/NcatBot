"""配置数据模型 - 纯 Pydantic 结构定义，不含业务逻辑。"""

import os
import warnings
from typing import Any, Dict, List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    field_validator,
    model_validator,
)

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

    def get_uri_with_token(self) -> str:
        """返回带 access_token 的 WebSocket URI。"""
        import urllib.parse

        encoded_token = urllib.parse.quote(self.ws_token, safe="")
        return f"{self.ws_uri}?access_token={encoded_token}"


# ==================== 日志配置 ====================


class LoggingConfig(BaseConfig):
    """日志相关配置。"""

    event_log_levels: Dict[str, str] = Field(
        default_factory=lambda: {"meta_event": "NONE"}
    )
    """事件日志级别覆盖。

    键为事件类型前缀（如 ``"meta_event.heartbeat"``、``"meta_event"``），
    值为日志级别字符串（``"DEBUG"``、``"INFO"``、``"WARNING"``、``"NONE"``）。
    ``NONE`` 表示完全不记录该事件。
    未匹配的事件默认以 INFO 级别记录。
    匹配时精确匹配优先，然后按前缀匹配。

    示例::

        logging:
          event_log_levels:
            meta_event.heartbeat: DEBUG
            meta_event.lifecycle: DEBUG
    """

    @field_validator("event_log_levels")
    @classmethod
    def _normalize_levels(cls, v: Dict[str, str]) -> Dict[str, str]:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "NONE"}
        result = {}
        for key, level in v.items():
            upper = level.upper()
            if upper not in valid:
                raise ValueError(
                    f"无效的日志级别 '{level}'（事件类型 '{key}'）。"
                    f"可选值: {', '.join(sorted(valid))}"
                )
            result[key] = upper
        return result


# ==================== 适配器配置条目 ====================


class AdapterEntry(BaseConfig):
    """单个适配器的声明。

    示例::

        adapters:
          - type: napcat
            platform: qq
            enabled: true
            config:
              ws_uri: ws://localhost:3001
              ws_token: napcat_ws
    """

    type: str
    """适配器类型名，对应注册表中的 key（如 ``"napcat"``、``"lagrange"``）。"""
    platform: str = ""
    """平台标识。留空则使用适配器类的默认 ``platform`` 属性。"""
    enabled: bool = True
    """是否启用此适配器。"""
    config: Dict[str, Any] = Field(default_factory=dict)
    """适配器专属配置，透传给适配器构造函数。"""


class Config(BaseConfig):
    """主配置模型 — 聚合所有子配置。"""

    adapters: List[AdapterEntry] = Field(default_factory=list)
    """适配器声明列表。"""
    napcat: Optional[NapCatConfig] = Field(default=None)
    """(deprecated) 旧版 NapCat 配置。请迁移到 adapters 列表。"""
    plugin: PluginConfig = Field(default_factory=PluginConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    bot_uin: str = DEFAULT_BOT_UIN
    root: str = DEFAULT_ROOT
    debug: bool = False
    enable_webui_interaction: bool = True
    github_proxy: Optional[str] = Field(
        default_factory=lambda: os.getenv("GITHUB_PROXY")
    )
    http_proxy: Optional[str] = Field(default_factory=lambda: os.getenv("HTTP_PROXY"))
    """标准 HTTP/SOCKS5 代理地址（如 ``http://127.0.0.1:7890``）。

    用于 Attachment 下载、MiscAPI 请求等。
    也可通过环境变量 ``HTTP_PROXY`` 设置。
    """
    check_ncatbot_update: bool = True
    skip_ncatbot_install_check: bool = False
    websocket_timeout: int = 15

    # 标记本次加载是否发生了旧格式迁移（供 ConfigManager 判断是否回写）
    _migrated: bool = PrivateAttr(default=False)

    @model_validator(mode="before")
    @classmethod
    def _migrate_legacy_napcat(cls, data: Any) -> Any:
        """向后兼容：将旧版 ``napcat:`` 顶层配置自动迁移到 ``adapters:`` 列表。"""
        if not isinstance(data, dict):
            return data

        has_adapters = bool(data.get("adapters"))
        has_napcat = "napcat" in data and data["napcat"] is not None

        if has_adapters:
            # 新格式，无需迁移
            return data

        if has_napcat:
            # 旧格式迁移
            napcat_cfg = data.pop("napcat")
            if isinstance(napcat_cfg, dict):
                data["adapters"] = [
                    {"type": "napcat", "platform": "qq", "config": napcat_cfg}
                ]
            else:
                data["adapters"] = [{"type": "napcat", "platform": "qq"}]
            data["__migrated_sentinel"] = True
            warnings.warn(
                "配置项 'napcat:' 已弃用，请迁移到 'adapters:' 列表格式。"
                "本次启动已自动迁移，配置文件将被自动更新。",
                DeprecationWarning,
                stacklevel=2,
            )
        else:
            # 两者都不存在 → 默认 napcat 适配器
            data["adapters"] = [{"type": "napcat", "platform": "qq"}]

        return data

    def model_post_init(self, __context: Any) -> None:
        # 从 extra 字段中提取迁移哨兵标记
        if self.__pydantic_extra__ and self.__pydantic_extra__.pop(
            "__migrated_sentinel", None
        ):
            self._migrated = True

    @field_validator("bot_uin", "root", mode="before")
    @classmethod
    def _coerce_to_str(cls, v) -> str:
        return str(v)

    @field_validator("websocket_timeout")
    @classmethod
    def _validate_timeout(cls, v: int) -> int:
        return max(1, v)

    def to_dict(self) -> dict:
        d = self.model_dump(exclude_none=True)
        # 排除内部标记
        d.pop("_migrated", None)
        d.pop("__migrated_sentinel", None)
        return d
