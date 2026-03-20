# 事件处理链路参考

追踪"消息从接收到处理"或"API 从调用到发送"的完整链路时使用。

## 入站链路（收消息）

```text
NapCatAdapter（WebSocket 收消息）
  → OB11Protocol（解析 OneBot 协议）
  → NapCatEventParser（构造事件实体）
  → AsyncEventDispatcher（广播事件）
  → HandlerDispatcher（匹配 handler + 执行 Hook 链）
  → 用户 handler 函数
```

## 出站链路（发消息 / 调 API）

```text
用户调用 BotAPIClient 方法
  → IAPIClient 接口
  → NapCatBotAPI 实现
  → WebSocket 发送请求
```

## 读代码的策略

1. **用搜索（Explore 子代理）** 查找从文档中获得的关键类名/函数名
2. **只读目标文件**，不遍历整个模块
3. **追踪调用链时**，从已知入口顺着调用走，而非全局搜索
