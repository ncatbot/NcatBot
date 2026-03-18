"""BotAPIClient — 多平台 API 纯组合器

各平台通过 ``api.qq`` / ``api.github`` / ``api.platform("telegram")`` 访问。
BotAPIClient 本身不持有业务逻辑，仅组合各平台的 APIClient。

调用示例::

    await api.qq.messaging.send_group_msg(group_id, message)
    await api.qq.manage.set_group_ban(group_id, user_id, 600)
    await api.qq.send_group_text(group_id, "hello")  # sugar
"""

from __future__ import annotations

from typing import Any, Dict

from ncatbot.utils import get_log
from .qq import QQAPIClient
from .bilibili import IBiliAPIClient
from .github import IGitHubAPIClient


LOG = get_log("BotAPIClient")


class BotAPIClient:
    """多平台 API 纯组合器

    每个平台注册自己的 APIClient，通过属性访问::

        api.qq          -> QQAPIClient
        api.bilibili    -> IBiliAPIClient
        api.github      -> IGitHubAPIClient
        api.telegram    -> TelegramAPIClient (future)
    """

    def __init__(self) -> None:
        self._platforms: Dict[str, Any] = {}

    def register_platform(self, name: str, client: Any) -> None:
        """注册平台 APIClient 实例"""
        self._platforms[name] = client
        LOG.info("注册平台 API: %s", name)

    def platform(self, name: str) -> Any:
        """获取指定平台的 APIClient"""
        if name not in self._platforms:
            raise KeyError(f"未注册的平台: {name}")
        return self._platforms[name]

    @property
    def qq(self) -> QQAPIClient:
        """QQ 平台 API 快捷访问"""
        return self.platform("qq")

    @property
    def bilibili(self) -> IBiliAPIClient:
        """Bilibili 平台 API 快捷访问"""
        return self.platform("bilibili")

    @property
    def github(self) -> IGitHubAPIClient:
        """GitHub 平台 API 快捷访问"""
        return self.platform("github")

    @property
    def platforms(self) -> Dict[str, Any]:
        """已注册的所有平台"""
        return dict(self._platforms)
