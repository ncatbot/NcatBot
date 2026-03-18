# CLI 工具 — 命令行管理 NcatBot

> 通过 `ncatbot` 命令完成项目初始化、启动、插件管理、配置管理和 NapCat 诊断。

## Quick Reference

安装 NcatBot 后即可使用 `ncatbot` 命令。

### 命令一览

| 命令 | 参数 | 说明 |
|------|------|------|
| `ncatbot init` | `[--force]` | 初始化项目（生成 config.yaml + plugins/ + 模板插件） |
| `ncatbot run` | `[--config PATH]` | 启动 Bot |
| `ncatbot dev` | `[--config PATH]` | 开发模式启动（debug + 热重载） |
| `ncatbot` | — | 进入交互模式（REPL） |
| `ncatbot config get <key>` | | 读取配置值 |
| `ncatbot config set <key> <value>` | | 设置配置值 |
| `ncatbot plugin list` | | 列出已安装插件 |
| `ncatbot plugin install <name>` | | 安装插件 |
| `ncatbot plugin remove <name>` | | 卸载插件 |

## 本目录索引

| 文件 | 说明 | 难度 |
|------|------|------|
| [1.commands.md](1.commands.md) | 命令详解（初始化 / 启动 / 插件与配置管理） | ⭐ |

## 推荐阅读顺序

1. 先读 [命令详解](1.commands.md) — 从零创建并运行 Bot，管理插件和配置
