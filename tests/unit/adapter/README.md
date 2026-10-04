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

### SnowLumaAdapter (`test_snowluma_adapter.py`)

测试 SnowLuma 适配器的内置注册、配置模型与 CLI 配置钩子。

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| SL-01 | 内置注册 | `adapter_registry.discover()` 包含 `snowluma` |
| SL-02 | `SnowLumaConfig` 规范化 | 自动补全 `ws://` / `http://`，并正确拼接 `access_token` |
| SL-03 | `cli_configure()` 自动安装分支 | 调用安装钩子、跳过手动输入、返回默认连接参数 |
| SL-04 | `cli_configure()` 手动分支 | 采集 `ws_uri` / `ws_token` / `webui_uri` / `skip_setup` |

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

### SessionSource (`test_bilibili_session_source.py`)

测试 SessionSource 私信时间戳过滤逻辑。

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| BL-24a | 新鲜私信正常推送 | age < max_msg_age 的消息传播到回调 |
| BL-24b | 过期私信被丢弃 | age > max_msg_age 的消息不触发回调 |
| BL-24c | timestamp=0 视为过期 | 无时间戳的消息被丢弃 |
| BL-24d | 自定义 max_msg_age | 自定义阈值生效 |

### LiveSource (`test_bilibili_live_source.py`)

测试 LiveSource 的断线重连和停止状态管理。

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| BL-25a | 断线后重连 | `connect()` 自然返回后创建新的 `LiveDanmaku` 并继续连接 |
| BL-25b | 停止时清理状态 | `stop()` 在断开前设置停止标记，并在结束后清理线程/循环状态 |

### BiliQueryAPI (`test_bilibili_query_api.py`)

测试 Bilibili 查询操作 Mixin：视频 ID 解析、音频流获取、字幕获取。

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| BQ-01 | parse_bili_id 匹配 BV 号 | 标准 BV、URL 中 BV、大小写 |
| BQ-02 | parse_bili_id 匹配 av 号 | 标准 av、混合文本中 av |
| BQ-03 | parse_bili_id 匹配 b23 短链 | mock 重定向后提取 BV |
| BQ-04 | parse_bili_id 无匹配 | 返回 None |
| BQ-05 | parse_bili_id 完整 URL | 从长 URL 提取 BV |
| BQ-06 | get_video_audio_url DASH 模式 | 返回独立 AudioStreamDownloadURL |
| BQ-07 | get_video_audio_url html5 回退 | DASH 失败后回退 html5 合并流 |
| BQ-08 | get_video_audio_url 完全失败 | DASH + html5 均失败返回 None |
| BQ-09 | get_video_subtitle 正常 | 拼接字幕 body.content |
| BQ-10 | get_video_subtitle 无字幕 | 返回 None |
| BQ-11 | get_video_subtitle 语言选择 | 按 language 参数选取字幕 |

### AIAdapter (`test_ai_adapter.py`)

测试 AI 适配器：chat、image_generation、视频生成/查询/下载、transcription（ASR）。

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| AI-03 | chat() str 包装 | 自动包装为 messages 列表 |
| AI-04 | chat() list 透传 | 直接透传 list[dict] |
| AI-05 | 未指定模型 | chat/embeddings/image_generation 抛 ValueError |
| AI-06 | 模型回退 | 模型不存在时回退到默认模型 |
| AI-07 | 生命周期 | connect/disconnect/listen |
| AI-08 | 未 connect | get_api() 抛 RuntimeError |
| AI-09 | chat_text() | 返回 str，None → "" |
| AI-10 | generate_image() | url → Image, b64 → base64://Image |
| AI-11 | MessageArray 纯文本 | 拼接为普通字符串 |
| AI-12 | MessageArray 图片 | 转为多模态 content |
| AI-13 | At 段 | 默认 @id，nickname_map → @昵称 |
| AI-14 | 不支持段 | 跳过并警告 |
| AI-15 | 单个 MessageSegment | 直接传入 Image |
| AI-16 | transcription() | 调用 atranscription，传递 model/file |
| AI-17 | transcription 无模型 | 未指定 asr_model 抛 ValueError |
| AI-18 | transcription 模型回退 | 不存在模型回退到 asr_model |
| AI-19 | transcription_text() | 返回 str，None → "" |
| AI-20 | transcription kwargs | 透传 language/prompt/response_format/temperature |
| AI-32 | 视频生成参数 | 默认/覆盖模型、通用参数覆盖、时长/尺寸/参考图像 |
| AI-33 | 视频生成无模型 | 不请求提供商，抛 ValueError 提示 video_model |
| AI-34 | 视频模型回退 | 仅模型不存在时回退一次，其他错误原样传播 |
| AI-35 | 视频查询/下载 | 按完整任务 ID 请求、合并认证参数，无默认模型也可调用，不回退 |
| AI-36 | 视频模型启动验证 | 验证 video_model，失败不阻止连接 |
