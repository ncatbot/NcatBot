"""
Bilibili 事件解析器测试

数据来源: tests/fixtures/bilibili_events.json (构造数据, 符合 BiliEventParser 输入格式)

规范:
  BL-01: 直播弹幕 (DANMU_MSG) 解析
  BL-02: 直播礼物 (SEND_GIFT) 解析
  BL-03: 醒目留言 (SUPER_CHAT_MESSAGE) 解析
  BL-04: 大航海 (GUARD_BUY) 解析
  BL-05: 进入/关注 (INTERACT_WORD_V2) 解析
  BL-06: 点赞 (LIKE_INFO_V3_CLICK) 解析
  BL-07: 人气 (VIEW) 解析
  BL-08: 开播/下播 (LIVE/PREPARING) 解析
  BL-09: 直播间变更 + 禁言/解禁 + 观看人数变更
  BL-10: 弹幕聚合 + 进场特效 + 系统连接事件
  BL-11: 私信解析
  BL-12: 私信撤回解析
  BL-13: 评论解析
  BL-14: 全量夹具一致性 — 全部事件可解析且非 None
  BL-15: LIVE 事件 live_event_type 设置为 LIVE
  BL-16: PREPARING 事件 live_event_type 设置为 PREPARING
  BL-17: LIVE 事件携带 room_info 时附加 LiveRoomInfo
  BL-18: 动态图文 (DYNAMIC_TYPE_DRAW) 解析
  BL-19: 动态视频 (DYNAMIC_TYPE_AV) 解析
  BL-20: 删除动态解析 — dynamic_event_type 为 DELETED_DYNAMIC
  BL-21: 转发动态 (DYNAMIC_TYPE_FORWARD) 解析
  BL-22: DataPair 时间戳缓存与深拷贝
"""

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from ncatbot.adapter.bilibili.parser import BiliEventParser
from ncatbot.types.bilibili.events import (
    BiliCommentEventData,
    BiliConnectionEventData,
    BiliDynamicEventData,
    BiliPrivateMessageEventData,
    BiliPrivateMessageWithdrawEventData,
    DanmuAggregationEventData,
    DanmuMsgEventData,
    EntryEffectEventData,
    GiftEventData,
    GuardBuyEventData,
    InteractEventData,
    LikeEventData,
    LiveStatusEventData,
    RoomBlockEventData,
    RoomChangeEventData,
    RoomSilentEventData,
    SuperChatEventData,
    ViewEventData,
    WatchedChangeEventData,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent.parent / "fixtures" / "bilibili_events.json"
)


@pytest.fixture(scope="module")
def fixtures() -> List[Dict[str, Any]]:
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def parser() -> BiliEventParser:
    return BiliEventParser(self_id="test_bili")


def _get(fixtures, source_type, cmd=None, **extra):
    """按 source_type + cmd 查找夹具"""
    for fix in fixtures:
        if fix["source_type"] != source_type:
            continue
        raw = fix["raw_data"]
        if cmd and raw.get("type") != cmd:
            continue
        match = True
        for k, v in extra.items():
            if raw.get(k) != v:
                match = False
                break
        if match:
            return fix
    pytest.skip(f"夹具中不存在 source_type={source_type}, cmd={cmd}")


class TestDanmu:
    """BL-01: 直播弹幕"""

    def test_bl01_danmu_msg(self, parser, fixtures):
        fix = _get(fixtures, "live", "DANMU_MSG")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, DanmuMsgEventData)
        assert result.user_id == "10001"
        assert result.user_name == "TestUser1"
        assert result.message.text == "测试弹幕消息"
        assert result.sender.medal_name == "TestMedal"


class TestGift:
    """BL-02: 直播礼物"""

    def test_bl02_send_gift(self, parser, fixtures):
        fix = _get(fixtures, "live", "SEND_GIFT")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, GiftEventData)
        assert result.gift_name == "辣条"
        assert result.num == 5
        assert result.price == 100


class TestSuperChat:
    """BL-03: 醒目留言"""

    def test_bl03_super_chat(self, parser, fixtures):
        fix = _get(fixtures, "live", "SUPER_CHAT_MESSAGE")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, SuperChatEventData)
        assert result.content == "SC 测试消息"
        assert result.price == 30
        assert result.duration == 60


