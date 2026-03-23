# Config 模块测试

源码模块: `ncatbot.utils.config`

## 验证规范

### Config Migration (`test_config_migration.py`)

测试旧版 `napcat` 配置格式到新版 `adapters` 格式的自动迁移，以及 `Config` 模型的字段校验。

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| CF-01 | 旧格式自动迁移 | 旧 `napcat` dict → `adapters` 列表 + `_migrated=True` |
| CF-02 | 新格式不迁移 | 已有 `adapters` → 不触发迁移、`_migrated=False` |
| CF-03 | 两者都无 | 无 `napcat` 也无 `adapters` → 默认 napcat adapter |
| CF-04 | AdapterEntry 字段验证 | 字段类型、必填项校验 |
| CF-05 | 字段 coerce / clamp | `bot_uin`/`root` 整数强转、`websocket_timeout` 范围限制 |

### Config 分层与运行时 (`test_config_layer.py`)

`NCATBOT_BOT_UIN` / `NCATBOT_ROOT` 与 yaml 的优先级、合并保存与 `ConfigManager` 运行时覆盖。

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| CE-01 | yaml 优先于 env | 文件中已有 `bot_uin` 时忽略 `NCATBOT_BOT_UIN` |
| CE-02 | env 补全缺失键 | yaml 无 `bot_uin` 时从 env 解析并标记 env-only |
| CE-03 | save 不固化 env-only | `save()` 后 yaml 不出现仅来自 env 的 `bot_uin` |
| CE-04 | effective_* 与 clear | `apply_runtime_overrides` 与 `clear_runtime_overrides` 行为 |
| CE-05 | update_value 显式持久化 | `update_value("bot_uin", …)` 后写入 yaml |
