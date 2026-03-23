# CLI 模块测试

源码模块: `ncatbot.cli`

## 验证规范

### CLI 冒烟 (`test_cli_smoke.py`)

#### `--help`（不进入命令回调）

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| CX-01 | 根命令帮助 | `ncatbot --help` 退出码 0 |
| CX-02 | 一级子命令帮助 | `run` / `dev` / `config` / `plugin` / `napcat` / `init` / `adapter` 的 `--help` |
| CX-03 | 嵌套子命令帮助 | `napcat diagnose --help` 退出码 0 |

#### 参数绑定（执行命令回调，mock 副作用）

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| CX-04 | `run` 全选项 | `--debug` `--no-hot-reload` `--plugins-dir` → `BotClient` mock 与 `kwargs` |
| CX-05 | `run` 仅插件目录 | 仅 `--plugins-dir` 时 `debug`/`hot_reload` 为 `MISSING` |
| CX-06 | `dev` | `debug=True`、`hot_reload=True`、`--plugins-dir` 绑定 |
| CX-07 | 负向：旧选项名 | `--plugin-dir` 解析失败（非 0） |
| CX-08 | `config show` | 临时 `NCATBOT_CONFIG_PATH` + 最小 yaml，进入回调并输出 |
| CX-09 | `napcat install -y` | `PlatformOps` mock 已安装早退，绑定 `-y` |
| CX-10 | `napcat diagnose ws` | `--uri` / `--token` 传入 `check_ws`（mock） |
