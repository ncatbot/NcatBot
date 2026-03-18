# Quick Start

> 从零开始，5 分钟运行你的第一个 NcatBot。覆盖安装、配置、非插件模式和插件模式两种启动方式。

---

## Quick Reference

### 最小非插件模式

安装 → 写 config.yaml → 写 main.py → 运行：

```bash
pip install ncatbot5
```

```python
# main.py
from ncatbot.app import BotClient
from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent

bot = BotClient()

@registrar.on_group_command("hello", ignore_case=True)
async def on_hello(event: GroupMessageEvent):
    await event.reply(text="Hello, NcatBot!")

if __name__ == "__main__":
    bot.run()
```

### 最小插件模式

```bash
pip install ncatbot5
ncatbot init        # 交互式生成 config.yaml + 模板插件
ncatbot run         # 启动 Bot
```

---

## 本目录索引

| 文件 | 内容 |
|------|------|
| [1.install-config.md](1.install-config.md) | 安装 NcatBot、编写 config.yaml、确认 NapCat 连接 |
| [2.non-plugin-mode.md](2.non-plugin-mode.md) | 非插件模式完整流程 — 直接在 main.py 注册回调，适合快速原型 |
| [3.plugin-mode.md](3.plugin-mode.md) | 插件模式完整流程 — 创建插件目录 + manifest + 插件类，适合正式项目 |

---

## 交叉引用

- 两种模式的区别 → [使用指南首页](../README.md)
- 插件开发深入 → [插件开发指南](../plugin/)
- CLI 命令详解 → [CLI 指南](../cli/)
