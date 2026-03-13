# API 模块

本文档详细介绍 NcatBot 的 API 层，包括 BotAPI 组合设计、各子 API 方法列表、同步/异步机制和客户端协议。

> 源码位置：`ncatbot/core/api/`

## 1. 架构概述

BotAPI 采用**多重继承组合**模式，将五个功能子模块整合为统一接口：

```
                    ┌─────────────┐
                    │   BotAPI    │
                    └──────┬──────┘
           ┌───────┬───────┼───────┬──────────┐
           ▼       ▼       ▼       ▼          ▼
      AccountAPI GroupAPI MessageAPI PrivateAPI SupportAPI
           │       │       │        │          │
           └───────┴───────┴────────┴──────────┘
                          │
                   ┌──────▼──────┐
                   │ APIComponent │  ← 公共基类
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │ IAPIClient  │  ← 客户端协议
                   └─────────────┘
```

### 1.1 BotAPI 初始化

```python
class BotAPI(AccountAPI, GroupAPI, MessageAPI, PrivateAPI, SupportAPI):
    def __init__(
        self,
        async_callback: Callable[[str, Optional[Dict]], Coroutine[Any, Any, Dict]],
        service_manager: Optional[ServiceManager] = None,
    ):
        ...
```

- `async_callback`：异步回调函数，用于发送 API 请求到 NapCat（实际由 `MessageRouter.send` 提供）
- `service_manager`：服务管理器引用，可选

### 1.2 APIComponent — 子模块基类

所有 API 子模块都继承自 `APIComponent`：

```python
class APIComponent:
    """API 组件基类，提供 IAPIClient 访问"""

    @property
    def client(self) -> IAPIClient:
        """获取 API 客户端"""
        ...
```

---

## 2. 客户端协议

> 源码位置：`ncatbot/core/api/client.py`

### 2.1 IAPIClient — 抽象接口

```python
class IAPIClient(ABC):
    """API 客户端抽象接口"""
    @abstractmethod
    async def request(self, endpoint: str, params: Optional[Dict]) -> APIResponse:
        ...
```

### 2.2 CallbackAPIClient — 回调实现

```python
class CallbackAPIClient(IAPIClient):
    """基于回调函数的 API 客户端"""
    def __init__(self, callback: Callable[[str, Optional[Dict]], Coroutine]):
        self._callback = callback

    async def request(self, endpoint: str, params: Optional[Dict]) -> APIResponse:
        raw = await self._callback(endpoint, params)
        return APIResponse.from_dict(raw)
```

### 2.3 APIResponse — 统一响应

```python
@dataclass
class APIResponse:
    retcode: int          # 返回码（0 = 成功）
    message: str          # 状态消息
    data: Any = None      # 响应数据
    raw: Dict = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.retcode == 0

    @classmethod
    def from_dict(cls, data: Dict) -> "APIResponse":
        ...
```

---

## 3. 同步/异步机制

NcatBot 的所有 API 方法默认为异步（`async`），同时通过 `@generate_sync_methods` 装饰器自动生成同步版本。

### 3.1 异步调用（推荐）

```python
# 在异步上下文中直接使用
await bot.api.post_group_msg(group_id="123", text="你好")
```

### 3.2 同步调用

```python
# 每个 async 方法都有对应的 _sync 版本
bot.api.post_group_msg_sync(group_id="123", text="你好")
```

### 3.3 实现原理

```python
@generate_sync_methods
class MessageAPI(APIComponent):
    async def post_group_msg(self, group_id, text=None, **kwargs) -> str:
        ...

# 装饰器自动生成：
# def post_group_msg_sync(self, group_id, text=None, **kwargs) -> str:
#     return run_sync(self.post_group_msg(group_id, text, **kwargs))
```

`run_sync()` 内部使用 `AsyncRunner`（单例），它维护一个独立的事件循环线程，确保线程安全：

