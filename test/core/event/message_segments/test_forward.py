"""
forward.py 模块测试 - 测试转发消息类型 (Node, Forward)
"""
import pytest
from typing import Dict, Any, List

from ncatbot.core import Node, Forward
from ncatbot.core import (
    MessageArrayDTO,
    parse_message_segment,
)
from ncatbot.core import PlainText


class TestNode:
    """测试 Node 类"""
    
    def test_create_node_basic(self):
        """测试创建基本 Node 实例"""
        content = MessageArrayDTO(message=[PlainText(text="hello")])
        node = Node(user_id="12345678", nickname="Test User", content=content)
        
        assert node.user_id == "12345678"
        assert node.nickname == "Test User"
        assert len(node.content.message) == 1
    
    def test_create_node_with_int_user_id(self):
        """测试使用整数 user_id 创建 Node"""
        content = MessageArrayDTO(message=[PlainText(text="test")])
        node = Node(user_id=12345678, nickname="Test", content=content)
        
        # user_id 应该被转换为字符串
        assert node.user_id == "12345678"
    
    def test_node_with_multiple_messages(self):
        """测试包含多条消息的 Node"""
        content = MessageArrayDTO(message=[
            PlainText(text="Line 1"),
            PlainText(text="Line 2"),
            PlainText(text="Line 3"),
        ])
        node = Node(user_id="12345", nickname="User", content=content)
        
        assert len(node.content.message) == 3


class TestForward:
    """测试 Forward 类"""
    
    def test_create_forward_with_id(self):
        """测试使用 ID 创建 Forward 实例"""
        forward = Forward(id="7589518469182843880")
        
        assert forward.id == "7589518469182843880"
        assert forward.type == "forward"
        assert forward.content is None
    
    def test_create_forward_with_content(self):
        """测试使用内容创建 Forward 实例"""
        content = MessageArrayDTO(message=[PlainText(text="forwarded")])
        nodes = [
            Node(user_id="111", nickname="User1", content=content),
            Node(user_id="222", nickname="User2", content=content),
        ]
        forward = Forward(content=nodes)
        
        assert forward.id is None
        assert forward.content is not None
        assert len(forward.content) == 2
    
    def test_create_forward_with_both(self):
        """测试同时有 ID 和内容的 Forward"""
        content = MessageArrayDTO(message=[PlainText(text="test")])
        nodes = [Node(user_id="123", nickname="Test", content=content)]
        forward = Forward(id="12345", content=nodes)
        
        assert forward.id == "12345"
        assert forward.content is not None
    
    def test_forward_from_dict_with_id(self):
        """测试从字典创建 (仅有 ID)"""
        data = {
            "type": "forward",
            "data": {
                "id": "7589518469182843880"
            }
        }
        forward = Forward.from_dict(data)
        
        assert forward.id == "7589518469182843880"
    
    def test_forward_to_dict_with_id(self):
        """测试序列化 (仅有 ID)"""
        forward = Forward(id="12345")
        result = forward.to_dict()
        
        assert result["type"] == "forward"
        assert result["data"]["id"] == "12345"
    
    def test_forward_roundtrip_with_id(self):
        """测试仅有 ID 的序列化往返"""
        original = Forward(id="99999")
        serialized = original.to_dict()
        restored = parse_message_segment(serialized)
        
        assert isinstance(restored, Forward)
        assert restored.id == original.id


class TestForwardWithRealData:
    """使用真实测试数据测试转发消息"""
    
    def test_real_forward_segments(self, forward_segments: List[Dict[str, Any]]):
        """测试真实的转发消息段"""
        if not forward_segments:
            pytest.skip("No forward segments in test data")
        
        for seg_data in forward_segments:
            seg = parse_message_segment(seg_data)
            assert isinstance(seg, Forward)
            
            # 转发消息应该有 id 或 content
            assert seg.id is not None or seg.content is not None
    
    def test_real_forward_has_valid_id(self, forward_segments: List[Dict[str, Any]]):
        """测试真实转发消息的 ID 有效"""
        if not forward_segments:
            pytest.skip("No forward segments in test data")
        
        for seg_data in forward_segments:
            seg = parse_message_segment(seg_data)
            if seg.id:
                # ID 应该是非空字符串
                assert isinstance(seg.id, str)
                assert len(seg.id) > 0


