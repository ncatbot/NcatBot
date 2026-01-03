"""字符串分词器

支持命令行参数解析，包括短选项、长选项、参数赋值和转义字符串处理。
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Any
from ncatbot.utils import NcatBotError


class TokenType(Enum):
    """Token 类型枚举"""

    WORD = "word"  # 普通单词
    SHORT_OPTION = "short_option"  # 短选项 -v, -xvf
    LONG_OPTION = "long_option"  # 长选项 --verbose
    ARGUMENT = "argument"  # 参数值
    QUOTED_STRING = "quoted_string"  # 引用字符串 "content"
    SEPARATOR = "separator"  # 分隔符 =
    NON_TEXT_ELEMENT = "non_text_element"  # 非文本元素
    EOF = "eof"  # 结束标记


class QuoteState(Enum):
    """引号状态"""

    NONE = "none"  # 无引号
    DOUBLE = "double"  # 双引号状态


@dataclass
class Token:
    """词法单元"""

    type: TokenType
    value: str
    position: int

    def __str__(self):
        return f"Token({self.type.value}, '{self.value}', pos={self.position})"

    def __repr__(self):
        return self.__str__()


@dataclass
class NonTextToken(Token):
    """非文本元素 Token"""

    segment: Any  # MessageSegment
    element_type: str

    def __init__(self, segment, position: int):
        element_type = self._get_element_type(segment)
        super().__init__(
            type=TokenType.NON_TEXT_ELEMENT,
            value=f"[{element_type}]",
            position=position,
        )
        self.segment = segment
        self.element_type = element_type

    def _get_element_type(self, segment) -> str:
        """根据 MessageSegment 类型获取元素类型"""
        type_map = {
            "At": "at",
            "Image": "image",
            "Video": "video",
            "Face": "face",
            "Reply": "reply",
            "Node": "node",
            "Forward": "forward",
        }
        class_name = segment.__class__.__name__
        return type_map.get(class_name) or class_name.lower()


class QuoteMismatchError(NcatBotError):
    """引号不匹配错误"""

    def __init__(self, position: int, quote_char: str):
        super().__init__(f"Position {position}: Unmatched quote '{quote_char}'")
        self.position = position
        self.quote_char = quote_char


class InvalidEscapeSequenceError(NcatBotError):
    """无效转义序列错误"""

    def __init__(self, position: int, sequence: str):
        super().__init__(f"Position {position}: Invalid escape sequence '\\{sequence}'")
        self.position = position
        self.sequence = sequence


class StringTokenizer:
    """字符串分词器

    将输入字符串解析为 Token 序列，支持：
    - 短选项：-v, -x, -xvf (组合)
    - 长选项：--verbose, --help
    - 参数赋值：-p=1234, --para=value
    - 转义字符串："有 空格 的 字符串"
    - 转义序列：\\", \\\\, \\n, \\t, \\r
    """

    # 支持的转义序列映射
    ESCAPE_SEQUENCES = {
        '"': '"',
        "\\": "\\",
        "n": "\n",
        "t": "\t",
        "r": "\r",
        "/": "/",
    }

    def __init__(self, text: str):
        self.text = text
        self.length = len(text)
        self.position = 0
        self.tokens: List[Token] = []

    def tokenize(self) -> List[Token]:
        """执行分词，返回 Token 列表"""
        self.tokens = []
        self.position = 0

        while self.position < self.length:
            self._skip_whitespace()
            if self.position >= self.length:
                break

            char = self.text[self.position]

            if char == '"':
                self._parse_quoted_string()
            elif char == "-" and self._peek() == "-":
                self._parse_long_option()
            elif char == "-" and self._peek() and self._peek() != "-":
                self._parse_short_option()
            elif char == "=":
                self._add_token(TokenType.SEPARATOR, char)
                self.position += 1
            else:
                self._parse_word()

        self._add_token(TokenType.EOF, "")
        return self.tokens

    def _peek(self, offset: int = 1) -> Optional[str]:
        """查看后续字符"""
        peek_pos = self.position + offset
        if peek_pos < self.length:
            return self.text[peek_pos]
        return None

    def _skip_whitespace(self):
        """跳过空白字符"""
        while self.position < self.length and self.text[self.position].isspace():
            self.position += 1

    def _add_token(self, token_type: TokenType, value: str):
        """添加 Token"""
        token = Token(token_type, value, self.position - len(value))
        self.tokens.append(token)

    def _parse_quoted_string(self):
        """解析引用字符串"""
        start_pos = self.position
        self.position += 1  # 跳过开始引号

        value = ""
        while self.position < self.length:
            char = self.text[self.position]

            if char == '"':
                self.position += 1
                self._add_token(TokenType.QUOTED_STRING, value)
                return
            elif char == "\\":
                self.position += 1
                if self.position >= self.length:
                    raise InvalidEscapeSequenceError(self.position - 1, "EOF")

                escape_char = self.text[self.position]
                if escape_char in self.ESCAPE_SEQUENCES:
                    value += self.ESCAPE_SEQUENCES[escape_char]
                else:
                    raise InvalidEscapeSequenceError(self.position - 1, escape_char)
                self.position += 1
            else:
                value += char
                self.position += 1

        raise QuoteMismatchError(start_pos, '"')

    def _parse_long_option(self):
        """解析长选项"""
        start_pos = self.position
        self.position += 2  # 跳过 --

        option_name = ""
        while (
            self.position < self.length
            and not self.text[self.position].isspace()
            and self.text[self.position] != "="
        ):
            option_name += self.text[self.position]
            self.position += 1

        if not option_name:
            while (
                self.position < self.length and not self.text[self.position].isspace()
            ):
                self.position += 1
            self._add_token(TokenType.WORD, self.text[start_pos : self.position])
            return

        self._add_token(TokenType.LONG_OPTION, option_name)

    def _parse_short_option(self):
        """解析短选项"""
        start_pos = self.position
        self.position += 1  # 跳过 -

        options = ""
        while self.position < self.length and self.text[self.position].isalpha():
            options += self.text[self.position]
            self.position += 1

        if not options:
            while (
                self.position < self.length and not self.text[self.position].isspace()
            ):
                self.position += 1
            self._add_token(TokenType.WORD, self.text[start_pos : self.position])
            return

        self._add_token(TokenType.SHORT_OPTION, options)

    def _parse_word(self):
        """解析普通单词"""
        value = ""
        while (
            self.position < self.length
            and not self.text[self.position].isspace()
            and self.text[self.position] not in '="'
        ):
            value += self.text[self.position]
            self.position += 1

        if value:
            self._add_token(TokenType.WORD, value)
