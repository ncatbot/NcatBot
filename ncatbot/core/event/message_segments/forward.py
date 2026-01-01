from typing import Any, Dict, List, Optional, ClassVar, TYPE_CHECKING
from pydantic import field_validator, model_validator
from .base import MessageArrayDTO, MessageSegment, BaseModel


class Node(BaseModel):
    user_id: str
    nickname: str
    content: MessageArrayDTO

    @field_validator("user_id", mode="before")
    def ensure_str(cls, v):
        return str(v) if v is not None else v
    
    def to_node_dict(self) -> Dict[str, Any]:
        """转换为 OneBot 节点格式
        
        处理嵌套转发消息：当 content 中包含 Forward 类型时，
        需要将其展开为节点列表格式。
        """
        content_list = []
        
        if self.content:
            for seg in self.content.message:
                if isinstance(seg, Forward):
                    # 嵌套转发：展开为节点列表
                    if seg.content:
                        for inner_node in seg.content:
                            content_list.append(inner_node.to_node_dict())
                else:
                    # 普通消息段：正常序列化
                    content_list.append(seg.to_dict())
        
        return {
            "type": "node",
            "data": {
                "name": self.nickname,
                "uin": self.user_id,
                "content": content_list,
            }
        }


class Forward(MessageSegment):
    type: ClassVar[str] = "forward"
    id: Optional[str] = None
    content: Optional[List[Node]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典格式
        
        重写基类方法以正确序列化嵌套结构。
        当 Forward 作为消息段被包含时使用此方法。
        """
        if self.content:
            # 有内容时，序列化为节点列表
            content_data = [node.to_node_dict() for node in self.content]
            return {"type": "forward", "data": {"content": content_data}}
        elif self.id:
            # 只有 ID 时
            return {"type": "forward", "data": {"id": self.id}}
        else:
            return {"type": "forward", "data": {}}
    
    def to_forward_dict(self) -> Dict[str, Any]:
        """
        转换为 send_forward_msg API 需要的参数字典
        
        Returns:
            Dict 包含 messages, news 等参数
        """
        if not self.content:
            return {"messages": []}
        
        messages = [node.to_node_dict() for node in self.content]
        return {"messages": messages}
    
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
