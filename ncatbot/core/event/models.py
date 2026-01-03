# models.py
from typing import Optional
from pydantic import BaseModel, field_validator

__all__ = [
    "BaseDataModel",
    "BaseSender",
    "GroupSender",
    "Anonymous",
    "FileInfo",
    "Status",
]


class BaseDataModel(BaseModel):
    """基础数据模型，用于处理通用字段转换"""

    @field_validator("*", mode="before")
    def force_str_ids(cls, v, info):
        # 自动将所有 id 结尾的字段转为 str
        if info.field_name.endswith("_id") and isinstance(v, (int, float)):
            return str(v)
        return v


class BaseSender(BaseDataModel):
    user_id: Optional[str] = None
    nickname: Optional[str] = "QQ用户"
    sex: Optional[str] = "unknown"
    age: Optional[int] = 0


class GroupSender(BaseSender):
    card: Optional[str] = None
    area: Optional[str] = None
    level: Optional[str] = None
    role: Optional[str] = None
    title: Optional[str] = None


class Anonymous(BaseDataModel):
    id: int  # 匿名 ID 可能需要保持数值或转 str，这里视具体实现而定
    name: str
    flag: str


class FileInfo(BaseDataModel):
    id: str
    name: str
    size: int
    busid: int


class Status(BaseModel):
    online: bool = True
    good: bool = True
