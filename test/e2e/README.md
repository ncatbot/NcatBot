# NcatBot 端到端测试

本目录包含 NcatBot 的各类端到端测试（E2E Tests）。

## 目录结构

```
test/e2e/
├── api/                # API 服务端到端测试
│   ├── run.py              # API 测试入口脚本
│   ├── README.md           # API 测试详细文档
│   ├── __init__.py         # API 测试模块定义
│   ├── framework/          # API 测试框架
│   ├── data/               # API 测试数据
│   └── test_*.py           # API 测试用例
└── plugin_config/      # PluginConfig 服务端到端测试
    ├── __init__.py         # PluginConfig 测试模块
    ├── test_plugin.py      # 测试插件
    └── test_plugin_config_e2e.py  # PluginConfig E2E 测试用例
```

## 测试类型

### API 端到端测试 (`api/`)

基于真实的 NapCat 服务连接的完整端到端测试，覆盖所有 API 功能：

- **账号管理**: 登录信息、状态查询、版本信息
- **好友管理**: 好友列表、好友操作、好友申请处理
- **消息处理**: 私聊/群聊消息、消息操作、转发消息
- **群组管理**: 群信息、成员管理、管理员操作
- **文件操作**: 私聊文件、群文件、相册管理

**运行方式**:
```bash
# 运行 API 端到端测试
uv run python test/e2e/api/run.py

# 只运行账号相关测试
uv run python test/e2e/api/run.py --category account

# 生成测试报告
uv run python test/e2e/api/run.py --report ./reports/api_test.md
```

### PluginConfig 服务测试 (`plugin_config/`)

基于 `utils/testing` 框架的插件配置服务端到端测试：

- **配置注册**: 验证配置项正确注册和默认值
- **配置修改**: 测试配置值的动态修改功能
- **配置持久化**: 验证配置保存和加载
- **配置隔离**: 确保插件间的配置不会相互干扰
- **错误处理**: 测试无效配置操作的处理

**运行方式**:
```bash
# 运行 PluginConfig E2E 测试
uv run pytest test/e2e/plugin_config/ -v
```

## 注意事项

1. **API 测试**: 需要真实的 NapCat 服务运行，请先启动 NapCat 并确保网络连接正常
2. **PluginConfig 测试**: 基于 Mock 框架，无需真实服务，可直接运行
3. **测试数据**: API 测试需要配置测试数据文件，请参考 `api/README.md`
4. **权限要求**: 某些 API 测试需要管理员权限或特殊配置

## 添加新测试

### 添加 API 测试

在 `api/` 目录下添加新的测试场景或用例，请参考 `api/README.md` 的详细说明。

### 添加服务测试

1. 在 `test/e2e/` 下创建新的服务目录
2. 基于 `utils/testing/suite.py` 的 `E2ETestSuite` 框架
3. 创建测试插件和服务测试用例
4. 更新本 README.md 文件

## CI/CD 集成

- API 测试需要标记为需要手动运行或在有 NapCat 服务的环境中运行
- PluginConfig 等服务测试可以集成到常规的 CI/CD 流程中
