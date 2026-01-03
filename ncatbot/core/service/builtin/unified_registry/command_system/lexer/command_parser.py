"""命令解析器

从 Token 序列解析出命令结构。
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

from .tokenizer import Token, TokenType


@dataclass
class Element:
    """命令元素 - 未解析的原始部分"""

    type: str  # "text", "image", "at", etc.
    content: Any  # 原始内容
    position: int  # 在原始序列中的位置

    def __str__(self):
        return f"Element({self.type}, '{self.content}', pos={self.position})"

    def __repr__(self):
        return self.__str__()


@dataclass
class ParsedCommand:
    """解析后的命令结构"""

    options: Dict[str, bool]  # 选项表 {选项名: True}
    named_params: Dict[str, Any]  # 命名参数表 {参数名: 值}
    elements: List[Element]  # 未解析的元素（按位置顺序）
    raw_tokens: List[Token]  # 原始 token 序列

    def __str__(self):
        return (
            f"ParsedCommand(options={self.options}, "
            f"named_params={self.named_params}, "
            f"elements={self.elements})"
        )

    def __repr__(self):
        return self.__str__()

    def get_text_params(self) -> Dict[str, str]:
        """获取文本类型的命名参数"""
        return {k: v for k, v in self.named_params.items() if isinstance(v, str)}

    def get_segment_params(self) -> Dict[str, Any]:
        """获取 MessageSegment 类型的命名参数"""
        return {k: v for k, v in self.named_params.items() if hasattr(v, "type")}


class CommandParser:
    """命令解析器

    从 Token 序列解析出：
    - options: 选项表（布尔状态）
    - named_params: 命名参数表（键值对）
    - elements: 未解析的元素（保持原始位置）
    """

    def parse(self, tokens: List[Token]) -> ParsedCommand:
        """解析 Token 序列

        Args:
            tokens: Token 序列

        Returns:
            ParsedCommand: 解析结果
        """
        options: Dict[str, bool] = {}
        named_params: Dict[str, Any] = {}
        elements: List[Element] = []

        i = 0
        while i < len(tokens) and tokens[i].type != TokenType.EOF:
            token = tokens[i]

            if token.type == TokenType.SHORT_OPTION:
                i = self._handle_short_option(tokens, i, options, named_params)

            elif token.type == TokenType.LONG_OPTION:
                i = self._handle_long_option(tokens, i, options, named_params)

            elif token.type in (TokenType.WORD, TokenType.QUOTED_STRING):
                element = Element(
                    type="text", content=token.value, position=len(elements)
                )
                elements.append(element)
                i += 1

            elif token.type == TokenType.NON_TEXT_ELEMENT:
                # token 此时是 NonTextToken 类型
                non_text = token  # type: NonTextToken
                element = Element(
                    type=non_text.element_type,
                    content=non_text.segment,
                    position=len(elements),
                )
                elements.append(element)
                i += 1

            else:
                # 跳过 SEPARATOR, EOF 等
                i += 1

        return ParsedCommand(
            options=options,
            named_params=named_params,
            elements=elements,
            raw_tokens=tokens,
        )

    def _handle_short_option(
        self,
        tokens: List[Token],
        index: int,
        options: Dict[str, bool],
        named_params: Dict[str, Any],
    ) -> int:
        """处理短选项"""
        token = tokens[index]

        if self._has_assignment(tokens, index):
            # -p=value 形式 → named_params
            name, value = self._parse_assignment(tokens, index)
            named_params[name] = value
            return index + 3  # 跳过 option + separator + value
        else:
            # -v 或 -xvf 形式 → options
            for char in token.value:
                options[char] = True
            return index + 1

    def _handle_long_option(
        self,
        tokens: List[Token],
        index: int,
        options: Dict[str, bool],
        named_params: Dict[str, Any],
    ) -> int:
        """处理长选项"""
        token = tokens[index]

        if self._has_assignment(tokens, index):
            # --name=value 形式 → named_params
            name, value = self._parse_assignment(tokens, index)
            named_params[name] = value
            return index + 3
        else:
            # --verbose 形式 → options
            options[token.value] = True
            return index + 1

    def _has_assignment(self, tokens: List[Token], index: int) -> bool:
        """检查选项是否有赋值"""
        return (
            index + 1 < len(tokens)
            and tokens[index + 1].type == TokenType.SEPARATOR
            and index + 2 < len(tokens)
            and tokens[index + 2].type != TokenType.EOF
            and tokens[index + 2].type
            in (TokenType.WORD, TokenType.QUOTED_STRING, TokenType.NON_TEXT_ELEMENT)
        )

    def _parse_assignment(self, tokens: List[Token], index: int) -> Tuple[str, Any]:
        """解析选项赋值"""
        option_name = tokens[index].value
        value_token = tokens[index + 2]

        if value_token.type == TokenType.NON_TEXT_ELEMENT:
            # value_token 此时是 NonTextToken 类型
            non_text = value_token  # type: NonTextToken
            return option_name, non_text.segment
        else:
            return option_name, value_token.value


# 保持向后兼容的别名
AdvancedCommandParser = CommandParser
