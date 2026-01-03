"""参数解析端到端测试

测试：
- 基础参数
- 类型转换
- 短选项/长选项
- 命名参数
- 选项组
- 复杂组合
"""

import pytest


class TestBasicParams:
    """基础参数测试"""

    @pytest.mark.asyncio
    async def test_basic_params_complete(self, params_suite):
        """测试基础参数功能（综合测试）

        测试内容：
        - 单参数
        - 多参数
        - 引用字符串参数
        """
        # 1. 测试单参数
        await params_suite.inject_private_message("/say hello")
        params_suite.assert_reply_sent("你说: hello")

        # 2. 测试多参数
        params_suite.clear_call_history()
        await params_suite.inject_private_message("/concat hello world")
        params_suite.assert_reply_sent("helloworld")

        # 3. 测试引用字符串参数
        params_suite.clear_call_history()
        await params_suite.inject_private_message('/say "hello world"')
        params_suite.assert_reply_sent("你说: hello world")


class TestTypeConversion:
    """类型转换测试"""

    @pytest.mark.asyncio
    async def test_type_conversion_complete(self, params_suite):
        """测试类型转换功能（综合测试）

        测试内容：
        - 整数参数
        - 带运算符的整数参数
        - 整数默认参数
        """
        # 1. 测试整数参数
        await params_suite.inject_private_message("/calc 10 5")
        params_suite.assert_reply_sent("结果: 15")

        # 2. 测试带运算符的整数参数
        params_suite.clear_call_history()
        await params_suite.inject_private_message("/calc 10 5 -")
        params_suite.assert_reply_sent("结果: 5")

        # 3. 测试整数默认参数
        params_suite.clear_call_history()
        await params_suite.inject_private_message("/repeat abc 3")
        params_suite.assert_reply_sent("abcabcabc")


class TestShortOptions:
    """短选项测试"""

    @pytest.mark.asyncio
    async def test_short_options_complete(self, params_suite):
        """测试短选项功能（综合测试）

        测试内容：
        - 基础列表命令
        - 单个短选项
        - 组合短选项
        - 所有选项加路径
        """
        # 1. 测试基础列表命令
        await params_suite.inject_private_message("/list")
        params_suite.assert_reply_sent("列出目录: .")

        # 2. 测试单个短选项
        params_suite.clear_call_history()
        await params_suite.inject_private_message("/list -l")
        params_suite.assert_reply_sent("列出目录: . (长格式)")

        # 3. 测试组合短选项
        params_suite.clear_call_history()
        await params_suite.inject_private_message("/list -la")
        params_suite.assert_reply_sent("列出目录: . (长格式, 显示隐藏)")

        # 4. 测试所有选项加路径
        params_suite.clear_call_history()
        await params_suite.inject_private_message("/list -lah /home")
        params_suite.assert_reply_sent("列出目录: /home (长格式, 显示隐藏, 人类可读)")


class TestLongOptions:
    """长选项测试"""

    @pytest.mark.asyncio
    async def test_long_options_complete(self, params_suite):
        """测试长选项功能（综合测试）

        测试内容：
        - 基础备份命令
        - 压缩选项
        - 多个长选项
        """
        # 1. 测试基础备份命令
        await params_suite.inject_private_message("/backup /data")
        params_suite.assert_reply_sent("备份 /data")

        # 2. 测试压缩选项
        params_suite.clear_call_history()
        await params_suite.inject_private_message("/backup /data --compress")
        params_suite.assert_reply_sent("备份 /data 到 /backup [压缩]")

        # 3. 测试多个长选项
        params_suite.clear_call_history()
        await params_suite.inject_private_message("/backup /data --compress --encrypt")
        params_suite.assert_reply_sent("备份 /data 到 /backup [压缩, 加密]")


class TestNamedParams:
    """命名参数测试"""

    @pytest.mark.asyncio
    async def test_named_params_complete(self, params_suite):
        """测试命名参数功能（综合测试）

        测试内容：
        - 命名参数（保留单个测试，功能单一）
        """
        params_suite.clear_call_history()
        await params_suite.inject_private_message("/backup /data --dest=/archive")
        params_suite.assert_reply_sent("备份 /data 到 /archive")


class TestOptionGroups:
    """选项组测试"""

    @pytest.mark.asyncio
    async def test_option_groups_complete(self, params_suite):
        """测试选项组功能（综合测试）

        测试内容：
        - 默认格式
        - CSV 格式
        - XML 格式
        """
        # 1. 测试默认格式
        await params_suite.inject_private_message("/export users")
        params_suite.assert_reply_sent("导出 users 数据为 json 格式")

        # 2. 测试 CSV 格式
        params_suite.clear_call_history()
        await params_suite.inject_private_message("/export users --csv")
        params_suite.assert_reply_sent("导出 users 数据为 csv 格式")

        # 3. 测试 XML 格式
        params_suite.clear_call_history()
        await params_suite.inject_private_message("/export users --xml")
        params_suite.assert_reply_sent("导出 users 数据为 xml 格式")


class TestComplexCombinations:
    """复杂组合测试"""

    @pytest.mark.asyncio
    async def test_complex_combinations_complete(self, params_suite):
        """测试复杂组合功能（综合测试）

        测试内容：
        - 基础处理命令
        - 指定输出
        - 带标志的处理命令
        - 引用文件名
        """
        # 1. 测试基础处理命令
        await params_suite.inject_private_message("/process data.csv")
        params_suite.assert_reply_sent("处理文件: data.csv → result.txt (json格式)")

        # 2. 测试指定输出
        params_suite.clear_call_history()
        await params_suite.inject_private_message(
            "/process data.csv --output=out.xml --format=xml"
        )
        params_suite.assert_reply_sent("处理文件: data.csv → out.xml (xml格式)")

        # 3. 测试带标志的处理命令
        params_suite.clear_call_history()
        await params_suite.inject_private_message("/process data.csv -v --force")
        params_suite.assert_reply_sent("[详细模式]")
        params_suite.assert_reply_sent("[强制模式]")

        # 4. 测试引用文件名
        params_suite.clear_call_history()
        await params_suite.inject_private_message('/process "my file.txt" -v')
        params_suite.assert_reply_sent("处理文件: my file.txt")
        params_suite.assert_reply_sent("[详细模式]")
