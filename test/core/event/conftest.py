"""
pytest 配置文件，提供测试夹具和数据加载器
"""

import ast
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

# 默认数据文件路径（相对于项目根目录）
DEFAULT_DATA_FILE = "dev/data.txt"

# 环境变量名，用于指定自定义数据文件路径
DATA_FILE_ENV_VAR = "NCATBOT_TEST_DATA_FILE"

# 全局标记：数据是否可用
_data_file_path: Optional[Path] = None
_data_available: Optional[bool] = None


def parse_event_dict_str(data_str: str) -> Dict[str, Any] | None:
    """解析事件字典字符串

    支持两种格式:
    1. 标准 JSON 格式（双引号）
    2. Python repr 格式（单引号）
    """
    # 首先尝试标准 JSON 解析
    try:
        return json.loads(data_str)
    except json.JSONDecodeError:
        pass

    # 如果失败，尝试使用 ast.literal_eval 解析 Python 格式
    try:
        return ast.literal_eval(data_str)
    except (ValueError, SyntaxError):
        pass

    return None


def _find_project_root() -> Path:
    """查找项目根目录（包含 pyproject.toml 或 setup.py 的目录）"""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / "setup.py").exists():
            return current
        current = current.parent
    # 如果找不到，使用 conftest.py 的上三级目录作为默认值
    return Path(__file__).resolve().parent.parent.parent.parent


def _resolve_data_file() -> Optional[Path]:
    """解析数据文件路径

    优先级：
    1. 环境变量 NCATBOT_TEST_DATA_FILE 指定的路径
    2. 默认路径 dev/data.txt

    Returns:
        数据文件路径，如果找不到则返回 None
    """
    global _data_file_path, _data_available

    # 如果已经解析过，直接返回缓存结果
    if _data_available is not None:
        return _data_file_path

    project_root = _find_project_root()

    # 1. 检查环境变量
    env_path = os.environ.get(DATA_FILE_ENV_VAR)
    if env_path:
        custom_path = Path(env_path)
        if not custom_path.is_absolute():
            custom_path = project_root / custom_path
        if custom_path.exists() and custom_path.is_file():
            _data_file_path = custom_path
            _data_available = True
            print(f"\n✓ 使用环境变量指定的数据文件: {custom_path}")
            return _data_file_path
        else:
            print(f"\n✗ 环境变量指定的文件不存在: {custom_path}")

    # 2. 检查默认路径
    default_path = project_root / DEFAULT_DATA_FILE
    if default_path.exists() and default_path.is_file():
        _data_file_path = default_path
        _data_available = True
        print(f"\n✓ 使用默认数据文件: {default_path}")
        return _data_file_path

    # 3. 找不到数据文件
    _data_available = False
    _data_file_path = None
    print("\n✗ 未找到测试数据文件")
    print(f"  默认路径: {default_path}")
    print(f"  可通过环境变量 {DATA_FILE_ENV_VAR} 指定自定义路径")
    print("  依赖真实数据的测试将被跳过\n")
    return None


