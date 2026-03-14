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

from ncatbot.utils import get_log, ncatbot_config, post_json
from ncatbot.adapter.napcat.constants import NAPCAT_WEBUI_SALT

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


class RateLimitError(AuthError):
    pass


class AuthHandler:
    """登录认证处理器"""

    WEBUI_CONNECT_TIMEOUT = 90
    QRCODE_LOGIN_TIMEOUT = 60
    QRCODE_FETCH_TIMEOUT = 15
    WEBUI_RETRY_INTERVAL = 2

    def __init__(self):
        self._base_uri = (
            f"http://{ncatbot_config.napcat.webui_host}:"
            f"{ncatbot_config.napcat.webui_port}"
        )
        self._header: Optional[dict] = None
        self._connect_webui()

    def _connect_webui(self) -> None:
        expire_time = time.time() + self.WEBUI_CONNECT_TIMEOUT
        last_error: Optional[Exception] = None
        attempt = 0

        while time.time() < expire_time:
            if attempt > 0:
                time.sleep(self.WEBUI_RETRY_INTERVAL)
            attempt += 1
            try:
                credential = self._try_auth()
                if credential:
                    self._header = {"Authorization": f"Bearer {credential}"}
                    LOG.debug("成功连接到 WebUI")
                    return
            except RateLimitError as e:
                last_error = e
                LOG.warning(f"WebUI 速率限制, 等待冷却后重试 (第{attempt}次)")
                time.sleep(5)  # 额外等待
                continue
            except AuthError:
                # 认证失败(非连接问题), 无需重试
                raise
            except Exception as e:
                last_error = e
                remaining = int(expire_time - time.time())
                LOG.debug(f"连接 WebUI 失败 (第{attempt}次, 剩余{remaining}s): {e}")
                continue

        detail = f": {last_error}" if last_error else ""
        raise WebUIConnectionError(
            f"连接 WebUI 超时 (已重试{attempt}次, 超时{self.WEBUI_CONNECT_TIMEOUT}s){detail}"
        )

    def _try_auth(self) -> Optional[str]:
        hashed_token = hashlib.sha256(
            f"{ncatbot_config.napcat.webui_token}.{NAPCAT_WEBUI_SALT}".encode()
        ).hexdigest()

        try:
            content = post_json(
                f"{self._base_uri}/api/auth/login",
                payload={"hash": hashed_token},
                timeout=5,
            )
        except TimeoutError:
            raise  # 连接超时, 交给 _connect_webui 重试
        except Exception as e:
            raise ConnectionError(f"无法连接 WebUI ({self._base_uri}): {e}") from e

        code = content.get("code")
        message = content.get("message", "")

        if code == 0:
            credential = content.get("data", {}).get("Credential")
            if credential:
                return credential
            raise AuthError("认证响应异常: 缺少 Credential 字段")

        if "rate limit" in message.lower():
            raise RateLimitError(f"WebUI 登录速率限制: {message}")

        raise AuthError(
            f"WebUI 认证失败 (code={code}): {message}. 请检查 webui_token 配置是否正确"
        )

    def _handle_connection_error(self, error: Exception) -> None:
        LOG.error("连接 WebUI 失败")
        LOG.info("建议: 使用 bot.run(enable_webui=False) 跳过鉴权")
        LOG.info(traceback.format_exc())
        raise WebUIConnectionError(f"连接 WebUI 失败: {error}")

    def _api_call(
        self,
        endpoint: str,
        payload: Optional[dict] = None,
        timeout: int = 5,
    ) -> dict:
        return post_json(
            f"{self._base_uri}{endpoint}",
            headers=self._header,
            payload=payload,
            timeout=timeout,
        )

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

        target_uin = str(ncatbot_config.bot_uin)
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
        uin = str(ncatbot_config.bot_uin)
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
        LOG.info(f"二维码对应的 QQ 号: {ncatbot_config.bot_uin}")
        qr = qrcode.QRCode()
        qr.add_data(url)
        qr.print_ascii(invert=True)

    def qrcode_login(self) -> None:
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
        status = self.report_status()
        if status == LoginStatus.OK:
            LOG.info("已登录")
            return
        if status > LoginStatus.NOT_LOGGED_IN:
            LOG.error("登录状态异常, 请物理重启本机")
            raise AuthError("登录状态异常")

        if self.quick_login():
            LOG.info("快速登录成功")
            return

        self.qrcode_login()

        if self.report_status() != LoginStatus.OK:
            LOG.error("登录状态异常, 请检查是否使用了正确的 bot 账号扫码登录")
            raise AuthError("登录状态异常")