```python
class AsyncRunner:
    """线程安全的异步运行器（单例）"""
    # 在独立线程中运行事件循环
    # 通过 concurrent.futures.Future 桥接同步调用
```

---

## 4. AccountAPI — 账号管理

> 源码位置：`ncatbot/core/api/api_account.py`

### 4.1 账号信息

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `get_login_info()` | — | `LoginInfo` | 获取登录信息（昵称、QQ号） |
| `get_status()` | — | `dict` | 获取当前状态 |
| `set_qq_profile()` | `nickname`, `personal_note`, `sex` | `None` | 设置个人信息 |
| `set_online_status()` | `status`, `ext_status`, `battery_status` | `None` | 设置在线状态 |
| `set_qq_avatar()` | `file: str` | `None` | 设置头像 |
| `set_self_longnick()` | `long_nick: str` | `None` | 设置个性签名 |

### 4.2 好友管理

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `get_friend_list()` | — | `List[dict]` | 获取好友列表 |
| `get_friends_with_cat()` | — | `List[dict]` | 获取分组好友列表 |
| `send_like()` | `user_id`, `times=1` | `Dict` | 点赞 |
| `set_friend_add_request()` | `flag`, `approve`, `remark=None` | `None` | 处理好友申请 |
| `delete_friend()` | `user_id`, `block=True`, `both=True` | `None` | 删除好友 |
| `set_friend_remark()` | `user_id`, `remark` | `None` | 设置好友备注 |
| `get_recent_contact()` | — | `List[dict]` | 获取最近联系人 |

### 4.3 消息状态

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `mark_group_msg_as_read()` | `group_id` | `None` | 标记群消息已读 |
| `mark_private_msg_as_read()` | `user_id` | `None` | 标记私聊已读 |
| `create_collection()` | `raw_data`, `brief` | `None` | 创建收藏 |

---

## 5. GroupAPI — 群管理

> 源码位置：`ncatbot/core/api/api_group/`

### 5.1 成员管理

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `set_group_kick()` | `group_id`, `user_id`, `reject_add_request=False` | `None` | 踢出成员 |
| `set_group_ban()` | `group_id`, `user_id`, `duration=1800` | `None` | 禁言（0=解禁） |
| `set_group_whole_ban()` | `group_id`, `enable=True` | `None` | 全群禁言 |
| `set_group_admin()` | `group_id`, `user_id`, `enable=True` | `None` | 设置/取消管理员 |
| `set_group_card()` | `group_id`, `user_id`, `card=""` | `None` | 设置群名片 |
| `set_group_leave()` | `group_id`, `is_dismiss=False` | `None` | 退群/解散 |
| `set_group_special_title()` | `group_id`, `user_id`, `special_title=""`, `duration=-1` | `None` | 设置专属头衔 |

### 5.2 群信息查询

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `get_group_info()` | `group_id` | `GroupInfo` | 获取群信息 |
| `get_group_info_ex()` | `group_id` | `dict` | 获取群详细信息 |
| `get_group_list()` | `info=False` | `List[str\|dict]` | 获取群列表 |
| `get_group_member_info()` | `group_id`, `user_id` | `GroupMemberInfo` | 获取成员信息 |
| `get_group_member_list()` | `group_id` | `GroupMemberList` | 获取成员列表 |
| `get_group_shut_list()` | `group_id` | `GroupMemberList` | 获取禁言列表 |
| `get_group_honor_info()` | `group_id`, `type` | `GroupChatActivity` | 获取群荣誉 |

### 5.3 群精华消息

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `set_essence_msg()` | `message_id` | `None` | 设为精华消息 |
| `delete_essence_msg()` | `message_id` | `None` | 取消精华消息 |
| `get_essence_msg_list()` | `group_id` | `List[EssenceMessage]` | 获取精华列表 |