def load_test_data(data_file: Path) -> List[Dict[str, Any]]:
    """加载测试数据文件

    按行解析，查找包含 JSON/Dict 格式且含有 post_type 字段的事件数据
    """
    events = []

    with open(data_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # 查找行中的第一个 { 位置
            brace_start = line.find("{")
            if brace_start == -1:
                continue

            # 从 { 开始提取完整的字典
            dict_str = _extract_dict_from_position(line, brace_start)
            if dict_str:
                event = parse_event_dict_str(dict_str)
                if event and isinstance(event, dict) and "post_type" in event:
                    events.append(event)

    return events


def _extract_dict_from_position(text: str, start_pos: int) -> str | None:
    """从指定位置提取完整的字典字符串"""
    brace_count = 0
    in_string = False
    escape_next = False

    for i in range(start_pos, len(text)):
        char = text[i]

        if escape_next:
            escape_next = False
            continue

        if char == "\\":
            escape_next = True
            continue

        if char == '"' and not in_string:
            in_string = True
        elif char == '"' and in_string:
            in_string = False
        elif char == "'" and not in_string:
            in_string = True
        elif char == "'" and in_string:
            in_string = False
        elif char == "{" and not in_string:
            brace_count += 1
        elif char == "}" and not in_string:
            brace_count -= 1
            if brace_count == 0:
                return text[start_pos : i + 1]

    return None


class TestDataProvider:
    """测试数据提供器，按类型分类存储事件数据"""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self._events: List[Dict[str, Any]] = []
        self._message_events: List[Dict[str, Any]] = []
        self._meta_events: List[Dict[str, Any]] = []
        self._notice_events: List[Dict[str, Any]] = []
        self._request_events: List[Dict[str, Any]] = []
        self._segments_by_type: Dict[str, List[Dict[str, Any]]] = {}
        self._events_by_type: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        self._data_loaded = False
        self._load_all_data()

    @property
    def has_data(self) -> bool:
        """检查是否有可用的测试数据"""
        return self._data_loaded and len(self._events) > 0

    def _load_all_data(self):
        """加载测试数据

        优先从 dev/data.txt 加载，找不到则标记为无数据
        """
        data_file = _resolve_data_file()
        if data_file:
            events = load_test_data(data_file)
            self._events.extend(events)
            self._data_loaded = True

        # 分类事件
        for event in self._events:
            post_type = event.get("post_type")

            # 初始化 post_type 的存储
            if post_type not in self._events_by_type:
                self._events_by_type[post_type] = {}

            if post_type == "message":
                self._message_events.append(event)
                # 按 message_type 分类
                msg_type = event.get("message_type", "unknown")
                if msg_type not in self._events_by_type[post_type]:
                    self._events_by_type[post_type][msg_type] = []
                self._events_by_type[post_type][msg_type].append(event)
                # 提取消息段
                for seg in event.get("message", []):
                    seg_type = seg.get("type")
                    if seg_type:
                        if seg_type not in self._segments_by_type:
                            self._segments_by_type[seg_type] = []
                        self._segments_by_type[seg_type].append(seg)

            elif post_type == "meta_event":
                self._meta_events.append(event)
                # 按 meta_event_type 分类
                meta_type = event.get("meta_event_type", "unknown")
                if meta_type not in self._events_by_type[post_type]:
                    self._events_by_type[post_type][meta_type] = []
                self._events_by_type[post_type][meta_type].append(event)

            elif post_type == "notice":
                self._notice_events.append(event)
                # 按 notice_type 或 sub_type (对于 notify) 分类
                notice_type = event.get("notice_type", "unknown")
                if notice_type == "notify":
                    sub_type = event.get("sub_type", "unknown")
                    key = f"notify_{sub_type}"
                else:
                    key = notice_type
                if key not in self._events_by_type[post_type]:
                    self._events_by_type[post_type][key] = []
                self._events_by_type[post_type][key].append(event)

            elif post_type == "request":
                self._request_events.append(event)
                # 按 request_type 分类
                req_type = event.get("request_type", "unknown")
                if req_type not in self._events_by_type[post_type]:
                    self._events_by_type[post_type][req_type] = []
                self._events_by_type[post_type][req_type].append(event)

    @property
    def all_events(self) -> List[Dict[str, Any]]:
        """获取所有事件"""
        return self._events

    @property
    def message_events(self) -> List[Dict[str, Any]]:
        """获取所有消息事件"""
        return self._message_events

    @property
    def meta_events(self) -> List[Dict[str, Any]]:
        """获取所有元事件"""
        return self._meta_events

    @property
    def notice_events(self) -> List[Dict[str, Any]]:
        """获取所有通知事件"""
        return self._notice_events

    @property
    def request_events(self) -> List[Dict[str, Any]]:
        """获取所有请求事件"""
        return self._request_events

    def get_segments_by_type(self, seg_type: str) -> List[Dict[str, Any]]:
        """获取指定类型的消息段"""
        return self._segments_by_type.get(seg_type, [])

    @property
    def available_segment_types(self) -> List[str]:
        """获取所有可用的消息段类型"""
        return list(self._segments_by_type.keys())

    def get_all_segments(self) -> List[Dict[str, Any]]:
        """获取所有消息段"""
        all_segments = []
        for segments in self._segments_by_type.values():
            all_segments.extend(segments)
        return all_segments

    def get_events_by_post_type(self, post_type: str) -> List[Dict[str, Any]]:
        """获取指定 post_type 的所有事件"""
        if post_type == "message":
            return self._message_events
        elif post_type == "meta_event":
            return self._meta_events
        elif post_type == "notice":
            return self._notice_events
        elif post_type == "request":
            return self._request_events
        return []

    def get_events_by_type(
        self, post_type: str, secondary_type: str
    ) -> List[Dict[str, Any]]:
        """获取指定 post_type 和二级类型的事件

        Args:
            post_type: 一级类型 (message, meta_event, notice, request)
            secondary_type: 二级类型 (private, group, heartbeat, lifecycle, poke 等)
        """
        if post_type not in self._events_by_type:
            return []
        return self._events_by_type[post_type].get(secondary_type, [])

    def get_notice_events_by_subtype(self, sub_type: str) -> List[Dict[str, Any]]:
        """获取指定 sub_type 的 notify 事件 (如 poke, lucky_king 等)"""
        return self.get_events_by_type("notice", f"notify_{sub_type}")


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """测试数据目录"""
    return Path(__file__).parent


@pytest.fixture(scope="session")
def data_provider(test_data_dir: Path) -> TestDataProvider:
    """测试数据提供器"""
    return TestDataProvider(test_data_dir)


def _skip_if_no_data(data: List) -> None:
    """如果数据为空则跳过测试"""
    if not data:
        pytest.skip(
            "测试数据不可用 - 请设置 NCATBOT_TEST_DATA_FILE 环境变量或确保 dev/data.txt 存在"
        )


@pytest.fixture
def message_events(data_provider: TestDataProvider) -> List[Dict[str, Any]]:
    """消息事件数据（无数据时自动跳过测试）"""
    events = data_provider.message_events
    _skip_if_no_data(events)
    return events
