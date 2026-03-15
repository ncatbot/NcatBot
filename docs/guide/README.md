# 使用指南

> NcatBot 从入门到进阶的完整指南

---

## Quick Start

从零开始，5 步跑通你的第一个 Bot。

### 1. 安装 NcatBot

```bash
pip install ncatbot
```

### 2. 创建项目目录

```bash
mkdir my-bot && cd my-bot
```

### 3. 编写入口文件

创建 `main.py`：

```python
from ncatbot.app import BotClient

bot = BotClient()


@bot.on("message")
async def on_message(event):
    if event.raw_message == "hello":
        await event.reply("Hello, NcatBot!")


if __name__ == "__main__":
    bot.run()
```

### 4. 配置连接

创建 `config.yaml`：

```yaml
bt_uin: "你的QQ号"
ws_uri: "ws://localhost:3001"
```

### 5. 启动 Bot

确保 NapCat 已运行，然后：

```bash
python main.py
```

发送 `hello` 给 Bot，收到回复即成功 🎉

> **下一步：** 阅读 [插件开发指南](plugin/) 学习如何用插件组织代码。

---

## 指南索引

| 目录 | 说明 | 难度 |
|------|------|------|
| [plugin/](plugin/) | 插件开发完整指南（12 篇） | ⭐ - ⭐⭐⭐ |
| [send_message/](send_message/) | 消息发送指南（6 篇） | ⭐ |
| [api_usage/](api_usage/) | Bot API 使用指南（3 篇） | ⭐⭐ |
| [configuration/](configuration/) | 配置管理指南（2 篇） | ⭐⭐ |
| [rbac/](rbac/) | RBAC 权限管理指南（2 篇） | ⭐⭐⭐ |
| [testing/](testing/) | 插件测试指南（3 篇） | ⭐⭐ |

### plugin/ — 插件开发

从快速入门到高级主题的完整路径：

1. [快速入门](plugin/1.quick-start.md) — 5 分钟跑通第一个插件
2. [插件结构](plugin/2.structure.md) — manifest.toml、目录布局、基类选择
3. [生命周期](plugin/3.lifecycle.md) — 插件加载 / 卸载流程、Mixin 钩子链
4. [事件处理](plugin/4.event-handling.md) — 三种事件消费模式
5. [Mixin 能力体系](plugin/5.mixins.md) — 配置、数据、权限、定时任务
6. [Hook 机制](plugin/6.hooks.md) — 中间件、过滤器、参数绑定
7. [高级主题](plugin/7.advanced.md) — 热重载、依赖管理、多步对话

### send_message/ — 消息发送

- [快速上手](send_message/1_quickstart.md) — 三种发送方式速览
- [消息段参考](send_message/2_segments.md) — 所有消息段类型详解
- [MessageArray](send_message/3_array.md) — 消息容器与链式构造
- [合并转发](send_message/4_forward.md) — ForwardNode / Forward 构造
- [便捷接口](send_message/5_sugar.md) — MessageSugarMixin 速查
- [实战示例](send_message/6_examples.md) — 14 个常见场景

### api_usage/ — Bot API 使用

- [API 概览](api_usage/1_overview.md) — API 分类与调用方式
- [常用接口](api_usage/2_common.md) — 消息发送、群管理、信息查询
- [文件操作](api_usage/3_file.md) — 文件上传与下载

> 另有旧版单文件指南：[api-usage.md](api-usage.md)

### configuration/ — 配置管理

- [全局配置](configuration/1_global.md) — config.yaml 全部字段说明
- [插件配置](configuration/2_plugin.md) — ConfigManager 与安全检查

> 另有旧版单文件指南：[configuration.md](configuration.md)

### rbac/ — 权限管理

- [RBAC 模型](rbac/1_model.md) — 角色权限模型、Trie 权限路径
- [RBACMixin](rbac/2_mixin.md) — 在插件中使用权限控制

> 另有旧版单文件指南：[rbac.md](rbac.md)

---

### testing/ — 插件测试

- [快速入门](testing/1.quick-start.md) — 5 分钟写出第一个插件测试
- [Harness 详解](testing/2.harness.md) — TestHarness 与 PluginTestHarness 深入使用
- [工厂与场景](testing/3.factory-scenario.md) — 事件工厂、Scenario 构建器、自动冒烟

---

## 推荐阅读顺序

| 我想… | 推荐路径 |
|-------|--------|
| **开发一个插件** | plugin/1 → plugin/2 → plugin/4 → api_usage/ |
| **发送各种消息** | send_message/1 → send_message/2 → send_message/6 |
| **了解权限控制** | rbac/1 → rbac/2 |
| **为插件编写测试** | testing/1 → testing/2 → testing/3 |
| **查 API 签名** | → [API 参考](../reference/) |