### 5.4 群管理操作

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `set_group_name()` | `group_id`, `name` | `None` | 设置群名称 |
| `set_group_avatar()` | `group_id`, `file` | `None` | 设置群头像 |
| `set_group_remark()` | `group_id`, `remark` | `None` | 设置群备注 |
| `set_group_sign()` | `group_id` | `None` | 群签到 |
| `set_group_todo()` | `group_id`, `message_id` | `dict` | 设置群代办 |
| `_send_group_notice()` | `group_id`, `content`, `confirm_required=False`, `image=None`, ... | `None` | 发送群公告 |

### 5.5 群文件管理

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `upload_group_file()` | `group_id`, `file`, `name`, `folder=None` | `None` | 上传群文件 |
| `post_group_file()` | `group_id`, `image=None`, `record=None`, `video=None`, `file=None` | `str` | 发送群文件 |
| `get_group_root_files()` | `group_id`, `file_count=50` | `dict` | 获取群根目录文件 |
| `get_group_files_by_folder()` | `group_id`, `folder_id`, `file_count=50` | `dict` | 获取文件夹内容 |
| `get_group_file_url()` | `group_id`, `file_id` | `str` | 获取文件下载链接 |
| `get_file()` | `file_id`, `file` | `File` | 获取文件信息 |
| `create_group_file_folder()` | `group_id`, `folder_name` | `None` | 创建文件夹 |
| `move_group_file()` | `group_id`, `file_id`, `current_dir`, `target_dir` | `None` | 移动文件 |
| `rename_group_file()` | `group_id`, `file_id`, `new_name` | `None` | 重命名文件 |
| `delete_group_file()` | `group_id`, `file_id` | `None` | 删除文件 |
| `delete_group_folder()` | `group_id`, `folder_id` | `None` | 删除文件夹 |

### 5.6 群相册

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `get_group_album_list()` | `group_id` | `List[dict]` | 获取群相册列表 |
| `upload_image_to_group_album()` | `group_id`, `file`, `album_id=""`, `album_name=""` | `None` | 上传图片到相册 |

---

## 6. MessageAPI — 消息操作

> 源码位置：`ncatbot/core/api/api_message/`

### 6.1 群消息发送

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `post_group_msg()` | `group_id`, `text=None`, `at=None`, `reply=None`, `image=None`, `rtf=None` | `str` | 发送群消息（便捷接口） |
| `post_group_array_msg()` | `group_id`, `msg: MessageArray` | `str` | 发送群消息（数组格式） |
| `send_group_msg()` | `group_id`, `message: List[dict]` | `str` | 发送群消息（底层接口） |
| `send_group_text()` | `group_id`, `text` | `str` | 发送文本（支持 CQ 码） |
| `send_group_plain_text()` | `group_id`, `text` | `str` | 发送纯文本 |
| `send_group_image()` | `group_id`, `image` | `str` | 发送图片 |
| `send_group_record()` | `group_id`, `file` | `str` | 发送语音 |
| `send_group_file()` | `group_id`, `file`, `name=None` | `str` | 发送文件 |

### 6.2 私聊消息发送

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `post_private_msg()` | `user_id`, `text=None`, `reply=None`, `image=None`, `rtf=None` | `str` | 发送私聊消息（便捷接口） |
| `post_private_array_msg()` | `user_id`, `msg: MessageArray` | `str` | 发送私聊消息（数组格式） |
| `send_private_msg()` | `user_id`, `message: List[dict]` | `str` | 发送私聊消息（底层接口） |
| `send_private_text()` | `user_id`, `text` | `str` | 发送文本 |
| `send_private_plain_text()` | `user_id`, `text` | `str` | 发送纯文本 |
| `send_private_image()` | `user_id`, `image` | `str` | 发送图片 |
| `send_private_record()` | `user_id`, `file` | `str` | 发送语音 |
| `send_private_file()` | `user_id`, `file`, `name=None` | `str` | 发送文件 |

