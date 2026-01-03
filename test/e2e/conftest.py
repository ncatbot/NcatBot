"""
E2E 测试全局配置
"""


def pytest_configure(config):
    """配置 pytest"""
    config.addinivalue_line("markers", "asyncio: mark test as async")


# 注意：共享 MockServer 的方案在实践中存在连接复用问题
# WebSocket 连接有状态，多个 BotClient 实例无法安全地共享同一个 MockServer
# 因此暂时回退到每个测试创建独立 MockServer 的方案
#
# 未来可能的优化方向：
# 1. 使用端口池，避免端口冲突
# 2. Class 级别的 fixture，同一测试类内共享
# 3. 改进 MockServer 以支持多个并发连接
