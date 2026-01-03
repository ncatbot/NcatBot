"""
E2E 测试辅助函数

提供通用的工具函数，供各个测试场景使用。

API 返回类型明确定义（禁止使用泛用接口）：

"""

import os
import base64
from typing import Any


def model_to_dict(obj: Any) -> Any:
    """
    将模型对象转换为字典

    Args:
        obj: 要转换的对象（模型对象、字典或其他）

    Returns:
        转换后的字典或字符串表示
    """
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    return str(obj)


def create_test_file(file_path: str, content: str = None) -> str:
    """
    创建测试文件

    Args:
        file_path: 文件路径
        content: 文件内容，如果为空则使用默认内容

    Returns:
        创建的文件路径
    """
    if content is None:
        import datetime

        content = f"E2E 测试文件内容 - 生成时间: {datetime.datetime.now()}"

    os.makedirs(os.path.dirname(file_path) or "/tmp", exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path


def create_test_image(image_path: str) -> str:
    """
    创建测试图片（1x1 PNG）

    创建一个简单的 1x1 像素 PNG 图片用于测试

    Args:
        image_path: 图片文件路径

    Returns:
        创建的图片路径
    """
    # 1x1 红色 PNG 图片的 Base64 编码
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    os.makedirs(os.path.dirname(image_path) or "/tmp", exist_ok=True)
    with open(image_path, "wb") as f:
        f.write(png_data)
    return image_path


def ensure_test_image(data: dict) -> str:
    """
    确保测试图片存在，返回图片路径

    优先返回配置的 URL 图片，如果不存在则创建本地测试图片

    Args:
        data: 测试配置数据

    Returns:
        图片路径或 URL
    """
    messages_data = data.get("messages", {})
    test_images = messages_data.get("test_images", {})

    # 优先使用 URL 图片
    url_image = test_images.get("url_image")
    if url_image:
        return url_image

    # 尝试使用或创建本地图片
    local_image = test_images.get("local_image", "/tmp/test_image.png")

    if not os.path.exists(local_image):
        try:
            create_test_image(local_image)
        except Exception:
            pass

    return (
        local_image
        if os.path.exists(local_image)
        else "https://via.placeholder.com/300x200.png"
    )
