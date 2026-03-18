"""
NapCat 启动编排

两种模式:
- setup 模式 (默认): 保证 NapCat 完整运行环境, 按需安装/配置/启动/登录
- connect 模式 (skip_setup=true): 直接连接已有服务, 失败报错

详见 README.md
"""

import asyncio
import json
import time
from typing import Optional, TYPE_CHECKING

import websockets

from ncatbot.utils import NcatBotError, get_log  # type: ignore[attr-defined]
from .auth import AuthHandler
from .config import NapCatConfigManager
from .installer import NapCatInstaller
from .platform import PlatformOps, UnsupportedPlatformError

if TYPE_CHECKING:
    from ncatbot.utils.config.models import NapCatConfig

LOG = get_log("NapCatLauncher")


class NapCatLauncher:
    """NapCat 启动编排

    Parameters
    ----------
    napcat_config:
        NapCatConfig 实例，由 NapCatAdapter 注入。
    bot_uin:
        目标 QQ 号。
    websocket_timeout:
        WebSocket 超时秒数。
    """

    def __init__(
        self,
        napcat_config: "NapCatConfig",
        bot_uin: str = "",
        websocket_timeout: int = 15,
    ):
        self._napcat_config = napcat_config
        self._bot_uin = bot_uin
        self._websocket_timeout = websocket_timeout
        self._platform: Optional[PlatformOps] = None
        self._installer: Optional[NapCatInstaller] = None
        self._config: Optional[NapCatConfigManager] = None

    @property
    def platform(self) -> PlatformOps:
        if self._platform is None:
            self._platform = PlatformOps.create()
        return self._platform

    def _ensure_components(self) -> None:
        if self._installer is None:
            self._installer = NapCatInstaller(
                self.platform,
                napcat_config=self._napcat_config,
            )
        if self._config is None:
            self._config = NapCatConfigManager(
                self.platform,
                napcat_config=self._napcat_config,
                bot_uin=self._bot_uin,
            )

    # ==================== WebSocket 连接测试 ====================

    async def _test_websocket(self, log_failure: bool = False) -> Optional[int]:
        """测试 WS 连接, 成功返回 self_id (登录的 QQ 号), 失败返回 None。"""
        uri = self._napcat_config.get_uri_with_token()
        try:
            async with websockets.connect(uri, open_timeout=5) as ws:
                data = json.loads(await ws.recv())
                if data.get("status") == "failed":
                    retcode = data.get("retcode")
                    message = data.get("message", "未知错误")
                    if retcode == 1403:
                        raise NcatBotError("WebSocket Token 填写错误", False)
                    raise NcatBotError(f"WebSocket 连接失败: {message}", False)
                return data.get("self_id")
        except NcatBotError:
            raise
        except Exception as e:
            if log_failure:
                LOG.warning(f"测试 WebSocket 连接失败: {e}")
            return None

    async def is_service_ok(self, timeout: int = 0, show_info: bool = True) -> bool:
        """WS 是否连通 (即 QQ 是否已登录)。"""
        LOG.debug(f"测试 NapCat WebSocket 连接 (timeout={timeout})")
        if timeout == 0:
            return await self._test_websocket(show_info) is not None

        expire_time = time.time() + timeout
        while True:
            if await self.is_service_ok(show_info=(time.time() > expire_time)):
                return True
            if time.time() > expire_time:
                return False
            await asyncio.sleep(0.5)

    async def wait_for_service(self, timeout: int = 60) -> None:
        if not await self.is_service_ok(timeout):
            raise NcatBotError("连接 NapCat WebSocket 服务器超时")
        LOG.info("连接 NapCat WebSocket 服务器成功!")

    # ==================== Connect 模式 ====================

    async def _connect_only(self) -> None:
        """直连模式: 连接失败直接报错"""
        LOG.info("Connect 模式, 正在连接 NapCat 服务...")
        if not await self.is_service_ok():
            raise NcatBotError(
                f"无法连接 NapCat WebSocket ({self._napcat_config.ws_uri}), "
                f"请检查 NapCat 服务是否已启动"
            )
        LOG.info("NapCat 服务连接成功")

    # ==================== Setup 模式 ====================

    async def _setup_and_connect(self) -> None:
        """Setup 模式: 保证环境就绪, 按需安装/配置/启动/登录"""
        LOG.info("Setup 模式, 检查 NapCat 服务...")

        # 环境已就绪, 跳过准备
        if await self.is_service_ok():
            LOG.info(f"NapCat 服务 {self._napcat_config.ws_uri} 在线, 跳过环境准备")
            await self._verify_account()
            return

        # 环境未就绪, 完整准备流程
        try:
            _ = self.platform
        except UnsupportedPlatformError:
            raise NcatBotError("当前操作系统不支持 Setup 模式, 请使用 skip_setup: true")

        self._ensure_components()
        assert self._installer is not None
        assert self._config is not None

        if not self._installer.ensure_installed():
            raise NcatBotError("安装或更新 NapCat 失败")

        self._config.configure_all()
        self.platform.start_napcat(self._bot_uin)

        await self._wait_and_login()

    async def _verify_account(self) -> None:
        """通过 WS self_id 校验当前登录的 QQ 号是否为目标账号。"""
        self_id = await self._test_websocket()
        if self_id is None:
            raise NcatBotError("WebSocket 连接异常, 无法获取登录账号信息")

        target_uin = int(self._bot_uin)
        if self_id != target_uin:
            raise NcatBotError(
                f"NapCat 当前登录账号 {self_id} 与目标账号 {target_uin} 不匹配"
            )
        LOG.info(f"账号验证通过 (QQ {self_id})")

    async def _wait_and_login(self) -> None:
        """NapCat 刚启动后, 等待服务就绪并完成登录"""
        # 先等几秒: 有缓存 session 时 NapCat 会自动登录
        if await self.is_service_ok(5):
            LOG.info("NapCat 已就绪 (缓存登录)")
            return

        if not self._napcat_config.enable_webui:
            # WebUI 禁用, 只能等待 NapCat 自行完成登录
            timeout = self._websocket_timeout
            if not await self.is_service_ok(timeout):
                raise NcatBotError(
                    f"NapCat 未能在 {timeout} 秒内完成登录, WebSocket 连接失败"
                )
            return

        # 通过 WebUI 引导登录
        LOG.info("NapCat 未自动登录, 通过 WebUI 引导...")
        AuthHandler(
            napcat_config=self._napcat_config,
            bot_uin=self._bot_uin,
        ).login()
        await self.wait_for_service()
        LOG.info("NapCat 登录成功")

    # ==================== 主入口 ====================

    async def launch(self) -> None:
        """启动 NapCat 服务（根据配置选择模式）"""
        if self._napcat_config.skip_setup:
            await self._connect_only()
        else:
            await self._setup_and_connect()
