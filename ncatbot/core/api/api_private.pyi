"""
类型存根文件 - PrivateAPI

此文件由 dev/tools/generate_sync_stubs.py 自动生成。
请勿手动编辑。
"""

from typing import Optional, Union
from ncatbot.core.api.client import IAPIClient
from ncatbot.core.service import ServiceManager

class PrivateAPI:
    """
    PrivateAPI 类型存根

    包含异步方法和动态生成的同步方法（*_sync）。
    """

    # 属性声明
    _client: IAPIClient
    _service_manager: Optional[ServiceManager]

    def __init__(
        self, client: IAPIClient, service_manager: Optional[ServiceManager] = ...
    ) -> None: ...
    async def get_private_file_url(self, file_id: str) -> str: ...
    def get_private_file_url_sync(self, file_id: str) -> str: ...
    async def post_private_file(
        self,
        user_id: Union[str, int],
        image: Optional[str] = ...,
        record: Optional[str] = ...,
        video: Optional[str] = ...,
        file: Optional[str] = ...,
    ) -> str: ...
    def post_private_file_sync(
        self,
        user_id: Union[str, int],
        image: Optional[str] = ...,
        record: Optional[str] = ...,
        video: Optional[str] = ...,
        file: Optional[str] = ...,
    ) -> str: ...
    async def send_private_file(self, user_id: Union[str, int], file: str) -> str: ...
    def send_private_file_sync(self, user_id: Union[str, int], file: str) -> str: ...
    async def send_private_image(self, user_id: Union[str, int], image: str) -> str: ...
    def send_private_image_sync(self, user_id: Union[str, int], image: str) -> str: ...
    async def send_private_record(self, user_id: Union[str, int], file: str) -> str: ...
    def send_private_record_sync(self, user_id: Union[str, int], file: str) -> str: ...
    async def send_private_video(self, user_id: Union[str, int], video: str) -> str: ...
    def send_private_video_sync(self, user_id: Union[str, int], video: str) -> str: ...
    async def set_input_status(
        self, event_type: int, user_id: Union[str, int]
    ) -> None: ...
    def set_input_status_sync(
        self, event_type: int, user_id: Union[str, int]
    ) -> None: ...
    async def upload_private_file(
        self, user_id: Union[str, int], file: str, name: str
    ) -> None: ...
    def upload_private_file_sync(
        self, user_id: Union[str, int], file: str, name: str
    ) -> None: ...
