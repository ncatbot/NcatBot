"""日志核心：BoundLogger 包装器和 get_log 工厂函数。"""

import logging
from typing import Any, Optional

# 记录所有 early logger 创建的临时 handler，供 setup_logging() 清理
_early_handlers: list[tuple[logging.Logger, logging.Handler]] = []


class BoundLogger:
    """包装标准 Logger，支持 bind 上下文和消息预处理。

    用法:
        log = get_log("plugin.my_plugin")
        log.info("启动完成")

        # 绑定上下文
        log = log.bind(user_id="12345", group_id="67890")
        log.info("收到消息")  # extra 中自动携带 user_id, group_id
    """

    __slots__ = ("_logger", "_context")

    def __init__(self, logger: logging.Logger, context: dict[str, Any] | None = None):
        self._logger = logger
        self._context = context or {}

    # ---- 核心 API ----

    def bind(self, **kwargs: Any) -> "BoundLogger":
        """返回携带新上下文的 BoundLogger（不可变，返回新实例）。"""
        merged = {**self._context, **kwargs}
        return BoundLogger(self._logger, merged)

    def unbind(self, *keys: str) -> "BoundLogger":
        """移除指定上下文键，返回新实例。"""
        new_ctx = {k: v for k, v in self._context.items() if k not in keys}
        return BoundLogger(self._logger, new_ctx)

    # ---- 日志方法 ----

    def debug(self, msg: str, *args, **kwargs):
        self._log(logging.DEBUG, msg, args, kwargs)

    def info(self, msg: str, *args, **kwargs):
        self._log(logging.INFO, msg, args, kwargs)

    def warning(self, msg: str, *args, **kwargs):
        self._log(logging.WARNING, msg, args, kwargs)

    def error(self, msg: str, *args, **kwargs):
        self._log(logging.ERROR, msg, args, kwargs)

    def critical(self, msg: str, *args, **kwargs):
        self._log(logging.CRITICAL, msg, args, kwargs)

    def exception(self, msg: str, *args, **kwargs):
        kwargs.setdefault("exc_info", True)
        self._log(logging.ERROR, msg, args, kwargs)

    # ---- 属性代理 ----

    @property
    def name(self) -> str:
        return self._logger.name

    @property
    def level(self) -> int:
        return self._logger.level

    def setLevel(self, level: int | str) -> None:
        self._logger.setLevel(level)

    def isEnabledFor(self, level: int) -> bool:
        return self._logger.isEnabledFor(level)

    # ---- 内部实现 ----

    def _log(self, level: int, msg: str, args: tuple, kwargs: dict):
        if not self._logger.isEnabledFor(level):
            return
        extra = kwargs.pop("extra", {})
        extra.update(self._context)
        kwargs["extra"] = extra
        kwargs.setdefault("stacklevel", 3)
        self._logger.log(level, msg, *args, **kwargs)


def get_log(name: Optional[str] = None) -> BoundLogger:
    """获取 BoundLogger 实例。

    通过 get_log() 创建的 logger 会被显式设为 DEBUG 级别，
    而第三方库的 logger 继承 root 的 INFO 级别，其 DEBUG 自然不输出。

    Args:
        name: logger 名称，None 返回 root logger 的包装。

    Returns:
        BoundLogger 实例。
    """
    logger = logging.getLogger(name)
    if name is not None:
        logger.setLevel(logging.DEBUG)
    return BoundLogger(logger)


def get_early_logger(name: str) -> logging.Logger:
    """获取一个在 setup_logging() 之前就能输出的轻量 logger。

    自带一个简单的 StreamHandler，setup_logging() 初始化时会自动清理。
    适用于配置加载等早期阶段。
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter("[%(name)s] %(levelname)s: %(message)s"))
        logger.addHandler(handler)
        _early_handlers.append((logger, handler))
    return logger


def cleanup_early_handlers() -> None:
    """清理所有 early handler（由 setup_logging 调用）。"""
    for logger, handler in _early_handlers:
        logger.removeHandler(handler)
    _early_handlers.clear()
