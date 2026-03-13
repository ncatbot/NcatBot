"""
NapCat 事件转换器

从 core/event/parser.py 迁移 + 适配。
将 NapCat (OneBot v11) 原始数据转换为标准 BaseEvent。
"""

from typing import Any, Dict, Optional, TYPE_CHECKING

from ncatbot.core.event.parser import EventParser
from ncatbot.utils import get_log

if TYPE_CHECKING:
    from ncatbot.core.api.interface import IBotAPI
    from ncatbot.core.event.events import BaseEvent

LOG = get_log("NapCatEventConverter")


class NapCatEventConverter:
    """NapCat 事件转换器

    将 OneBot v11 原始 JSON 数据转换为框架标准 BaseEvent 对象。
    内部委托给 EventParser 完成实际的解析和对象创建。
    """

    def __init__(self, api_instance: "IBotAPI"):
        self._api = api_instance

    def convert(self, raw_data: Dict[str, Any]) -> Optional["BaseEvent"]:
        """将原始数据转换为标准事件

        Args:
            raw_data: OneBot v11 原始事件数据

        Returns:
            标准 BaseEvent 子类实例，无法解析时返回 None
        """
        # 跳过非事件消息（如 API 响应）
        if "post_type" not in raw_data:
            return None

        try:
            return EventParser.parse(raw_data, self._api)
        except ValueError as e:
            LOG.debug(f"事件转换跳过: {e}")
            return None
        except Exception as e:
            LOG.warning(f"事件转换失败: {e}")
            return None
