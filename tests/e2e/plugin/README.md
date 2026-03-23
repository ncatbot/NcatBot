# 插件 E2E 测试

使用 `PluginTestHarness` 对 `examples/` 中的示例插件进行离线 E2E 测试，验证插件加载、命令响应、生命周期等。

## Fixtures (`conftest.py`)

| Fixture | 说明 |
|---------|------|
| `example_harness` | 工厂 fixture，根据 `@pytest.mark.plugin_names` / `@pytest.mark.plugins_dir` 自动创建 `PluginTestHarness` |
| `make_example_harness()` | 辅助函数，手动创建 `PluginTestHarness` 实例（需自行管理生命周期） |

## 验证规范

### hello_world (`test_hello_world.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| PL-01 | 插件加载成功 | `on_load` 执行，插件出现在 `loaded_plugins` |
| PL-02 | 群消息 "hello" | → `send_group_msg` 调用 |
| PL-03 | 私聊消息 "hello" | → `send_private_msg` 调用 |
| PL-04 | 插件卸载 | `on_close` 执行，插件从列表中移除 |

### event_handling (`test_event_handling.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| PL-10 | 装饰器命令 "ping" | → `event.reply('pong')` → `send_group_msg` |
| PL-11 | 事件流消费 | 后台私聊监控不崩溃 |
| PL-12 | wait_event 超时 | "确认测试" 命令超时/确认处理 |

### hook_and_filter (`test_hook_and_filter.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| PL-20 | BEFORE_CALL 关键词过滤 | "回声 违禁词" → SKIP → 不回复 |
| PL-21 | AFTER_CALL 日志 | 正常命令通过 Hook 链后日志记录（不崩溃） |
| PL-22 | ON_ERROR Hook | "除零" → 异常 → 错误通知回复 |
| PL-23 | 正常通过 | "回声 你好" → 回复 "🔊 你好" |

### rbac (`test_rbac.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| PL-30 | 权限初始化 | `on_load` 中权限路径和角色已注册 |
| PL-31 | 无权限拒绝 | 无权限用户执行 "管理命令" → 回复权限不足 |
| PL-32 | 授权后可访问 | RBAC 授权后管理命令可执行 |
| PL-33 | 权限查询 | "查权限" / "权限信息" → 回复权限状态 |

### multi_step_dialog (`test_multi_step_dialog.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| PL-40 | 完整注册流程 | 注册 → 名字 → 年龄 → 确认 → 保存 |
| PL-41 | 超时退出 | 等待超时后自动取消 |
| PL-42 | 用户取消 | 输入 "取消" → 退出注册 |
| PL-43 | data 持久化 | 注册完成后 data 中有用户信息 |

### full_featured_bot (`test_full_featured.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| PL-50 | 多功能加载 | full_featured_bot 插件加载成功 |
| PL-51 | 签到与积分 | "签到" → 积分、重复签到提示、"积分" → 查看 |
| PL-52 | Config/Data | 加载后 config 有默认值，data 有初始化结构 |
| PL-53 | 帮助/关键词/配置 | "帮助" / 关键词管理 / "查看配置" 命令 |

## 人工验收

除自动化测试外，插件还可通过 `run.py` 进行人工验收，详见 [../README.md](../README.md)。
