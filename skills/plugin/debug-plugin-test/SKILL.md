# debug-plugin-test — 调试 NcatBot 插件测试失败

## 触发条件

当用户报告插件测试失败、测试超时、断言错误、或插件加载异常时，使用此技能。

## 诊断流程

### 1. 收集错误信息

- 读取 pytest 输出中的完整 traceback
- 识别失败的测试函数名和断言位置
- 检查是否有 `asyncio.TimeoutError` 或 `RuntimeError`

### 2. 常见失败原因及修复

> 参考文档：[guide/testing/2.harness.md](docs/guide/testing/2.harness.md#7-常见模式与陷阱)

#### A. 插件加载失败 — `"插件 xxx 未索引"`

**原因**: `plugin_dir` 路径错误，或 manifest.toml 不在预期位置

**排查**:
1. 检查 `PluginTestHarness(plugin_dir=...)` 的路径是否正确
2. `plugin_dir` 应该是包含插件文件夹的**父目录**，不是插件文件夹本身
3. 验证 manifest.toml 存在: `plugin_dir / folder_name / manifest.toml`

**修复**: `plugin_dir` 应指向例如 `examples/`，而不是 `examples/01_hello_world/`

#### B. API 未被调用 — `assert h.api_called("send_group_msg")` 失败

**原因**:
1. **命令不匹配**: 注入的消息文本与 `@registrar.on_group_command("xxx")` 不一致
2. **settle 时间不足**: handler 还没执行完毕
3. **Hook 拦截**: BEFORE_CALL Hook 返回了 SKIP
4. **事件类型不匹配**: 注入了群消息但 handler 只监听私聊，或反之

**排查**:
1. 检查注入的消息文本是否与命令完全匹配
2. 尝试增大 `settle(0.2)` 或 `settle(0.5)`
3. 检查是否有 Hook 可能拦截（查看是否有 `@add_hooks` 装饰器）
4. 检查事件工厂函数：群消息用 `group_message()`，私聊用 `private_message()`

**修复示例**:
```python
# 错误：文本不匹配
await h.inject(group_message("Hello"))  # 命令是 ignore_case=True 的 "hello"
# 正确：
await h.inject(group_message("hello"))
```

#### C. settle 时序问题

> 参考文档：[guide/testing/2.harness.md](docs/guide/testing/2.harness.md#2-事件注入)

**原因**: `await h.settle(0.05)` 默认 50ms 可能不够

**排查**:
1. 如果 handler 内有 `await self.wait_event()` 或 `asyncio.sleep()`，需要更长 settle
2. 多步对话场景需要在每步之间 settle

**修复**: 增大 settle 时间，或者在多步对话中每步都 settle：
```python
await h.inject(group_message("注册", ...))
await h.settle(0.1)  # 等待第一步处理

await h.inject(group_message("张三", ...))
await h.settle(0.1)  # 等待第二步处理
```

#### D. Mock API 返回值缺失

> 参考文档：[guide/testing/2.harness.md](docs/guide/testing/2.harness.md#4-mock-响应配置)

**原因**: 某些 handler 依赖 API 返回值（如 `get_group_member_info`）

**排查**: 检查 handler 代码中是否有 `result = await self.api.xxx()`

**修复**: 预配置 Mock API 返回值：
```python
h.mock_api.set_response("get_group_member_info", {"user_id": "99", "nickname": "test"})
```

未配置的 API 调用返回空 `{}`。

#### E. RBAC/Service 不可用

**原因**: `skip_builtin=True`（默认）不加载 RBAC 等服务

**排查**: 检查 `plugin.rbac` 是否为 None

**修复**: RBAC 服务未启动时，RBACMixin 会做降级处理。如果确实需要 RBAC，可设置 `skip_builtin=False`。

#### F. 依赖插件缺失

**原因**: 目标插件依赖了其他插件，但 manifest 不在 plugin_dir 中

**排查**: 检查 manifest.toml 的 `[dependencies]` 部分

**修复**: 确保所有依赖插件的目录都在同一个 `plugin_dir` 下

### 3. 调试工具

> 参考文档：[reference/testing/1_harness.md](docs/reference/testing/1_harness.md), [reference/testing/2_factory_scenario_mock.md](docs/reference/testing/2_factory_scenario_mock.md#mockbotapi)

```python
# 打印所有 API 调用记录
for call in h.api_calls:
    print(f"  {call.action}({call.args}, {call.kwargs})")

# 打印已加载的插件
print(h.loaded_plugins)

# 获取插件实例检查状态
plugin = h.get_plugin("xxx")
print(plugin.data)
print(plugin.config)
```

## 参考文档

- Harness 使用详解: [docs/guide/testing/2.harness.md](docs/guide/testing/2.harness.md)
- TestHarness API: [docs/reference/testing/1_harness.md](docs/reference/testing/1_harness.md)
- MockBotAPI API: [docs/reference/testing/2_factory_scenario_mock.md](docs/reference/testing/2_factory_scenario_mock.md#mockbotapi)
- 事件工厂 API: [docs/reference/testing/2_factory_scenario_mock.md](docs/reference/testing/2_factory_scenario_mock.md#事件工厂函数)
