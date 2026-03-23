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

from ncatbot.utils import NcatBotError, get_config_manager, get_log  # type: ignore[attr-defined]
from ncatbot.utils.config.models import DEFAULT_BOT_UIN
from .auth import AuthHandler
from .config import NapCatConfigManager
from .installer import NapCatInstaller
from .platform import PlatformOps, UnsupportedPlatformError
from .webui_client import WebUIClient

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
        self._webui_client: Optional[WebUIClient] = None

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
                webui_client=self._webui_client,
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

        start = time.time()
        expire_time = start + timeout
        warned_5 = False
        warned_10 = False
        while True:
            if await self.is_service_ok():
                return True
            elapsed = time.time() - start
            if not warned_5 and elapsed >= 5:
                LOG.warning("NapCat WebSocket 已等待 5s 仍未就绪...")
                warned_5 = True
            if not warned_10 and elapsed >= 10:
                LOG.warning(
                    "NapCat WebSocket 已等待 10s 仍未就绪，请检查 NapCat 是否正常运行"
                )
                warned_10 = True
            if time.time() >= expire_time:
                return False
            await asyncio.sleep(0.5)

    async def wait_for_service(self, timeout: int = 15) -> None:
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
        await self._verify_account()

    # ==================== Setup 模式 ====================

    async def _setup_and_connect(self) -> None:
        """Setup 模式: 保证环境就绪, 按需安装/配置/启动/登录"""
        LOG.debug("Setup 模式, 检查 NapCat 服务...")

        # 环境已就绪, 跳过准备
        if await self.is_service_ok():
            LOG.debug(f"NapCat 服务 {self._napcat_config.ws_uri} 在线, 跳过环境准备")
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

        skip_confirm = get_config_manager().effective_skip_napcat_install_confirm()
        if not self._installer.ensure_installed(skip_confirm=skip_confirm):
            raise NcatBotError("安装或更新 NapCat 失败")

        self._config.configure_all()
        self.platform.start_napcat(self._bot_uin)

        await self._wait_and_login()
        await self._verify_account()

    async def _verify_account(self) -> None:
        """通过 WS self_id 校验当前登录的 QQ 号是否为目标账号。

        默认 bot_uin 且不匹配时：警告并写回实际账号 + 通过 HTTP 创建 WS 配置。
        非默认 bot_uin 且不匹配时：报错终止。
        """
        self_id = await self._test_websocket()
        if self_id is None:
            raise NcatBotError("WebSocket 连接异常, 无法获取登录账号信息")

        actual_uin = str(self_id)
        target_uin = self._bot_uin

        if actual_uin == target_uin:
            LOG.info(f"账号验证通过 (QQ {actual_uin})")
            return

        # 账号不匹配
        if target_uin == DEFAULT_BOT_UIN:
            # 默认值：警告 + 写回实际账号 + 通过 HTTP 推送 WS 配置
            LOG.warning(
                f"bot_uin 未配置 (仍为默认值 {DEFAULT_BOT_UIN}), "
                f"当前登录账号为 {actual_uin}"
            )
            self._update_bot_uin(actual_uin)
            self._push_ws_config_via_http(actual_uin)
            return

        # 非默认值且不匹配：报错终止
        raise NcatBotError(
            f"NapCat 当前登录账号 {actual_uin} 与配置的 bot_uin {target_uin} 不匹配, "
            f"请确认 config.yaml 中的 bot_uin 与实际扫码登录的 QQ 号一致"
        )

    def _update_bot_uin(self, actual_uin: str) -> None:
        """将实际登录的 QQ 号写回 config 并更新内部状态。"""
        try:
            from ncatbot.utils.config import get_config_manager

            mgr = get_config_manager()
            mgr.update_value("bot_uin", actual_uin)
            mgr.save()
            LOG.warning(f"已将 bot_uin 自动更新为 {actual_uin} 并保存到 config.yaml")
        except Exception as e:
            LOG.warning(f"自动更新 bot_uin 失败: {e}")

        # 更新 launcher 内部状态
        self._bot_uin = actual_uin
        if self._config is not None:
            self._config._bot_uin = actual_uin

    def _push_ws_config_via_http(self, uin: str) -> None:
        """登录后通过 HTTP 为实际账号推送 WebSocket 配置。"""
        if not self._webui_client or not self._webui_client.is_connected:
            LOG.debug("无可用的 WebUI 客户端, 跳过 HTTP 配置推送")
            return

        self._ensure_components()
        try:
            self._config.configure_onebot_http(self._webui_client)
            LOG.info(f"已通过 HTTP 为账号 {uin} 推送 WebSocket 配置")
        except Exception as e:
            LOG.warning(f"HTTP 推送 WebSocket 配置失败 (非致命): {e}")

    def _post_login_config_check(self, auth: AuthHandler) -> None:
        """登录后通过 HTTP 检查实际账号, 必要时更新 bot_uin 并推送 WS 配置。

        必须在 wait_for_service() 之前调用, 因为 WS 可能尚未配置。
        """
        info = auth.get_login_info()
        if not info:
            LOG.debug("无法获取登录信息, 跳过登录后配置检查")
            return

        actual_uin = str(info.get("uin", ""))
        if not actual_uin or actual_uin == self._bot_uin:
            return

        if self._bot_uin == DEFAULT_BOT_UIN:
            LOG.warning(
                f"bot_uin 未配置 (仍为默认值 {DEFAULT_BOT_UIN}), "
                f"当前登录账号为 {actual_uin}"
            )
            self._update_bot_uin(actual_uin)
            self._push_ws_config_via_http(actual_uin)
        else:
            raise NcatBotError(
                f"扫码登录的 QQ ({actual_uin}) 与配置的 bot_uin ({self._bot_uin}) 不匹配, "
                f"请使用正确的 QQ 扫码, 或修改 config.yaml 中的 bot_uin"
            )

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
        self._webui_client = WebUIClient(self._napcat_config)
        self._webui_client.connect()
        auth = AuthHandler(
            napcat_config=self._napcat_config,
            bot_uin=self._bot_uin,
            webui_client=self._webui_client,
        )
        auth.login()
        self._post_login_config_check(auth)
        await self.wait_for_service()
        LOG.info("NapCat 登录成功")

    # ==================== 主入口 ====================

    async def launch(self) -> None:
        """启动 NapCat 服务（根据配置选择模式）"""
        if self._napcat_config.skip_setup:
            await self._connect_only()
        else:
            await self._setup_and_connect()
