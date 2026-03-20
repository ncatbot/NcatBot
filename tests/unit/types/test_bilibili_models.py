"""
Bilibili 数据模型测试

规范:
  LR-01: LiveRoomInfo.from_raw() 完整解析 — 全字段正确映射
  LR-02: from_raw() 空/缺失字段回退默认值
  LR-03: from_raw() 异常数据返回 None
"""

from ncatbot.types.bilibili.models import (
    AnchorInfo,
    LiveRoomInfo,
    RoomInfo,
    WatchedShow,
)

# ---- 真实结构的测试数据 ----

FULL_RAW = {
    "room_info": {
        "uid": 12345,
        "room_id": 67890,
        "title": "测试直播间",
        "cover": "https://example.com/cover.jpg",
        "background": "https://example.com/bg.jpg",
        "description": "这是一个测试直播间",
        "tags": "游戏,虚拟主播,聊天",
        "live_status": 1,
        "live_start_time": 1700000000,
        "parent_area_name": "虚拟主播",
        "parent_area_id": 9,
        "area_name": "聊天室",
        "area_id": 371,
        "keyframe": "https://example.com/keyframe.jpg",
        "online": 5000,
    },
    "anchor_info": {
        "base_info": {
            "uname": "TestAnchor",
            "face": "https://example.com/face.jpg",
            "gender": "女",
            "official_info": {"title": "bilibili知名UP主"},
        },
        "medal_info": {
            "medal_name": "测试勋章",
            "fansclub": 10000,
        },
        "live_info": {
            "level": 40,
            "score": 123456,
            "upgrade_score": 200000,
        },
    },
    "watched_show": {
        "num": 23000,
        "text_small": "2.3万",
        "text_large": "2.3万人看过",
    },
}


class TestFromRawFull:
    """LR-01: LiveRoomInfo.from_raw() 完整解析"""

    def test_lr01_room_info_fields(self):
        """LR-01: room_info 字段正确映射"""
        info = LiveRoomInfo.from_raw(FULL_RAW)
        assert info is not None

        r = info.room_info
        assert isinstance(r, RoomInfo)
        assert r.uid == 12345
        assert r.room_id == 67890
        assert r.title == "测试直播间"
        assert r.cover_url == "https://example.com/cover.jpg"
        assert r.background_url == "https://example.com/bg.jpg"
        assert r.description == "这是一个测试直播间"
        assert r.tags == ("游戏", "虚拟主播", "聊天")
        assert r.live_status == 1
        assert r.live_start_time == 1700000000
        assert r.parent_area_name == "虚拟主播"
        assert r.parent_area_id == 9
        assert r.area_name == "聊天室"
        assert r.area_id == 371
        assert r.keyframe_url == "https://example.com/keyframe.jpg"
        assert r.online == 5000

    def test_lr01_anchor_info_fields(self):
        """LR-01: anchor_info 字段正确映射"""
        info = LiveRoomInfo.from_raw(FULL_RAW)
        assert info is not None

        a = info.anchor_info
        assert isinstance(a, AnchorInfo)
        assert a.name == "TestAnchor"
        assert a.face_url == "https://example.com/face.jpg"
        assert a.gender == "女"
        assert a.official_info == "bilibili知名UP主"
        assert a.fanclub_name == "测试勋章"
        assert a.fanclub_num == 10000
        assert a.live_level == 40
        assert a.live_score == 123456
        assert a.live_upgrade_score == 200000

    def test_lr01_watched_show_fields(self):
        """LR-01: watched_show 字段正确映射"""
        info = LiveRoomInfo.from_raw(FULL_RAW)
        assert info is not None

        w = info.watched_show
        assert isinstance(w, WatchedShow)
        assert w.num == 23000
        assert w.text_small == "2.3万"
        assert w.text_large == "2.3万人看过"

    def test_lr01_tags_empty_string(self):
        """LR-01: tags 为空字符串时解析为空元组"""
        raw = {"room_info": {"tags": ""}}
        info = LiveRoomInfo.from_raw(raw)
        assert info is not None
        assert info.room_info.tags == ()


class TestFromRawDefaults:
    """LR-02: 空/缺失字段回退默认值"""

    def test_lr02_empty_dict(self):
        """LR-02: 传入空 dict 返回全默认值的 LiveRoomInfo"""
        info = LiveRoomInfo.from_raw({})
        assert info is not None
        assert info.room_info.uid == 0
        assert info.room_info.title == ""
        assert info.room_info.tags == ()
        assert info.anchor_info.name == ""
        assert info.anchor_info.live_level == 0
        assert info.watched_show.num == 0

    def test_lr02_partial_room_info(self):
        """LR-02: room_info 只有部分字段，其余回退默认值"""
        raw = {"room_info": {"title": "部分标题", "uid": 999}}
        info = LiveRoomInfo.from_raw(raw)
        assert info is not None
        assert info.room_info.title == "部分标题"
        assert info.room_info.uid == 999
        assert info.room_info.room_id == 0
        assert info.room_info.online == 0

    def test_lr02_missing_anchor_sub_dicts(self):
        """LR-02: anchor_info 缺少 base_info/medal_info/live_info"""
        raw = {"anchor_info": {}}
        info = LiveRoomInfo.from_raw(raw)
        assert info is not None
        assert info.anchor_info.name == ""
        assert info.anchor_info.fanclub_name == ""
        assert info.anchor_info.live_level == 0


class TestFromRawError:
    """LR-03: 异常数据返回 None"""

    def test_lr03_none_input(self):
        """LR-03: 传入 None 时返回 None（触发 AttributeError）"""
        result = LiveRoomInfo.from_raw(None)  # type: ignore[arg-type]
        assert result is None

    def test_lr03_non_dict_input(self):
        """LR-03: 传入非 dict 类型返回 None"""
        result = LiveRoomInfo.from_raw("not a dict")  # type: ignore[arg-type]
        assert result is None
