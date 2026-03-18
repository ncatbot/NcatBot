# API 参考

> Bot API 层完整参考 — NcatBot 5.2 多平台 API 的签名、参数与用法索引。

---

## Quick Reference

```python
from ncatbot.api import BotAPIClient
```

### 架构总览

```text
BotAPIClient                        ← 多平台路由（纯门面，无业务方法）
├── .qq : QQAPIClient               ← QQ 平台 API
│   ├── .messaging : QQMessaging    ← 消息收发 / 表情 / 已读 / 转发 / 历史
│   ├── .manage : QQManage          ← 群管理 / 好友管理 / 个人资料
│   ├── .query : QQQuery            ← 信息查询（40+ 方法）
│   ├── .file : QQFile              ← 文件上传 / 下载 / 文件夹管理
│   ├── post_group_msg()            ← QQMessageSugarMixin 便捷方法
│   └── send_group_text() ...
├── .bilibili : IBiliAPIClient      ← Bilibili 平台 API
│   ├── send_danmu()                ← 弹幕
│   ├── send_private_msg()          ← 私信
│   ├── send_comment()              ← 评论
│   └── ban_user() ...              ← 直播间管理
├── .platform("xxx")                ← 按名称获取平台 API
└── .platforms                      ← 所有已注册平台 Dict[str, IAPIClient]
```

### Trait 协议（跨平台）

| Trait | 核心方法 | 说明 |
|---|---|---|
| `IMessaging` | `send_private_msg`, `send_group_msg`, `delete_msg`, `send_forward_msg` | 消息发送与撤回 |
| `IGroupManage` | `set_group_kick`, `set_group_ban`, `set_group_admin` ... | 群管理 |
| `IQuery` | `get_login_info`, `get_friend_list`, `get_group_list` ... | 信息查询 |
| `IFileTransfer` | `upload_group_file`, `download_file` | 文件上传/下载 |

> 完整方法签名参见各子文档，或查阅 [guide/api_usage/](../../guide/api_usage/) 中的速查表。

---

## 本目录索引

### 通用

| 文件 | 说明 |
|------|------|
| [Trait 协议参考](common/traits.md) | IMessaging, IGroupManage, IQuery, IFileTransfer 完整签名 |

### QQ 平台

| 文件 | 说明 |
|------|------|
| [消息 API](qq/1_message_api.md) | QQMessaging 核心消息方法 + QQMessageSugarMixin 便捷方法 |
| [管理 API](qq/2_manage_api.md) | QQManage 群管理、好友管理与个人资料 |
| [查询与文件 API](qq/3_info_support_api.md) | QQQuery 信息查询 + QQFile 文件操作 |

### Bilibili 平台

| 文件 | 说明 |
|------|------|
| [Bilibili API](bilibili/1_api.md) | IBiliAPIClient 完整方法签名 |
