import urllib.parse
from dataclasses import dataclass, field
from typing import Optional


from ncatbot.utils.logger import get_log
from ncatbot.utils.status import status
from .base import BaseConfig
from .utils import strong_password_check, generate_strong_password

logger = get_log("Config")


@dataclass(frozen=False)
class NapCatConfig(BaseConfig):
    """NapCat 客户端配置。"""

    ws_uri: str = "ws://localhost:3001"
    ws_token: str = "NcatBot"
    ws_listen_ip: str = "localhost"
    webui_uri: str = "http://localhost:6099"
    webui_token: str = "NcatBot"
    enable_webui: bool = True
    check_napcat_update: bool = False
    stop_napcat: bool = False
    remote_mode: bool = False
    report_self_message: bool = False
    report_forward_message_detail: bool = True

    ws_host: Optional[str] = field(default=None, init=False)
    webui_host: Optional[str] = field(default=None, init=False)
    ws_port: Optional[int] = field(default=None, init=False)
    webui_port: Optional[int] = field(default=None, init=False)

    def _standardize_ws_uri(self) -> None:
        if not (self.ws_uri.startswith("ws://") or self.ws_uri.startswith("wss://")):
            self.ws_uri = f"ws://{self.ws_uri}"
        parsed = urllib.parse.urlparse(self.ws_uri)
        self.ws_host = parsed.hostname
        self.ws_port = parsed.port

    def _standardize_webui_uri(self) -> None:
        if not (
            self.webui_uri.startswith("http://")
            or self.webui_uri.startswith("https://")
        ):
            self.webui_uri = f"http://{self.webui_uri}"
        parsed = urllib.parse.urlparse(self.webui_uri)
        self.webui_host = parsed.hostname
        self.webui_port = parsed.port

    def _security_check(self) -> None:
        def generate_password():
            password = generate_strong_password()
            logger.info(f"已生成强密码: {password}")
            return password

        if self.ws_listen_ip == "0.0.0.0":
            if not strong_password_check(self.ws_token):
                logger.error(
                    "WS 令牌强度不足，请修改为强密码，或者修改 ws_listen_ip 本地监听 `localhost`"
                )
                if input("WS 令牌强度不足，是否修改为强密码？(y/n): ").lower() == "y":
                    self.ws_token = generate_password()
                else:
                    raise ValueError(
                        "WS 令牌强度不足, 请修改为强密码, 或者修改 ws_listen_ip 本地监听 `localhost`"
                    )

        if self.enable_webui:
            if not strong_password_check(self.webui_token):
                if (
                    input("WebUI 令牌强度不足，是否修改为强密码？(y/n): ").lower()
                    == "y"
                ):
                    self.webui_token = generate_password()
                else:
                    raise ValueError("WebUI 令牌强度不足, 请修改为强密码")

    def validate(self) -> None:
        self._standardize_ws_uri()
        self._standardize_webui_uri()
        self._security_check()

        if self.ws_host not in ["localhost", "127.0.0.1"]:
            logger.info("NapCat 服务不是本地的，请确保远程服务配置正确")

        if self.ws_listen_ip not in {"0.0.0.0", self.ws_host}:
            logger.warning("WS 监听地址与 WS 地址不匹配，连接可能失败")
        status.update_logger_level()
