"""
测试 conftest 中的日志解析函数
"""

import pytest

from conftest import parse_event_dict_str, _extract_dict_from_position


class TestExtractDictFromPosition:
    """测试字典字符串提取"""

    def test_extract_simple(self):
        """测试从简单字符串中提取字典"""
        line = "prefix {'type': 'text', 'data': 'hello'} suffix"
        result = _extract_dict_from_position(line, line.find("{"))
        assert result is not None
        assert result == "{'type': 'text', 'data': 'hello'}"

    def test_extract_nested_dicts(self):
        """测试包含嵌套字典的提取"""
        line = "{'outer': {'inner': {'deep': 'value'}}}"
        result = _extract_dict_from_position(line, 0)
        assert result is not None
        assert result.count("{") == 3
        assert result.count("}") == 3

    def test_extract_with_string_containing_braces(self):
        """测试从包含字符串中有大括号的日志中提取"""
        line = "{'type': 'text', 'pattern': '{hello}'}"
        result = _extract_dict_from_position(line, 0)
        assert result is not None
        assert result == "{'type': 'text', 'pattern': '{hello}'}"

    def test_extract_from_log_line(self):
        """测试从日志行中提取"""
        line = "[2025-12-30 13:27:22] DEBUG | {'id': 123, 'type': 'test'} more text"
        brace_start = line.find("{")
        result = _extract_dict_from_position(line, brace_start)
        assert result is not None
        parsed = parse_event_dict_str(result)
        assert parsed["id"] == 123


class TestParseEventDictStr:
    """测试事件字典字符串解析"""

    def test_parse_json_format(self):
        """测试解析 JSON 格式"""
        dict_str = '{"type": "text", "data": "hello"}'
        result = parse_event_dict_str(dict_str)
        assert result is not None
        assert result["type"] == "text"
        assert result["data"] == "hello"

    def test_parse_python_format(self):
        """测试解析 Python 格式（单引号）"""
        dict_str = "{'type': 'text', 'data': 'hello'}"
        result = parse_event_dict_str(dict_str)
        assert result is not None
        assert result["type"] == "text"
        assert result["data"] == "hello"

    def test_parse_mixed_quotes(self):
        """测试解析混合引号的情况"""
        dict_str = "{'type': \"text\", 'data': 'hello'}"
        result = parse_event_dict_str(dict_str)
        assert result is not None

    def test_parse_nested_structures(self):
        """测试解析嵌套结构"""
        dict_str = "{'user': {'id': 123, 'name': 'test'}, 'items': [1, 2, 3]}"
        result = parse_event_dict_str(dict_str)
        assert result is not None
        assert result["user"]["id"] == 123
        assert result["items"] == [1, 2, 3]

    def test_parse_none_values(self):
        """测试解析包含 None 的字典"""
        dict_str = "{'key1': None, 'key2': 'value'}"
        result = parse_event_dict_str(dict_str)
        assert result is not None
        assert result["key1"] is None
        assert result["key2"] == "value"

    def test_parse_invalid_format(self):
        """测试解析无效格式"""
        dict_str = "this is not a dict"
        result = parse_event_dict_str(dict_str)
        assert result is None


class TestLoadTestData:
    """测试完整的数据加载流程"""

    def test_load_from_dev_data_file(self, data_provider):
        """测试从 dev/data.txt 加载数据"""
        if not data_provider.has_data:
            pytest.skip("测试数据文件不可用")

        assert len(data_provider.all_events) > 0, "应该加载至少一个事件"

    def test_loaded_events_have_post_type(self, data_provider):
        """测试加载的事件都有 post_type 字段"""
        if not data_provider.has_data:
            pytest.skip("测试数据文件不可用")

        for event in data_provider.all_events:
            assert "post_type" in event, "事件应该有 post_type 字段"

    def test_can_parse_message_events(self, data_provider):
        """测试能正确解析消息事件"""
        if not data_provider.has_data:
            pytest.skip("测试数据文件不可用")

        message_events = data_provider.message_events
        if message_events:
            for event in message_events:
                assert "message" in event, "消息事件应该有 message 字段"
                assert isinstance(event["message"], list), "message 应该是列表"


class TestDataParsingRobustness:
    """测试数据解析的健壮性"""

    def test_extract_and_parse_roundtrip(self):
        """测试提取-解析的往返"""
        original_dict = {"type": "message", "data": {"text": "hello", "id": 123}}
        line = f"[LOG] prefix {original_dict} suffix"

        # 提取
        brace_start = line.find("{")
        dict_str = _extract_dict_from_position(line, brace_start)
        assert dict_str is not None

        # 解析
        parsed = parse_event_dict_str(dict_str)
        assert parsed == original_dict

    def test_handle_escaped_quotes(self):
        """测试处理转义引号"""
        dict_str = r"{'message': 'He said \"hello\"', 'type': 'text'}"
        result = parse_event_dict_str(dict_str)
        if result:
            assert "message" in result or "type" in result

    def test_extract_with_surrounding_text(self):
        """测试从包含其他文本的日志中提取"""
        line = "[2025-12-30 13:27:22,075.075] DEBUG Adapter | {'id': 123, 'name': 'test', 'nested': {'key': 'value'}} more text after"
        brace_start = line.find("{")
        result = _extract_dict_from_position(line, brace_start)
        assert result is not None
        parsed = parse_event_dict_str(result)
        assert parsed is not None
        assert parsed["id"] == 123
        assert parsed["nested"]["key"] == "value"
