"""
SessionManager — BaseService

管理所有 Session 的生命周期。
"""

from typing import Dict, Optional

from ncatbot.core.service.base import BaseService
from ncatbot.utils import get_log

from .session import Session

LOG = get_log("SessionManager")


class SessionManager(BaseService):
    """
    Session 管理器

    管理所有 Session 实例的创建、获取、关闭、清理。
    """

    name = "session_manager"
    description = "会话管理器"

    def __init__(self, **config):
        super().__init__(**config)
        self._sessions: Dict[str, Session] = {}

    async def on_load(self) -> None:
        LOG.info("SessionManager 已加载")

    async def on_close(self) -> None:
        # 关闭所有 session
        for session in self._sessions.values():
            session.close()
        self._sessions.clear()
        LOG.info("SessionManager 已关闭")

    # ==================== Session 管理 ====================

    def get_or_create(
        self,
        session_key: str,
        plugin_name: str,
        ttl: Optional[float] = None,
    ) -> Session:
        """获取或创建 Session"""
        existing = self._sessions.get(session_key)
        if existing and not existing.is_expired():
            existing.touch()
            return existing

        # 关闭旧的 session (如果存在)
        if existing:
            existing.close()

        session = Session(
            session_key=session_key,
            plugin_name=plugin_name,
            ttl=ttl,
        )
        self._sessions[session_key] = session
        LOG.debug(f"创建 session: {session_key} (plugin={plugin_name}, ttl={ttl})")
        return session

    def get(self, session_key: str) -> Optional[Session]:
        """获取 Session (不存在或过期返回 None)"""
        session = self._sessions.get(session_key)
        if session is None:
            return None
        if session.is_expired():
            self._sessions.pop(session_key, None)
            return None
        return session

    def feed_event(self, session_key: str, event) -> bool:
        """向 Session 投递事件"""
        session = self.get(session_key)
        if session is None:
            return False
        return session.feed(event)

    def close_session(self, session_key: str) -> None:
        """关闭 Session"""
        session = self._sessions.pop(session_key, None)
        if session:
            session.close()
            LOG.debug(f"关闭 session: {session_key}")

    def revoke_plugin(self, plugin_name: str) -> int:
        """热重载: 关闭该插件的所有 Session"""
        to_remove = [
            key for key, s in self._sessions.items() if s.plugin_name == plugin_name
        ]
        for key in to_remove:
            self.close_session(key)
        return len(to_remove)

    def cleanup(self) -> int:
        """清理过期 Session"""
        expired = [key for key, s in self._sessions.items() if s.is_expired()]
        for key in expired:
            self._sessions.pop(key, None)
        return len(expired)

    @property
    def active_count(self) -> int:
        return len(self._sessions)
