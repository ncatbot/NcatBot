# 功能预览工作流

> 本文件为 agent 参考，定义端到端功能预览的格式规范、askQuestion 确认模板和预览样板。

---

## 端到端预览格式规范

每个功能点按以下结构编写预览：

```markdown
### 功能 N：<功能名称>

<一句话描述功能效果>

**触发方式**：<用户命令 / 外部事件 / 定时任务>

**对话流**：

用户: <具体输入>
Bot:  <具体输出>
用户: <后续输入（如果有）>
Bot:  <后续输出>
...

**边界情况**：
- <异常输入时的行为>
- <超时/取消时的行为>
```

### 格式要点

- **对话流**必须是具体的输入/输出文本，不是抽象描述。用户看到预览应能直观理解"群里发什么，Bot 回什么"。
- **外部事件驱动**的功能（如 GitHub webhook 通知），用 `[事件]` 标记触发源而非 `用户:`。
- 每个功能点独立，不要合并多个功能到一个预览中。
- **边界情况**可选，复杂功能建议写出。

---

## askQuestion 模板库

### 外部依赖确认模板

当需求涉及第三方 API/服务时使用。**精简，只在有实质选择时才问**。

```json
{
  "header": "天气数据源",
  "question": "你想用哪个天气 API？",
  "options": [
    { "label": "和风天气 (免费额度 1000次/天)", "description": "国内常用，中文友好" },
    { "label": "OpenWeatherMap (免费额度 60次/分)", "description": "国际标准，英文 API" },
    { "label": "我不知道，你帮我选一个", "recommended": true }
  ]
}
```

> 规则：
> - 每个问题**必须**有"我不知道，你帮我选一个"选项，标记 `recommended: true`。
> - 不问框架内部选择（插件模式、Mixin、Hook 等由 agent 自决）。
> - 如果只有一个合理选项，不要问，直接用。

### 功能确认模板

预览写好后，逐功能确认：

```json
{
  "header": "功能 1：每日签到",
  "question": "以下是该功能的预期效果，请确认：",
  "options": [
    { "label": "✅ 满意", "description": "按这个效果来实现" },
    { "label": "✏️ 需要调整", "description": "我会在下方说明要改什么" },
    { "label": "❌ 不要这个功能" }
  ]
}
```

> 如果选 ✏️，通过 `freeText` 收集调整意见，修改预览后重新确认该功能。

### 批量确认模板（功能较多时）

当功能点 ≥ 5 个时，可先一次性展示全部预览，然后批量确认：

```json
{
  "header": "功能预览确认",
  "question": "以上 N 个功能的预览你满意吗？如有要调整的，请在下方说明功能编号和调整意见。",
  "options": [
    { "label": "全部满意，开始实现", "recommended": true },
    { "label": "部分需要调整（见下方说明）" },
    { "label": "整体方向有问题，重新讨论" }
  ]
}
```

---

## 端到端预览样板

以下是 5 个不同类型的功能预览样板，覆盖常见模式。编写预览时可参考对应样板。

### 样板 1：简单命令响应

> 来源：`docs/docs/examples/common/01_hello_world/`

```markdown
### 功能 1：打招呼

收到 hello 命令时回复问候语。

**触发方式**：群聊/私聊发送 `hello`

**对话流**：

用户: hello
Bot:  Hello, World! 👋

用户: Hello
Bot:  Hello, World! 👋

用户: hi
Bot:  你好呀！这是跨平台 hello world 🎉
```

---

### 样板 2：多步对话

> 来源：`docs/docs/examples/common/06_multi_step_dialog/`

```markdown
### 功能 2：用户注册

通过多步对话收集用户信息并保存。

**触发方式**：群聊/私聊发送 `注册`

**对话流**：

用户: 注册
Bot:  📝 开始注册！请输入你的名字（30秒内回复，输入「取消」退出）：
用户: 张三
Bot:  好的，张三！请输入你的年龄：
用户: 25
Bot:  请确认你的信息:
        名字: 张三
        年龄: 25
      回复「确认」完成注册：
用户: 确认
Bot:  ✅ 注册成功！欢迎你，张三（25岁）

**边界情况**：
- 30 秒内未回复 → Bot: "⏰ 注册超时，已取消"
- 输入 "取消" → Bot: "❌ 注册已取消"
- 年龄非数字 → Bot: "❌ 年龄必须是数字，注册已取消"

**查询已注册信息**：

用户: 我的信息
Bot:  👤 你的注册信息:
        名字: 张三
        年龄: 25
```

---

### 样板 3：外部 API 集成

> 来源：`docs/docs/examples/common/07_external_api/`

```markdown
### 功能 3：每日一言

调用外部 API 获取随机一句话。

**触发方式**：群聊/私聊发送 `每日一言`

**对话流**：

用户: 每日一言
Bot:  📜 人生若只如初见，何事秋风悲画扇。
          —— 木兰花·拟古决绝词柬友 (纳兰性德)

**管理命令**：

用户: 设置一言源 https://v1.hitokoto.cn
Bot:  一言 API 已更新为: https://v1.hitokoto.cn

用户: api状态
Bot:  🔌 API 状态:
        一言 API: https://v1.hitokoto.cn
        累计调用: 42 次

**边界情况**：
- API 请求超时 → Bot: "⚠️ 网络请求失败，请稍后重试"
- API 返回非 200 → Bot: "⚠️ API 请求失败 (HTTP 502)"
```

---

### 样板 4：外部事件驱动通知

> 来源：`plugins/version_notifier/` + 虚构场景

```markdown
### 功能 4：GitHub 仓库动态通知

监听 GitHub 仓库的 Release 和 Push 事件，自动通知到 QQ 群。

**触发方式**：GitHub Webhook 事件（无需用户输入）

**行为流**：

[GitHub] ncatbot/NcatBot 发布 Release v5.3.0
Bot → 群 201487478:
  🎉 NcatBot 发布新版本 v5.3.0！

  修复若干 bug，新增 Bilibili 直播间适配器。

  详情: https://github.com/ncatbot/NcatBot/releases/tag/v5.3.0
  📄 用户手册已更新至群文件，请查阅。

[GitHub] dev 分支收到 push (3 commits by @huan-yp)
Bot → 群 201487478:
  🔔 [NcatBot] dev 分支收到 3 个新提交:
  · fix: 修复 WebSocket 重连逻辑 — @huan-yp
  · feat: 新增 Bilibili 弹幕事件 — @huan-yp
  · docs: 更新多平台开发指南 — @huan-yp

**边界情况**：
- 预发布版本(prerelease) → 跳过通知
- Release 中未找到附件 → 仅发通知，不上传文件
```

---

### 样板 5：命令组 + 权限控制

> 虚构场景

```markdown
### 功能 5：群管理工具

提供管理员专用的群管理命令组。

**触发方式**：群聊发送 `/admin <子命令>`

**对话流（管理员）**：

用户(管理员): /admin ban @张三 10m
Bot:  🔇 已禁言 张三 10分钟

用户(管理员): /admin kick @李四
Bot:  👢 已将 李四 移出群聊

用户(管理员): /admin welcome 欢迎新成员！请先看群公告 📋
Bot:  ✅ 入群欢迎语已更新

**对话流（普通用户）**：

用户(普通): /admin ban @张三 10m
Bot:  ⛔ 权限不足：此命令需要「管理员」权限

**帮助信息**：

用户: /help admin
Bot:  📋 admin — 群管理工具
      子命令：
        ban <@用户> <时长>   禁言指定用户
        kick <@用户>         移出群聊
        welcome <文本>       设置入群欢迎语
      权限要求：管理员
```
