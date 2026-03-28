"""飞书富文本 (post) 消息构造器 & MessageArray → post 序列化器"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ncatbot.types.common.segment.array import MessageArray

__all__ = [
    "LarkPostBuilder",
    "message_array_to_post",
]


class LarkPostBuilder:
    """飞书富文本 (post) 消息链式构造器

    用法::

        content = (
            LarkPostBuilder("标题")
            .text("第一行: ", styles=["bold"])
            .link("飞书", "https://www.feishu.cn")
            .newline()
            .text("第二行 ")
            .at("ou_xxxx")
            .newline()
            .img("img_key_xxx")
            .hr()
            .code_block("print('hi')", language="Python")
            .build()
        )
    """

    def __init__(self, title: str = "") -> None:
        self._title = title
        self._lines: List[List[Dict[str, Any]]] = []
        self._current_line: List[Dict[str, Any]] = []

    # ---- 行内元素 ----

    def text(self, text: str, styles: Optional[List[str]] = None) -> LarkPostBuilder:
        """添加文本段"""
        node: Dict[str, Any] = {"tag": "text", "text": text}
        if styles:
            node["style"] = styles
        self._current_line.append(node)
        return self

    def link(
        self,
        text: str,
        href: str,
        styles: Optional[List[str]] = None,
    ) -> LarkPostBuilder:
        """添加超链接"""
        node: Dict[str, Any] = {"tag": "a", "href": href, "text": text}
        if styles:
            node["style"] = styles
        self._current_line.append(node)
        return self

    def at(self, user_id: str, styles: Optional[List[str]] = None) -> LarkPostBuilder:
        """添加 @用户"""
        node: Dict[str, Any] = {"tag": "at", "user_id": user_id}
        if styles:
            node["style"] = styles
        self._current_line.append(node)
        return self

    def emotion(self, emoji_type: str) -> LarkPostBuilder:
        """添加表情"""
        self._current_line.append({"tag": "emotion", "emoji_type": emoji_type})
        return self

    # ---- 块级元素（自成一行） ----

    def img(self, image_key: str) -> LarkPostBuilder:
        """添加图片（独占一行）"""
        self._flush_line()
        self._lines.append([{"tag": "img", "image_key": image_key}])
        return self

    def media(self, file_key: str, image_key: str = "") -> LarkPostBuilder:
        """添加媒体/视频（独占一行）"""
        self._flush_line()
        node: Dict[str, Any] = {"tag": "media", "file_key": file_key}
        if image_key:
            node["image_key"] = image_key
        self._lines.append([node])
        return self

    def hr(self) -> LarkPostBuilder:
        """添加分割线（独占一行）"""
        self._flush_line()
        self._lines.append([{"tag": "hr"}])
        return self

    def code_block(self, text: str, language: str = "") -> LarkPostBuilder:
        """添加代码块（独占一行）"""
        self._flush_line()
        node: Dict[str, Any] = {"tag": "code_block", "text": text}
        if language:
            node["language"] = language
        self._lines.append([node])
        return self

    def md(self, text: str) -> LarkPostBuilder:
        """添加 Markdown 块（独占一行）"""
        self._flush_line()
        self._lines.append([{"tag": "md", "text": text}])
        return self

    # ---- 换行 ----

    def newline(self) -> LarkPostBuilder:
        """结束当前行，开始新行"""
        self._flush_line()
        return self

    # ---- 构建 ----

    def build(self) -> str:
        """构建为 JSON 字符串（可直接作为 send_message 的 content 参数）"""
        self._flush_line()
        post = {
            "zh_cn": {
                "title": self._title,
                "content": self._lines,
            }
        }
        return json.dumps(post, ensure_ascii=False)

    def build_dict(self) -> Dict[str, Any]:
        """构建为字典"""
        self._flush_line()
        return {
            "zh_cn": {
                "title": self._title,
                "content": self._lines,
            }
        }

    # ---- 内部 ----

    def _flush_line(self) -> None:
        if self._current_line:
            self._lines.append(self._current_line)
            self._current_line = []


def message_array_to_post(msg: "MessageArray", title: str = "") -> str:
    """将 MessageArray 转换为飞书 post 格式 JSON 字符串

    映射规则:
    - PlainText → {"tag": "text", "text": "..."}  (遇 \\n 换行)
    - At → {"tag": "at", "user_id": "..."}
    - Image → {"tag": "img", "image_key": "..."}  (独占一行)
    - Video → {"tag": "media", "file_key": "..."}  (独占一行)
    - Reply 段被忽略（飞书引用回复通过 reply_message API 实现）
    """
    from ncatbot.types.common.segment.text import At, PlainText, Reply
    from ncatbot.types.common.segment.media import Image, Video

    builder = LarkPostBuilder(title)

    for seg in msg:
        if isinstance(seg, Reply):
            continue
        elif isinstance(seg, PlainText):
            lines = seg.text.split("\n")
            for i, line_text in enumerate(lines):
                if line_text:
                    builder.text(line_text)
                if i < len(lines) - 1:
                    builder.newline()
        elif isinstance(seg, At):
            if seg.user_id == "all":
                builder.at("all")
            else:
                builder.at(seg.user_id)
        elif isinstance(seg, Image):
            builder.img(seg.file)
        elif isinstance(seg, Video):
            builder.media(seg.file)
        else:
            # 未知段类型 → 尝试提取文本表示
            text_repr = getattr(seg, "text", None)
            if text_repr:
                builder.text(str(text_repr))

    return builder.build()
