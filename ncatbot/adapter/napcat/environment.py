"""
NapCat 环境管理

从 core/adapter/nc/service.py 迁移。
负责 NapCat 服务的安装、配置、启动、登录等流程。
"""

import json
import time
import asyncio
from typing import Optional

import websockets

from ncatbot.utils import NcatBotError, get_log, ncatbot_config
from ncatbot.core.adapter.nc.auth import AuthHandler, LoginStatus
from ncatbot.core.adapter.nc.config_manager import ConfigManager
from ncatbot.core.adapter.nc.platform import PlatformOps, UnsupportedPlatformError

LOG = get_log("NapCatEnvironment")


class NapCatLoginError(NcatBotError):
    """登录错误"""

    def __init__(self, info: str):
        super().__init__(info, False)


class NapCatEnvironment:
    """NapCat 环境管理器

    统一管理 NapCat 的安装、配置、启动、登录等流程。
    支持本地模式和远程模式。

    此类从 NapCatService 重构，定位为 Adapter 层的环境准备组件。
    """

    def __init__(self):
        self._platform: Optional[PlatformOps] = None
        self._config: Optional[ConfigManager] = None

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
                if data.get("status") == "failed":
                    retcode = data.get("retcode")
                    message = data.get("message", "未知错误")
                    if retcode == 1403:
                        raise NcatBotError("WebSocket Token 填写错误", False)
                    raise NcatBotError(f"WebSocket 连接失败: {message}", False)
                return True
        except NcatBotError:
            raise
        except Exception as e:
            if report_status:
                LOG.warning(f"测试 WebSocket 连接失败: {e}")
            return False

    def is_service_ok(self, timeout: int = 0, show_info: bool = True) -> bool:
        """检查 NapCat 服务是否正常"""
        if timeout == 0:
            result = asyncio.run(self._test_websocket_async(show_info))
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

        LOG.info(
            f"NapCat 服务器 {ncatbot_config.napcat.ws_uri} 在线, 正在检查账号状态..."
        )

        if not ncatbot_config.napcat.enable_webui:
            LOG.warning(
                f"跳过基于 WebUI 交互的检查, "
                f"请自行确保 NapCat 已登录正确的 QQ {ncatbot_config.bot_uin}"
            )
            return True

        status = AuthHandler().report_status()

        if status == LoginStatus.OK:
            return True
        elif status == LoginStatus.ABNORMAL:
            LOG.error("登录状态异常, 请检查远端 NapCat 服务")
            raise NapCatLoginError("登录状态异常, 请检查远端 NapCat 服务")
        elif status == LoginStatus.UIN_MISMATCH:
            LOG.error("远端登录的 QQ 与配置的 QQ 号不匹配")
            raise NapCatLoginError("登录的 QQ 号与配置的 QQ 号不匹配")

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

        if self.is_service_ok():
            if self._check_remote_service():
                LOG.debug("NapCat 服务正常")
                return

        try:
            _ = self.platform
        except UnsupportedPlatformError:
            raise NcatBotError("本地模式不支持该操作系统, 请使用远端模式")

        if not self.platform.check_and_update():
            raise NcatBotError("安装或更新 NapCat 失败")

        self.config.configure_all()
        self.platform.start_napcat(str(ncatbot_config.bot_uin))

        self._handle_login()

    def _handle_login(self) -> None:
        """处理登录流程"""
        nc = ncatbot_config.napcat

        if nc.enable_webui:
            if not self.is_service_ok(3):
                LOG.info("登录中...")
                AuthHandler().login()
                self.wait_for_service()
                LOG.info("连接成功")
            else:
                LOG.info("快速登录成功, 跳过登录引导")
        else:
            timeout = ncatbot_config.websocket_timeout
            if not self.is_service_ok(timeout):
                raise TimeoutError(
                    f"NapCat 未能在 {timeout} 秒内启动, WebSocket 连接失败"
                )

    # ==================== 主入口 ====================

    def launch(self) -> None:
        """启动 NapCat 服务（根据配置选择模式）"""
        if ncatbot_config.napcat.remote_mode:
            self._launch_remote()
        else:
            self._launch_local()
