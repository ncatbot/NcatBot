# NcatBot API 端到端测试

本目录包含 NcatBot 的 API 端到端测试（E2E Tests）。

## 目录结构

```
test/e2e/
├── run.py              # 测试入口
├── README.md           # 本文档
├── api/                # API 测试用例
│   ├── test_account.py       # 账号相关
│   ├── test_friend.py        # 好友相关
│   ├── test_message_private.py   # 私聊消息
│   ├── test_message_group.py     # 群聊消息
│   ├── test_message_ops.py       # 消息操作
│   ├── test_group_info.py        # 群信息查询
│   ├── test_group_admin.py       # 群管理操作
│   └── test_file.py              # 文件操作
├── framework/          # 测试框架
│   ├── types.py        # 类型定义
│   ├── decorators.py   # 装饰器
│   ├── runner.py       # 测试运行器
│   ├── reporter.py     # 报告生成器
│   ├── config.py       # 配置加载器
│   └── output.py       # 输出格式化
└── data/               # 测试数据
    ├── config.example.json     # 主配置示例
    ├── messages.example.json   # 消息测试数据示例
    ├── friends.example.json    # 好友测试数据示例
    ├── groups.example.json     # 群组测试数据示例
    └── files.example.json      # 文件测试数据示例
```

## 快速开始

### 1. 配置测试数据

复制示例配置文件并填写实际值：

```bash
cd test/e2e/data
cp config.example.json config.json
cp messages.example.json messages.json
cp friends.example.json friends.json
cp groups.example.json groups.json
cp files.example.json files.json
```

编辑 `config.json`，填写测试目标：

```json
{
  "targets": {
    "test_group": 123456789,      // 测试群号
    "test_user": 987654321,       // 测试用户 QQ 号
    "test_admin_group": 123456789 // 有管理员权限的群
  },
  "options": {
    "auto_cleanup": true,
    "skip_destructive": false,
    "verbose": true,
    "timeout_seconds": 30
  }
}
```

### 2. 启动 NapCat 服务

确保 NapCat 服务已启动并登录。

### 3. 运行测试

```bash
# 运行所有测试
uv run python test/e2e/run.py

# 只运行账号相关测试
uv run python test/e2e/run.py --category account

# 只运行 basic 标签的测试
uv run python test/e2e/run.py --tag basic

# 列出所有测试用例
uv run python test/e2e/run.py --list

# 生成测试报告
uv run python test/e2e/run.py --report ./reports/e2e_test.md
```

## 测试分类

| 分类 | 描述 |
|------|------|
| account | 账号信息相关 |
| friend | 好友管理相关 |
| message | 消息发送和操作 |
| group | 群组管理相关 |
| file | 文件操作相关 |

## 测试标签

| 标签 | 描述 |
|------|------|
| basic | 基础功能测试 |
| query | 查询类 API |
| action | 操作类 API |
| admin | 需要管理员权限 |
| dangerous | 危险操作（如删除） |
| forward | 转发消息相关 |

## 测试数据配置

### config.json

主配置文件，包含测试目标和选项。

### messages.json

消息相关测试数据：
- `text_messages`: 测试用的文本消息
- `forward_messages`: 转发消息测试数据
- `music_messages`: 音乐分享测试数据

### friends.json

好友相关测试数据：
- `friend_operations`: 好友操作参数
- `friend_requests`: 好友申请处理参数
- `private_file`: 私聊文件测试数据

### groups.json

群组相关测试数据：
- `member_operations`: 成员操作参数
- `essence_messages`: 精华消息测试数据
- `album`: 群相册测试数据

### files.json

文件相关测试数据：
- `group_files`: 群文件测试数据
- `private_files`: 私聊文件测试数据
- `media_files`: 媒体文件测试数据

## 已覆盖的 API

### 账号相关
- `get_login_info` - 获取登录信息
- `get_status` - 获取状态
- `get_version_info` - 获取版本信息