class TestGuardBuy:
    """BL-04: 大航海"""

    def test_bl04_guard_buy(self, parser, fixtures):
        fix = _get(fixtures, "live", "GUARD_BUY")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, GuardBuyEventData)
        assert result.guard_level == 3
        assert result.price == 198000


class TestInteract:
    """BL-05: 进入/关注"""

    def test_bl05_interact(self, parser, fixtures):
        fix = _get(fixtures, "live", "INTERACT_WORD_V2")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, InteractEventData)
        assert result.interact_type == 1


class TestLike:
    """BL-06: 点赞"""

    def test_bl06_like(self, parser, fixtures):
        fix = _get(fixtures, "live", "LIKE_INFO_V3_CLICK")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, LikeEventData)
        assert result.like_count == 42


class TestView:
    """BL-07: 人气"""

    def test_bl07_view(self, parser, fixtures):
        fix = _get(fixtures, "live", "VIEW")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, ViewEventData)
        assert result.view == 12345


class TestLiveStatus:
    """BL-08: 开播/下播"""

    def test_bl08_live(self, parser, fixtures):
        fix = _get(fixtures, "live", "LIVE")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, LiveStatusEventData)
        assert result.status == "live"

    def test_bl08_preparing(self, parser, fixtures):
        fix = _get(fixtures, "live", "PREPARING")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, LiveStatusEventData)
        assert result.status == "preparing"


class TestRoomEvents:
    """BL-09: 直播间变更 + 禁言 + 观看人数"""

    def test_bl09_room_change(self, parser, fixtures):
        fix = _get(fixtures, "live", "ROOM_CHANGE")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, RoomChangeEventData)
        assert result.title == "测试直播间标题"
        assert result.area_name == "虚拟主播"

    def test_bl09_room_block(self, parser, fixtures):
        fix = _get(fixtures, "live", "ROOM_BLOCK_MSG")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, RoomBlockEventData)
        assert result.user_name == "BadUser"

    def test_bl09_silent_on(self, parser, fixtures):
        fix = _get(fixtures, "live", "ROOM_SILENT_ON")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, RoomSilentEventData)
        assert result.level == 1

    def test_bl09_silent_off(self, parser, fixtures):
        fix = _get(fixtures, "live", "ROOM_SILENT_OFF")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, RoomSilentEventData)
        assert result.second == 0

    def test_bl09_watched_change(self, parser, fixtures):
        fix = _get(fixtures, "live", "WATCHED_CHANGE")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, WatchedChangeEventData)
        assert result.num == 1234


class TestMiscLive:
    """BL-10: 弹幕聚合 + 进场特效 + 系统连接"""

    def test_bl10_danmu_aggregation(self, parser, fixtures):
        fix = _get(fixtures, "live", "DANMU_AGGREGATION")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, DanmuAggregationEventData)
        assert result.aggregation_num == 88

    def test_bl10_entry_effect(self, parser, fixtures):
        fix = _get(fixtures, "live", "ENTRY_EFFECT")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, EntryEffectEventData)
        assert result.user_name == "TestUser8"

    def test_bl10_connection(self, parser, fixtures):
        fix = _get(fixtures, "live", "VERIFICATION_SUCCESSFUL")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, BiliConnectionEventData)
        assert result.event_type == "verification_successful"


class TestPrivateMessage:
    """BL-11: 私信"""

    def test_bl11_private_message(self, parser, fixtures):
        fix = _get(fixtures, "session")
        # 取第一个 session fixture (非撤回)
        for f in fixtures:
            if f["source_type"] == "session" and f["raw_data"].get("msg_type") != "5":
                fix = f
                break
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, BiliPrivateMessageEventData)
        assert result.message.text == "你好，这是一条测试私信"


class TestPrivateMessageWithdraw:
    """BL-12: 私信撤回"""

    def test_bl12_withdraw(self, parser, fixtures):
        for f in fixtures:
            if f["source_type"] == "session" and f["raw_data"].get("msg_type") == "5":
                fix = f
                break
        else:
            pytest.skip("无撤回夹具")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, BiliPrivateMessageWithdrawEventData)
        assert result.msg_key == "key_12345"


class TestComment:
    """BL-13: 评论"""

    def test_bl13_comment(self, parser, fixtures):
        fix = _get(fixtures, "comment")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, BiliCommentEventData)
        assert result.content == "测试评论内容"
        assert result.like_count == 15
        assert result.user_name == "CommentUser"


