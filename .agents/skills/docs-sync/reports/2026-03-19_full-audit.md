# Docs-Sync 全面审计报告 — 2026-03-19

## 执行概要

| 阶段 | 审计内容 | 已自动修复 | 待人工处理 |
|------|---------|:----------:|:----------:|
| Phase A | 链接完整性 & 索引一致 | 3 | 0 |
| Phase B | guide↔reference 内容对齐 | 0 | 21 |
| Phase D | Code↔Docs API 对齐 | 0 | 20 |

---

## Phase A — 链接完整性 & 索引 ✅ 已完成

### 已自动修复

| # | 文件 | 修复内容 | 严重度 |
|---|------|---------|--------|
| A1 | `reference/README.md` | `<9. 测试指南/>` → `<9. 测试框架/>` 断链修复 | P0 |
| A2 | `examples/README.md` | 添加 `08_command_group` 索引条目 | P1 |
| A3 | `guide/11. 架构与概念/README.md` | 新建缺失的目录 README | P0 |

### 验证结果

- **contributing/ 交叉引用**：subagent 报告 16 个断链 — **经验证全部为误报**，`../guide/...` 路径从 contributing/ 正确解析
- **reference/ 章节 README display text**：如 `[1a_config.md](<1. 配置.md>)` — 链接目标有效，仅 display text 为旧命名，P2 级化妆问题

---

## Phase B — Guide↔Reference 内容对齐 ⚠️ 待人工处理

### 插件系统（guide/3 ↔ reference/5）— 9 个发现

| # | 类型 | 严重度 | 问题摘要 |
|---|------|--------|---------|
| B1 | MISMATCH | **P0** | `add_scheduled_task` 签名缺少 `callback` 参数（Guide 遗漏） |
| B2 | MISMATCH | **P0** | Guide 称回调"必须同名"，但 Reference 有 `callback=None` 参数覆盖 |
| B3 | MISMATCH | **P0** | 装饰器表列 `on_poke()` 无前缀 vs 代码示例用 `registrar.qq.on_poke()` — 调用路径矛盾 |
| B4 | MISMATCH | P2 | `_manifest` 类型标注 `PluginManifest` vs `PluginManifest | None` |
| B5 | GUIDE_ONLY | P1 | `self.config` 在 Guide 正式使用但 Reference 未文档化 |
| B6 | MISMATCH | P1 | Guide README 速查表缺少 `remove_permission` / `user_has_role` / `get_task_status` |
| B7 | MISMATCH | P1 | Guide README 装饰器表缺少 `on_message_sent` / `on_meta` / `on_group_recall` |
| B8 | REF_ONLY | P1 | PluginLoader API（`reload_plugin` 等）仅 Reference 覆盖 |
| B9 | REF_ONLY | P1 | `DependencyResolver.resolve_subset()` / `PluginVersionError` 仅 Reference 覆盖 |

### 消息系统（guide/4 ↔ reference/1,3）— 12 个发现

| # | 类型 | 严重度 | 问题摘要 |
|---|------|--------|---------|
| B10 | MISMATCH | **P0** | Image/Record QQ 专属字段（sub_type/magic）混入通用消息段表 |
| B11 | MISMATCH | **P0** | `send_private_forward_msg_by_id` Guide 有但 Reference 缺少 |
| B12 | MISMATCH | **P0** | GitHub API README 签名与实际方法签名完全不一致 |
| B13 | MISMATCH | P1 | `from ncatbot.types import Json` vs `from ncatbot.types.qq import Json` 导入路径冲突 |
| B14 | MISMATCH | P1 | 通用 README 用内部路径 `ncatbot.types.common.segment` 而非公共 API 路径 |
| B15 | MISMATCH | P1 | ForwardConstructor 导入路径 Guide 内部都不一致 |
| B16 | REF_ONLY | P1 | `friend_poke()` 仅 Reference 覆盖 |
| B17 | REF_ONLY | P1 | `add_segments` / `filter_at` / `get_attachments` 仅 Reference 覆盖 |
| B18 | MISMATCH | P2 | Face / Share / Location / Music 平台归类不一致 |
| B19 | MISMATCH | P2 | MessageArray.filter 返回类型 `list` vs `List[T]` |
| B20 | DRIFT | P2 | "sugar 方法" vs "便捷方法" 术语不统一 |
| B21 | REF_ONLY | P1 | `mark_group_msg_as_read` / `send_like` / `forward_*_single_msg` 等仅 Reference 覆盖 |

### 事件系统（guide/5,3.4 ↔ reference/2）— 9 个发现

| # | 类型 | 严重度 | 问题摘要 |
|---|------|--------|---------|
| B22 | MISMATCH | **P0** | "notice.poke" 事件类型字符串错误，应为 notice.notify + sub_type=poke |
| B23 | MISMATCH | **P0** | registrar vs registrar.qq 前缀混淆（同 B3） |
| B24 | GUIDE_ONLY | P1 | `on_group_recall()` 代码示例用了但装饰器表未列出 |
| B25 | MISMATCH | P1 | HasAttachments trait 和 get_attachments() 在 Guide 事件表中遗漏 |
| B26 | REF_ONLY | P1 | Reference README 速查表缺少 HasAttachments（内部不一致） |
| B27 | MISMATCH | P1 | MESSAGE_SENT 事件类别在 Guide 类型体系总览表中缺失 |
| B28 | DRIFT | P2 | ban(duration=60) 示例值 vs 默认值 1800 易误导 |
| B29 | DRIFT | P2 | reply() 参数简化遗漏 at_sender=True |
| B30 | DRIFT | P2 | "QQ 号" 术语用于通用事件描述 |