### 好友相关
- `get_friend_list` - 获取好友列表
- `get_friends_with_category` - 获取带分类的好友列表
- `get_recent_contact` - 获取最近联系人
- `get_stranger_info` - 获取陌生人信息
- `send_like` - 发送好友赞
- `friend_poke` - 好友戳一戳
- `get_friend_msg_history` - 获取好友消息历史
- `set_friend_add_request` - 处理好友申请
- `delete_friend` - 删除好友

### 消息相关
- `send_private_msg` - 发送私聊消息
- `send_group_msg` - 发送群聊消息
- `send_poke` - 发送戳一戳
- `delete_msg` - 撤回消息
- `get_msg` - 获取消息详情
- `get_group_msg_history` - 获取群消息历史
- `get_forward_msg` - 获取转发消息
- `forward_group_single_msg` - 转发群单条消息
- `forward_private_single_msg` - 转发私聊单条消息
- `send_forward_msg` - 发送合并转发消息
- `post_group_forward_msg` - POST 发送群转发消息
- `send_group_forward_msg_by_id` - 通过 ID 发送群转发消息
- `send_group_music` - 发送群音乐分享
- `send_group_custom_music` - 发送群自定义音乐
- `group_poke` - 群戳一戳
- `post_group_array_msg` - 发送群数组消息
- `set_msg_emoji_like` - 设置消息表情回应
- `fetch_emoji_like` - 获取消息表情回应
- `get_image` - 获取图片信息
- `get_record` - 获取语音信息

### 群组相关
- `get_group_list` - 获取群列表
- `get_group_info` - 获取群信息
- `get_group_member_list` - 获取群成员列表
- `get_group_member_info` - 获取群成员信息
- `get_group_shut_list` - 获取群禁言列表
- `set_group_kick` - 踢出群成员
- `set_group_ban` - 群禁言
- `set_group_whole_ban` - 全员禁言
- `set_group_admin` - 设置群管理员
- `set_group_special_title` - 设置群头衔
- `set_group_card` - 设置群名片
- `set_essence_msg` - 设置精华消息
- `delete_essence_msg` - 删除精华消息
- `get_essence_msg_list` - 获取精华消息列表
- `get_group_album_list` - 获取群相册列表
- `upload_image_to_group_album` - 上传图片到群相册
- `set_group_sign` - 群打卡

### 文件相关
- `upload_private_file` - 上传私聊文件
- `get_private_file_url` - 获取私聊文件 URL
- `post_private_file` - POST 发送私聊文件
- `upload_group_file` - 上传群文件
- `post_group_file` - POST 发送群文件
- `get_group_root_files` - 获取群根目录文件
- `get_group_files_by_folder` - 获取文件夹内文件
- `get_group_file_url` - 获取群文件 URL
- `get_file` - 获取文件信息
- `create_group_file_folder` - 创建群文件夹
- `move_group_file` - 移动群文件
- `rename_group_file` - 重命名群文件
- `delete_group_file` - 删除群文件
- `delete_group_folder` - 删除群文件夹

## 添加新测试

1. 在相应的测试文件中添加测试方法
2. 使用 `@test_case` 装饰器标记
3. 测试函数接收 `api` 和 `data` 两个参数

```python
@staticmethod
@test_case(
    name="测试名称",
    description="测试描述",
    category="分类",
    api_endpoint="/api_endpoint",
    expected="预期结果",
    tags=["tag1", "tag2"],
    requires_input=False,  # 是否需要人工输入
)
async def test_example(api, data):
    """测试示例"""
    target_group = data.get("target_group")
    result = await api.some_api(group_id=target_group)
    return result
```

## 注意事项

1. 某些测试需要管理员权限
2. 危险操作（如删除好友、踢人）会要求确认
3. 建议在测试群和测试账号上进行测试
4. 测试前确保 NapCat 服务正常运行
