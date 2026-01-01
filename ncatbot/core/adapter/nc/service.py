"""
NapCat 服务管理模块

提供 NapCat 服务的启动、连接、状态检查等核心功能。
"""

import json
import time
from typing import Optional

import websockets

from ....utils import NcatBotError, get_log, ncatbot_config, run_coroutine
from .auth import AuthHandler, LoginStatus, get_auth_handler, login
from .config_manager import ConfigManager
from .platform import PlatformOps, UnsupportedPlatformError

LOG = get_log("ncatbot.core.adapter.nc.service")


class NcatBotLoginError(NcatBotError):
    """登录错误"""

    def __init__(self, info: str):
        super().__init__(info, False)


class NapCatService:
    """
    NapCat 服务管理器

    统一管理 NapCat 的安装、配置、启动、登录等流程。
    支持本地模式和远程模式。
    """

    def __init__(self):
        self._platform: Optional[PlatformOps] = None
        self._config: Optional[ConfigManager] = None
        self._auth: Optional[AuthHandler] = None

    @property
    def platform(self) -> PlatformOps:
        """懒加载平台操作实例"""
        if self._platform is None:
            self._platform = PlatformOps.create()
        return self._platform

    @property
    def config(self) -> ConfigManager:
        """懒加载配置管理器"""
        if self._config is None:
            self._config = ConfigManager(self.platform)
        return self._config

    # ==================== WebSocket 连接测试 ====================

    @staticmethod
    async def _test_websocket_async(report_status: bool = False) -> bool:
        """异步测试 WebSocket 连接"""
        uri = ncatbot_config.get_uri_with_token()
        try:
            async with websockets.connect(uri, open_timeout=5) as ws:
                data = json.loads(await ws.recv())
                # NapCat 连接成功后会发送 meta_event lifecycle 事件
                # 如果 token 验证失败，会返回 status: failed
                if data.get("status") == "failed":
                    retcode = data.get("retcode")
                    message = data.get("message", "未知错误")
                    if retcode == 1403:
                        raise NcatBotError("WebSocket Token 填写错误", False)
                    raise NcatBotError(f"WebSocket 连接失败: {message}", False)
                # 收到 meta_event 或其他非错误消息表示连接成功
                return True
        except NcatBotError:
            raise
        except Exception as e:
            if report_status:
                LOG.warning(f"测试 WebSocket 连接失败: {e}")
            return False

    def is_service_ok(self, timeout: int = 0, show_info: bool = True) -> bool:
        """
        检查 NapCat 服务是否正常

        Args:
            timeout: 超时时间（秒），0 表示立即返回
            show_info: 是否显示日志信息

        Returns:
            服务是否正常
        """
        if timeout == 0:
            result = run_coroutine(self._test_websocket_async, show_info)
            return bool(result)

        expire_time = time.time() + timeout
        while True:
            if self.is_service_ok(show_info=(time.time() > expire_time)):
                return True
            if time.time() > expire_time:
                return False
            time.sleep(0.5)

    def wait_for_service(self, timeout: int = 60) -> None:
        """等待服务就绪，超时抛出异常"""
        if not self.is_service_ok(timeout):
            raise NcatBotError("连接 NapCat WebSocket 服务器超时")
        LOG.info("连接 NapCat WebSocket 服务器成功!")

    # ==================== 远程模式 ====================

    def _check_remote_service(self) -> bool:
        """检查远程 NapCat 服务状态"""
        if not self.is_service_ok():
            LOG.info("NapCat 服务器离线或未登录")
            return False

        LOG.info(f"NapCat 服务器 {ncatbot_config.napcat.ws_uri} 在线, 正在检查账号状态...")

        # 跳过 WebUI 交互检查
        if not ncatbot_config.napcat.enable_webui and not ncatbot_config.enable_webui_interaction:
            LOG.warning(
                f"跳过基于 WebUI 交互的检查, "
                f"请自行确保 NapCat 已登录正确的 QQ {ncatbot_config.bt_uin}"
            )
            return True

        # 检查登录状态
        status = get_auth_handler().report_status()

        if status == LoginStatus.OK:
            return True
        elif status == LoginStatus.ABNORMAL:
            LOG.error("登录状态异常, 请检查远端 NapCat 服务")
            LOG.error("对运行 NapCat 的服务器进行物理重启一般能解决该问题")
            raise NcatBotLoginError("登录状态异常, 请检查远端 NapCat 服务")
        elif status == LoginStatus.UIN_MISMATCH:
            LOG.error("远端登录的 QQ 与配置的 QQ 号不匹配")
            raise NcatBotLoginError("登录的 QQ 号与配置的 QQ 号不匹配")

        return False

    def _launch_remote(self) -> None:
        """远程模式启动"""
        LOG.info("正在以远端模式运行, 检查中...")
        if not self._check_remote_service():
            raise NcatBotError("远端 NapCat 服务异常, 请检查远端服务或关闭远端模式")

    # ==================== 本地模式 ====================

    def _launch_local(self) -> None:
        """本地模式启动"""
        LOG.info("正在以本地模式运行, 检查中...")

        # 如果服务已经在运行
        if self.is_service_ok():
            if self._check_remote_service():
                LOG.debug("NapCat 服务正常")
                return

        # 检查平台支持
        try:
            _ = self.platform
        except UnsupportedPlatformError:
            raise NcatBotError("本地模式不支持该操作系统, 请使用远端模式")

        # 安装/更新 NapCat
        if not self.platform.check_and_update():
            raise NcatBotError("安装或更新 NapCat 失败")

        # 配置并启动
        self.config.configure_all()
        self.platform.start_napcat(str(ncatbot_config.bt_uin))

        # 登录流程
        self._handle_login()

    def _handle_login(self) -> None:
        """处理登录流程"""
        nc = ncatbot_config.napcat

        if nc.enable_webui and ncatbot_config.enable_webui_interaction:
            # WebUI 交互模式
            if not self.is_service_ok(3):
                LOG.info("登录中...")
                login(reset=True)
                self.wait_for_service()
                LOG.info("连接成功")
            else:
                LOG.info("快速登录成功, 跳过登录引导")
        elif nc.enable_webui:
            # WebUI 禁用交互
            if not self.is_service_ok(15):
                raise NcatBotError("禁用 WebUI 交互时, 必须手动登录")
        else:
            # 无 WebUI
            timeout = ncatbot_config.websocket_timeout
            if not self.is_service_ok(timeout):
                raise TimeoutError(
                    f"NapCat 未能在 {timeout} 秒内启动, WebSocket 连接失败"
                )

    # ==================== 主入口 ====================

    def launch(self) -> None:
        """
        启动 NapCat 服务

        根据配置自动选择本地或远程模式。
        """
        if ncatbot_config.napcat.remote_mode:
            self._launch_remote()
        else:
            self._launch_local()


# ==================== 模块级便捷函数 ====================

_service: Optional[NapCatService] = None


def get_service() -> NapCatService:
    """获取服务单例"""
    global _service
    if _service is None:
        _service = NapCatService()
    return _service


def launch_napcat_service(*args, **kwargs) -> None:
    """启动 NapCat 服务（兼容旧接口）"""
    get_service().launch()


def napcat_service_ok(timeout: int = 0, show_info: bool = True) -> bool:
    """检查服务是否正常（兼容旧接口）"""
    return get_service().is_service_ok(timeout, show_info)
