# 插件测试指南

> 为你的 NcatBot 插件编写自动化测试。

---

## Quick Reference

### 核心组件

| 组件 | 说明 |
|------|------|
| `PluginTestHarness` | 加载真实插件目录，模拟事件流的完整测试编排器 |
| `TestHarness` | 轻量无插件测试，直接注册 handler 并注入事件 |
| `Scenario` | 链式构建器，编排多步交互场景 |
| `MockAdapter` / `MockBotAPI` | 内存级模拟，无需网络 |

### 事件工厂函数

| 工厂函数 | 说明 |
|---------|------|
| `group_message(text, group_id=, user_id=)` | 群消息事件 |
| `private_message(text, user_id=)` | 私聊消息事件 |
| `friend_request(user_id=, comment=)` | 好友请求 |
| `group_request(group_id=, user_id=)` | 加群请求 |
| `group_increase(group_id=, user_id=)` | 群成员增加 |
| `group_decrease(group_id=, user_id=)` | 群成员减少 |
| `group_ban(group_id=, user_id=)` | 群禁言 |
| `poke(group_id=, user_id=)` | 戳一戳 |

### Harness 常用方法

| 方法 | 说明 |
|------|------|
| `h.inject(event)` | 注入事件 |
| `h.settle()` | 等待所有 handler 执行完成 |
| `h.api_called("method_name")` | 断言：API 被调用 → `bool` |
| `h.api_not_called("method_name")` | 断言：API 未被调用 → `bool` |
| `h.get_api_calls("method_name")` | 获取 API 调用记录列表 |

### 典型测试示例

```python
import pytest
from ncatbot.testing import PluginTestHarness, group_message

@pytest.mark.asyncio
async def test_hello_command():
    async with PluginTestHarness(plugin_names=["hello_world"], plugin_dir=Path("plugins/")) as h:
        await h.inject(group_message("hello", group_id="100", user_id="99"))
        await h.settle()
        assert h.api_called("send_group_msg")
```

---

## 本目录索引

| 章节 | 说明 | 难度 |
|------|------|------|
| [1. 快速入门](1.quick-start.md) | 5 分钟写出第一个插件测试 | ⭐ |
| [2. Harness 详解](2.harness.md) | TestHarness 与 PluginTestHarness 深入使用 | ⭐⭐ |
| [3. 工厂与场景](3.factory-scenario.md) | 事件工厂、Scenario 构建器、自动冒烟测试 | ⭐⭐ |
