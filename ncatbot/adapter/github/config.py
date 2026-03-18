"""GitHub 适配器配置模型"""

from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field


class GitHubConfig(BaseModel):
    """GitHub 适配器专属配置"""

    # 认证
    token: str = ""

    # 监听仓库
    repos: List[str] = Field(default_factory=list)

    # 连接模式
    mode: Literal["webhook", "polling"] = "webhook"

    # Webhook 配置
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 8080
    webhook_path: str = "/webhook"
    webhook_secret: str = ""

    # Polling 配置
    poll_interval: float = 60.0