class TestBulkConsistency:
    """BL-14: 全量一致性"""

    def test_bl14_all_fixtures_parse(self, parser, fixtures):
        """全部夹具事件可解析且非 None"""
        failed = []
        for i, fix in enumerate(fixtures):
            result = parser.parse(fix["source_type"], fix["raw_data"])
            if result is None:
                cmd = fix["raw_data"].get("type", fix["source_type"])
                failed.append((i, cmd))
        assert not failed, f"解析返回 None: {failed}"


class TestLiveEventType:
    """BL-15 / BL-16: live_event_type 正确设置"""

    def test_bl15_live_event_type_is_live(self, parser, fixtures):
        """BL-15: LIVE 事件的 live_event_type 为 BiliLiveEventType.LIVE"""
        from ncatbot.types.bilibili.enums import BiliLiveEventType

        fix = _get(fixtures, "live", "LIVE")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, LiveStatusEventData)
        assert result.live_event_type == BiliLiveEventType.LIVE

    def test_bl16_preparing_event_type_is_preparing(self, parser, fixtures):
        """BL-16: PREPARING 事件的 live_event_type 为 BiliLiveEventType.PREPARING"""
        from ncatbot.types.bilibili.enums import BiliLiveEventType

        fix = _get(fixtures, "live", "PREPARING")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, LiveStatusEventData)
        assert result.live_event_type == BiliLiveEventType.PREPARING


class TestLiveRoomInfoAttach:
    """BL-17: LIVE 事件携带 room_info 时附加 LiveRoomInfo"""

    def test_bl17_live_with_room_info(self, parser):
        """BL-17: callback_info 中携带 room_info 时，解析结果附带 LiveRoomInfo"""
        from ncatbot.types.bilibili.models import LiveRoomInfo

        raw = {
            "type": "LIVE",
            "room_real_id": "12345",
            "room_display_id": "12345",
            "data": {},
            "room_info": {
                "room_info": {
                    "uid": 100,
                    "room_id": 12345,
                    "title": "测试开播",
                    "area_name": "聊天",
                    "live_status": 1,
                    "online": 999,
                },
                "anchor_info": {
                    "base_info": {"uname": "TestStreamer", "face": ""},
                },
                "watched_show": {
                    "num": 500,
                    "text_small": "500",
                    "text_large": "500人看过",
                },
            },
        }
        result = parser.parse("live", raw)
        assert isinstance(result, LiveStatusEventData)
        assert result.room_info is not None
        assert isinstance(result.room_info, LiveRoomInfo)
        assert result.room_info.room_info.title == "测试开播"
        assert result.room_info.anchor_info.name == "TestStreamer"
        assert result.room_info.watched_show.num == 500

    def test_bl17_live_without_room_info(self, parser, fixtures):
        """BL-17: 不携带 room_info 时，字段为 None"""
        fix = _get(fixtures, "live", "LIVE")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, LiveStatusEventData)
        assert result.room_info is None

    def test_bl17_preparing_no_room_info(self, parser, fixtures):
        """BL-17: PREPARING 事件不附加 room_info"""
        fix = _get(fixtures, "live", "PREPARING")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, LiveStatusEventData)
        assert result.room_info is None


# ==================== 动态解析 ====================


def _get_dynamic(fixtures, dynamic_type=None, status=None):
    """按 dynamic_type + status 查找动态夹具"""
    for fix in fixtures:
        if fix["source_type"] != "dynamic":
            continue
        raw = fix["raw_data"]
        dyn = raw.get("dynamic", {})
        if dynamic_type and dyn.get("type") != dynamic_type:
            continue
        if status and raw.get("status") != status:
            continue
        return fix
    pytest.skip(f"夹具中不存在 dynamic_type={dynamic_type}, status={status}")


class TestDynamicDraw:
    """BL-18: 动态图文 (DYNAMIC_TYPE_DRAW)"""

    def test_bl18_draw_dynamic(self, parser, fixtures):
        """BL-18: 图文动态解析字段正确"""
        fix = _get_dynamic(fixtures, "DYNAMIC_TYPE_DRAW")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, BiliDynamicEventData)
        assert result.dynamic_id == "999000111222333"
        assert result.dynamic_type == "DYNAMIC_TYPE_DRAW"
        assert result.uid == "621240130"
        assert result.user_name == "TestDynUser"
        assert result.text == "这是一条图文动态测试"
        assert result.pics_url == [
            "https://example.com/pic1.jpg",
            "https://example.com/pic2.jpg",
        ]
        assert result.pub_ts == 1700000100
        assert result.tag == "置顶"
        assert result.stat is not None
        assert result.stat.comment_count == 10
        assert result.stat.like_count == 50
        assert result.stat.forward_count == 3
        assert result.dynamic_status == "new"


