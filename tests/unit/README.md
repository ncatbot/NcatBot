# 单元测试

按 NcatBot 模块组织的单元测试，每个子目录对应一个源码模块。

## 模块映射

| 目录 | 源码模块 | 规范范围 |
|------|----------|----------|
| [types/](types/) | `ncatbot.types` | T-01 ~ T-05, S-01 ~ S-10, CQ-01 ~ CQ-08, N-01 ~ N-05, MA-01 ~ MA-04, FW-01 ~ FW-03, SEG-01 |
| [event/](event/) | `ncatbot.event` | E-01 ~ E-04, GHE-01 ~ GHE-04, QMA-01 ~ QMA-03 |
| [api/](api/) | `ncatbot.api` | A-01 ~ A-02, AE-01 ~ AE-07, SG-01 ~ SG-06, FL-01 ~ FL-06 |
| [core/](core/) | `ncatbot.core` | D-01 ~ D-09, K-01 ~ K-21, H-01 ~ H-11, R-01 ~ R-07, PR-01 ~ PR-06 |
| [service/](service/) | `ncatbot.service` | SM-01 ~ SM-08, SC-01 ~ SC-12, TS-01 ~ TS-06 |
| [plugin/](plugin/) | `ncatbot.plugin.mixin` | M-01 ~ M-41, ID-01 ~ ID-02, LD-01 ~ LD-05 |
| [adapter/](adapter/) | `ncatbot.adapter.napcat` | P-01 ~ P-07, RF-01 ~ RF-08, AR-01 ~ AR-05, GM-01 ~ GM-05, BL-01 ~ BL-14, GH-01 ~ GH-11 |
| [config/](config/) | `ncatbot.utils.config` | CF-01 ~ CF-05, CS-01 ~ CS-05, CE-01 ~ CE-05 |
| [cli/](cli/) | `ncatbot.cli` | CX-01 ~ CX-14 |

## 公共 Fixtures (`conftest.py`)

| Fixture | 类型 | 说明 |
|---------|------|------|
| `mock_api` | sync | `MockBotAPI` 实例 |
| `event_dispatcher` | async | `AsyncEventDispatcher`，测试后自动 `close()` |
| `handler_dispatcher` | async | `HandlerDispatcher`，测试后自动 `stop()` |
| `fresh_registrar` | sync | 全新 `Registrar`，自动清理全局 `_pending_handlers` |
| `tmp_plugin_workspace` | sync | 临时插件工作目录 (`tmp_path` 子目录) |
