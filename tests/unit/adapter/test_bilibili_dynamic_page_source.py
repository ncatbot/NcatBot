"""BL-23: DynamicPageSource 多 UID 管理与增量检测测试

DynamicPageSource 的 UID 管理、基线初始化、新动态检测逻辑，
不涉及任何网络请求（纯离线单元测试）。

规范:
  BL-23a: UID 增删管理 — add_uid / has_uid / remove_uid / empty 属性
  BL-23b: 基线初始化 — _init_baselines 仅记录已订阅 UID 的最大时间戳
  BL-23c: 新动态检测 — _detect_new_dynamics 按 ts > last_ts 过滤，升序推送
"""

from ncatbot.adapter.bilibili.source.dynamic_page_source import DynamicPageSource


# ─── 辅助工具 ───────────────────────────────────────────────────────────────


def _make_item(uid: int, ts: int) -> dict:
    """构造最小动态 item（仅含解析所需字段）"""
    return {
        "id_str": f"{uid}_{ts}",
        "type": "DYNAMIC_TYPE_WORD",
        "modules": {
            "module_author": {
                "mid": uid,
                "name": f"user_{uid}",
                "pub_ts": ts,
            }
        },
    }


class _Collector:
    """收集回调调用记录"""

    def __init__(self):
        self.calls: list[tuple] = []

    async def __call__(self, source_type: str, raw_data: dict) -> None:
        self.calls.append((source_type, raw_data))


def _make_source(
    watched_uids: list[int] | None = None,
) -> tuple[DynamicPageSource, _Collector]:
    """创建 DynamicPageSource 实例，不启动轮询 task"""
    coll = _Collector()
    src = DynamicPageSource(credential=None, callback=coll, poll_interval=999.0)
    for uid in watched_uids or []:
        src.add_uid(uid)
    return src, coll


# ─── BL-23a: UID 增删管理 ───────────────────────────────────────────────────


class TestBL23aUidManagement:
    """BL-23a: UID 增删管理"""

    def test_bl23a_add_has_uid(self):
        src, _ = _make_source()
        src.add_uid(111)
        assert src.has_uid(111)

    def test_bl23a_remove_uid(self):
        src, _ = _make_source([111, 222])
        src.remove_uid(111)
        assert not src.has_uid(111)
        assert src.has_uid(222)

    def test_bl23a_empty_when_no_uids(self):
        src, _ = _make_source()
        assert src.empty

    def test_bl23a_not_empty_after_add(self):
        src, _ = _make_source([333])
        assert not src.empty

    def test_bl23a_empty_after_remove_all(self):
        src, _ = _make_source([444])
        src.remove_uid(444)
        assert src.empty

    def test_bl23a_remove_clears_last_ts(self):
        src, _ = _make_source([555])
        src._last_ts[555] = 100
        src.remove_uid(555)
        assert 555 not in src._last_ts

    def test_bl23a_duplicate_add_is_idempotent(self):
        src, _ = _make_source([100])
        src.add_uid(100)
        src.add_uid(100)
        assert src.has_uid(100)
        assert len(src._watched_uids) == 1


# ─── BL-23b: 基线初始化 ─────────────────────────────────────────────────────


class TestBL23bInitBaselines:
    """BL-23b: 基线初始化"""

    def test_bl23b_sets_last_ts_for_watched_uid(self):
        src, _ = _make_source([100])
        # 两条动态，取最大 ts
        items = [_make_item(100, 900), _make_item(100, 1000)]
        src._init_baselines(items)
        assert src._last_ts[100] == 1000

    def test_bl23b_ignores_unwatched_uid(self):
        src, _ = _make_source([100])
        items = [_make_item(999, 5000)]  # uid 999 未订阅
        src._init_baselines(items)
        assert 999 not in src._last_ts

    def test_bl23b_multiple_uids_independent(self):
        src, _ = _make_source([100, 200])
        items = [_make_item(100, 500), _make_item(200, 300)]
        src._init_baselines(items)
        assert src._last_ts[100] == 500
        assert src._last_ts[200] == 300

    def test_bl23b_empty_items_leaves_no_baseline(self):
        src, _ = _make_source([100])
        src._init_baselines([])
        assert 100 not in src._last_ts


# ─── BL-23c: 新动态检测 ─────────────────────────────────────────────────────


class TestBL23cNewDynamicDetection:
    """BL-23c: 新动态检测与推送"""

    async def test_bl23c_new_dynamic_triggers_callback(self):
        src, coll = _make_source([100])
        src._last_ts[100] = 1000
        await src._detect_new_dynamics([_make_item(100, 1001)])
        assert len(coll.calls) == 1
        source_type, raw = coll.calls[0]
        assert source_type == "dynamic"
        assert raw["uid"] == 100
        assert raw["status"] == "new"

    async def test_bl23c_equal_ts_no_callback(self):
        src, coll = _make_source([100])
        src._last_ts[100] = 1000
        await src._detect_new_dynamics([_make_item(100, 1000)])
        assert len(coll.calls) == 0

    async def test_bl23c_old_ts_no_callback(self):
        src, coll = _make_source([100])
        src._last_ts[100] = 1000
        await src._detect_new_dynamics([_make_item(100, 999)])
        assert len(coll.calls) == 0

    async def test_bl23c_updates_last_ts_after_push(self):
        src, coll = _make_source([100])
        src._last_ts[100] = 1000
        await src._detect_new_dynamics([_make_item(100, 1005)])
        assert src._last_ts[100] == 1005

    async def test_bl23c_multiple_new_items_sorted_ascending(self):
        """多条新动态按 pub_ts 升序推送"""
        src, coll = _make_source([100])
        src._last_ts[100] = 1000
        items = [_make_item(100, 1030), _make_item(100, 1010), _make_item(100, 1020)]
        await src._detect_new_dynamics(items)
        assert len(coll.calls) == 3
        pushed_ts = [
            c[1]["dynamic"]["modules"]["module_author"]["pub_ts"] for c in coll.calls
        ]
        assert pushed_ts == [1010, 1020, 1030]

    async def test_bl23c_unwatched_uid_not_pushed(self):
        src, coll = _make_source([100])
        src._last_ts[100] = 1000
        items = [_make_item(999, 9999)]  # uid 999 未订阅
        await src._detect_new_dynamics(items)
        assert len(coll.calls) == 0

    async def test_bl23c_no_baseline_zero_treated_as_floor(self):
        """未初始化基线时 last_ts 默认 0，任何 ts > 0 均为新动态"""
        src, coll = _make_source([100])
        # 不调用 _init_baselines —— _last_ts.get(100, 0) == 0
        await src._detect_new_dynamics([_make_item(100, 1)])
        assert len(coll.calls) == 1

    async def test_bl23c_multi_uid_isolation(self):
        """不同 UID 的检测互不干扰"""
        src, coll = _make_source([100, 200])
        src._last_ts[100] = 2000
        src._last_ts[200] = 500
        items = [
            _make_item(100, 1999),  # old for uid 100
            _make_item(200, 600),  # new for uid 200
        ]
        await src._detect_new_dynamics(items)
        assert len(coll.calls) == 1
        assert coll.calls[0][1]["uid"] == 200

    async def test_bl23c_last_ts_is_max_of_pushed(self):
        """推送多条后 last_ts 更新为最大 ts"""
        src, coll = _make_source([100])
        src._last_ts[100] = 1000
        items = [_make_item(100, 1010), _make_item(100, 1050), _make_item(100, 1030)]
        await src._detect_new_dynamics(items)
        assert src._last_ts[100] == 1050
