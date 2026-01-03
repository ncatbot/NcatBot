"""
NapCat 配置管理模块

负责 NapCat 的 OneBot11、WebUI 等配置文件管理。
"""

import json
import shutil
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from ....utils import get_log, ncatbot_config
from ....utils.assets.default_webui_config import config as default_webui_config
from .platform import PlatformOps

LOG = get_log("ncatbot.core.adapter.nc.config")


class ConfigManager:
    """
    NapCat 配置管理器

    统一管理 OneBot11、WebUI 等配置文件的读写。
    """

    def __init__(self, platform_ops: Optional[PlatformOps] = None):
        self._platform = platform_ops or PlatformOps.create()
        self._napcat_dir = self._platform.napcat_dir
        self._config_dir = self._platform.config_dir

    @property
    def uin(self) -> str:
        """Bot QQ 号"""
        return str(ncatbot_config.bt_uin)

    # ==================== 路径属性 ====================

    @property
    def onebot_config_path(self) -> Path:
        """OneBot11 配置文件路径"""
        return self._config_dir / f"onebot11_{self.uin}.json"

    @property
    def webui_config_path(self) -> Path:
        """WebUI 配置文件路径"""
        return self._config_dir / "webui.json"

    @property
    def quick_login_script_path(self) -> Path:
        """快速登录脚本路径"""
        return self._napcat_dir / f"{self.uin}_quickLogin.bat"

    # ==================== JSON 文件操作 ====================

    @staticmethod
    def _read_json(path: Path) -> dict:
        """读取 JSON 文件"""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _write_json(path: Path, data: dict) -> None:
        """写入 JSON 文件"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    # ==================== OneBot11 配置 ====================

    def _build_expected_ws_server(self) -> dict:
        """构建期望的 WebSocket 服务器配置"""
        ws_port = urlparse(ncatbot_config.napcat.ws_uri).port or 3001
        ws_token = ncatbot_config.napcat.ws_token

        return {
            "name": "WsServer",
            "enable": True,
            "host": ncatbot_config.napcat.ws_listen_ip,
            "port": int(ws_port),
            "messagePostFormat": "array",
            "reportSelfMessage": ncatbot_config.napcat.report_self_message,
            "token": str(ws_token) if ws_token else "",
            "enableForcePushEvent": True,
            "debug": False,
            "heartInterval": 30000,
        }

    def _get_default_onebot_config(self) -> dict:
        """获取默认的 OneBot11 配置"""
        return {
            "network": {"websocketServers": []},
            "musicSignUrl": "",
            "enableLocalFile2Url": False,
            "parseMultMsg": ncatbot_config.napcat.report_forward_message_detail,
        }

    def configure_onebot(self) -> None:
        """配置 OneBot11"""
        # 读取或创建配置
        if self.onebot_config_path.exists():
            config = self._read_json(self.onebot_config_path)
            # 同步解析合并转发消息配置
            expected = ncatbot_config.napcat.report_forward_message_detail
            if config.get("parseMultMsg") != expected:
                LOG.warning(f"解析合并转发消息配置不匹配, 将修改为: {expected}")
                config["parseMultMsg"] = expected
        else:
            config = self._get_default_onebot_config()

        # 确保 network.websocketServers 存在
        if "network" not in config:
            config["network"] = {"websocketServers": []}
        if "websocketServers" not in config["network"]:
            config["network"]["websocketServers"] = []

        # 配置 WebSocket 服务器
        expected_server = self._build_expected_ws_server()
        servers = config["network"]["websocketServers"]

        if expected_server not in servers:
            # 检查端口冲突
            target_port = expected_server["port"]
            for server in servers[:]:  # 使用切片避免迭代时修改
                if server.get("port") == target_port:
                    prompt = f"端口 {target_port} 已存在配置, 是否强制覆盖 (y/n): "
                    if input(prompt).lower() == "y":
                        servers.remove(server)
                    else:
                        raise ValueError(f"端口 {target_port} 已存在, 请更改端口")
            servers.append(expected_server)

        # 写入配置
        try:
            self._write_json(self.onebot_config_path, config)
        except Exception as e:
            LOG.error(f"配置 OneBot 失败: {e}")
            raise

    # ==================== WebUI 配置 ====================

    def configure_webui(self) -> None:
        """配置 WebUI"""
        nc = ncatbot_config.napcat

        if not self.webui_config_path.exists():
            # 首次运行，创建配置
            LOG.warning("第一次运行 WebUI, 将创建配置文件")
            config = dict(default_webui_config)
            config["port"] = nc.webui_port if nc.enable_webui else 0
            config["token"] = nc.webui_token
            config["wsListenIp"] = nc.ws_listen_ip
            self._write_json(self.webui_config_path, config)
            return

        # 读取现有配置
        config = self._read_json(self.webui_config_path)
        updates = {}

        if not nc.enable_webui:
            LOG.warning("WebUI 已禁用")
            if config.get("port", 0) != 0:
                updates["port"] = 0
        else:
            # 检查并更新各项配置
            checks = [
                ("token", nc.webui_token, "WebUI 令牌"),
                ("port", nc.webui_port, "WebUI 端口"),
                ("wsListenIp", nc.ws_listen_ip, "WebUI 监听 IP"),
            ]
            for key, expected, name in checks:
                if config.get(key) != expected:
                    LOG.warning(f"{name}不匹配, 将修改为: {expected}")
                    updates[key] = expected

        # 应用更新
        if updates:
            config.update(updates)
            self._write_json(self.webui_config_path, config)

    # ==================== 快速登录脚本 ====================

    def configure_quick_login(self) -> None:
        """配置快速登录脚本（Windows）"""
        template = self._napcat_dir / "quickLoginExample.bat"
        if template.exists():
            shutil.copy(template, self.quick_login_script_path)

    # ==================== 主配置方法 ====================

    def configure_all(self) -> None:
        """配置所有 NapCat 设置"""
        self.configure_onebot()
        self.configure_quick_login()
        self.configure_webui()


def config_napcat() -> None:
    """配置 napcat 服务器（便捷函数）"""
    ConfigManager().configure_all()
