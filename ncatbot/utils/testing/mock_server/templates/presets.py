"""
预定义数据模板

提供常用的测试数据模板。
"""

import time
from typing import Dict, List

from .creators import (
    create_bot_data,
    create_user_data,
    create_group_member_data,
    create_group_data,
    create_file_data,
    create_folder_data,
)


def get_minimal_data() -> dict:
    """
    获取最小化测试数据

    只包含一个 Bot 和一个好友、一个群。
    """
    return {
        "bot": create_bot_data("123456789", "TestBot"),
        "friends": [
            create_user_data("100001", "好友1"),
        ],
        "groups": [
            create_group_data(
                "200001",
                "测试群",
                "123456789",
                members=[
                    create_group_member_data("123456789", "TestBot", role="owner"),
                    create_group_member_data("100001", "好友1", role="member"),
                ],
            ),
        ],
        "group_messages": {},
        "private_messages": {},
        "group_files": {},
    }


def get_standard_data() -> dict:
    """
    获取标准测试数据

    包含多个好友、多个群、预设的群文件结构。
    """
    return {
        "bot": create_bot_data("123456789", "TestBot"),
        "friends": [
            create_user_data("100001", "好友1", remark="测试好友1"),
            create_user_data("100002", "好友2", remark="测试好友2"),
            create_user_data("100003", "好友3", remark="测试好友3"),
        ],
        "groups": [
            # 群1：Bot 是群主
            create_group_data(
                "200001",
                "测试群1",
                "123456789",
                members=[
                    create_group_member_data("123456789", "TestBot", role="owner"),
                    create_group_member_data("100001", "好友1", role="admin"),
                    create_group_member_data("100002", "好友2", role="member"),
                    create_group_member_data("100003", "好友3", role="member"),
                ],
            ),
            # 群2：Bot 是管理员
            create_group_data(
                "200002",
                "测试群2",
                "100001",
                members=[
                    create_group_member_data("100001", "好友1", role="owner"),
                    create_group_member_data("123456789", "TestBot", role="admin"),
                    create_group_member_data("100002", "好友2", role="member"),
                ],
            ),
            # 群3：Bot 是普通成员
            create_group_data(
                "200003",
                "测试群3",
                "100002",
                members=[
                    create_group_member_data("100002", "好友2", role="owner"),
                    create_group_member_data("123456789", "TestBot", role="member"),
                ],
            ),
        ],
        "group_messages": {
            "200001": [
                {
                    "message_id": "1001",
                    "message_type": "group",
                    "group_id": "200001",
                    "user_id": "100001",
                    "message": [{"type": "text", "data": {"text": "Hello"}}],
                    "raw_message": "Hello",
                    "time": 1704067200,
                    "sender": {"user_id": "100001", "nickname": "好友1"},
                    "message_seq": 1,
                },
                {
                    "message_id": "1002",
                    "message_type": "group",
                    "group_id": "200001",
                    "user_id": "123456789",
                    "message": [{"type": "text", "data": {"text": "World"}}],
                    "raw_message": "World",
                    "time": 1704067260,
                    "sender": {"user_id": "123456789", "nickname": "TestBot"},
                    "message_seq": 2,
                },
            ],
        },
        "private_messages": {
            "100001_123456789": [
                {
                    "message_id": "2001",
                    "message_type": "private",
                    "user_id": "100001",
                    "target_id": "123456789",
                    "message": [{"type": "text", "data": {"text": "Hi Bot"}}],
                    "raw_message": "Hi Bot",
                    "time": 1704067200,
                    "sender": {"user_id": "100001", "nickname": "好友1"},
                    "message_seq": 1,
                },
            ],
        },
        "group_files": {
            "200001": {
                "folder_id": "/",
                "folder_name": "/",
                "files": [
                    create_file_data(
                        "file_001", "readme.txt", 256, "123456789", "TestBot"
                    ),
                    create_file_data(
                        "file_002", "document.pdf", 10240, "100001", "好友1"
                    ),
                ],
                "folders": [
                    create_folder_data(
                        "folder_001",
                        "资料",
                        "123456789",
                        "TestBot",
                        files=[
                            create_file_data(
                                "file_003", "notes.txt", 512, "123456789", "TestBot"
                            ),
                        ],
                        folders=[
                            create_folder_data(
                                "folder_002",
                                "图片",
                                "100001",
                                "好友1",
                                files=[
                                    create_file_data(
                                        "file_004", "photo.jpg", 2048, "100001", "好友1"
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            },
        },
    }


def get_rich_data() -> dict:
    """
    获取丰富测试数据

    包含大量测试数据，适用于压力测试和边界测试。
    """
    # 生成大量好友
    friends = [
        create_user_data(f"10{i:04d}", f"好友{i}", remark=f"测试好友{i}")
        for i in range(1, 101)
    ]

    # 生成群成员
    def make_members(group_num: int, count: int) -> List[dict]:
        members = [
            create_group_member_data(
                "123456789", "TestBot", role="owner" if group_num == 1 else "member"
            ),
        ]
        for i in range(1, min(count, 100)):
            role = "admin" if i <= 3 else "member"
            members.append(
                create_group_member_data(f"10{i:04d}", f"好友{i}", role=role)
            )
        return members

    # 生成群组
    groups = [
        create_group_data(
            f"20{i:04d}",
            f"测试群{i}",
            "123456789" if i == 1 else f"10{i:04d}",
            members=make_members(i, 20 + i * 5),
        )
        for i in range(1, 11)
    ]

    # 生成群消息
    group_messages: Dict[str, List[dict]] = {}
    for i in range(1, 4):
        group_id = f"20{i:04d}"
        messages = []
        for j in range(1, 51):
            messages.append(
                {
                    "message_id": f"{i}00{j:03d}",
                    "message_type": "group",
                    "group_id": group_id,
                    "user_id": f"10{(j % 10) + 1:04d}",
                    "message": [{"type": "text", "data": {"text": f"消息 {j}"}}],
                    "raw_message": f"消息 {j}",
                    "time": int(time.time()) - (50 - j) * 60,
                    "sender": {
                        "user_id": f"10{(j % 10) + 1:04d}",
                        "nickname": f"好友{(j % 10) + 1}",
                    },
                    "message_seq": j,
                }
            )
        group_messages[group_id] = messages

    return {
        "bot": create_bot_data("123456789", "TestBot"),
        "friends": friends,
        "groups": groups,
        "group_messages": group_messages,
        "private_messages": {},
        "group_files": {
            "200001": {
                "folder_id": "/",
                "folder_name": "/",
                "files": [
                    create_file_data(
                        f"file_{i:03d}",
                        f"file_{i}.txt",
                        1024 * i,
                        "123456789",
                        "TestBot",
                    )
                    for i in range(1, 21)
                ],
                "folders": [
                    create_folder_data(
                        f"folder_{i:03d}",
                        f"文件夹{i}",
                        "123456789",
                        "TestBot",
                        files=[
                            create_file_data(
                                f"sub_file_{i}_{j}",
                                f"subfile_{j}.txt",
                                512,
                                "123456789",
                                "TestBot",
                            )
                            for j in range(1, 6)
                        ],
                    )
                    for i in range(1, 6)
                ],
            },
        },
    }
