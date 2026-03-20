<div align="center">

# 🚀 ncatbot

---

![logo.png](https://socialify.git.ci/ncatbot/NcatBot/image?custom_description=ncatbot+%EF%BC%8C%E5%9F%BA%E4%BA%8E+OneBot11%E5%8D%8F%E8%AE%AE+%E7%9A%84+QQ+%E6%9C%BA%E5%99%A8%E4%BA%BA+Python+SDK%EF%BC%8C%E5%BF%AB%E9%80%9F%E5%BC%80%E5%8F%91%EF%BC%8C%E8%BD%BB%E6%9D%BE%E9%83%A8%E7%BD%B2%E3%80%82&description=1&font=Jost&forks=1&issues=1&logo=https%3A%2F%2Fimg.remit.ee%2Fapi%2Ffile%2FAgACAgUAAyEGAASHRsPbAAO9Z_FYKczZ5dly9IKmC93J_sF7qRUAAmXEMRtA2ohX1eSKajqfARABAAMCAAN5AAM2BA.jpg&pattern=Signal&pulls=1&stargazers=1&theme=Auto)

 <a href="https://pypi.org/project/ncatbot5/"><img src="https://img.shields.io/pypi/v/ncatbot5"></a>
 [![OneBot v11](https://img.shields.io/badge/OneBot-v11-black.svg)](https://github.com/botuniverse/onebot)
 [![访问量统计](https://visitor-badge.laobi.icu/badge?page_id=li-yihao0328.ncatbot_sync)](https://github.com/ncatbot/ncatbot)
  <a><img src="https://img.shields.io/badge/License-NcatBot License-green.svg"></a>
    <a href="https://qm.qq.com/q/CHbzJ2LH4k"><img src="https://img.shields.io/badge/官方群聊-201487478-brightgreen.svg"></a>
    <a href="https://qm.qq.com/q/CHbzJ2LH4k"><img src="https://img.shields.io/badge/官方频道-pd63222487-brightgreen.svg"></a>
    <a href="https://ippclub.org"><img src="https://img.shields.io/badge/I%2B%2B%E4%BF%B1%E4%B9%90%E9%83%A8-%E8%AE%A4%E8%AF%81-11A7E2?logo=data%3Aimage%2Fsvg%2Bxml%3Bcharset%3Dutf-8%3Bbase64%2CPHN2ZyB2aWV3Qm94PSIwIDAgMjg4IDI3NCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiB4bWw6c3BhY2U9InByZXNlcnZlIiBzdHlsZT0iZmlsbC1ydWxlOmV2ZW5vZGQ7Y2xpcC1ydWxlOmV2ZW5vZGQ7c3Ryb2tlLWxpbmVqb2luOnJvdW5kO3N0cm9rZS1taXRlcmxpbWl0OjIiPjxwYXRoIGQ9Im0xNDYgMzEgNzIgNTVWMzFoLTcyWiIgc3R5bGU9ImZpbGw6I2Y2YTgwNjtmaWxsLXJ1bGU6bm9uemVybyIvPjxwYXRoIGQ9Im0xNjkgODYtMjMtNTUgNzIgNTVoLTQ5WiIgc3R5bGU9ImZpbGw6I2VmN2EwMDtmaWxsLXJ1bGU6bm9uemVybyIvPjxwYXRoIGQ9Ik0yNiAzMXY1NWg4MEw4MSAzMUgyNloiIHN0eWxlPSJmaWxsOiMwN2ExN2M7ZmlsbC1ydWxlOm5vbnplcm8iLz48cGF0aCBkPSJNMTA4IDkydjExMmwzMS00OC0zMS02NFoiIHN0eWxlPSJmaWxsOiNkZTAwNWQ7ZmlsbC1ydWxlOm5vbnplcm8iLz48cGF0aCBkPSJNMCAyNzR2LTUyaDk3bC0zMyA1MkgwWiIgc3R5bGU9ImZpbGw6I2Y2YTgwNjtmaWxsLXJ1bGU6bm9uemVybyIvPjxwYXRoIGQ9Im03NyAyNzQgNjctMTA3djEwN0g3N1oiIHN0eWxlPSJmaWxsOiNkZjI0MzM7ZmlsbC1ydWxlOm5vbnplcm8iLz48cGF0aCBkPSJNMTUyIDI3NGgyOWwtMjktNTN2NTNaIiBzdHlsZT0iZmlsbDojMzM0ODVkO2ZpbGwtcnVsZTpub256ZXJvIi8%2BPHBhdGggZD0iTTE5MSAyNzRoNzl2LTUySDE2N2wyNCA1MloiIHN0eWxlPSJmaWxsOiM0ZTI3NWE7ZmlsbC1ydWxlOm5vbnplcm8iLz48cGF0aCBkPSJNMjg4IDEwMGgtMTdWODVoLTEzdjE1aC0xN3YxM2gxN3YxNmgxM3YtMTZoMTd2LTEzWiIgc3R5bGU9ImZpbGw6I2M1MTgxZjtmaWxsLXJ1bGU6bm9uemVybyIvPjxwYXRoIGQ9Im0yNiA4NiA1Ni01NUgyNnY1NVoiIHN0eWxlPSJmaWxsOiMzMzQ4NWQ7ZmlsbC1ydWxlOm5vbnplcm8iLz48cGF0aCBkPSJNOTMgMzFoNDJsLTMwIDI5LTEyLTI5WiIgc3R5bGU9ImZpbGw6IzExYTdlMjtmaWxsLXJ1bGU6bm9uemVybyIvPjxwYXRoIGQ9Ik0xNTggMTc2Vjg2bC0zNCAxNCAzNCA3NloiIHN0eWxlPSJmaWxsOiMwMDU5OGU7ZmlsbC1ydWxlOm5vbnplcm8iLz48cGF0aCBkPSJtMTA2IDU5IDQxLTEtMTItMjgtMjkgMjlaIiBzdHlsZT0iZmlsbDojMDU3Y2I3O2ZpbGwtcnVsZTpub256ZXJvIi8%2BPHBhdGggZD0ibTEyNCAxMDAgMjItNDEgMTIgMjctMzQgMTRaIiBzdHlsZT0iZmlsbDojNGUyNzVhO2ZpbGwtcnVsZTpub256ZXJvIi8%2BPHBhdGggZD0ibTEwNiA2MCA0MS0xLTIzIDQxLTE4LTQwWiIgc3R5bGU9ImZpbGw6IzdiMTI4NTtmaWxsLXJ1bGU6bm9uemVybyIvPjxwYXRoIGQ9Im0xMDggMjA0IDMxLTQ4aC0zMXY0OFoiIHN0eWxlPSJmaWxsOiNiYTAwNzc7ZmlsbC1ydWxlOm5vbnplcm8iLz48cGF0aCBkPSJtNjUgMjc0IDMzLTUySDBsNjUgNTJaIiBzdHlsZT0iZmlsbDojZWY3YTAwO2ZpbGwtcnVsZTpub256ZXJvIi8%2BPHBhdGggZD0iTTc3IDI3NGg2N2wtNDAtNDUtMjcgNDVaIiBzdHlsZT0iZmlsbDojYTgxZTI0O2ZpbGwtcnVsZTpub256ZXJvIi8%2BPHBhdGggZD0iTTE2NyAyMjJoNThsLTM0IDUyLTI0LTUyWiIgc3R5bGU9ImZpbGw6IzExYTdlMjtmaWxsLXJ1bGU6bm9uemVybyIvPjxwYXRoIGQ9Im0yNzAgMjc0LTQ0LTUyLTM1IDUyaDc5WiIgc3R5bGU9ImZpbGw6IzA1N2NiNztmaWxsLXJ1bGU6bm9uemVybyIvPjxwYXRoIGQ9Ik0yNzUgNTVoLTU3VjBoMjV2MzFoMzJ2MjRaIiBzdHlsZT0iZmlsbDojZGUwMDVkO2ZpbGwtcnVsZTpub256ZXJvIi8%2BPHBhdGggZD0iTTE4NSAzMWg1N3Y1NWgtMjVWNTVoLTMyVjMxWiIgc3R5bGU9ImZpbGw6I2M1MTgxZjtmaWxsLXJ1bGU6bm9uemVybyIvPjwvc3ZnPg%3D%3D&labelColor=fff"></a>
</p>

[文档](https://docs.ncatbot.xyz) | [许可证](LICENSE) | [QQ群](https://qm.qq.com/q/AmdNUkSxFY) | [插件社区](https://www.ityzs.com/)

NcatBot 是基于 OneBot11 协议的 Python SDK/Framework，提供**开箱即用**的 QQ 机器人开发体验。<br>

它深度考虑了 AI 时代的开发者需求，工作区内置丰富的 Skills 能力，Agent 可自主完成插件编写、调试与测试。<br>

**只需要一句话，就能写出你的 QBot！**<br>

</div>

## 快速开始

### 1. 安装

```bash
pip install ncatbot5
```

### 2. 获取 AI 参考资料（推荐）

前往本项目 [GitHub Releases](https://github.com/ncatbot/NcatBot/releases) 页面，在最新版本的 Assets 中找到 `ncatbot5-X.Y.Z-user-reference.zip`，下载并解压到你的**项目根目录**。解压后目录结构如下：

```
your-project/
├── .agents/skills/   ← AI Agent 技能文件
├── docs/             ← 框架文档（含示例代码 docs/docs/examples/）
├── config.yaml
└── plugins/
```

> 这些文件让 AI Agent（如 VS Code 中的 Copilot Chat）理解 NcatBot 的 API 和用法，从而提供精准的代码建议。

### 3. 初始化项目

```bash
ncatbot init
```

按提示输入机器人 QQ 号和管理员 QQ 号，CLI 会自动生成 `config.yaml` 和一个以你计算机用户名命名的模板插件。该模板插件的功能是：在群聊或私聊中发送 `hello` 时，机器人回复 `hi`。

### 4. 启动

```bash
ncatbot run
```

## AI Agent 开发

工作区中预置了领域专有技能（Skills），在 VS Code 中使用 Copilot Chat 即可获得定制化辅助：

- **开发插件**：Agent 利用 `framework-usage` 技能提供消息发送、事件注册、Hook/过滤器等建议
- **框架开发**：`codebase-nav`（代码定位）、`framework-dev`（框架开发）、`testing`（测试）、`release`（发版）

直接用自然语言描述你要实现的功能，Agent 会自主编写插件代码。

## 其它资源

- **容器化部署**：推荐使用 Docker [部署环境](https://github.com/ncatbot/NcatBot-Docker)
- **官方文档**：[docs.ncatbot.xyz](https://docs.ncatbot.xyz)

## 交流群体

[是 QQ 群哦喵~](https://qm.qq.com/q/L6XGXYqL86)

## 获取帮助

遇到问题时，请按以下顺序尝试：

1. 阅读[文档](https://docs.ncatbot.xyz)
2. 搜索 [Issue 列表](https://github.com/ncatbot/ncatbot/issues)
3. 提交 [Issue](https://github.com/ncatbot/ncatbot/issues) 或[进群](https://qm.qq.com/q/L6XGXYqL86)提问

## 使用限制

1. **严禁将本项目以任何形式用于传播淫秽、反动或暴力等信息。**
2. **未经授权，禁止将本项目以任何形式用于盈利。**

## 致谢

感谢 [NapCat](https://github.com/NapNeko/NapCatQQ) 提供底层接口 | [IppClub](https://github.com/IppClub) 的宣传支持 | [Fcatbot](https://github.com/Fish-LP/Fcatbot) 提供代码和灵感。

感谢 [林枫云](https://www.dkdun.cn/) 提供服务器支持。

## 参与贡献

欢迎给本 Repo 贡献代码！请先阅读 [贡献指南](CONTRIBUTING.md)。


<div align="center">

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ncatbot/ncatbot&type=Date)](https://www.star-history.com/#ncatbot/ncatbot&Date)

## 贡献者们

<a href="https://github.com/ncatbot/ncatbot/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=ncatbot/ncatbot" />
</a>

</div>
