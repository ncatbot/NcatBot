"""
登录认证模块

负责 NapCat WebUI 认证和 QQ 登录管理。
"""

import time
from enum import IntEnum
from typing import Optional, TYPE_CHECKING

import qrcode

from ncatbot.utils import get_log
from .webui_client import (
    WebUIClient,
    WebUIAuthError,
    WebUIConnectionError as _WebUIConnectionError,
)

if TYPE_CHECKING:
    from ncatbot.utils.config.models import NapCatConfig

LOG = get_log("AuthHandler")


class LoginStatus(IntEnum):
    OK = 0
    NOT_LOGGED_IN = 1
    UIN_MISMATCH = 2
    ABNORMAL = 3


class QQLoginedError(Exception):
    pass


class AuthError(Exception):
    pass


class WebUIConnectionError(AuthError):
    pass


class LoginTimeoutError(AuthError):
    pass


class AuthHandler:
    """登录认证处理器

    Parameters
    ----------
    napcat_config:
        NapCatConfig 实例。
    bot_uin:
        目标 QQ 号。
    """

    QRCODE_LOGIN_TIMEOUT = 60
    QRCODE_FETCH_TIMEOUT = 15

    def __init__(
        self,
        napcat_config: "NapCatConfig",
        bot_uin: str = "",
        webui_client: Optional[WebUIClient] = None,
    ):
        self._napcat_config = napcat_config
        self._bot_uin = bot_uin

        if webui_client is not None and webui_client.is_connected:
            self._client = webui_client
        else:
            self._client = WebUIClient(napcat_config)
            try:
                self._client.connect()
            except _WebUIConnectionError as e:
                raise WebUIConnectionError(str(e)) from e
            except WebUIAuthError as e:
                raise AuthError(str(e)) from e

    def _api_call(
        self,
        endpoint: str,
        payload: Optional[dict] = None,
        timeout: int = 5,
    ) -> dict:
        return self._client.api_call(endpoint, payload, timeout)

    # ==================== 登录状态检查 ====================

    def check_login_status(self) -> bool:
        try:
            data = self._api_call("/api/QQLogin/CheckLoginStatus")
            return data.get("data", {}).get("isLogin", False)
        except Exception:
            LOG.warning("检查登录状态超时, 默认未登录")
            return False

    def get_login_info(self) -> Optional[dict]:
        try:
            return self._api_call("/api/QQLogin/GetQQLoginInfo").get("data", {})
        except Exception:
            LOG.warning("获取登录信息超时")
            return None

    def report_status(self) -> LoginStatus:
        if not self.check_login_status():
            return LoginStatus.NOT_LOGGED_IN

        info = self.get_login_info()
        if not info:
            return LoginStatus.ABNORMAL

        target_uin = self._bot_uin
        current_uin = str(info.get("uin", ""))
        is_online = info.get("online", False)

        if current_uin != target_uin:
            return LoginStatus.UIN_MISMATCH
        if not is_online:
            return LoginStatus.ABNORMAL

        return LoginStatus.OK

    # ==================== 快速登录 ====================

    def get_quick_login_list(self) -> list:
        try:
            data = self._api_call("/api/QQLogin/GetQuickLoginListNew")
            records = data.get("data", [])
            return [str(r["uin"]) for r in records if r.get("isQuickLogin")]
        except Exception:
            LOG.warning("获取快速登录列表失败")
            return []

    def quick_login(self) -> bool:
        uin = self._bot_uin
        quick_list = self.get_quick_login_list()
        LOG.info(f"快速登录列表: {quick_list}")

        if uin not in quick_list:
            return False

        LOG.info("正在发送快速登录请求...")
        try:
            status = self._api_call(
                "/api/QQLogin/SetQuickLogin",
                payload={"uin": uin},
                timeout=8,
            )
            success = status.get("message", "") in ["success", "QQ Is Logined"]
            if not success:
                LOG.warning(f"快速登录请求失败: {status}")
            return success
        except Exception:
            LOG.warning("快速登录失败")
            return False

    # ==================== 二维码登录 ====================

    def get_qrcode_url(self) -> str:
        expire_time = time.time() + self.QRCODE_FETCH_TIMEOUT

        while time.time() < expire_time:
            time.sleep(0.2)
            try:
                data = self._api_call("/api/QQLogin/GetQQLoginQrcode")
                if data.get("message") == "QQ Is Logined":
                    raise QQLoginedError()

                qrcode_url = data.get("data", {}).get("qrcode")
                if qrcode_url:
                    return qrcode_url
            except QQLoginedError:
                raise
            except Exception:
                pass

        raise LoginTimeoutError("获取二维码超时")

    @staticmethod
    def show_qrcode(url: str) -> None:
        qr = qrcode.QRCode()
        qr.add_data(url)
        qr.print_ascii(invert=True)

    def qrcode_login(self) -> None:
        try:
            try:
                qrcode_url = self.get_qrcode_url()
                self.show_qrcode(qrcode_url)
            except QQLoginedError:
                if self.check_login_status():
                    LOG.info("QQ 已登录（账号验证由 launcher 处理）")
                    return
                LOG.error("NapCat 报告 QQ 已登录但状态检查不一致, 请物理重启本机")
                raise AuthError("登录状态异常")

            expire_time = time.time() + self.QRCODE_LOGIN_TIMEOUT
            warn_time = time.time() + 30

            while not self.check_login_status():
                if time.time() > expire_time:
                    LOG.error("登录超时, 请重新操作")
                    raise LoginTimeoutError("登录超时")
                if time.time() > warn_time:
                    LOG.warning("二维码即将失效, 请尽快扫码登录")
                    warn_time += 60

            LOG.info("扫码登录成功")

        except (QQLoginedError, LoginTimeoutError, AuthError):
            raise
        except Exception as e:
            LOG.error(f"二维码登录出错: {e}")
            raise AuthError("登录失败")

    # ==================== 主登录流程 ====================

    def login(self) -> None:
        """通过 WebUI 执行登录 (快速登录 → 二维码)。

        仅在 launcher 确认 WS 不通 (即未登录) 时调用。
        """
        if self.quick_login():
            LOG.info("快速登录成功")
            return

        self.qrcode_login()
