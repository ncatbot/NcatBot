from typing import Any, Dict, List, Type, ClassVar
from pydantic import BaseModel, ConfigDict
from abc import ABC, abstractmethod

TYPE_MAP: Dict[str, Type["MessageSegment"]] = {}


class MessageSegment(BaseModel, ABC):
    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)
    type: ClassVar[str]
    
    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # 只有定义了具体 type 值的子类才注册到 TYPE_MAP
        # 跳过抽象基类（如 DownloadableMessageSegment）
        if hasattr(cls, "type") and isinstance(getattr(cls, "type", None), str):
            TYPE_MAP[cls.type] = cls
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MessageSegment":
        """从 {"type": "...", "data": {...}} 结构解析"""
        obj = cls(**data.get("data", {}))
        return obj

    def to_dict(self) -> Dict[str, Any]:
        """序列化为 {"type": "...", "data": {...}} 结构"""
        dump: Dict[str, Any] = self.model_dump(exclude={"type"}, exclude_none=True)
        return {"type": self.type, "data": dump}


class MessageArrayDTO(BaseModel):
    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)
    message: List[MessageSegment]

    @classmethod
    def from_list(cls, data: List[Dict[str, Any]]) -> "MessageArrayDTO":
        return cls(message=[parse_message_segment(seg) for seg in data])

    def to_list(self) -> Dict[str, Any]:
        return self.model_dump()
    
    
def parse_message_segment(data: Dict[str, Any]) -> MessageSegment:
    """从 {"type": "...", "data": {...}} 结构或扁平结构解析"""
    seg_type: Any = data.get("type")
    if not seg_type:
        raise ValueError("Missing 'type' field in message segment data")
    
    target_cls: Type[MessageSegment] | None = TYPE_MAP.get(seg_type)
    if not target_cls:
        raise ValueError(f"Unknown message segment type: {seg_type}")
    return target_cls.from_dict(data)
    