class TestDynamicVideo:
    """BL-19: 动态视频 (DYNAMIC_TYPE_AV)"""

    def test_bl19_video_dynamic(self, parser, fixtures):
        """BL-19: 视频动态解析字段正确"""
        fix = _get_dynamic(fixtures, "DYNAMIC_TYPE_AV")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, BiliDynamicEventData)
        assert result.dynamic_id == "999000111222444"
        assert result.dynamic_type == "DYNAMIC_TYPE_AV"
        assert result.video is not None
        assert result.video.title == "测试视频标题"
        assert result.video.bv_id == "BV1test123"
        assert result.video.av_id == "100200300"
        assert result.video.duration_text == "10:30"
        assert result.video.dynamic_text == "视频动态文本"
        assert result.video.play_count == "12345"
        assert result.video.danmaku_count == "678"


class TestDynamicDeleted:
    """BL-20: 删除动态"""

    def test_bl20_deleted_dynamic(self, parser, fixtures):
        """BL-20: 删除动态的 dynamic_event_type 为 DELETED_DYNAMIC"""
        from ncatbot.types.bilibili.enums import BiliDynamicEventType

        fix = _get_dynamic(fixtures, status="deleted")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, BiliDynamicEventData)
        assert result.dynamic_event_type == BiliDynamicEventType.DELETED_DYNAMIC
        assert result.dynamic_status == "deleted"
        assert result.text == "这条动态被删除了"


class TestDynamicForward:
    """BL-21: 转发动态 (DYNAMIC_TYPE_FORWARD)"""

    def test_bl21_forward_dynamic(self, parser, fixtures):
        """BL-21: 转发动态解析字段正确"""
        fix = _get_dynamic(fixtures, "DYNAMIC_TYPE_FORWARD")
        result = parser.parse(fix["source_type"], fix["raw_data"])
        assert isinstance(result, BiliDynamicEventData)
        assert result.dynamic_type == "DYNAMIC_TYPE_FORWARD"
        assert result.text == "转发一下"
        assert result.forward_dynamic_id == "888000111222333"


class TestDynamicDataPair:
    """BL-22: DataPair 时间戳缓存与深拷贝"""

    def test_bl22_initial_update(self):
        """BL-22: 首次 update 初始化 old/new 双端"""
        from ncatbot.adapter.bilibili.source.dynamic_source import _DynamicDataPair

        pair = _DynamicDataPair()
        item = {"id_str": "111", "modules": {"module_author": {"pub_ts": 100}}}
        pair.update(item, 100)

        assert pair.old_ts == 100
        assert pair.new_ts == 100
        assert pair.old_data["id_str"] == "111"
        assert pair.new_data["id_str"] == "111"
        # old_data 是深拷贝，修改 new_data 不影响 old_data
        pair.new_data["id_str"] = "modified"
        assert pair.old_data["id_str"] == "111"

    def test_bl22_subsequent_update(self):
        """BL-22: 后续 update 将 new 移到 old，新数据放入 new"""
        from ncatbot.adapter.bilibili.source.dynamic_source import _DynamicDataPair

        pair = _DynamicDataPair()
        item1 = {"id_str": "aaa"}
        pair.update(item1, 100)

        item2 = {"id_str": "bbb"}
        pair.update(item2, 200)

        assert pair.old_ts == 100
        assert pair.new_ts == 200
        assert pair.old_data["id_str"] == "aaa"
        assert pair.new_data["id_str"] == "bbb"

    def test_bl22_deep_copy_isolation(self):
        """BL-22: old_data 深拷贝与 new_data 相互独立"""
        from ncatbot.adapter.bilibili.source.dynamic_source import _DynamicDataPair

        pair = _DynamicDataPair()
        item1 = {"id_str": "first", "nested": {"key": "val"}}
        pair.update(item1, 100)

        item2 = {"id_str": "second", "nested": {"key": "val2"}}
        pair.update(item2, 200)

        # old_data 应是 item1 的深拷贝，修改 old_data 不影响 new_data
        pair.old_data["nested"]["key"] = "changed"
        assert pair.new_data["nested"]["key"] == "val2"
