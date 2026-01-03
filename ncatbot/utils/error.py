from .config import ncatbot_config
from .logger import get_log
import sys
import traceback


class NcatBotError(Exception):
    logger = get_log("NcatBotError")

    def __init__(self, info, log: bool = True, stacklevel: int = 3):
        if log:
            self.logger.error(f"{info}", stacklevel=stacklevel)
            if ncatbot_config.debug:
                # 检查是否有活动的异常上下文
                if sys.exc_info()[0] is not None:
                    self.logger.info(
                        f"stacktrace:\n{traceback.format_exc()}", stacklevel=stacklevel
                    )
                else:
                    # 没有活动异常时，输出当前调用栈
                    self.logger.info(
                        f"stacktrace:\n{''.join(traceback.format_stack()[:-1])}",
                        stacklevel=stacklevel,
                    )
        super().__init__(info)


class AdapterEventError(Exception):
    logger = get_log("AdapterEventError")

    def __init__(self, info, log: bool = True):
        if log:
            self.logger.error(f"{info}", stacklevel=2)
            if ncatbot_config.debug:
                # 检查是否有活动的异常上下文
                if sys.exc_info()[0] is not None:
                    self.logger.info(f"stacktrace:\n{traceback.format_exc()}")
                else:
                    # 没有活动异常时，输出当前调用栈
                    self.logger.info(
                        f"stacktrace:\n{''.join(traceback.format_stack()[:-1])}"
                    )
        super().__init__(info)


class NcatBotValueError(NcatBotError):
    def __init__(self, var_name, val_name, must_be: bool = False):
        super().__init__(
            f"{var_name} 的值{'必须' if must_be else '不能'}为 {val_name}", stacklevel=3
        )


class NcatBotConnectionError(Exception):
    def __init__(self, info):
        super().__init__(f"网络连接错误: {info}")
