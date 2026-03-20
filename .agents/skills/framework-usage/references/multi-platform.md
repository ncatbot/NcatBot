# 多平台使用参考

> 参考文档：[guide/10. 多平台开发/](docs/guide/10. 多平台开发/), [guide/2. 适配器/](docs/guide/2. 适配器/)（各平台登录与配置）, [reference/7. 适配器/](docs/reference/7. 适配器/), [reference/1. Bot API/](docs/reference/1. Bot API/)

## 各平台登录与配置

| 平台 | 认证方式 | 指南 |
|------|---------|------|
| QQ (NapCat) | WebUI 扫码 / 快速登录 | `docs/guide/2. 适配器/1. NapCat QQ.md` |
| Bilibili | 终端扫码 (bilibili-api-python) | `docs/guide/2. 适配器/2. Bilibili.md` |
| GitHub | Personal Access Token | `docs/guide/2. 适配器/3. GitHub.md` |
| Mock | 无需认证 | `docs/guide/2. 适配器/4. Mock 适配器.md` |

## 多适配器启动

```python
from ncatbot.app import BotClient
from ncatbot.adapter import NapCatAdapter
from ncatbot.adapter.github import GitHubAdapter

bot = BotClient(adapters=[
    NapCatAdapter(),           # platform="qq"
    GitHubAdapter(),           # platform="github"
    # TelegramAdapter(),       # platform="telegram" (未来)
])
bot.run()
```

每个适配器的 `platform` 必须唯一，重复会抛 `ValueError`。

### GitHub 适配器配置

GitHub 适配器支持 Webhook 和 Polling 两种模式：

```yaml
# config.yaml
adapters:
  - type: github
    token: "ghp_xxxx"          # GitHub Personal Access Token
    repos:
      - "owner/repo1"
      - "owner/repo2"
    mode: webhook              # "webhook"(default) | "polling"
    # Webhook 模式
    webhook_host: "0.0.0.0"
    webhook_port: 8080
    webhook_path: "/webhook"
    webhook_secret: "your-secret"
    # Polling 模式
    poll_interval: 60.0
```

## 多平台 API 访问

```python
# 默认委托（第一个注册的平台）
await api.send_group_msg(group_id, message)

# 显式平台
await api.qq.send_group_msg(group_id, message)
await api.github.create_issue_comment(repo, issue_number, body)
# await api.platform("telegram").send_message(chat_id, text)

# 查看已注册平台
print(api.platforms)  # {"qq": <QQAPIClient>, "github": <GitHubBotAPI>, ...}
```

## 平台过滤

所有装饰器均支持 `platform` 参数：

```python
@registrar.on_group_message(platform="qq")
async def qq_only(event): ...

@registrar.on_command("/help", platform="qq")
async def help_cmd(event): ...

@registrar.on_message()  # 不指定 = 所有平台
async def all_platforms(event):
    print(event.platform)
```

## Trait 协议（跨平台编程）

### API Trait（`ncatbot.api.traits`）

| Trait | 方法 |
|---|---|
| `IMessaging` | `send_private_msg`, `send_group_msg`, `delete_msg`, `send_forward_msg` |
| `IGroupManage` | `set_group_kick`, `set_group_ban`, `set_group_admin`, ... |
| `IQuery` | `get_login_info`, `get_friend_list`, `get_group_list`, ... |
| `IFileTransfer` | `upload_group_file`, `upload_private_file`, `download_file` |

### Event Trait（`ncatbot.event.common.mixins`，通过 `ncatbot.event` 重新导出）

| Trait | 能力 |
|---|---|
| `Replyable` | `reply()`, `send()` |
| `Deletable` | `delete()` |
| `HasSender` | `sender` 属性 |
| `GroupScoped` | `group_id` 属性 |
| `Kickable` | `kick()` |
| `Bannable` | `ban()` |
| `Approvable` | `approve()`, `reject()` |
| `HasAttachments` | `get_attachments() -> AttachmentList` |

> **Attachment 体系**（`ncatbot.types` 重新导出）：
> - `Attachment`（基类）— `name`, `url`, `size`, `content_type`, `kind`, `extra`
> - `ImageAttachment`, `VideoAttachment`, `AudioAttachment`, `FileAttachment` — 类型化子类
> - `AttachmentList`（`list` 子类）— `images()`, `videos()`, `audios()`, `files()`, `by_kind()`, `first()`, `largest()`, `download_all()`
> - 每个 Attachment 带 `download(dest)`, `as_bytes()`, `to_segment()`, `to_local_segment(cache_dir)` 方法
> - `DownloadableSegment`（Image/Video/Record/File）带 `to_attachment()` 反向转换
> - `MessageArray.get_attachments()` 提取所有可下载段为 AttachmentList

### 跨平台 handler 示例

```python
from ncatbot.event import Replyable, GroupScoped, HasAttachments

@bot.on("message")
async def handler(event):
    if isinstance(event, Replyable):
        await event.reply("收到!")
    if isinstance(event, GroupScoped):
        print(f"群 {event.group_id}")
    if isinstance(event, HasAttachments):
        atts = await event.get_attachments()
        for img in atts.images():
            await img.download("/tmp/images")
        for vid in atts.videos():
            seg = vid.to_segment()  # 转为消息段用于转发
```

## event.platform

所有事件实体都有 `platform` 属性（字符串），来自适配器的 `platform` 类属性。

```python
@bot.on("message")
async def handler(event):
    if event.platform == "qq":
        # QQ 专用逻辑
        ...
```
