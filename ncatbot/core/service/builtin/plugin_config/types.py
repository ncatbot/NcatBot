"""
插件配置类型定义

包含：
- PluginConfig: 只读配置字典包装器
- ConfigItem: 配置项元数据封装类
"""

from typing import Any, Dict, Optional, Callable, Iterator, Union, TYPE_CHECKING
from collections.abc import Mapping
import copy

if TYPE_CHECKING:
    from .service import PluginConfigService

# 支持的配置值类型
ConfigValueType = Union[str, int, float, bool, list, dict]


class PluginConfig(Mapping):
    """
    只读配置字典包装器

    禁止直接修改（如 config["key"] = value），
    只能通过 update/set 方法更新，这会触发原子写入操作。
    """

    def __init__(
        self,
        plugin_name: str,
        data: Dict[str, Any],
        config_service: "PluginConfigService",
    ):
        self._plugin_name = plugin_name
        self._data: Dict[str, Any] = copy.deepcopy(data)
        self._config_service = config_service

    # -------------------------------------------------------------------------
    # Mapping 接口实现（只读操作）
    # -------------------------------------------------------------------------

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, key: object) -> bool:
        return key in self._data

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def __repr__(self) -> str:
        return f"PluginConfig({self._plugin_name!r}, {self._data!r})"

    # -------------------------------------------------------------------------
    # 禁止的操作
    # -------------------------------------------------------------------------

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError(
            f"PluginConfig 不支持直接赋值 config[{key!r}] = value。"
            f"请使用 self.set_config({key!r}, value) 或 self.config.update({key!r}, value)"
        )

    def __delitem__(self, key: str) -> None:
        raise TypeError(
            f"PluginConfig 不支持直接删除 del config[{key!r}]。"
            f"请使用 self.config.remove({key!r})"
        )

    # -------------------------------------------------------------------------
    # 允许的写操作（触发原子保存）
    # -------------------------------------------------------------------------

    def update(self, key: str, value: Any) -> tuple:
        """更新单个配置项（触发原子写入）"""
        result = self._config_service.set_atomic(self._plugin_name, key, value)
        self._data[key] = result[1]
        return result

    def remove(self, key: str) -> Any:
        """删除配置项（触发原子写入）"""
        if key not in self._data:
            raise KeyError(key)
        old_value = self._data.pop(key)
        self._config_service.delete_config_item(self._plugin_name, key)
        return old_value

    def bulk_update(self, updates: Dict[str, Any]) -> None:
        """批量更新配置项（单次原子写入）"""
        if not updates:
            return
        self._config_service.set_plugin_config_atomic(self._plugin_name, updates)
        self._data.update(updates)

    def _sync_from_service(self) -> None:
        """从服务同步数据（内部使用）"""
        self._data = copy.deepcopy(
            self._config_service._configs.get(self._plugin_name, {})
        )


class ConfigItem:
    """配置项封装类"""

    def __init__(
        self,
        name: str,
        default_value: Any,
        description: str,
        value_type: type,
        metadata: Optional[Dict[str, Any]],
        plugin_name: str,
        on_change: Optional[Callable] = None,
    ):
        self.name = name
        self.default_value = default_value
        self.description = description
        self.value_type = value_type
        self.metadata = metadata or {}
        self.plugin_name = plugin_name
        self.on_change = on_change

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ConfigItem):
            return self.name == other.name and self.plugin_name == other.plugin_name
        if isinstance(other, str):
            return self.name == other
        return False

    def parse_value(self, value: Any) -> Any:
        """解析值为目标类型"""
        if self.value_type in (dict, list):
            if isinstance(value, self.value_type):
                return copy.deepcopy(value)
            elif isinstance(value, str):
                import json

                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, self.value_type):
                        return parsed
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"无法将 {value!r} 转换为 {self.value_type.__name__}")

        if self.value_type is bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                if value.lower() in ["true", "1", "yes", "on"]:
                    return True
                elif value.lower() in ["false", "0", "no", "off"]:
                    return False
            raise ValueError(f"Invalid boolean value: {value}")

        return self.value_type(value)
