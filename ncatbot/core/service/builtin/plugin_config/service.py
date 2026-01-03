"""
插件配置服务

负责所有插件配置的统一管理和持久化。
采用"严格的写时保存"策略，每次写配置时立即持久化到特定配置项。
"""

from typing import Any, Dict, Optional, Callable
from pathlib import Path
import yaml
import aiofiles
import copy

from ...base import BaseService
from ncatbot.utils import get_log
from ncatbot.utils.config.constants import CONFIG_PATH
from .types import PluginConfig, ConfigItem
from .persistence import ConfigPersistence

LOG = get_log("PluginConfigService")


class PluginConfigService(BaseService):
    """插件配置服务 - 统一管理所有插件的配置"""

    name: str = "plugin_config"
    description: str = "插件配置服务 - 统一管理所有插件的配置"

    def __init__(self, **config: Any):
        super().__init__(**config)
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._config_items: Dict[str, Dict[str, ConfigItem]] = {}
        self._config_path = Path(CONFIG_PATH)
        self._dirty = False
        self._persistence = ConfigPersistence(self._config_path)

    async def on_load(self) -> None:
        self._configs = await self._persistence.load_all()
        LOG.info("插件配置服务已加载，已加载 %d 个插件的配置", len(self._configs))

    async def on_close(self) -> None:
        if self._dirty:
            await self._persistence.save_all(self._configs)
        LOG.info("插件配置服务已关闭，配置已保存")

    # -------------------------------------------------------------------------
    # 配置注册
    # -------------------------------------------------------------------------

    def register_config(
        self,
        plugin_name: str,
        name: str,
        default_value: Any,
        description: str = "",
        value_type: type = str,
        metadata: Optional[Dict[str, Any]] = None,
        on_change: Optional[Callable] = None,
    ) -> ConfigItem:
        """注册一个配置项"""
        if plugin_name not in self._config_items:
            self._config_items[plugin_name] = {}

        if name in self._config_items[plugin_name]:
            raise ValueError(f"插件 {plugin_name} 的配置 {name} 已存在")

        if isinstance(value_type, str):
            value_type = eval(value_type)

        config_item = ConfigItem(
            name=name,
            default_value=default_value,
            description=description,
            value_type=value_type,
            metadata=metadata,
            plugin_name=plugin_name,
            on_change=on_change,
        )

        self._config_items[plugin_name][name] = config_item

        if plugin_name not in self._configs:
            self._configs[plugin_name] = {}

        if name not in self._configs[plugin_name]:
            if value_type in (dict, list):
                self._configs[plugin_name][name] = copy.deepcopy(default_value)
            else:
                self._configs[plugin_name][name] = (
                    value_type(default_value)
                    if not isinstance(default_value, value_type)
                    else default_value
                )
            self._dirty = True

        LOG.debug(f"插件 {plugin_name} 注册配置 {name}")
        return config_item

    def get_registered_configs(self, plugin_name: str) -> Dict[str, ConfigItem]:
        """获取指定插件的所有已注册配置项"""
        return self._config_items.get(plugin_name, {})

    def unregister_plugin_configs(self, plugin_name: str) -> None:
        """注销插件的所有配置项注册（不删除配置值，仅清理注册信息）

        用于插件卸载时清理配置项注册，以便插件重新加载时可以再次注册。
        配置值会保留在 _configs 中，实现配置持久化。
        """
        if plugin_name in self._config_items:
            del self._config_items[plugin_name]
            LOG.debug(f"已清理插件 {plugin_name} 的配置项注册")

    # -------------------------------------------------------------------------
    # 配置读写
    # -------------------------------------------------------------------------

    def get(self, plugin_name: str, name: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._configs.get(plugin_name, {}).get(name, default)

    def set(self, plugin_name: str, name: str, value: Any) -> tuple:
        """设置配置值（非原子，仅标记脏数据）"""
        if plugin_name not in self._configs:
            self._configs[plugin_name] = {}

        old_value = self._configs[plugin_name].get(name)

        config_item = self._config_items.get(plugin_name, {}).get(name)
        if config_item:
            value = config_item.parse_value(value)
            if config_item.on_change and old_value != value:
                try:
                    config_item.on_change(old_value, value)
                except Exception as e:
                    LOG.warning(f"配置 {plugin_name}.{name} 变更回调失败: {e}")

        self._configs[plugin_name][name] = value
        self._dirty = True
        return (old_value, value)

    def set_atomic(self, plugin_name: str, name: str, value: Any) -> tuple:
        """设置配置值（原子操作，立即保存该项）

        注意：在异步环境中推荐使用 set_atomic_async 以确保保存完成。
        """
        result = self.set(plugin_name, name, value)
        self._persistence.atomic_save_item(self._configs, plugin_name, name)
        return result

    async def set_atomic_async(self, plugin_name: str, name: str, value: Any) -> tuple:
        """设置配置值（异步原子操作，等待保存完成）

        推荐在异步环境中使用此方法，确保配置保存完成后再继续。
        """
        result = self.set(plugin_name, name, value)
        await self._persistence.atomic_save_item_async(self._configs, plugin_name, name)
        return result

    def delete_config_item(self, plugin_name: str, name: str) -> None:
        """删除单个配置项（原子操作）"""
        if plugin_name in self._configs and name in self._configs[plugin_name]:
            del self._configs[plugin_name][name]
            self._persistence.atomic_save_item(
                self._configs, plugin_name, name, deleted=True
            )

    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """获取指定插件的所有配置（返回副本）"""
        return self._configs.get(plugin_name, {}).copy()

    def get_plugin_config_wrapper(self, plugin_name: str) -> PluginConfig:
        """获取插件配置的只读包装器"""
        if plugin_name not in self._configs:
            self._configs[plugin_name] = {}
        return PluginConfig(plugin_name, self._configs[plugin_name], self)

    async def get_or_migrate_config(
        self, plugin_name: str, legacy_data_file: "Path"
    ) -> PluginConfig:
        """
        TODO: 潜在的不一致问题；外部手工修改和内部修改可能不同步。
        获取插件配置包装器，如果配置不存在且有旧版文件则自动迁移。

        Args:
            plugin_name: 插件名称
            legacy_data_file: 旧版配置文件路径

        Returns:
            PluginConfig 只读配置包装器
        """
        existing_config = self.get_plugin_config(plugin_name)
        if not existing_config and legacy_data_file.exists():
            async with aiofiles.open(legacy_data_file, "r", encoding="utf-8") as f:
                legacy_config = yaml.safe_load(await f.read()) or {}
            if legacy_config:
                await self.migrate_from_legacy(plugin_name, legacy_config)
                LOG.info(f"已从旧版文件迁移插件 {plugin_name} 的配置")
        return self.get_plugin_config_wrapper(plugin_name)

    def set_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> None:
        """批量设置插件配置（非原子）"""
        if plugin_name not in self._configs:
            self._configs[plugin_name] = {}
        self._configs[plugin_name].update(config)
        self._dirty = True

    def set_plugin_config_atomic(
        self, plugin_name: str, config: Dict[str, Any]
    ) -> None:
        """批量设置插件配置（原子操作，只保存修改的配置项）"""
        self.set_plugin_config(plugin_name, config)
        self._persistence.atomic_save_items(
            self._configs, plugin_name, list(config.keys())
        )

    async def set_plugin_config_atomic_async(
        self, plugin_name: str, config: Dict[str, Any]
    ) -> None:
        """批量设置插件配置（异步原子操作，等待保存完成）"""
        self.set_plugin_config(plugin_name, config)
        await self._persistence.atomic_save_items_async(
            self._configs, plugin_name, list(config.keys())
        )

    def delete_plugin_config(self, plugin_name: str) -> None:
        """删除插件的所有配置"""
        if plugin_name in self._configs:
            del self._configs[plugin_name]
            self._dirty = True
        if plugin_name in self._config_items:
            del self._config_items[plugin_name]

    # -------------------------------------------------------------------------
    # 强制操作
    # -------------------------------------------------------------------------

    async def force_save(self) -> None:
        """强制保存所有配置"""
        self._dirty = True
        await self._persistence.save_all(self._configs)
        self._dirty = False

    async def reload_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """
        重载指定插件的配置，从配置文件重新读入。

        Args:
            plugin_name: 插件名称

        Returns:
            重载后的插件配置
        """
        new_config = await self._persistence.load_plugin(plugin_name)
        self._configs[plugin_name] = new_config
        LOG.info(f"已重载插件 {plugin_name} 的配置")
        return new_config

    async def migrate_from_legacy(
        self, plugin_name: str, legacy_config: Dict[str, Any]
    ) -> None:
        """从旧格式迁移配置"""
        if plugin_name not in self._configs:
            self._configs[plugin_name] = {}
        for key, value in legacy_config.items():
            if key not in self._configs[plugin_name]:
                self._configs[plugin_name][key] = value
        self._dirty = True
        LOG.info(f"已迁移插件 {plugin_name} 的旧配置")
