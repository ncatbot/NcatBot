# Core 模块测试

源码模块: `ncatbot.core`

## 验证规范

### AsyncEventDispatcher (`test_dispatcher.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| D-01 | 事件类型推导 | `callback` 接收 `BaseEventData` 后正确推导类型 |
| D-02 | `events()` 返回 EventStream | 支持 `async for` 迭代 |
| D-03 | `events(type)` 精确过滤 | 只返回指定类型的事件 |
| D-04 | `events(type)` 前缀匹配 | `"message"` 匹配 `"message.group"` 等 |
| D-05 | 多消费者广播 | 多个 `events()` 同时收到同一事件 |
| D-06 | `wait_event(predicate)` | 只返回满足条件的事件 |
| D-07 | `wait_event(timeout)` | 超时抛出 `TimeoutError` |
| D-08 | `close()` 终止 | 所有活跃 stream 终止 |
| D-09 | 队列溢出 | 队列满时丢弃最旧事件，不阻塞生产者 |

### Hook 系统 (`test_hooks.py` + `test_builtin_hooks.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| K-01 | 装饰器绑定 | `Hook` 作为装饰器写入 `func.__hooks__` |
| K-02 | `add_hooks()` 批量添加 | 多个 Hook 同时添加 |
| K-03 | `get_hooks()` 优先级排序 | 按 `priority` 降序返回 |
| K-04 | `HookContext` 传递 | 正确传递上下文信息 |
| K-05 | `MessageTypeFilter` | 内置消息类型过滤 Hook |
| K-06 | `PostTypeFilter` | 内置 post_type 过滤 Hook |
| K-07 | `StartsWithHook` | 前缀匹配过滤，不匹配 → SKIP |
| K-08 | `KeywordHook` | 任一关键词命中 → CONTINUE，全不匹配 → SKIP |
| K-09 | `RegexHook` | 正则匹配 → CONTINUE + 注入 `match`，否则 SKIP |
| K-10 | `NoticeTypeFilter` | `notice_type` 枚举匹配过滤 |
| K-11 | `RequestTypeFilter` | `request_type` 枚举匹配过滤 |
| K-12 | `CommandHook` 精确匹配 | 无额外参数时 `text.strip() == name` |
| K-13 | `CommandHook` ignore_case | 大小写不敏感匹配 |
| K-14 | `CommandHook` str 参数绑定 | 前缀匹配 + 剩余文本提取 |
| K-15 | `CommandHook` At 参数绑定 | 从 `message.filter_at()` 按序提取 At |
| K-16 | `CommandHook` int/float 转换 | 文本 token 中查找可转换值 |
| K-17 | `CommandHook` 可选参数 | 有默认值的参数缺失时使用默认值 |
| K-18 | `CommandHook` 必选参数缺失 | 必选参数缺失 → SKIP |
| K-19 | `on_group_command` 等便捷方法 | 单装饰器封装 `MessageTypeFilter` + `CommandHook` |
| K-20 | QQ 平台子注册器方法 | `registrar.qq.on_group_increase` 等注册精确事件类型 |
| K-21 | 所有文本匹配使用 `message.text` | 统一使用 `MessageArray.text`，不使用 `raw_message` |

### HandlerDispatcher (`test_handler_dispatcher.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| H-01 | 精确匹配 | 事件类型精确匹配 handler |
| H-02 | 前缀匹配 | 事件类型前缀匹配 |
| H-03 | 不匹配 | 不匹配的事件不触发 handler |
| H-04 | 优先级排序 | 高优先级 handler 先执行 |
| H-05 | BEFORE_CALL SKIP | Hook 返回 SKIP 阻止 handler 执行 |
| H-06 | BEFORE_CALL CONTINUE | Hook 返回 CONTINUE 允许继续 |
| H-07 | AFTER_CALL 执行顺序 | AFTER_CALL Hook 在 handler 之后执行 |
| H-08 | ON_ERROR Hook | handler 异常时触发 ON_ERROR Hook |
| H-09 | `revoke_plugin` | 移除指定插件的所有 handler |
| H-10 | handler 接收 EventEntity | handler 接收到的是 EventEntity 而非原始 data |
| H-11 | `stop()` | 停止后不再处理新事件 |

### Registrar (`test_registrar.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| R-01 | `on()` 收集 + `flush_pending` | handler 先收集到 pending，flush 后注册 |
| R-02 | ContextVar 隔离 | 不同 `plugin_name` 的 handler 分开收集 |
| R-03 | `fork()` | 创建独立 Registrar 实例 |
| R-04 | `clear_pending()` | 清理残留的 pending handler |
| R-08 | `bilibili.on_live_start()` 路由 | 路由到 `live.live` 事件类型 |
| R-09 | `bilibili.on_live_end()` 路由 | 路由到 `live.preparing` 事件类型 |

### Registrar 堆叠装饰器去重 (`test_duplicate_handler.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| R-05 | 堆叠装饰器 pending 去重 | 同一函数堆叠装饰器后 pending 只收集 1 次 |
| R-06 | 堆叠装饰器 flush 去重 | flush 后同一函数只注册 1 个 entry |
| R-07 | 堆叠装饰器端到端分发去重 | 注入一条群消息 handler 只执行 1 次 |

### Predicate 谓词 DSL (`test_predicate.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| PR-01 | `match_event_type` 谓词 | 精确匹配事件类型 |
| PR-02 | `match_prefix` 谓词 | 前缀匹配事件类型 |
| PR-03 | `match_any` 组合 | 任一谓词满足即通过 |
| PR-04 | `match_all` 组合 | 所有谓词满足才通过 |
| PR-05 | `match_not` 取反 | 否定谓词 |
| PR-06 | 谓词用于 `wait_event` | 与 `AsyncEventDispatcher` 集成 |