---

## Phase D — Code↔Docs API 对齐 ⚠️ 待人工处理

### 核心模块（ncatbot/core/ ↔ reference/4）— 15 个发现

| # | 类型 | 严重度 | 问题摘要 |
|---|------|--------|---------|
| D1 | SIG_MISMATCH | **P0** | `HandlerDispatcher.__init__` 签名完全不一致（BotAPIClient → IAPIClient + 2 新参数） |
| D2 | SIG_MISMATCH | **P0** | `register()` 方法实际为 `register_handler()`，参数完全不同 |
| D3 | SIG_MISMATCH | **P0** | `unregister()` 实际为 `unregister_handler()`，参数类型不同 |
| D4 | SIG_MISMATCH | **P0** | `same_user(event)` 实际为 `same_user(user_id)` — 语义完全不同 |
| D5 | SIG_MISMATCH | **P0** | `same_group(event)` 实际为 `same_group(group_id)` — 语义完全不同 |
| D6 | SIG_MISMATCH | **P0** | `P.__call__` 操作 `Event` 而非文档的 `BaseEventData` |
| D7 | SIG_MISMATCH | **P0** | Hook `__call__` 文档写法错误，实际执行入口为 `execute()` |
| D8 | SIG_MISMATCH | **P0** | `HookContext` 字段名不一致（handler→handler_entry, service_manager→services） |
| D9 | GHOST_DOC | **P0** | 装饰器 `hooks`/`predicate`/`block` 参数在代码中不存在 |
| D10 | GHOST_DOC | **P0** | 便捷装饰器 `on_poke()` 等在 Registrar 上不存在（仅在 QQRegistrar 上） |
| D11 | CODE_UNDOC | P1 | `Registrar.on()` 的 `platform` 参数未文档化 |
| D12 | CODE_UNDOC | P1 | `Registrar.fork()` 方法未文档化 |
| D13 | CODE_UNDOC | P1 | 平台子注册器 `registrar.qq` / `.bilibili` / `.github` 未文档化 |
| D14 | CODE_UNDOC | P1 | `HandlerDispatcher.set_platform_api()` 未文档化 |
| D15 | CODE_UNDOC | P1 | `CommandGroup` / `CommandGroupHook` 未文档化 |

### 插件系统（ncatbot/plugin/ ↔ reference/5）— 3 个发现

| # | 类型 | 严重度 | 问题摘要 |
|---|------|--------|---------|
| D16 | CODE_UNDOC | P1 | `BasePlugin.logger` 属性未文档化 |
| D17 | CODE_UNDOC | P2 | `PluginLoader.get_plugin_name_by_folder()` 未文档化 |
| D18 | CODE_UNDOC | P1 | `PluginLoader.setup_hot_reload()` 签名未文档化 |

### 服务层（ncatbot/service/ ↔ reference/6）— 2 个发现

| # | 类型 | 严重度 | 问题摘要 |
|---|------|--------|---------|
| D19 | CODE_UNDOC | P1 | `PermissionPath` / `PermissionTrie` 公开导出但无 API 文档 |
| D20 | CODE_UNDOC | P2 | `ServiceManager.set_debug_mode()` / `set_test_mode()` 未文档化 |

---

## 统计汇总

| 严重度 | Phase A (已修) | Phase B (待修) | Phase D (待修) | 合计 |
|--------|:-----------:|:-----------:|:-----------:|:----:|
| **P0** | 2 | 8 | 10 | **20** |
| **P1** | 1 | 10 | 7 | **18** |
| **P2** | 0 | 3 | 3 | **6** |
| **合计** | 3 | 21 | 20 | **44** |

### 建议修复优先级

1. **核心模块 Reference（reference/4）**：10 个 P0，文档与代码严重脱节 — 建议重写 `注册表.md`、`谓词系统.md`、`内部实现.md`
2. **Guide 事件/装饰器章节（guide/3.4, 3.5）**：registrar/registrar.qq 前缀混乱、notice.poke 类型错误 — 需统一
3. **Guide 消息段章节（guide/4.1）**：QQ 字段混入通用段、导入路径不一致 — 需拆分 QQ 专属内容
4. **GitHub API README**：签名与代码完全不匹配 — 需按实际代码重写

---

## 修复说明

Phase B/D 的发现涉及**文档内容与代码语义的对齐**，需要人工判断以下方向：
- 代码 API 是否已经稳定？→ 按代码修改文档
- 文档描述的是设计意图？→ 按文档修改代码
- 既有遗留变更？→ 需要确认版本后处理

**自动修复仅适用于 Phase A 的机械性链接/索引问题，已全部完成。**
