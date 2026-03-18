from .base import IAPIClient
from .client import BotAPIClient
from .errors import (
    APIError,
    APINotFoundError,
    APIPermissionError,
    APIRequestError,
)
from .traits import IMessaging, IGroupManage, IQuery, IFileTransfer
from .qq import IQQAPIClient, QQAPIClient
from .bilibili import IBiliAPIClient
from .github import IGitHubAPIClient

__all__ = [
    "IAPIClient",
    "BotAPIClient",
    "APIError",
    "APIRequestError",
    "APIPermissionError",
    "APINotFoundError",
    # traits
    "IMessaging",
    "IGroupManage",
    "IQuery",
    "IFileTransfer",
    # qq
    "IQQAPIClient",
    "QQAPIClient",
    # bilibili
    "IBiliAPIClient",
    # github
    "IGitHubAPIClient",
]
