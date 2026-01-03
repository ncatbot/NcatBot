"""装饰器验证器

验证命令装饰器的合理性和一致性。
"""

import warnings as warnings_module
from typing import Callable, List, Dict, Set
from ..utils import CommandRegistrationError, OptionSpec, OptionGroupSpec, ParameterSpec


class DecoratorValidator:
    """装饰器验证器

    验证装饰器的合理性和一致性。
    """

    @staticmethod
    def validate_function_decorators(func: Callable):
        """验证函数上的装饰器

        验证内容包括：
        1. 选项名冲突检查（短选项和长选项）
        2. 参数名冲突检查
        3. 选项组验证
        4. 选项名格式验证
        5. 选项组值冲突检查
        """
        validator = _DecoratorValidatorImpl(func)
        validator.validate()


class _DecoratorValidatorImpl:
    """装饰器验证器实现"""

    def __init__(self, func: Callable):
        self.func = func
        self.errors: List[str] = []
        self.warnings: List[str] = []

        # 获取装饰器信息
        self.options: List[OptionSpec] = getattr(func, "__command_options__", [])
        self.params: List[ParameterSpec] = getattr(func, "__command_params__", [])
        self.groups: List[OptionGroupSpec] = getattr(
            func, "__command_option_groups__", []
        )

        # 索引映射
        self.short_options: Dict[str, dict] = {}
        self.long_options: Dict[str, dict] = {}
        self.all_option_names: Set[str] = set()
        self.param_names: Dict[str, dict] = {}
        self.group_names: Dict[str, dict] = {}
        self.all_group_choices: Set[str] = set()

    def validate(self):
        """执行所有验证"""
        self._validate_options()
        self._validate_params()
        self._validate_option_groups()
        self._report_errors()
        self._report_warnings()

    def _validate_options(self):
        """验证选项名冲突和格式"""
        for i, option in enumerate(self.options):
            option_info = f"选项 #{i + 1}"

            # 验证短选项
            if option.short_name:
                self._validate_short_option(option.short_name, i, option_info)

            # 验证长选项
            if option.long_name:
                self._validate_long_option(option.long_name, i, option_info)

            # 检查选项是否为空
            if not option.short_name and not option.long_name:
                self.errors.append(
                    f"{option_info}: 选项必须至少指定一个短选项名或长选项名"
                )

    def _validate_short_option(self, short_name: str, index: int, option_info: str):
        """验证短选项"""
        # 格式验证
        if not short_name.isalnum() or len(short_name) != 1:
            self.errors.append(
                f"{option_info}: 短选项名 '{short_name}' 必须是单个字母或数字"
            )

        # 冲突检查
        if short_name in self.short_options:
            existing_idx = self.short_options[short_name]["index"]
            self.errors.append(
                f"{option_info}: 短选项名 '{short_name}' 与选项 #{existing_idx + 1} 冲突"
            )
        else:
            self.short_options[short_name] = {"index": index}
            self.all_option_names.add(short_name)

    def _validate_long_option(self, long_name: str, index: int, option_info: str):
        """验证长选项"""
        # 格式验证
        if not long_name.replace("-", "").replace("_", "").isalnum():
            self.errors.append(
                f"{option_info}: 长选项名 '{long_name}' 只能包含字母、数字、连字符和下划线"
            )

        if long_name.startswith("--"):
            self.errors.append(
                f"{option_info}: 长选项名 '{long_name}' 不应包含 '--' 前缀"
            )
            self.warnings.append(
                f"{option_info}: 建议将 '{long_name}' 改为 '{long_name.lstrip('-')}'"
            )

        if len(long_name) < 2:
            self.errors.append(
                f"{option_info}: 长选项名 '{long_name}' 至少需要两个字符"
            )

        # 冲突检查
        if long_name in self.long_options:
            existing_idx = self.long_options[long_name]["index"]
            self.errors.append(
                f"{option_info}: 长选项名 '{long_name}' 与选项 #{existing_idx + 1} 冲突"
            )
        else:
            self.long_options[long_name] = {"index": index}
            self.all_option_names.add(long_name)

    def _validate_params(self):
        """验证参数名冲突和格式"""
        for i, param in enumerate(self.params):
            param_info = f"参数 #{i + 1}"
            name = param.name

            # 格式验证
            if not name.replace("_", "").replace("-", "").isalnum():
                self.errors.append(
                    f"{param_info}: 参数名 '{name}' 只能包含字母、数字、连字符和下划线"
                )

            # 冲突检查
            if name in self.param_names:
                existing_idx = self.param_names[name]["index"]
                self.errors.append(
                    f"{param_info}: 参数名 '{name}' 与参数 #{existing_idx + 1} 冲突"
                )
            else:
                self.param_names[name] = {"index": i}

            # 与选项名冲突检查
            if name in self.all_option_names:
                self.errors.append(f"{param_info}: 参数名 '{name}' 与选项名冲突")

    def _validate_option_groups(self):
        """验证选项组"""
        for i, group in enumerate(self.groups):
            group_info = f"选项组 #{i + 1}"
            name = group.name

            if not name:
                self.errors.append(f"{group_info}: 选项组必须指定名称")
                continue

            self._validate_group_name(name, i, group_info)
            self._validate_group_choices(group, group_info)

    def _validate_group_name(self, name: str, index: int, group_info: str):
        """验证选项组名称"""
        # 组名冲突检查
        if name in self.group_names:
            existing_idx = self.group_names[name]["index"]
            self.errors.append(
                f"{group_info}: 选项组名 '{name}' 与选项组 #{existing_idx + 1} 冲突"
            )
        else:
            self.group_names[name] = {"index": index}

        # 组名和选项名冲突检查
        if name in self.all_option_names:
            self.errors.append(f"{group_info}: 选项组名 '{name}' 与选项名冲突")

        # 组名和参数名冲突检查
        if name in self.param_names:
            self.errors.append(f"{group_info}: 选项组名 '{name}' 与参数名冲突")

    def _validate_group_choices(self, group: OptionGroupSpec, group_info: str):
        """验证选项组的选项列表"""
        name = group.name
        choices = group.choices

        if not choices:
            self.errors.append(f"{group_info}: 选项组 '{name}' 必须指定选项列表")
            return

        # 检查选项是否重复
        if len(choices) != len(set(choices)):
            self.errors.append(f"{group_info}: 选项组 '{name}' 的选项列表包含重复项")

        # 检查默认值是否在选项中
        if group.default and group.default not in choices:
            self.errors.append(
                f"{group_info}: 选项组 '{name}' 的默认值 '{group.default}' 不在选项列表中"
            )

        # 检查每个选项值的冲突
        for choice in choices:
            self._validate_group_choice(choice, name, group_info)

    def _validate_group_choice(self, choice: str, group_name: str, group_info: str):
        """验证单个选项组值"""
        # 与其他选项组值冲突
        if choice in self.all_group_choices:
            self.errors.append(
                f"{group_info}: 选项组 '{group_name}' 的值 '{choice}' 与其他选项组的值冲突"
            )
        self.all_group_choices.add(choice)

        # 与短选项名冲突
        if choice in self.short_options:
            existing_idx = self.short_options[choice]["index"]
            self.errors.append(
                f"{group_info}: 选项组 '{group_name}' 的值 '{choice}' "
                f"与短选项 '{choice}' (选项 #{existing_idx + 1}) 冲突"
            )

        # 与长选项名冲突
        if choice in self.long_options:
            existing_idx = self.long_options[choice]["index"]
            self.errors.append(
                f"{group_info}: 选项组 '{group_name}' 的值 '{choice}' "
                f"与长选项 '{choice}' (选项 #{existing_idx + 1}) 冲突"
            )

        # 与参数名冲突
        if choice in self.param_names:
            existing_idx = self.param_names[choice]["index"]
            self.errors.append(
                f"{group_info}: 选项组 '{group_name}' 的值 '{choice}' "
                f"与参数 '{choice}' (参数 #{existing_idx + 1}) 冲突"
            )

    def _report_errors(self):
        """报告错误"""
        if not self.errors:
            return

        error_details = [f"  • {error}" for error in self.errors]
        suggestions = self._generate_suggestions()

        raise CommandRegistrationError(
            self.func.__name__,
            f"装饰器验证失败，发现 {len(self.errors)} 个错误",
            details="\n".join(error_details),
            suggestions=suggestions,
        )

    def _generate_suggestions(self) -> List[str]:
        """生成修复建议"""
        suggestions = []
        error_text = "; ".join(self.errors)

        if "选项名冲突" in error_text:
            suggestions.append("检查是否有重复的选项名，确保每个选项名都是唯一的")

        if "参数名冲突" in error_text:
            suggestions.append("检查是否有重复的参数名，确保每个参数名都是唯一的")

        if "格式" in error_text:
            suggestions.append(
                "确保选项名和参数名符合命名规范：字母、数字、连字符和下划线"
            )

        if "选项组" in error_text:
            suggestions.append("检查选项组配置，确保名称唯一且选项列表正确")

        return suggestions

    def _report_warnings(self):
        """报告警告"""
        for warning in self.warnings:
            warnings_module.warn(f"命令 '{self.func.__name__}': {warning}", UserWarning)
