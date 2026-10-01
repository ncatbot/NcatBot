"""在线状态 API：公开管理接口到 NapCat 协议的离线回归。"""

import json

import pytest

from ncatbot.adapter.napcat.api.bot_api import NapCatBotAPI
from ncatbot.adapter.napcat.connection.protocol import OB11Protocol
from ncatbot.api.qq import QQAPIClient

pytestmark = pytest.mark.asyncio


class StatusTransport:
    """模拟 NapCat 必填参数校验，通过实际协议 echo 返回响应。"""

    def __init__(self):
        self.requests = []
        self.protocol = OB11Protocol(self)

    async def send(self, data):
        data = json.loads(json.dumps(data))
        self.requests.append(data)
        missing = {"status", "ext_status", "battery_status"} - data["params"].keys()
        await self.protocol.on_message(
            {
                "echo": data["echo"],
                "status": "failed" if missing else "ok",
                "retcode": 1400 if missing else 0,
                "message": f"Expected required property: {sorted(missing)}"
                if missing
                else "",
                "data": None,
            }
        )


async def test_online_status_default_battery():
    """I-23: 旧整数调用自动补齐 NapCat 必填 battery_status，避免 1400。"""
    transport = StatusTransport()
    api = QQAPIClient(NapCatBotAPI(transport.protocol))

    await api.manage.set_online_status(10)

    assert transport.requests[0]["action"] == "set_online_status"
    assert transport.requests[0]["params"] == {
        "status": 10,
        "ext_status": 0,
        "battery_status": 0,
    }


async def test_online_status_preserves_positional_parameters():
    """I-24: 保留第三位置参数 custom_status，并支持关键字指定电量。"""
    transport = StatusTransport()
    api = QQAPIClient(NapCatBotAPI(transport.protocol))

    await api.manage.set_online_status(10, 1000, "legacy", battery_status=75)

    assert transport.requests[0]["params"] == {
        "status": 10,
        "ext_status": 1000,
        "custom_status": "legacy",
        "battery_status": 75,
    }
