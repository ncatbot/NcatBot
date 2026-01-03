"""
数据创建函数

提供创建测试数据的辅助函数。
"""

import time
from typing import List, Optional


def create_bot_data(
    user_id: str = "123456789",
    nickname: str = "TestBot",
) -> dict:
    """创建 Bot 数据"""
    return {
        "user_id": user_id,
        "nickname": nickname,
    }


def create_user_data(
    user_id: str,
    nickname: str,
    remark: str = "",
    sex: str = "unknown",
    age: int = 0,
) -> dict:
    """创建用户数据"""
    return {
        "user_id": user_id,
        "nickname": nickname,
        "remark": remark,
        "sex": sex,
        "age": age,
    }


def create_group_member_data(
    user_id: str,
    nickname: str,
    card: str = "",
    role: str = "member",
    title: str = "",
) -> dict:
    """创建群成员数据"""
    return {
        "user_id": user_id,
        "nickname": nickname,
        "card": card,
        "role": role,
        "title": title,
        "join_time": 0,
        "last_sent_time": 0,
        "level": "1",
    }


def create_group_data(
    group_id: str,
    group_name: str,
    owner_id: str,
    members: Optional[List[dict]] = None,
    max_member_count: int = 500,
) -> dict:
    """创建群数据"""
    return {
        "group_id": group_id,
        "group_name": group_name,
        "owner_id": owner_id,
        "members": members or [],
        "max_member_count": max_member_count,
    }


def create_file_data(
    file_id: str,
    file_name: str,
    file_size: int = 1024,
    uploader: str = "",
    uploader_name: str = "",
) -> dict:
    """创建文件数据"""
    return {
        "file_id": file_id,
        "file_name": file_name,
        "file_size": file_size,
        "busid": 0,
        "upload_time": int(time.time()),
        "dead_time": 0,
        "modify_time": int(time.time()),
        "download_times": 0,
        "uploader": uploader,
        "uploader_name": uploader_name,
    }


def create_folder_data(
    folder_id: str,
    folder_name: str,
    creator: str = "",
    creator_name: str = "",
    files: Optional[List[dict]] = None,
    folders: Optional[List[dict]] = None,
) -> dict:
    """创建文件夹数据"""
    return {
        "folder_id": folder_id,
        "folder_name": folder_name,
        "create_time": int(time.time()),
        "creator": creator,
        "creator_name": creator_name,
        "total_file_count": len(files or []),
        "files": files or [],
        "folders": folders or [],
    }
