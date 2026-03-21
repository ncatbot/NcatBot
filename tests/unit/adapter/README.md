# Adapter 模块测试

源码模块: `ncatbot.adapter.napcat`

## 验证规范

### EventParser (`test_event_parser.py`)

测试 `EventParser` 注册表、路由推导、OB11 JSON 解析及 `NapCatEventParser` 包装器。

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| P-01 | 注册表完整性 | `_registry` 包含全部 17 种内置事件类型 |
| P-02 | `_get_key()` 推导 | message/notice/request/meta_event 各 post_type 正确路由 |
| P-03 | `parse()` 解析真实 OB11 JSON | 私聊/群聊/心跳/生命周期/戳一戳/好友请求/群撤回/禁言/群增 |
| P-04 | 错误处理 | 缺失/未知 post_type → `ValueError` |
| P-05 | NapCatEventParser 包装器 | 缺 post_type → `None`，未知类型 → `None` |
| P-06 | message_sent 映射 | `message_sent` 映射到 `MESSAGE` + `message_type` |
| P-07 | notify 子类型推导 | `notice_type=notify` 时使用 `sub_type` 推导 |

## 运行方式

```bash
# 运行全部 adapter 测试
python -m pytest tests/unit/adapter/ -v
```

### AdapterRegistry (`test_registry.py`)

测试适配器注册表的注册、发现、创建、列举和错误处理。

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| AR-01 | `register()` + `discover()` | 注册后可通过 `discover()` 发现 |
| AR-02 | `list_available()` | 返回所有已注册适配器名称 |
| AR-03 | `create()` | 根据 AdapterEntry 创建适配器实例 |
| AR-04 | `create()` platform 覆盖 | `platform` 参数覆盖默认值 |
| AR-05 | 未知类型 | 抛 `ValueError` |

### BiliEventParser (`test_bilibili_parser.py`)

测试 Bilibili 三路由解析器（直播/私信/评论）。

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| BL-01 | 弹幕 (DANMU_MSG) | DanmuMsgEventData 字段正确 |
| BL-02 | 礼物 (SEND_GIFT) | GiftEventData 字段正确 |
| BL-03 | 醒目留言 (SUPER_CHAT) | SuperChatEventData 字段正确 |
| BL-04 | 大航海 (GUARD_BUY) | GuardBuyEventData 字段正确 |
| BL-05 | 互动 (INTERACT_WORD_V2) | InteractEventData 字段正确 |
| BL-06 | 点赞 (LIKE_INFO_V3_CLICK) | LikeEventData 字段正确 |
| BL-07 | 人气 (VIEW) | ViewEventData 字段正确 |
| BL-08 | 开播/下播 (LIVE/PREPARING) | LiveStatusEventData status 正确 |
| BL-09 | 房间变更 + 禁言 + 观看人数 | RoomChange/Block/Silent/Watched 正确 |
| BL-10 | 弹幕聚合 + 进场 + 连接 | Aggregation/Entry/Connection 正确 |
| BL-11 | 私信 | BiliPrivateMessageEventData 正确 |
| BL-12 | 私信撤回 | BiliPrivateMessageWithdrawEventData 正确 |
| BL-13 | 评论 | BiliCommentEventData 正确 |
| BL-14 | 全量夹具一致性 | 全部事件可解析且非 None |
| BL-15 | LIVE live_event_type | `live_event_type = BiliLiveEventType.LIVE` |
| BL-16 | PREPARING live_event_type | `live_event_type = BiliLiveEventType.PREPARING` |
| BL-17 | LIVE 附加 LiveRoomInfo | 携带 room_info 时解析为 `LiveRoomInfo` |
| BL-18 | 动态图文 (DYNAMIC_TYPE_DRAW) | BiliDynamicEventData 字段正确、tag/stat/pics 正确 |
| BL-19 | 动态视频 (DYNAMIC_TYPE_AV) | DynamicVideoInfo 字段正确 |
| BL-20 | 删除动态 | dynamic_event_type 为 DELETED_DYNAMIC |
| BL-21 | 转发动态 (DYNAMIC_TYPE_FORWARD) | text 和 forward_dynamic_id 正确 |
| BL-22 | DataPair 时间戳缓存 | 首次/后续 update 与深拷贝隔离 |
