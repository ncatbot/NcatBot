from typing import Literal, Optional, ClassVar
from .base import MessageSegment


class Share(MessageSegment):
    type: ClassVar[str] = "share"
    url: str
    title: str
    content: Optional[str] = None
    image: Optional[str] = None


class Location(MessageSegment):
    type: ClassVar[str] = "location"
    lat: float
    lon: float
    title: Optional[str] = None
    content: Optional[str] = None


class Music(MessageSegment):
    type: ClassVar[str] = "music"
    platform: Literal[
        "qq", "163", "custom"
    ]  # 仅用于透传访问, 与 Dict 交换时处理为 data['data']['type']
    id: Optional[str] = None
    url: Optional[str] = None
    audio: Optional[str] = None
    title: Optional[str] = None

    @classmethod
    def from_dict(cls, data):
        data["data"]["platform"] = data["data"]["type"]
        del data["data"]["type"]
        obj = super().from_dict(data)
        return obj

    def to_dict(self):
        data = super().to_dict()
        data["data"]["type"] = data["data"]["platform"]
        del data["data"]["platform"]
        return data


class Json(MessageSegment):
    type: ClassVar[str] = "json"
    data: str


class Markdown(MessageSegment):
    type: ClassVar[str] = "markdown"
    content: str

