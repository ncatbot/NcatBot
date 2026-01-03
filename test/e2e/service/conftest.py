"""
服务模块端到端测试共享 fixtures
"""

import pytest
import pytest_asyncio
import tempfile
from pathlib import Path

from ncatbot.utils.testing import E2ETestSuite


@pytest_asyncio.fixture
async def preupload_suite():
    """创建预上传测试套件

    该套件提供完整的 E2E 测试环境：
    - MockServer 模拟 NapCat API
    - BotClient 连接到 MockServer
    - ServiceManager 管理所有服务
    """
    suite = E2ETestSuite()
    await suite.setup()
    yield suite
    await suite.teardown()


@pytest.fixture
def temp_test_files():
    """创建临时测试文件

    创建多种类型的临时文件用于测试：
    - 小文件（单分片）
    - 中等文件（多分片）
    - 不同类型文件（图片、视频模拟）
    """
    files = {}
    temp_dir = tempfile.mkdtemp()

    # 小文件 - 100 字节
    small_file = Path(temp_dir) / "small.txt"
    small_file.write_bytes(b"A" * 100)
    files["small"] = str(small_file)

    # 中等文件 - 1MB（会产生多个分片）
    medium_file = Path(temp_dir) / "medium.bin"
    medium_file.write_bytes(b"B" * (1024 * 1024))
    files["medium"] = str(medium_file)

    # 模拟图片文件
    image_file = Path(temp_dir) / "test.jpg"
    # 最小的有效 JPEG 头
    jpeg_header = bytes(
        [
            0xFF,
            0xD8,
            0xFF,
            0xE0,
            0x00,
            0x10,
            0x4A,
            0x46,
            0x49,
            0x46,
            0x00,
            0x01,
            0x01,
            0x00,
            0x00,
            0x01,
            0x00,
            0x01,
            0x00,
            0x00,
        ]
    )
    image_file.write_bytes(jpeg_header + b"C" * 200)
    files["image"] = str(image_file)

    files["temp_dir"] = temp_dir

    yield files

    # 清理
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)