### 6.3 音乐分享

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `send_group_music()` | `group_id`, `type: "qq"\|"163"`, `id` | `str` | 发送群音乐（QQ音乐/网易云） |
| `send_group_custom_music()` | `group_id`, `url`, `title`, `image`, `audio=None`, `content=None` | `str` | 发送群自定义音乐 |
| `send_private_music()` | `user_id`, `type`, `id` | `str` | 发送私聊音乐 |
| `send_private_custom_music()` | `user_id`, `url`, `title`, `image`, `audio=None`, `content=None` | `str` | 发送私聊自定义音乐 |

### 6.4 戳一戳

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `group_poke()` | `group_id`, `user_id` | `None` | 群戳一戳 |
| `friend_poke()` | `user_id` | `None` | 好友戳一戳 |
| `send_poke()` | `user_id`, `group_id=None` | `None` | 通用戳一戳 |

### 6.5 通用消息操作

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `delete_msg()` | `message_id` | `None` | 撤回消息 |
| `set_msg_emoji_like()` | `message_id`, `emoji_id`, `set=True` | `None` | 表情回应 |
| `forward_group_single_msg()` | `group_id`, `message_id` | `None` | 转发到群 |
| `forward_private_single_msg()` | `user_id`, `message_id` | `None` | 转发给好友 |

### 6.6 消息获取

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `get_msg()` | `message_id` | `MessageEvent` | 获取消息详情 |
| `get_group_msg_history()` | `group_id`, `message_seq=None`, `count=20`, `reverse_order=False` | `List[GroupMessageEvent]` | 获取群历史消息 |
| `get_friend_msg_history()` | `user_id`, `message_seq`, `count=20`, `reverse_order=False` | `List[PrivateMessageEvent]` | 获取好友历史消息 |
| `get_forward_msg()` | `message_id` | `Forward` | 获取合并转发内容 |
| `get_record()` | `file=None`, `file_id=None`, `out_format="mp3"` | `Record` | 获取语音文件 |
| `get_image()` | `file=None`, `file_id=None` | `Image` | 获取图片文件 |

### 6.7 合并转发

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `post_group_forward_msg()` | `group_id`, `forward: Forward` | `str` | 发送群合并转发 |
| `post_private_forward_msg()` | `user_id`, `forward: Forward` | `str` | 发送私聊合并转发 |
| `post_forward_msg()` | `group_id=None`, `user_id=None`, `msg: Forward=None` | `str` | 通用合并转发 |
| `send_group_forward_msg_by_id()` | `group_id`, `messages: List[int\|str]` | `str` | 按消息ID转发到群 |
| `send_private_forward_msg_by_id()` | `user_id`, `messages: List[int\|str]` | `str` | 按消息ID转发给好友 |

---

## 7. PrivateAPI — 私聊扩展

> 源码位置：`ncatbot/core/api/api_private.py`

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `upload_private_file()` | `user_id`, `file`, `name` | `None` | 上传私聊文件 |
| `get_private_file_url()` | `file_id` | `str` | 获取私聊文件链接 |
| `post_private_file()` | `user_id`, `image=None`, `record=None`, `video=None`, `file=None` | `str` | 发送私聊文件 |
| `set_input_status()` | `event_type` (0=说话, 1=输入), `user_id` | `None` | 设置输入状态 |

---

## 8. SupportAPI — 辅助功能

> 源码位置：`ncatbot/core/api/api_support.py`

### 8.1 AI 语音聊天

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `get_ai_characters()` | `group_id`, `chat_type: 1\|2` | `AICharacterList` | 获取AI角色列表 |
| `get_ai_record()` | `group_id`, `character_id`, `text` | `str` | AI 文字转语音 |

### 8.2 能力检查

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `can_send_image()` | — | `bool` | 是否支持发送图片 |
| `can_send_record()` | `group_id` | `bool` | 是否支持发送语音 |

### 8.3 系统功能

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `ocr_image()` | `image` | `List[dict]` | 图片 OCR（仅 Windows） |
| `get_version_info()` | — | `dict` | 获取版本信息 |
| `bot_exit()` | — | `None` | 退出 Bot |

---

