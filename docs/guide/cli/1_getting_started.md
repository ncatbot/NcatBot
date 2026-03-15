# 项目初始化与启动

> 一句话：用 `ncatbot init` 创建项目骨架，用 `ncatbot run` / `ncatbot dev` 启动 Bot。

## 前提条件

- 已安装 NcatBot（`pip install ncatbot5`）
- NapCat 已在本地运行

## 初始化项目

```bash
ncatbot init
```

交互式引导会依次询问：

1. **机器人 QQ 号** — Bot 账号
2. **管理员 QQ 号** — 超级管理员账号

完成后自动创建：

```
my-bot/
├── config.yaml    # 配置文件
└── plugins/       # 插件目录
```

生成的 `config.yaml` 示例：

```yaml
bot_uin: "123456789"
root: "987654321"
debug: false
napcat:
  ws_uri: "ws://localhost:3001"
  ws_token: "napcat_ws"
  webui_uri: "http://localhost:6099"
  webui_token: "napcat_webui"
  enable_webui: true
plugin:
  plugins_dir: "plugins"
  load_plugin: true
  plugin_whitelist: []
  plugin_blacklist: []
```

可用 `--dir` 指定目标目录：

```bash
ncatbot init --dir ./my-bot
```

## 启动 Bot

### 生产模式

```bash
ncatbot run
```

常用选项：

| 选项 | 说明 |
|------|------|
| `--debug` | 启用调试模式（详细日志输出） |
| `--no-hot-reload` | 禁用插件热重载 |
| `--plugin-dir <路径>` | 指定插件目录（默认 `plugins`） |

示例：

```bash
# 启用 debug，使用自定义插件目录
ncatbot run --debug --plugin-dir my_plugins
```

### 开发模式

```bash
ncatbot dev
```

等价于 `ncatbot run --debug`，始终开启 debug 模式和热重载。支持 `--plugin-dir` 选项。

## 交互模式（REPL）

直接运行 `ncatbot`（不带子命令）进入交互式 Shell：

```
NcatBot CLI — 交互模式 [123456789]
输入命令执行操作，输入 help 查看帮助，输入 exit 退出。

ncatbot [123456789]> config show
ncatbot [123456789]> plugin list
ncatbot [123456789]> exit
```

在 REPL 中可以执行所有子命令，无需每次重复 `ncatbot` 前缀。

| 快捷命令 | 说明 |
|----------|------|
| `help` / `h` / `?` | 查看帮助 |
| `exit` / `quit` / `q` | 退出 REPL |

## 查看版本

```bash
ncatbot --version
```

## 延伸阅读

- [插件与配置管理](2_management.md) — 用 CLI 管理插件和配置
- [配置管理指南](../configuration/) — config.yaml 字段详解
