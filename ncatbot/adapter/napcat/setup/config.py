"""
NapCat 配置管理

负责 NapCat 的 OneBot11、WebUI 等配置文件管理。
"""

import json
import shutil
from pathlib import Path
from typing import Optional, TYPE_CHECKING
from urllib.parse import urlparse

from ncatbot.utils import get_log, confirm
from .default_webui_config import config as default_webui_config
from .platform import PlatformOps

if TYPE_CHECKING:
    from ncatbot.utils.config.models import NapCatConfig

LOG = get_log("NapCatConfigManager")


class NapCatConfigManager:
    """NapCat 配置管理器

    Parameters
    ----------
    platform_ops:
        平台操作实例。
    napcat_config:
        NapCatConfig 实例，由 NapCatAdapter 注入。
    bot_uin:
        目标 QQ 号。
    """

    def __init__(
        self,
        platform_ops: Optional[PlatformOps] = None,
        napcat_config: Optional["NapCatConfig"] = None,
        bot_uin: str = "",
    ):
        self._platform = platform_ops or PlatformOps.create()
        self._napcat_dir = self._platform.napcat_dir
        self._config_dir = self._platform.config_dir
        self._napcat_config = napcat_config
        self._bot_uin = bot_uin

    @property
    def uin(self) -> str:
        return self._bot_uin

    # ==================== 路径属性 ====================

    @property
    def onebot_config_path(self) -> Path:
        return self._config_dir / f"onebot11_{self.uin}.json"

    @property
    def webui_config_path(self) -> Path:
        return self._config_dir / "webui.json"

    @property
    def quick_login_script_path(self) -> Path:
        return self._napcat_dir / f"{self.uin}_quickLogin.bat"

    # ==================== JSON 文件操作 ====================

    @staticmethod
    def _read_json(path: Path) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _write_json(path: Path, data: dict) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    # ==================== OneBot11 配置 ====================

    def _build_expected_ws_server(self) -> dict:
        nc = self._napcat_config
        ws_port = urlparse(nc.ws_uri).port or 3001
        ws_token = nc.ws_token

        return {
            "name": "WsServer",
            "enable": True,
            "host": nc.ws_listen_ip,
            "port": int(ws_port),
            "messagePostFormat": "array",
            "reportSelfMessage": False,
            "token": str(ws_token) if ws_token else "",
            "enableForcePushEvent": True,
            "debug": False,
            "heartInterval": 30000,
        }

    def _get_default_onebot_config(self) -> dict:
        return {
            "network": {"websocketServers": []},
            "musicSignUrl": "",
            "enableLocalFile2Url": False,
            "parseMultMsg": True,
        }

    def configure_onebot(self) -> None:
        if self.onebot_config_path.exists():
            config = self._read_json(self.onebot_config_path)
        else:
            config = self._get_default_onebot_config()

        if "network" not in config:
            config["network"] = {"websocketServers": []}
        if "websocketServers" not in config["network"]:
            config["network"]["websocketServers"] = []

        expected_server = self._build_expected_ws_server()
        servers = config["network"]["websocketServers"]

        if expected_server not in servers:
            target_port = expected_server["port"]
            for server in servers[:]:
                if server.get("port") == target_port:
                    if confirm(
                        f"端口 {target_port} 已存在配置, 是否强制覆盖?", default=False
                    ):
                        servers.remove(server)
                    else:
                        raise ValueError(f"端口 {target_port} 已存在, 请更改端口")
            servers.append(expected_server)

        try:
            self._write_json(self.onebot_config_path, config)
        except Exception as e:
            LOG.error(f"配置 OneBot 失败: {e}")
            raise

    # ==================== WebUI 配置 ====================

    def configure_webui(self) -> None:
        nc = self._napcat_config

        if not self.webui_config_path.exists():
            LOG.warning("第一次运行 WebUI, 将创建配置文件")
            config = dict(default_webui_config)
            config["port"] = nc.webui_port if nc.enable_webui else 0
            config["token"] = nc.webui_token
            config["wsListenIp"] = nc.ws_listen_ip
            self._write_json(self.webui_config_path, config)
            return

        config = self._read_json(self.webui_config_path)
        updates = {}

        if not nc.enable_webui:
            LOG.warning("WebUI 已禁用")
            if config.get("port", 0) != 0:
                updates["port"] = 0
        else:
            checks = [
                ("token", nc.webui_token, "WebUI 令牌"),
                ("port", nc.webui_port, "WebUI 端口"),
                ("wsListenIp", nc.ws_listen_ip, "WebUI 监听 IP"),
            ]
            for key, expected, name in checks:
                if config.get(key) != expected:
                    LOG.warning(f"{name}不匹配, 将修改为: {expected}")
                    updates[key] = expected

        if updates:
            config.update(updates)
            self._write_json(self.webui_config_path, config)

    # ==================== 快速登录脚本 ====================

    def configure_quick_login(self) -> None:
        template = self._napcat_dir / "quickLoginExample.bat"
        if template.exists():
            shutil.copy(template, self.quick_login_script_path)

    # ==================== 主配置方法 ====================

    def configure_all(self) -> None:
        self.configure_onebot()
        self.configure_quick_login()
        self.configure_webui()
