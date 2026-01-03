"""
支持功能 API

提供 AI 声聊、状态检查、OCR、版本信息等辅助功能。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Optional, TYPE_CHECKING, Union

from .utils import (
    APIComponent,
    APIReturnStatus,
    generate_sync_methods,
)

if TYPE_CHECKING:
    pass


# =============================================================================
# 数据模型
# =============================================================================


@dataclass
class AICharacter:
    """AI 声聊角色"""

    character_id: str
    character_name: str
    preview_url: str

    def __init__(self, data: dict):
        self.character_id = data.get("character_id", "")
        self.character_name = data.get("character_name", "")
        self.preview_url = data.get("preview_url", "")

    def __repr__(self) -> str:
        return f"AICharacter(name={self.character_name!r})"

    def get_details(self) -> dict:
        """获取角色详细信息"""
        return {
            "character_id": self.character_id,
            "character_name": self.character_name,
            "preview_url": self.preview_url,
        }


class AICharacterList:
    """AI 声聊角色列表"""

    characters: List[AICharacter]

    def __init__(self, data: List[dict]):
        self.characters = [AICharacter(item) for item in data]

    def __repr__(self) -> str:
        return f"AICharacterList(count={len(self.characters)})"

    def __len__(self) -> int:
        return len(self.characters)

    def __iter__(self):
        return iter(self.characters)

    def get_id_by_name(self, name: str) -> Optional[str]:
        """
        通过名称获取角色 ID

        Args:
            name: 角色名称

        Returns:
            str | None: 角色 ID，未找到返回 None
        """
        for character in self.characters:
            if character.character_name == name:
                return character.character_id
        return None

    # 向后兼容别名
    def get_search_id_by_name(self, name: str) -> Optional[str]:
        """向后兼容：请使用 get_id_by_name"""
        return self.get_id_by_name(name)


# =============================================================================
# SupportAPI 实现
# =============================================================================


@generate_sync_methods
class SupportAPI(APIComponent):
    """
    支持功能 API

    提供 AI 声聊、状态检查、OCR、版本信息等辅助功能。
    """

    # -------------------------------------------------------------------------
    # region AI 声聊
    # -------------------------------------------------------------------------

    async def get_ai_characters(
        self,
        group_id: Union[str, int],
        chat_type: Literal[1, 2],
    ) -> AICharacterList:
        """
        获取 AI 声聊角色列表

        Args:
            group_id: 群号
            chat_type: 聊天类型 (1 或 2)

        Returns:
            AICharacterList: AI 角色列表
        """
        result = await self._request_raw(
            "/get_ai_characters",
            {"group_id": group_id, "chat_type": chat_type},
        )
        status = APIReturnStatus(result)
        all_characters = sum([item["characters"] for item in status.data], [])
        return AICharacterList(all_characters)

    async def get_ai_record(
        self,
        group_id: Union[str, int],
        character_id: str,
        text: str,
    ) -> str:
        """
        获取 AI 声聊语音

        Args:
            group_id: 群号
            character_id: 角色 ID
            text: 要转换的文本

        Returns:
            str: 语音链接

        Note:
            此功能可能不可用
        """
        result = await self._request_raw(
            "/get_ai_record",
            {"group_id": group_id, "character": character_id, "text": text},
        )
        status = APIReturnStatus(result)
        return status.data

    # -------------------------------------------------------------------------
    # region 状态检查
    # -------------------------------------------------------------------------

    async def can_send_image(self) -> bool:
        """
        检查是否可以发送图片

        Returns:
            bool: 是否可以发送
        """
        result = await self._request_raw("/can_send_image")
        status = APIReturnStatus(result)
        return status.data.get("yes", False)

    async def can_send_record(self, group_id: Union[str, int]) -> bool:
        """
        检查是否可以发送语音

        Args:
            group_id: 群号

        Returns:
            bool: 是否可以发送
        """
        result = await self._request_raw(
            "/can_send_record",
            {"group_id": group_id},
        )
        status = APIReturnStatus(result)
        return status.data.get("yes", False)

    # -------------------------------------------------------------------------
    # region OCR 相关
    # -------------------------------------------------------------------------

    async def ocr_image(self, image: str) -> List[dict]:
        """
        图片文字识别（OCR）

        Args:
            image: 图片路径/URL

        Returns:
            List[dict]: OCR 识别结果

        Note:
            仅 Windows 可用
        """
        result = await self._request_raw(
            "/ocr_image",
            {"image": image},
        )
        status = APIReturnStatus(result)
        return status.data

    # -------------------------------------------------------------------------
    # region 其它
    # -------------------------------------------------------------------------

    async def get_version_info(self) -> dict:
        """
        获取 NapCat 版本信息

        Returns:
            dict: 版本信息
        """
        result = await self._request_raw("/get_version_info")
        status = APIReturnStatus(result)
        return status.data

    async def bot_exit(self) -> None:
        """
        退出机器人

        Note:
            此功能可能需要测试
        """
        result = await self._request_raw("/bot_exit")
        APIReturnStatus.raise_if_failed(result)