## 9. 转发消息构造器

> 源码位置：`ncatbot/core/helper/forward_constructor.py`

`ForwardConstructor` 提供便捷的合并转发消息构造能力：

```python
from ncatbot.core import ForwardConstructor

# 创建构造器
fc = ForwardConstructor(user_id="123456", nickname="Bot")

# 添加消息节点
fc.attach_text("第一条消息")
fc.attach_text("第二条消息")
fc.attach_image("path/to/image.jpg")

# 切换作者
fc.set_author(user_id="789", nickname="其他人")
fc.attach_text("来自其他人的消息")

# 构建并发送
forward = fc.to_forward()
await bot.api.post_group_forward_msg(group_id="12345", forward=forward)
```

### 9.1 可用方法

| 方法 | 参数 | 说明 |
|------|------|------|
| `set_author()` | `user_id`, `nickname` | 设置当前作者信息 |
| `attach_text()` | `text`, `user_id=None`, `nickname=None` | 添加文本节点 |
| `attach_image()` | `image`, `user_id=None`, `nickname=None` | 添加图片节点 |
| `attach_file()` | `file`, `user_id=None`, `nickname=None` | 添加文件节点 |
| `attach_video()` | `video`, `user_id=None`, `nickname=None` | 添加视频节点 |
| `attach_message()` | `message: MessageArray`, `user_id=None`, `nickname=None` | 添加消息段节点 |
| `attach_forward()` | `forward: Forward`, `user_id=None`, `nickname=None` | 嵌套转发 |
| `to_forward()` | — | 构建 Forward 对象 |

---

## 10. 错误处理

> 源码位置：`ncatbot/core/api/utils/errors.py`

### 10.1 异常类型

```python
class NapCatAPIError(Exception):
    """NapCat API 调用返回错误"""
    retcode: int        # 错误码
    message: str        # 错误消息

class APIValidationError(Exception):
    """API 参数验证错误"""
    ...
```

### 10.2 响应状态检查

```python
class APIReturnStatus:
    """检查 API 响应状态，失败时抛出 NapCatAPIError"""
    ...

class MessageAPIReturnStatus(APIReturnStatus):
    """消息 API 响应状态，包含 message_id 提取"""
    ...
```

---

## 11. 使用示例

### 11.1 基本消息发送

```python
# 群消息
await bot.api.post_group_msg(group_id="123", text="你好")
await bot.api.send_group_image(group_id="123", image="path/to/image.jpg")

# 私聊消息
await bot.api.post_private_msg(user_id="456", text="你好")

# 带 @和回复
await bot.api.post_group_msg(
    group_id="123",
    text="你好",
    at=789,                # @某人
    reply=12345,           # 回复某条消息
)

# 富文本消息（MessageArray）
from ncatbot.core.event import MessageArray
rtf = MessageArray([
    {"type": "text", "data": {"text": "看这张图片："}},
    {"type": "image", "data": {"file": "path/to/image.jpg"}},
])
await bot.api.post_group_msg(group_id="123", rtf=rtf)
```

### 11.2 群管理

```python
# 踢出成员
await bot.api.set_group_kick(group_id="123", user_id="456")

# 禁言 10 分钟
await bot.api.set_group_ban(group_id="123", user_id="456", duration=600)

# 全群禁言
await bot.api.set_group_whole_ban(group_id="123", enable=True)

# 设置管理员
await bot.api.set_group_admin(group_id="123", user_id="456", enable=True)
```

### 11.3 文件操作

```python
# 上传群文件
await bot.api.upload_group_file(
    group_id="123",
    file="path/to/file.pdf",
    name="文件名.pdf"
)

# 获取文件链接
url = await bot.api.get_group_file_url(group_id="123", file_id="abc")
```

### 11.4 同步调用

```python
# 在非异步上下文中使用 _sync 后缀方法
info = bot.api.get_login_info_sync()
bot.api.post_group_msg_sync(group_id="123", text="同步发送")
```
