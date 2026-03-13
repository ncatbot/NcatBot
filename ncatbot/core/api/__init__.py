"""
NcatBot API 模块

提供与 NapCat 通信的 API 接口。
"""

from .api import BotAPI as BotAPI
from .interface import IBotAPI as IBotAPI
from .utils import AsyncRunner as AsyncRunner
from .utils import run_sync as run_sync
from .utils import generate_sync_methods as generate_sync_methods
