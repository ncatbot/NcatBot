from typing import Literal, Optional, ClassVar
from .base import MessageSegment


class DownloadableMessageSegment(MessageSegment):
    file: str
    url: Optional[str] = None
    file_id: Optional[str] = None
    file_size: Optional[int] = None
    file_name: Optional[str] = None


class Image(DownloadableMessageSegment):
    type: ClassVar[str] = "image"
    sub_type: int = 0
    image_type: Optional[Literal["flash", "normal"]] = None
    
    @classmethod
    def from_dict(cls, data):
        if "type" in data.get("data", {}):
            data["data"]["image_type"] = data["data"].pop("type")
        obj = super().from_dict(data)
        return obj

    def to_dict(self):
        data = super().to_dict()
        # 只有当 image_type 存在时才进行转换
        if "image_type" in data["data"] and data["data"]["image_type"] is not None:
            # 将 image_type 转换为 type 字段
            image_type = data["data"].pop("image_type")
            data["data"]["type"] = 1 if image_type == "flash" else 0
        return data

class Record(DownloadableMessageSegment):
    type: ClassVar[str] = "record"
    magic: Optional[int] = None


class Video(DownloadableMessageSegment):
    type: ClassVar[str] = "video"


class File(DownloadableMessageSegment):
    type: ClassVar[str] = "file"
