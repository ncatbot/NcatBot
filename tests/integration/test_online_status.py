"""在线状态 API：公开管理接口到 NapCat 协议的离线回归。"""

import json

import pytest

from ncatbot.adapter.napcat.api.bot_api import NapCatBotAPI
from ncatbot.adapter.napcat.connection.protocol import OB11Protocol
from ncatbot.api.qq import QQAPIClient
from ncatbot.adapter.mock import MockBotAPI
from ncatbot.types.qq import OnlineStatus

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


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (OnlineStatus.ONLINE, 10),
        (OnlineStatus.Q_ME, 60),
        (OnlineStatus.AWAY, 30),
        (OnlineStatus.BUSY, 50),
        (OnlineStatus.DO_NOT_DISTURB, 70),
        (OnlineStatus.INVISIBLE, 40),
        (12345, 12345),
    ],
)
async def test_online_status_enum_and_integer_wire_format(status, expected):
    """I-25: 枚举发送协议整数；未列入枚举的整数仍原样发送，不强制校验。"""
    transport = StatusTransport()
    api = QQAPIClient(NapCatBotAPI(transport.protocol))

    await api.manage.set_online_status(status)

    params = transport.requests[0]["params"]
    assert type(params["status"]) is int
    assert params == {"status": expected, "ext_status": 0, "battery_status": 0}


@pytest.mark.parametrize("status", [OnlineStatus.ONLINE, 10, 12345])
async def test_online_status_mock_matches_public_interface(status):
    """I-26: Mock API 与真实适配器一致接受枚举、整数及关键字电量参数。"""
    raw_api = MockBotAPI()
    api = QQAPIClient(raw_api)

    await api.manage.set_online_status(status, 1000, "legacy", battery_status=75)

    assert raw_api.get_calls("set_online_status")[0].params == {
        "status": status,
        "ext_status": 1000,
        "custom_status": "legacy",
        "battery_status": 75,
    }
