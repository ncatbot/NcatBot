"""命令规格数据类定义

提供类型安全的数据结构，替代字典存储选项、选项组和参数配置。
"""

from dataclasses import dataclass
from typing import Callable, Any, List, Optional
import inspect


class FuncSpec:
    def __init__(self, func: Callable):
        self.func = func
        self.aliases = getattr(func, "__aliases__", [])

        # 生成 metadata 以便代码更易于理解
        self.func_name = func.__name__
        self.func_module = func.__module__
        self.func_qualname = func.__qualname__
        self.signature = inspect.signature(func)
        self.param_list = list(self.signature.parameters.values())
        self.param_names = [param.name for param in self.param_list]
        self.param_annotations = [param.annotation for param in self.param_list]


@dataclass
class OptionSpec:
    """选项规格数据类

    替代原有的选项字典存储。
    """

    short_name: Optional[str] = None
    long_name: Optional[str] = None
    description: str = ""

    @property
    def name(self) -> Optional[str]:
        return self.long_name if self.long_name else self.short_name


@dataclass
class OptionGroupSpec:
    """选项组规格数据类

    替代原有的选项组字典存储。
    """

    choices: List[str]
    name: str
    default: str
    description: str = ""


@dataclass
class ParameterSpec:
    """参数规格数据类

    替代原有的参数字典存储。
    """

    name: str
    default: Any = None
    required: Optional[bool] = False
    description: str = ""
    choices: Optional[List[Any]] = None
    is_named: bool = True
    is_positional: bool = False
    index: int = -1  # 用于确认参数位置（param_types 中），由分析器设置


class CommandSpec:
    """命令规格

    彻底分析函数后得到的命令标识器，用于指导参数传递。
    """

    name: str
    plugin_name: str

    def __init__(
        self,
        options: List[OptionSpec],
        option_groups: List[OptionGroupSpec],
        params: List[ParameterSpec],
        param_types: List[type],
        func: Callable,
    ):
        self.options: List[OptionSpec] = options
        self.option_groups: List[OptionGroupSpec] = option_groups
        self.params: List[ParameterSpec] = params
        self.param_types: List[type] = param_types
        self.func: Callable = func

        # 必须外部重新设置的属性
        self.aliases: List[str] = []
        self.description: Optional[str] = None
        self.prefixes: List[str] = []

    def find_option(self, name: str) -> Optional[OptionSpec]:
        """查找匹配的选项"""
        for opt in self.options:
            if opt.name == name or opt.short_name == name:
                return opt
        return None

    def find_option_group(self, choice: str) -> Optional[OptionGroupSpec]:
        """查找包含该选项值的选项组"""
        for group in self.option_groups:
            if choice in group.choices:
                return group
        return None

    def find_param(self, name: str) -> Optional[ParameterSpec]:
        """查找匹配的参数"""
        for param in self.params:
            if param.name == name:
                return param
        return None

    def get_param_type(self, index: int) -> Optional[type]:
        """获取指定索引的参数类型"""
        if 0 <= index < len(self.param_types):
            return self.param_types[index]
        return None
