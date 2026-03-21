# NcatBot 测试套件

基于规范驱动测试设计（Spec-Driven Test Design），覆盖 NcatBot 框架核心功能。

## 目录结构

```
tests/
├── unit/              # 单元测试 — 按模块组织
│   ├── types/         # 类型系统 (T-01 ~ T-05, S-01 ~ S-10, CQ-01 ~ CQ-08, N-01 ~ N-05, MA-01 ~ MA-04, FW-01 ~ FW-03, SEG-01, LR-01 ~ LR-03)
│   ├── event/         # 事件工厂 (E-01 ~ E-04, GHE-01 ~ GHE-04, QMA-01 ~ QMA-03)
│   ├── api/           # API 客户端 + 错误层级 + Sugar (A-01 ~ A-02, AE-01 ~ AE-07, SG-01 ~ SG-06, FL-01 ~ FL-06)
│   ├── core/          # 核心分发与注册 + 谓词 (D-01 ~ D-09, K-01 ~ K-21, H-01 ~ H-11, R-01 ~ R-09, PR-01 ~ PR-06)
│   ├── service/       # 服务管理 + RBAC + 调度 (SM-01 ~ SM-08, SC-01 ~ SC-12, TS-01 ~ TS-06)
│   ├── plugin/        # 插件 Mixin + 导入去重 + Loader (M-01 ~ M-41, ID-01 ~ ID-02, LD-01 ~ LD-05)
│   ├── adapter/       # 适配器解析 + 注册表 + 真实数据 (P-01 ~ P-07, RF-01 ~ RF-08, AR-01 ~ AR-05, GM-01 ~ GM-05, BL-01 ~ BL-22, GH-01 ~ GH-11)
│   └── config/        # 配置迁移 + 安全 (CF-01 ~ CF-05, CS-01 ~ CS-05)
├── integration/       # 集成测试 (I-01 ~ I-21)
├── e2e/               # 端到端测试
│   ├── test_bot_client.py  # BotClient E2E (B-01 ~ B-05)
│   ├── plugin/        # 插件离线 E2E (PL-01 ~ PL-53)
│   └── napcat/        # NapCat 真实连接 E2E (NC-01 ~ NC-21)
└── fixtures/          # 共享测试数据
```

## 运行测试

```bash
# 全部测试
python -m pytest tests/ -v

# 单元测试
python -m pytest tests/unit/ -v

# 带覆盖率
python -m pytest tests/ --cov=ncatbot --cov-report=term-missing -v

# 指定模块
python -m pytest tests/unit/core/ -v

# NapCat E2E (需要真实连接，不使用 pytest，引导式执行)
# $env:NAPCAT_TEST_GROUP="123456"; $env:NAPCAT_TEST_USER="654321"
python tests/e2e/napcat/run.py

```

## 测试基础设施

| 组件 | 说明 |
|------|------|
| `ncatbot.testing.TestHarness` | 集成/E2E 测试脚手架，管理 MockAdapter + Dispatcher + HandlerDispatcher 生命周期 |
| `ncatbot.testing.factory` | 事件数据工厂函数，生成合法的 GroupMessage / PrivateMessage / Notice / Request 数据 |
| `ncatbot.adapter.mock.MockBotAPI` | Mock API 实现，记录所有 API 调用到 `call_log` |
| `ncatbot.adapter.mock.MockAdapter` | Mock 适配器，支持手动注入事件 |

## 规范编号体系

| 前缀 | 模块 | 范围 |
|------|------|------|
| T | Types / Segments | T-01 ~ T-05 |
| S | Segment 解析 (parse_segment) | S-01 ~ S-10 |
| CQ | CQ 码解析 | CQ-01 ~ CQ-08 |
| N | NapCat 类型模型 | N-01 ~ N-05 |
| E | Event Entity / Factory | E-01 ~ E-04 |
| A | API Client | A-01 ~ A-02 |
| AE | API Errors | AE-01 ~ AE-07 |
| P | EventParser / NapCatEventParser | P-01 ~ P-07 |
| AR | AdapterRegistry | AR-01 ~ AR-05 |
| CF | Config Migration | CF-01 ~ CF-05 |
| D | AsyncEventDispatcher | D-01 ~ D-09 |
| K | Hook System | K-01 ~ K-21 |
| H | HandlerDispatcher | H-01 ~ H-11 |
| R | Registrar | R-01 ~ R-09 |
| ID | Import Dedup (插件导入去重) | ID-01 ~ ID-02 |
| SM | ServiceManager | SM-01 ~ SM-08 |
| M | Plugin Mixin | M-01 ~ M-41 |
| I | Integration | I-01 ~ I-21 |
| B | BotClient E2E | B-01 ~ B-05 |
| PL | Plugin E2E | PL-01 ~ PL-53 |
| NC | NapCat E2E | NC-01 ~ NC-21 |
| SC | RBAC 权限系统 | SC-01 ~ SC-12 |
| PR | Predicate 谓词 DSL | PR-01 ~ PR-06 |
| TS | TimeTaskParser 调度解析 | TS-01 ~ TS-06 |
| LD | PluginLoader 生命周期 | LD-01 ~ LD-05 |
| CS | Config 安全检查 | CS-01 ~ CS-05 |
| SG | QQ Sugar 便捷方法 | SG-01 ~ SG-06 |
| MA | MessageArray 容器 | MA-01 ~ MA-04 |
| FW | Forward 转发消息 | FW-01 ~ FW-03 |
| RF | 真实日志夹具事件解析 | RF-01 ~ RF-08 |
| GM | 群消息批量真实数据 | GM-01 ~ GM-05 |
| BL | Bilibili 事件解析 | BL-01 ~ BL-17 |
| LR | Bilibili 数据模型 (LiveRoomInfo) | LR-01 ~ LR-03 |
| GH | GitHub 事件解析 | GH-01 ~ GH-11 |
| SEG | 消息段附件桥接 | SEG-01 |
| GHE | GitHub 事件实体 | GHE-01 ~ GHE-04 |
| QMA | QQ 消息附件 | QMA-01 ~ QMA-03 |
| FL | QQ 文件操作 | FL-01 ~ FL-06 |