class TestForwardIntegration:
    """转发消息集成测试"""
    
    def test_nested_forward_structure(self):
        """测试嵌套的转发消息结构"""
        # 创建内层消息
        inner_content = MessageArrayDTO(message=[
            PlainText(text="Inner message 1"),
            PlainText(text="Inner message 2"),
        ])
        
        inner_node = Node(
            user_id="11111",
            nickname="Inner User",
            content=inner_content
        )
        
        # 创建外层消息
        outer_content = MessageArrayDTO(message=[
            PlainText(text="Outer message"),
        ])
        
        outer_node = Node(
            user_id="22222",
            nickname="Outer User",
            content=outer_content
        )
        
        # 创建转发消息
        forward = Forward(content=[inner_node, outer_node])
        
        assert len(forward.content) == 2
        assert forward.content[0].nickname == "Inner User"
        assert forward.content[1].nickname == "Outer User"
    
    def test_forward_with_mixed_message_types(self):
        """测试包含混合消息类型的转发"""
        from ncatbot.core import At, Face
        
        content = MessageArrayDTO(message=[
            PlainText(text="Hello "),
            At(qq="123456"),
            PlainText(text=" "),
            Face(id="317"),
        ])
        
        node = Node(
            user_id="12345",
            nickname="Test User",
            content=content
        )
        
        forward = Forward(content=[node])
        
        assert len(forward.content) == 1
        assert len(forward.content[0].content.message) == 4

    def test_nested_forward_serialization(self):
        """测试嵌套转发消息的序列化（修复 Bug：嵌套转发无法正常发送）"""
        from ncatbot.core.event import MessageArray
        
        # 创建内层转发
        inner_content = MessageArrayDTO(message=[
            PlainText(text="Inner message"),
        ])
        inner_node = Node(
            user_id="10001",
            nickname="Inner User",
            content=inner_content
        )
        inner_forward = Forward(content=[inner_node])
        
        # 创建外层节点，其 content 包含 Forward
        outer_content = MessageArray(inner_forward)
        outer_node = Node(
            user_id="10002",
            nickname="Outer User",
            content=outer_content
        )
        
        # 创建外层转发
        forward = Forward(content=[outer_node])
        
        # 序列化为 API 格式
        result = forward.to_forward_dict()
        
        # 验证结构
        assert "messages" in result
        assert len(result["messages"]) == 1
        
        outer_msg = result["messages"][0]
        assert outer_msg["type"] == "node"
        assert outer_msg["data"]["name"] == "Outer User"
        assert outer_msg["data"]["uin"] == "10002"
        
        # 嵌套的 Forward 应该展开为节点列表
        inner_content_list = outer_msg["data"]["content"]
        assert len(inner_content_list) == 1
        assert inner_content_list[0]["type"] == "node"
        assert inner_content_list[0]["data"]["name"] == "Inner User"
        assert inner_content_list[0]["data"]["uin"] == "10001"
        
        # 最内层是文本消息
        innermost_content = inner_content_list[0]["data"]["content"]
        assert len(innermost_content) == 1
        assert innermost_content[0]["type"] == "text"
        assert innermost_content[0]["data"]["text"] == "Inner message"

    def test_forward_to_dict_with_content(self):
        """测试 Forward.to_dict() 方法正确序列化内容"""
        content = MessageArrayDTO(message=[
            PlainText(text="Test message"),
        ])
        node = Node(
            user_id="12345",
            nickname="Test User",
            content=content
        )
        forward = Forward(content=[node])
        
        result = forward.to_dict()
        
        assert result["type"] == "forward"
        assert "content" in result["data"]
        assert len(result["data"]["content"]) == 1
        
        # 验证节点格式
        node_dict = result["data"]["content"][0]
        assert node_dict["type"] == "node"
        assert node_dict["data"]["name"] == "Test User"
        assert node_dict["data"]["uin"] == "12345"
        assert node_dict["data"]["content"][0]["type"] == "text"
        assert node_dict["data"]["content"][0]["data"]["text"] == "Test message"
