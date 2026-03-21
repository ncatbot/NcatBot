# Types 模块测试

源码模块: `ncatbot.types`

## 验证规范

### 事件数据类型 (`test_types.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| T-01 | BaseEventData ID 强转 | `int` 类型的 `self_id`、`user_id` 自动转为 `str` |

### 消息段体系 (`test_segments.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| T-02 | `to_dict()` 输出格式 | 输出符合 OB11 `{"type": ..., "data": {...}}` 格式 |
| T-03 | `parse_segment()` 反序列化 | 从 dict 正确还原为 Segment 实例 |
| T-04 | 类型注册机制 | `SEGMENT_MAP` 包含所有内置类型，自定义类型可注册 |
| T-05 | MessageArray 链式构造 | `append()` 链式调用，`__len__`、`__iter__` 正确 |

### parse_segment 直接解析 (`test_segment_parsing.py`)

使用 `parse_segment()` 直接解析 OB11 `{"type": ..., "data": {...}}` 格式。

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| S-01 | 文本段解析 | text / Unicode / 空 |
| S-02 | face 段 id 强转 | `int` → `str` |
| S-03 | at 段 | qq 数字 / "all" / int 自动转 |
| S-04 | reply 段 | id 强转 |
| S-05 | image 段 | 必填 file + 可选 url/sub_type |
| S-06 | record/video/file 段 | DownloadableSegment 子类 |
| S-07 | 未知类型 | 抛 `ValueError` |
| S-08 | 序列化/反序列化往返 | `parse_segment → to_dict → parse_segment` 一致 |
| S-09 | extra="allow" 容错 | 额外字段不报错，缺必填字段抛异常 |
| S-10 | SEGMENT_MAP 完整性 | 包含所有 14 种内置类型 |

### CQ 码解析 (`test_cq_parser.py`)

测试 `parse_cq_code_to_onebot11()` 将 CQ 码字符串转为 OB11 消息数组。

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| CQ-01 | 纯文本 | 无 CQ 码 → 单个 text 段 |
| CQ-02 | 单个 CQ 码 | `[CQ:at,qq=123]` → at 段 |
| CQ-03 | 混合 | 前后文本 + 中间 CQ 码 |
| CQ-04 | 多参数 | `[CQ:image,file=...,url=...]` |
| CQ-05 | 转义还原 | `&amp;` → `&`, `&#91;` → `[` 等 |
| CQ-06 | 无参数 | `[CQ:shake]` → data 为空 |
| CQ-07 | 连续 CQ 码 | 中间无 text 段 |
| CQ-08 | 空字符串 | → 空列表 |

### NapCat 类型模型 (`test_napcat_types.py`)

测试 NapCat 响应模型的字段强转、字典兼容访问和模型构造。

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| N-01 | `*_id` 字段强转 | `int` 类型 ID 自动转为 `str` |
| N-02 | 字典兼容访问 | `__getitem__` / `get` / `__contains__` 支持 |
| N-03 | 允许额外字段 | 未知字段不报错 |
| N-04 | `SendMessageResult` | 正确解析 `message_id` |
| N-05 | 各模型基本构造 | 20+ 种 NapCat 模型均可正常实例化 |

### MessageArray 容器 (`test_message_array.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| MA-01 | filter 按类型过滤 | `filter(PlainText)` 只返回对应类型段 |
| MA-02 | is_at 判断 @ | 精确匹配 / @all 检测 |
| MA-03 | text 属性拼接 | `.text` 拼接所有 PlainText 段 |
| MA-04 | 链式构造 | `add_text().add_image().add_at()` 链式调用 |

### Forward 转发消息 (`test_forward.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| FW-01 | `Forward.from_dict` 反序列化 | legacy API 格式 / id-only 格式 |
| FW-02 | `Forward.to_dict` 序列化 | content 模式 / id 模式 |
| FW-03 | ForwardNode 内容解析 | 消息段正确解析为 Segment 列表 |

### 消息段附件桥接 (`test_segment_attachments.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| SEG-01 | 纯文本消息返回空 | `get_attachments()` 返回空 `AttachmentList` |

### Bilibili 数据模型 (`test_bilibili_models.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| LR-01 | `LiveRoomInfo.from_raw()` 完整解析 | 全字段正确映射 |
| LR-02 | `from_raw()` 空/缺失字段 | 回退默认值 |
| LR-03 | `from_raw()` 异常数据 | 返回 None |
