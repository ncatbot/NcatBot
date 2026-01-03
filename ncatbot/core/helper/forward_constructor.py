from typing import List, Optional
from ..event import (
    MessageArray,
    Image,
    Text,
    Forward,
    Node,
    File,
    Video,
)


class ForwardConstructor:
    def __init__(
        self,
        user_id: str = "123456",
        nickname: str = "QQ用户",
        content: Optional[List[Node]] = None,
    ):
        self.user_id = user_id
        self.nickname = nickname
        self.content = content if content else []

    def set_author(self, user_id: str, nickname: str):
        """设置当前作者信息，后续添加的消息将使用此作者"""
        self.user_id = user_id
        self.nickname = nickname

    def attach(
        self,
        content: MessageArray,
        user_id: Optional[str] = None,
        nickname: Optional[str] = None,
    ):
        self.content.append(
            Node(
                user_id=user_id if user_id else self.user_id,
                nickname=nickname if nickname else self.nickname,
                content=content,
            )
        )

    def attach_message(
        self,
        message: MessageArray,
        user_id: Optional[str] = None,
        nickname: Optional[str] = None,
    ):
        """添加一条 MessageArray 消息"""
        self.attach(message, user_id, nickname)

    def attach_text(
        self, text: str, user_id: Optional[str] = None, nickname: Optional[str] = None
    ):
        self.attach(MessageArray(Text(text)), user_id, nickname)

    def attach_image(
        self, image: str, user_id: Optional[str] = None, nickname: Optional[str] = None
    ):
        self.attach(MessageArray(Image(file=image)), user_id, nickname)

    def attach_file(
        self, file: str, user_id: Optional[str] = None, nickname: Optional[str] = None
    ):
        self.attach(MessageArray(File(file=file)), user_id, nickname)

    def attach_video(
        self, video: str, user_id: Optional[str] = None, nickname: Optional[str] = None
    ):
        self.attach(MessageArray(Video(file=video)), user_id, nickname)

    def attach_forward(
        self,
        forward: Forward,
        user_id: Optional[str] = None,
        nickname: Optional[str] = None,
    ):
        if forward.content is None:
            raise ValueError("Forward 对象的 content 不能为空")
        self.attach(MessageArray(forward), user_id, nickname)

    def attach_message_id(
        self,
        message_id: str,
        user_id: Optional[str] = None,
        nickname: Optional[str] = None,
    ):
        """通过消息 ID 引用已有消息（暂不支持）"""
        # NapCat 目前不支持通过消息 ID 引用
        pass

    def to_forward(self) -> Forward:
        return Forward(content=self.content)
