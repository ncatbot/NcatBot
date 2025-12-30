from typing import Literal, Union, ClassVar
from pydantic import field_validator
from .base import MessageSegment


class PlainText(MessageSegment):
    type: ClassVar[str] = "text"
    text: str


class Face(MessageSegment):
    type: ClassVar[str] = "face"
    id: str
    
    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, v) -> str:
        return str(v)


class At(MessageSegment):
    type: ClassVar[str] = "at"
    qq: str

    @field_validator("qq", mode="before")
    @classmethod
    def validate_qq(cls, v) -> str:
        str_v = str(v).strip()
        if str_v == "all":
            return str_v
        if str_v.isdigit():
            return str_v
        raise ValueError(f"At 消息的 qq 字段必须为纯数字或字符串 'all', 但读取到 {v}")


class Reply(MessageSegment):
    type: ClassVar[str] = "reply"
    id: str
    
    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, v) -> str:
        return str(v)
    
