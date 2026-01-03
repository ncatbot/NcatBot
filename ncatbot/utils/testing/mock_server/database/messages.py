"""
消息操作

Mock 数据库的消息相关操作。
"""
# pyright: reportAttributeAccessIssue=false

import time
from typing import List, Optional


class MessageOperationsMixin:
    """消息操作混入类"""

    # 以下属性/方法由 MockDatabase 提供（类型声明仅供参考）
    _data: dict

    def send_group_message(
        self,
        group_id: str,
        message: List[dict],
        user_id: Optional[str] = None,
    ) -> str:
        """发送群消息"""
        bot = self.get_login_info()
        sender_id = user_id or bot.get("user_id")

        msg_id = self._generate_message_id()
        group_key = str(group_id)

        if group_key not in self._data["group_messages"]:
            self._data["group_messages"][group_key] = []

        # 获取发送者信息
        sender_info = self.get_group_member_info(str(group_id), str(sender_id)) or {
            "user_id": sender_id,
            "nickname": "Unknown",
        }

        msg_data = {
            "message_id": msg_id,
            "message_type": "group",
            "group_id": group_id,
            "user_id": sender_id,
            "message": message,
            "raw_message": self._message_to_raw(message),
            "time": int(time.time()),
            "sender": sender_info,
            "message_seq": self._get_message_seq(f"group_{group_id}"),
        }

        self._data["group_messages"][group_key].append(msg_data)
        return msg_id

    def send_private_message(
        self,
        target_id: str,
        message: List[dict],
        user_id: Optional[str] = None,
    ) -> str:
        """发送私聊消息"""
        bot = self.get_login_info()
        sender_id = user_id or bot.get("user_id")

        msg_id = self._generate_message_id()

        # 使用双方 ID 的组合作为会话键
        ids = sorted([str(sender_id), str(target_id)])
        session_key = f"{ids[0]}_{ids[1]}"

        if session_key not in self._data["private_messages"]:
            self._data["private_messages"][session_key] = []

        # 获取发送者信息
        sender_info = self.get_stranger_info(str(sender_id)) or {
            "user_id": sender_id,
            "nickname": "Unknown",
        }

        msg_data = {
            "message_id": msg_id,
            "message_type": "private",
            "user_id": sender_id,
            "target_id": target_id,
            "message": message,
            "raw_message": self._message_to_raw(message),
            "time": int(time.time()),
            "sender": sender_info,
            "message_seq": self._get_message_seq(session_key),
        }

        self._data["private_messages"][session_key].append(msg_data)
        return msg_id

    def get_message(self, message_id: str) -> Optional[dict]:
        """获取消息"""
        # 搜索群消息
        for messages in self._data["group_messages"].values():
            for msg in messages:
                if str(msg.get("message_id")) == str(message_id):
                    return msg

        # 搜索私聊消息
        for messages in self._data["private_messages"].values():
            for msg in messages:
                if str(msg.get("message_id")) == str(message_id):
                    return msg

        return None

    def delete_message(self, message_id: str) -> bool:
        """删除（撤回）消息"""
        # 搜索群消息
        for messages in self._data["group_messages"].values():
            for i, msg in enumerate(messages):
                if str(msg.get("message_id")) == str(message_id):
                    messages.pop(i)
                    return True

        # 搜索私聊消息
        for messages in self._data["private_messages"].values():
            for i, msg in enumerate(messages):
                if str(msg.get("message_id")) == str(message_id):
                    messages.pop(i)
                    return True

        return False

    def get_group_msg_history(
        self,
        group_id: str,
        count: int = 20,
        message_seq: Optional[int] = None,
        reverse_order: bool = False,
    ) -> List[dict]:
        """获取群消息历史"""
        group_key = str(group_id)
        messages = self._data["group_messages"].get(group_key, [])

        if message_seq is not None:
            filtered = [m for m in messages if m.get("message_seq", 0) <= message_seq]
        else:
            filtered = messages[:]

        if reverse_order:
            filtered = list(reversed(filtered))

        return filtered[-count:] if len(filtered) > count else filtered

    def get_friend_msg_history(
        self,
        user_id: str,
        count: int = 20,
        message_seq: Optional[int] = None,
        reverse_order: bool = False,
    ) -> List[dict]:
        """获取好友消息历史"""
        bot = self.get_login_info()
        bot_id = bot.get("user_id")

        # 查找会话
        ids = sorted([str(bot_id), str(user_id)])
        session_key = f"{ids[0]}_{ids[1]}"

        messages = self._data["private_messages"].get(session_key, [])

        if message_seq is not None:
            filtered = [m for m in messages if m.get("message_seq", 0) <= message_seq]
        else:
            filtered = messages[:]

        if reverse_order:
            filtered = list(reversed(filtered))

        return filtered[-count:] if len(filtered) > count else filtered

    @staticmethod
    def _message_to_raw(message: List[dict]) -> str:
        """将消息数组转换为原始文本"""
        parts = []
        for seg in message:
            seg_type = seg.get("type", "")
            data = seg.get("data", {})

            if seg_type == "text":
                parts.append(data.get("text", ""))
            elif seg_type == "at":
                qq = data.get("qq", "")
                parts.append(f"[CQ:at,qq={qq}]")
            elif seg_type == "image":
                parts.append("[CQ:image]")
            elif seg_type == "face":
                parts.append(f"[CQ:face,id={data.get('id', '')}]")
            else:
                parts.append(f"[CQ:{seg_type}]")

        return "".join(parts)
