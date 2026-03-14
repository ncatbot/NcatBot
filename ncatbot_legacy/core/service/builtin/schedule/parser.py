"""
时间解析器

提供定时任务时间参数的解析功能。
"""

import re
from datetime import datetime
from typing import Dict, Union, Optional


class TimeTaskParser:
    """
    时间解析器

    支持以下时间格式：
    - 一次性任务: 'YYYY-MM-DD HH:MM:SS' 或 'YYYY:MM:DD-HH:MM:SS'
    - 每日任务: 'HH:MM'
    - 间隔任务:
        * 基础单位: '120s', '2h30m', '0.5d'
        * 冒号分隔: '00:15:30' (时:分:秒)
        * 自然语言: '2天3小时5秒'
    """

    # 时间单位转换为秒
    TIME_UNITS = {"d": 86400, "h": 3600, "m": 60, "s": 1}

    @classmethod
    def parse(cls, time_str: str) -> Dict[str, Union[str, float]]:
        """
        解析时间参数为调度配置字典

        Args:
            time_str: 时间参数字符串

        Returns:
            调度配置字典:
                - type: 调度类型 ('once'/'daily'/'interval')
                - value: 具体参数 (秒数/时间字符串)

        Raises:
            ValueError: 当时间格式无效时抛出
        """
        # 尝试解析为一次性任务
        result = cls._try_parse_once(time_str)
        if result:
            return result

        # 尝试解析为每日任务
        result = cls._try_parse_daily(time_str)
        if result:
            return result

        # 解析为间隔任务
        try:
            return {"type": "interval", "value": cls._parse_interval(time_str)}
        except ValueError as e:
            raise ValueError(f"无效的时间格式: {time_str}") from e

    @classmethod
    def _try_parse_once(cls, time_str: str) -> Optional[Dict[str, Union[str, float]]]:
        """尝试解析为一次性任务"""
        try:
            # GitHub Action 格式: YYYY:MM:DD-HH:MM:SS
            if re.match(r"^\d{4}:\d{2}:\d{2}-\d{2}:\d{2}:\d{2}$", time_str):
                dt_str = time_str.replace(":", "-", 2).replace("-", " ", 1)
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            else:
                # 标准格式: YYYY-MM-DD HH:MM:SS
                dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")

            now = datetime.now()
            if dt < now:
                raise ValueError("指定的时间已过期")

            return {"type": "once", "value": (dt - now).total_seconds()}
        except ValueError:
            return None

    @classmethod
    def _try_parse_daily(cls, time_str: str) -> Optional[Dict[str, Union[str, float]]]:
        """尝试解析为每日任务"""
        if re.match(r"^([0-1][0-9]|2[0-3]):([0-5][0-9])$", time_str):
            try:
                datetime.strptime(time_str, "%H:%M")
                return {"type": "daily", "value": time_str}
            except ValueError:
                pass
        return None

    @classmethod
    def _parse_interval(cls, time_str: str) -> int:
        """
        解析间隔时间参数为秒数

        Args:
            time_str: 间隔时间字符串

        Returns:
            总秒数

        Raises:
            ValueError: 当格式无效时抛出
        """
        # 单位组合格式 (如 2h30m)
        unit_match = re.match(r"^([\d.]+)([dhms])?$", time_str, re.IGNORECASE)
        if unit_match:
            num, unit = unit_match.groups()
            unit = unit.lower() if unit else "s"
            return int(float(num) * cls.TIME_UNITS[unit])

        # 冒号分隔格式 (如 01:30:00)
        if ":" in time_str:
            parts = list(map(float, time_str.split(":")))
            multipliers = [1, 60, 3600, 86400][-len(parts) :]
            return int(sum(p * m for p, m in zip(parts[::-1], multipliers)))

        # 自然语言格式 (如 2天3小时5秒)
        lang_match = re.match(r"(\d+)\s*天\s*(\d+)\s*小时\s*(\d+)\s*秒", time_str)
        if lang_match:
            d, h, s = map(int, lang_match.groups())
            return d * 86400 + h * 3600 + s

        raise ValueError("无法识别的间隔时间格式")
