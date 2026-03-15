# 贡献指南

> 为 NcatBot 贡献代码的指引

---

## Quick Start

5 步完成你的第一次贡献：

### 1. Fork & Clone

```bash
git clone https://github.com/<your-username>/NcatBot.git
cd NcatBot
```

### 2. 安装开发环境

```bash
uv sync
.venv\Scripts\activate.ps1   # Windows
# source .venv/bin/activate  # Linux/macOS
```

### 3. 创建分支

```bash
git checkout -b feat/my-feature
```

### 4. 开发 & 测试

```bash
# 运行测试
python -m pytest tests/

# 代码格式化
ruff format .
ruff check . --fix
```

### 5. 提交 PR

```bash
git add .
git commit -m "feat: 描述你的修改"
git push origin feat/my-feature
```

然后在 GitHub 上创建 Pull Request。

---

## 文档索引

| 目录 | 说明 |
|------|------|
| [development_setup/](development_setup/) | 开发环境搭建 |
| [design_decisions/](design_decisions/) | 设计决策记录（ADR） |
| [module_internals/](module_internals/) | 模块内部实现详解 |

### development_setup/ — 开发环境

详细的环境搭建与工具链配置：

- [基础环境](development_setup/0_basic.md) — Python、uv、依赖安装
- [高级配置](development_setup/1_advanced.md) — IDE 配置、调试、代码规范

> 旧版单文件指南：[development-setup.md](development-setup.md)

### design_decisions/ — 设计决策

架构决策记录（ADR），记录关键设计选择的背景与理由：

- [架构决策](design_decisions/1_architecture.md) — 分层架构、适配器模式
- [实现决策](design_decisions/2_implementation.md) — Dispatcher、Hook、热重载

> 旧版单文件指南：[design-decisions.md](design-decisions.md)

### module_internals/ — 模块内部实现

深入各模块的内部实现细节：

- WebSocket 连接管理
- 协议匹配与路由
- 拓扑排序（插件依赖）
- Trie 权限树
- 热重载机制

> 旧版单文件指南：[module-internals.md](module-internals.md)

---

## 贡献规范

- **分支命名**：`feat/xxx`、`fix/xxx`、`docs/xxx`
- **Commit 格式**：遵循 [Conventional Commits](https://www.conventionalcommits.org/)
- **代码风格**：使用 `ruff` 格式化，CI 会自动检查
- **测试**：新功能需附带测试（项目正在重构中，测试暂不强制）

---

## 交叉引用

| 如果你在找… | 去这里 |
|------------|--------|
| 架构总览 | [architecture.md](../architecture.md) |
| 插件开发教程 | [guide/plugin/](../guide/plugin/) |
| API 参考 | [reference/](../reference/) |
