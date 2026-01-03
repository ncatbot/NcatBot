"""
登录认证模块

负责 NapCat WebUI 认证和 QQ 登录管理。
"""

import hashlib
import time
import traceback
from enum import IntEnum
from typing import Optional

import qrcode

from ....utils import NAPCAT_WEBUI_SALT, get_log, ncatbot_config, post_json

LOG = get_log("ncatbot.core.adapter.nc.auth")


class LoginStatus(IntEnum):
    """登录状态枚举"""

    OK = 0  # 已正确登录
    NOT_LOGGED_IN = 1  # 未登录
    UIN_MISMATCH = 2  # 登录的 QQ 号与配置不匹配
    ABNORMAL = 3  # 登录状态异常，需要重启


class QQLoginedError(Exception):
    """QQ 已登录异常"""

    pass


class AuthError(Exception):
    """认证错误基类"""

    pass


class WebUIConnectionError(AuthError):
    """WebUI 连接失败"""

    pass


class LoginTimeoutError(AuthError):
    """登录超时"""

    pass


class AuthHandler:
    """
    登录认证处理器

    负责:
    - WebUI 认证
    - 快速登录
    - 二维码登录
    - 登录状态检查
    """

    # WebUI 连接超时时间
    WEBUI_CONNECT_TIMEOUT = 90
    # 二维码登录超时时间
    QRCODE_LOGIN_TIMEOUT = 60
    # 获取二维码超时时间
    QRCODE_FETCH_TIMEOUT = 15

    def __init__(self):
        self._base_uri = (
            f"http://{ncatbot_config.napcat.webui_host}:"
            f"{ncatbot_config.napcat.webui_port}"
        )
        self._header: Optional[dict] = None
        self._connect_webui()

    def _connect_webui(self) -> None:
        """连接并认证 WebUI"""
        expire_time = time.time() + self.WEBUI_CONNECT_TIMEOUT

        while time.time() < expire_time:
            time.sleep(0.02)
            try:
                credential = self._try_auth()
                if credential:
                    self._header = {"Authorization": f"Bearer {credential}"}
                    LOG.debug("成功连接到 WebUI")
                    return
            except Exception as e:
                if time.time() >= expire_time:
                    self._handle_connection_error(e)
                # 继续重试
                continue

        raise WebUIConnectionError("连接 WebUI 超时")

    def _try_auth(self) -> Optional[str]:
        """尝试认证，返回 Credential"""
        # 新版本认证方式
        hashed_token = hashlib.sha256(
            f"{ncatbot_config.napcat.webui_token}.{NAPCAT_WEBUI_SALT}".encode()
        ).hexdigest()

        try:
            content = post_json(
                f"{self._base_uri}/api/auth/login",
                payload={"hash": hashed_token},
                timeout=5,
            )
            return content.get("data", {}).get("Credential")
        except Exception:
            # 尝试旧版本认证方式
            try:
                content = post_json(
                    f"{self._base_uri}/api/auth/login",
                    payload={"token": ncatbot_config.napcat.webui_token},
                    timeout=5,
                )
                return content.get("data", {}).get("Credential")
            except Exception:
                return None

    def _handle_connection_error(self, error: Exception) -> None:
        """处理连接错误"""
        LOG.error("连接 WebUI 失败")
        LOG.info("建议: 使用 bot.run(enable_webui_interaction=False) 跳过鉴权")
        LOG.info(traceback.format_exc())
        raise WebUIConnectionError(f"连接 WebUI 失败: {error}")

    def _api_call(
        self, endpoint: str, payload: Optional[dict] = None, timeout: int = 5
    ) -> dict:
        """统一的 API 调用"""
        return post_json(
            f"{self._base_uri}{endpoint}",
            headers=self._header,
            payload=payload,
            timeout=timeout,
        )

    # ==================== 登录状态检查 ====================

    def check_login_status(self) -> bool:
        """检查 NapCat 是否已登录"""
        try:
            data = self._api_call("/api/QQLogin/CheckLoginStatus")
            return data.get("data", {}).get("isLogin", False)
        except Exception:
            LOG.warning("检查登录状态超时, 默认未登录")
            return False

    def get_login_info(self) -> Optional[dict]:
        """获取登录信息"""
        try:
            return self._api_call("/api/QQLogin/GetQQLoginInfo").get("data", {})
        except Exception:
            LOG.warning("获取登录信息超时")
            return None

    def report_status(self) -> LoginStatus:
        """
        报告当前登录状态

        Returns:
            LoginStatus 枚举值
        """
        if not self.check_login_status():
            return LoginStatus.NOT_LOGGED_IN

        info = self.get_login_info()
        if not info:
            return LoginStatus.ABNORMAL

        target_uin = str(ncatbot_config.bt_uin)
        current_uin = str(info.get("uin", ""))
        is_online = info.get("online", False)

        if current_uin != target_uin:
            return LoginStatus.UIN_MISMATCH
        if not is_online:
            return LoginStatus.ABNORMAL

        return LoginStatus.OK

    # ==================== 快速登录 ====================

    def get_quick_login_list(self) -> list:
        """获取可快速登录的 QQ 列表"""
        try:
            data = self._api_call("/api/QQLogin/GetQuickLoginListNew")
            records = data.get("data", [])
            return [str(r["uin"]) for r in records if r.get("isQuickLogin")]
        except Exception:
            LOG.warning("获取快速登录列表失败")
            return []

    def quick_login(self) -> bool:
        """尝试快速登录"""
        uin = str(ncatbot_config.bt_uin)
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
        """获取登录二维码 URL"""
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
        """在终端显示二维码"""
        LOG.info(f"二维码对应的 QQ 号: {ncatbot_config.bt_uin}")
        qr = qrcode.QRCode()
        qr.add_data(url)
        qr.print_ascii(invert=True)

    def qrcode_login(self) -> None:
        """二维码登录流程"""
        try:
            try:
                qrcode_url = self.get_qrcode_url()
                self.show_qrcode(qrcode_url)
            except QQLoginedError:
                if self.report_status() == LoginStatus.OK:
                    LOG.info("QQ 已登录")
                    return
                LOG.error("登录状态异常, 请物理重启本机")
                raise AuthError("登录状态异常")

            # 等待扫码
            expire_time = time.time() + self.QRCODE_LOGIN_TIMEOUT
            warn_time = time.time() + 30

            while not self.check_login_status():
                if time.time() > expire_time:
                    LOG.error("登录超时, 请重新操作")
                    raise LoginTimeoutError("登录超时")
                if time.time() > warn_time:
                    LOG.warning("二维码即将失效, 请尽快扫码登录")
                    warn_time += 60

            LOG.info("登录成功")
        except (QQLoginedError, LoginTimeoutError):
            raise
        except Exception as e:
            LOG.error(f"二维码登录出错: {e}")
            raise AuthError("登录失败")

    # ==================== 主登录流程 ====================

    def login(self) -> None:
        """
        执行登录流程

        优先尝试快速登录，失败则使用二维码登录
        """
        status = self.report_status()
        if status == LoginStatus.OK:
            LOG.info("已登录")
            return
        if status > LoginStatus.NOT_LOGGED_IN:
            LOG.error("登录状态异常, 请物理重启本机")
            raise AuthError("登录状态异常")

        # 尝试快速登录
        if self.quick_login():
            LOG.info("快速登录成功")
            return

        # 回退到二维码登录
        self.qrcode_login()

        # 验证登录结果
        if self.report_status() != LoginStatus.OK:
            LOG.error("登录状态异常, 请检查是否使用了正确的 bot 账号扫码登录")
            raise AuthError("登录状态异常")


# ==================== 模块级便捷函数 ====================

_handler: Optional[AuthHandler] = None


def get_auth_handler(reset: bool = False) -> AuthHandler:
    """获取认证处理器单例"""
    global _handler
    if _handler is None or reset:
        _handler = AuthHandler()
    return _handler


def login(reset: bool = False) -> None:
    """执行登录"""
    get_auth_handler(reset=reset).login()


def report_login_status(reset: bool = False) -> LoginStatus:
    """报告登录状态"""
    return get_auth_handler(reset=reset).report_status()
