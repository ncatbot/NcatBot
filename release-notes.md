## ✨ 新功能
- **webui**: 新增 WebUI 测试调试面板，支持可视化事件模拟与插件调试 (13e78fb2)
- **api**: 新增 QQ 用户头像查询 (e907a1ac)
- **plugin**: 新增 session 便利方法 (04bc2c66)
- **ai**: 新增 ASR 音频识别接口 (d012d098)
- **bilibili**: 新增查询接口 — 获取视频音频流 URL、获取视频字幕文本 (93318546)
- **bilibili**: 凭证凌晨自动刷新 (7a8c647e)
- 新增 event_log_format 配置字段，支持人类可读的事件日志摘要 (1ff670eb, 7155632f, fd099c7d)

## 🐛 修复
- **bilibili**: 私信发送图片接口正确处理路径，同时支持网络 URL 和本地路径 (f2122434)
- **adapter**: 调整 NapCat 配置默认值 (2a46cc1e)
- **plugin**: 增强插件类发现诊断 (05d42238)
- **event**: 完善 Notice 事件能力声明 (5d8cf1bf)
- **api**: 加固 QQ 消息段冲突处理 (cf7daf63)
- **napcat**: 修复 get_msg() 返回中 message 为 MessageArray (73b3f110)
- **napcat**: reply 中 at 参数防呆传 bool (3da3862b)
- **bilibili**: 修复 log 风格不一致问题，覆盖第三方库的 logger (7287eb3e)
- **testing**: MockBotAPI 补齐 sugar 方法，extract_text 支持 MessageArray (0a2446da)

## ✅ 测试
- **webui**: 新增 WebUI 单元/集成/E2E 测试 (2d6d4ec1)
- b 站新增接口与 ASR 测试 (e7e732c2)
- 修复 CI 环境无第三方库问题 (e1c66d05)

## 🔧 构建/维护
- 更新依赖版本（aiohttp、litellm）和 gitignore (9b29580d)
- 同步锁文件包版本 (e50f8fc4)

## 📝 文档
- 同步示例与技能参考 (62bac12c)
- 更新 stale example 引用 (eb6ec05d)
