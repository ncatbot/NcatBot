from typing import Any, Dict, List, Optional, ClassVar
from pydantic import field_validator, model_validator
from .base import MessageArrayDTO, MessageSegment, BaseModel


class Node(BaseModel):
    user_id: str
    nickname: str
    content: MessageArrayDTO

    @field_validator("user_id", mode="before")
    def ensure_str(cls, v):
        return str(v) if v is not None else v


class Forward(MessageSegment):
    type: ClassVar[str] = "forward"
    id: Optional[str] = None
    content: Optional[List[Node]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Forward":
        """从字典创建 Forward，处理不完整的 content 数据"""
        seg_data = data.get("data", {})
        
        # 处理 content 字段中的省略数据（如 [...]）
        content = seg_data.get("content")
        if content is not None:
            # 过滤掉省略符号和其他无效数据
            if isinstance(content, list):
                valid_content = []
                for item in content:
                    if isinstance(item, dict) and item is not ...:
                        # 如果项包含 message 字段，说明是完整的消息事件
                        # 需要转换为 Node 格式
                        if "message" in item:
                            node_data = {
                                "user_id": item.get("user_id"),
                                "nickname": item.get("sender", {}).get("nickname", ""),
                                "content": MessageArrayDTO.from_list(item.get("message", []))
                            }
                            valid_content.append(node_data)
                        else:
                            # 否则按原样保存
                            valid_content.append(item)
                
                if not valid_content:
                    seg_data = {**seg_data, "content": None}
                else:
                    seg_data = {**seg_data, "content": valid_content}
        
        return cls(**seg_data)
