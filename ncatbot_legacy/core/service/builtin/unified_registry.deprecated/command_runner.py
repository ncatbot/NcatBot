"""命令运行器

负责命令预处理、解析、参数绑定、执行。
"""

from typing import List, Optional, Callable, TYPE_CHECKING

from ncatbot.utils import get_log
from .trigger.binder import ArgumentBinder, BindResult
from .trigger.preprocessor import MessagePreprocessor, PreprocessResult
from .trigger.resolver import CommandResolver
from .command_system.lexer.tokenizer import StringTokenizer, Token

if TYPE_CHECKING:
    from ncatbot.core import MessageEvent, BotClient
    from .executor import FunctionExecutor

LOG = get_log("CommandRunner")


class CommandRunner:
    """命令运行器

    负责：
    - 消息预处理和前缀检测
    - 命令解析和匹配
    - 参数绑定
    - 命令执行
    """

    def __init__(
        self,
        prefixes: List[str],
        executor: "FunctionExecutor",
    ):
        self._executor = executor
        self._binder = ArgumentBinder()

        # 初始化预处理器
        self._preprocessor = MessagePreprocessor(
            prefixes=prefixes,
            require_prefix=False,
            case_sensitive=False,
        )

        # 初始化解析器
        self._resolver = CommandResolver(
            allow_hierarchical=False,
            prefixes=prefixes,
            case_sensitive=False,
        )

    @property
    def preprocessor(self) -> MessagePreprocessor:
        """获取预处理器"""
        return self._preprocessor

    @property
    def resolver(self) -> CommandResolver:
        """获取解析器"""
        return self._resolver

    def get_plugin_instance_if_needed(
        self,
        bot_client: "BotClient",
        func: Callable,
        name: str,
    ):
        """获取命令所属插件实例（如果适用）"""
        plugin_class = bot_client.get_plugin_class_by_name(name)
        if func in plugin_class.__dict__.values():
            return bot_client.get_plugin(plugin_class)
        return None

    async def run(self, event: "MessageEvent", bot_client: "BotClient") -> bool:
        """运行命令处理

        Args:
            event: 消息事件

        Returns:
            是否成功执行命令
        """
        # 前置检查与提取首段文本
        pre: Optional[PreprocessResult] = self._preprocessor.precheck(event)
        if pre is None:
            return False

        text = pre.command_text
        first_word = text.split(" ")[0]

        # 快速筛选可能匹配的命令
        commands = self._resolver.get_commands()
        hit = [
            command
            for command in commands
            if first_word.endswith(command.path_words[0])
        ]
        if not hit:
            return False

        # 分词和解析
        tokenizer = StringTokenizer(text)
        tokens: List[Token] = tokenizer.tokenize()

        prefix, match = self._resolver.resolve_from_tokens(tokens)
        if match is None:
            return False
        if prefix not in match.command.prefixes:
            return False

        LOG.debug(f"命中命令: {match.command.func.__name__}")

        # 参数绑定
        func = match.command.func
        ignore_words = match.path_words
        try:
            bind_result: BindResult = self._binder.bind(
                match.command, event, ignore_words, [prefix]
            )
        except Exception as e:
            LOG.exception(f"参数绑定失败: {e}", exc_info=True)
            return False

        # 执行命令
        try:
            plugin = self.get_plugin_instance_if_needed(
                bot_client, func, match.command.plugin_name
            )
            await self._executor.execute(
                func, plugin, event, *bind_result.args, **bind_result.named_args
            )
        except Exception as e:
            LOG.exception(f"命令 {func.__name__} 执行失败: {e}")
            return False

        return True

    def clear(self) -> None:
        """清理资源"""
        self._resolver.clear()
