# 开发环境搭建

> 从零搭建 NcatBot 开发环境的完整指南。

---

## Quick Start

以下步骤可在 5 分钟内完成 NcatBot 开发环境搭建。

### 1. Fork & Clone

```bash
# 1. 在 GitHub 上 Fork https://github.com/ncatbot/ncatbot
# 2. Clone 到本地
git clone https://github.com/<你的用户名>/ncatbot.git
cd ncatbot

# 3. 添加上游远程仓库
git remote add upstream https://github.com/ncatbot/ncatbot.git
git fetch upstream
```

### 2. 安装依赖

```bash
uv sync --extra dev
```

该命令会自动完成：
1. 创建 `.venv/` 虚拟环境
2. 安装 `pyproject.toml` 中的运行依赖
3. 安装开发工具（pytest、ruff、mypy、tox、pre-commit 等）

### 3. 激活虚拟环境

```powershell
# Windows PowerShell
.venv\Scripts\activate.ps1
```

```bash
# Linux / macOS
source .venv/bin/activate
```

激活后终端提示符前缀显示 `(.venv)`。

### 4. 验证安装

```bash
python -c "import ncatbot; print('ncatbot 可用')"
uv run pytest --version
```

### 5. 安装 pre-commit 钩子

```bash
uv run pre-commit install
```

### 6. 创建功能分支并开始开发

```bash
git fetch upstream
git checkout -b feat/你的功能描述 upstream/main

# 编写代码...
uv run pytest           # 运行测试
git add .
git commit -m "feat: 你的功能描述"
git push origin feat/你的功能描述
```

然后在 GitHub 上创建 Pull Request，目标分支为上游 `main`。

---

## 工具链速查

### 必需工具

| 工具 | 最低版本 | 说明 |
|------|---------|------|
| **Python** | ≥ 3.12 | 推荐 3.12 或 3.13 |
| **uv** | 最新稳定版 | Python 包管理器 + 虚拟环境管理 |
| **Git** | ≥ 2.30 | 版本控制 |

### 安装命令

```bash
# 安装 uv — Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 安装 uv — Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 版本验证

```bash
uv --version
python --version   # 确认 ≥ 3.12
git --version
```

### 开发工具链（由 `uv sync --extra dev` 自动安装）

| 工具 | 用途 |
|------|------|
| **pytest** | 测试框架 |
| **ruff** | 代码 lint + 格式化 |
| **mypy** | 静态类型检查 |
| **tox** | 多版本测试 |
| **pre-commit** | Git 提交前自动检查 |
| **codespell** | 拼写检查 |

---

## 常用开发命令

### 代码格式化与检查

```bash
# Ruff lint（自动修复）
uv run ruff check --fix .

# Ruff 格式化
uv run ruff format .

# 类型检查
uv run mypy ncatbot/

# 拼写检查
uv run codespell

# pre-commit 全量运行
uv run pre-commit run --all-files
```

### 测试

```bash
# 运行全部测试（含覆盖率）
uv run pytest

# 覆盖率详情
uv run pytest --cov=ncatbot --cov-report=term-missing

# 多版本测试（tox）
uv run tox              # 全部版本
uv run tox -e py312     # 仅 Python 3.12
uv run tox -e py313     # 仅 Python 3.13
```

> 覆盖率 HTML 报告输出到 `htmlcov/`，浏览器打开 `htmlcov/index.html` 查看。

### 依赖管理

```bash
# 添加依赖后重新锁定 + 同步
uv lock
uv sync --extra dev

# 升级所有依赖
uv lock --upgrade
uv sync --extra dev
```

| 文件 | 作用 |
|------|------|
| `pyproject.toml` | 定义顶层依赖（宽泛版本范围） |
| `uv.lock` | 自动生成的精确锁定版本（纳入版本控制） |

### 项目结构速览

```
ncatbot/
├── adapter/    协议适配器（NapCat、Mock）
├── api/        Bot API 封装（IBotAPI / BotAPIClient）
├── app/        应用编排层（BotClient 生命周期管理）
├── cli/        命令行工具（ncatbot run / dev / config / plugin）
├── core/       核心引擎（Dispatcher 事件分发 / Registry 处理器注册）
├── event/      事件实体（MessageEvent / NoticeEvent / RequestEvent）
├── plugin/     插件框架（NcatBotPlugin / Mixin / Loader）
├── service/    服务层（RBAC / Schedule / FileWatcher）
├── testing/    测试工具（TestHarness / 数据工厂）
├── types/      Pydantic 数据模型（消息段 / 事件数据 / 枚举）
└── utils/      公共工具（日志 / 配置 / 网络 / 错误定义）
```

各模块详细职责与数据流参阅 [架构文档](../../architecture.md)。

### 代码规范速查

- 遵循 **PEP 8**（Ruff 自动格式化）
- **尽量添加类型注解**，尤其是函数签名和返回值
- 行尾统一 **LF**（pre-commit 自动转换）
- 提交信息遵循 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/v1.0.0/)：`<type>(<scope>): <description>`

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 添加消息撤回功能` |
| `fix` | Bug 修复 | `fix(api): 修复消息队列溢出 #123` |
| `docs` | 文档变更 | `docs: 更新安装指南` |
| `refactor` | 重构 | `refactor(core): 简化事件分发逻辑` |
| `test` | 测试 | `test: 补充 Registry 单元测试` |
| `chore` | 构建/工具 | `chore: 升级 ruff 版本` |

### 分支命名

| 前缀 | 用途 | 示例 |
|------|------|------|
| `feat/` | 新功能 | `feat/message-recall` |
| `fix/` | Bug 修复 | `fix/queue-overflow` |
| `docs/` | 文档 | `docs/plugin-guide` |
| `refactor/` | 重构 | `refactor/dispatcher` |
| `test/` | 测试 | `test/registry-unit` |

### PR 描述模板

```markdown
## 变更说明
<!-- 简要描述本次变更的内容和动机 -->

## 变更类型
- [ ] 新功能 (feat)
- [ ] Bug 修复 (fix)
- [ ] 文档更新 (docs)
- [ ] 重构 (refactor)
- [ ] 测试 (test)
- [ ] 其他 (chore / style / perf)

## 关联 Issue
<!-- Closes #xxx 或 Refs #xxx -->

## 检查清单
- [ ] 代码通过 `uv run pytest`
- [ ] 代码通过 `uv run ruff check .`
- [ ] 已添加 / 更新相关测试（如适用）
- [ ] 已更新相关文档（如适用）
```

### PR 提交后

- **CI 检查**：GitHub Actions 自动运行 lint、测试和多版本验证
- **Code Review**：维护者审阅代码，可能要求修改
- **同步上游**：如果 PR 存在冲突：

```bash
git fetch upstream
git merge upstream/main
# 解决冲突后
git add .
git commit -m "chore: 合并上游变更"
```

---

## 深入阅读

| 文档 | 内容 |
|------|------|
| [高级开发环境](1_advanced.md) | IDE 配置（VSCode settings.json）、调试配置（launch.json）、CI/CD 本地模拟、NapCat 本地部署、常见问题排查 |
| [架构总览](../../architecture.md) | 项目整体架构、模块职责、数据流与生命周期 |
| [设计决策](../design-decisions.md) | 关键设计决策与取舍 |
| [模块内部实现](../module-internals.md) | 各模块内部实现细节 |
