from .base import MessageArrayDTO, parse_message_segment, MessageSegment
from typing import Any, List, Union, Iterable, Dict, Type, TypeVar, ClassVar, overload
from .media import Image, Video
from .primitives import PlainText, At, Face, Reply
from .forward import Forward
from pydantic.dataclasses import dataclass
import re

T = TypeVar("T", bound=MessageSegment)

@dataclass
class Text(str): # 兼容 4.4.x Text 类型
    type: ClassVar[str] = "text"
    text: str
    pass

@dataclass
class AtAll():
    type: ClassVar[str] = "at"
    qq: str = "all"
    pass

def parse_cq_code_to_onebot11(
    cq_string: str,
) -> List[Dict[str, Union[str, Dict[str, str]]]]:
    """
    将 CQ 码字符串解析为 OneBot 11 规范的消息数组格式，包含转义字符处理

    Args:
        cq_string: 包含 CQ 码的字符串，例如 "[CQ:image,file=123.jpg]这是一段文本[CQ:face,id=123]"

    Returns:
        OneBot 11 规范的消息数组，例如:
        [
            {"type": "image", "data": {"file": "123.jpg"}},
            {"type": "text", "data": {"text": "这是一段文本"}},
            {"type": "face", "data": {"id": "123"}}
        ]
    """
    # 正则表达式匹配 CQ 码
    cq_pattern = re.compile(r"\[CQ:([^,\]]+)(?:,([^\]]+))?\]")

    # 初始化结果列表
    message_segments = []
    last_pos = 0

    # HTML 实体转义映射
    html_unescape_map = {"&amp;": "&", "&#91;": "[", "&#93;": "]", "&#44;": ","}

    def unescape_cq(text: str) -> str:
        """取消 CQ 码中的 HTML 实体转义"""
        for escaped, unescaped in html_unescape_map.items():
            text = text.replace(escaped, unescaped)
        return text

    # 遍历所有匹配的 CQ 码
    for match in cq_pattern.finditer(cq_string):
        # 处理 CQ 码之前的文本（如果有）
        text_before = cq_string[last_pos : match.start()]
        if text_before:
            # 普通文本也需要反转义
            message_segments.append(
                {"type": "text", "data": {"text": unescape_cq(text_before)}}
            )

        # 处理 CQ 码
        cq_type = match.group(1)
        cq_params_str = match.group(2) or ""

        # 解析 CQ 码参数
        params = {}
        for param in cq_params_str.split(","):
            if "=" in param:
                key, value = param.split("=", 1)
                # 对参数值进行反转义处理
                params[key] = unescape_cq(value)

        # 添加到结果列表
        message_segments.append({"type": cq_type, "data": params})

        # 更新最后位置
        last_pos = match.end()

    # 处理最后一个 CQ 码之后的文本（如果有）
    text_after = cq_string[last_pos:]
    if text_after:
        message_segments.append(
            {"type": "text", "data": {"text": unescape_cq(text_after)}}
        )

    return message_segments

def parse_message_segments(data: Any) -> List[MessageSegment]:
    if isinstance(data, dict):
        return [parse_message_segment(data)]
    elif isinstance(data, MessageSegment):
        return [data]
    elif isinstance(data, str):
        segments_data = parse_cq_code_to_onebot11(data)
        return [parse_message_segment(seg) for seg in segments_data]
    elif isinstance(data, AtAll):
        return [At(qq="all")]
    elif isinstance(data, Iterable):
        segments: List[MessageSegment] = []
        for item in data:
            segments.extend(parse_message_segments(item))
        return segments
    return []

class MessageArray(MessageArrayDTO):
    """消息段数组封装类，继承自 MessageArrayDTO"""
    def __init__(self, *args, **kwargs):
        if "message" in kwargs:
            super().__init__(**kwargs)
        else:
            super().__init__(message=parse_message_segments(args))
            
    # -------------------
    # region 构造用接口
    # -------------------
    def add_by_list(self, data: List[Union[dict, MessageSegment]]):
        self.message.extend(parse_message_segments(data))
        return self

    def add_by_segment(self, segment: MessageSegment):
        self.message.append(segment)
        return self

    def add_by_dict(self, data: Dict):
        self.message.extend(parse_message_segments(data))
        return self

    def add_text(self, text: str):
        self.message.extend(parse_message_segments(text))
        return self

    def add_image(self, image: Union[str, Image]):
        """添加图片消息段
        
        Args:
            image: 可以是字符串路径/URL 或 Image 对象
                - URL: "http://example.com/image.jpg"
                - FilePath: "/path/to/image.jpg"
                - Base64: "base64://..."
                - Image 对象: Image(file="...")
        
        Returns:
            self: 支持链式调用
        """
        if isinstance(image, Image):
            self.message.append(image)
        elif isinstance(image, str):
            self.message.append(Image(file=image))
        else:
            raise TypeError(f"image must be str or Image, got {type(image)}")
        return self

    def add_at(self, user_id: Union[str, int]):
        self.message.append(At(qq=str(user_id)))
        return self

    def add_at_all(self):
        self.message.append(At(qq="all"))
        return self

    def add_reply(self, message_id: Union[str, int]):
        self.message.append(Reply(id=str(message_id)))
        return self

    def __add__(self, other):
        messages = self.message + parse_message_segments(other)
        return MessageArray(messages)

    def __radd__(self, other):
        return self.__add__(other)

    def is_forward_msg(self):
        return len(self.filter(Forward))

    # -------------------
    # region 解析用接口
    # -------------------

    def concatenate_text(self) -> str:
        return "".join(msg.text for msg in self.filter(PlainText))

    @overload
    def filter(self, cls: None = None) -> List[MessageSegment]: ...
    
    @overload
    def filter(self, cls: Type[T]) -> List[T]: ...

    def filter(self, cls: Union[Type[T], None] = None) -> Union[List[MessageSegment], List[T]]:
        if cls is None:
            return self.message
        msg = []
        if not issubclass(cls, MessageSegment):
            raise ValueError("过滤的类型必须是 MessageSegment 的子类")
        for item in self.message:
            if isinstance(item, cls):
                msg.append(item)
        return msg

    def filter_text(self) -> List[PlainText]:
        return self.filter(PlainText)

    def filter_at(self) -> List[At]:
        return self.filter(At)

    def filter_image(self) -> List[Image]:
        return self.filter(Image)

    def filter_video(self) -> List[Video]:
        return self.filter(Video)

    def filter_face(self) -> List[Face]:
        return self.filter(Face)

    def is_user_at(self, user_id: Union[str, int], all_except: bool = False) -> bool:
        user_id = str(user_id)
        all_at = False
        
        for at in self.filter(At):
            if at.qq == user_id:
                return True
            if at.qq == "all":
                all_at = True
        return not all_except and all_at

    def __iter__(self): # type: ignore
        return self.message.__iter__()

    def __len__(self):
        return len(self.message)
