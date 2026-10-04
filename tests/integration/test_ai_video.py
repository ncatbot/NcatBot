"""AI-37: AI 适配器 → API 门面 → LiteLLM → HTTP 的离线视频任务链路。"""

import httpx
import pytest

from litellm.llms.custom_httpx.http_handler import AsyncHTTPHandler

from ncatbot.adapter.ai import AIAdapter
from ncatbot.api import BotAPIClient

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("terminal_status", ["completed", "failed"])
async def test_video_workflow_through_litellm(monkeypatch, terminal_status):
    """AI-37: 真实 SDK 提交/查询/下载，保持任务路由和认证，失败时保留错误。"""
    requests = []
    statuses = iter(["in_progress", terminal_status])
    video_bytes = b"\x00\x00\x00\x18ftypmp42test-video"

    def respond(request):
        requests.append(request)
        assert request.url.host == "video.example"
        assert request.headers["authorization"] == "Bearer test-key"
        if request.method == "POST" and request.url.path == "/v1/videos":
            assert b"a cat" in request.content
            assert b"sora-2" in request.content
            return httpx.Response(
                200, json={"id": "video_test", "object": "video", "status": "queued"}
            )
        if request.method == "GET" and request.url.path == "/v1/videos/video_test":
            status = next(statuses)
            return httpx.Response(
                200,
                json={
                    "id": "video_test",
                    "object": "video",
                    "status": status,
                    "progress": 100 if status == "completed" else 50,
                    "error": {"code": "generation_failed", "message": "try again"}
                    if status == "failed"
                    else None,
                },
            )
        if (
            request.method == "GET"
            and request.url.path == "/v1/videos/video_test/content"
        ):
            assert terminal_status == "completed"
            assert request.url.params["variant"] == "video"
            return httpx.Response(200, content=video_bytes)
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        # 仅替换 HTTP 传输；保留真实 LiteLLM 参数转换、响应解析和 ID 编解码。
        monkeypatch.setattr(
            AsyncHTTPHandler, "create_client", lambda self, **kw: client
        )
        sdk_client = AsyncHTTPHandler()
        adapter = AIAdapter(
            config={
                "api_key": "test-key",
                "base_url": "https://video.example/v1",
                "video_model": "openai/sora-2",
            }
        )
        try:
            await adapter.connect()
            api = BotAPIClient()
            api.register_platform("ai", adapter.get_api())
            job = await api.ai.video_generation("a cat", seconds="8", client=sdk_client)
            assert job.status == "queued"

            pending = await api.ai.video_status(job.id, client=sdk_client)
            assert pending.status == "in_progress"
            result = await api.ai.call(
                "video_status", {"video_id": job.id, "client": sdk_client}
            )
            assert result.status == terminal_status
            if terminal_status == "completed":
                assert result.progress == 100
                data = await api.ai.video_content(
                    job.id, variant="video", client=sdk_client
                )
                assert data == video_bytes
            else:
                assert result.error["code"] == "generation_failed"
        finally:
            await adapter.disconnect()

    assert len(requests) == (4 if terminal_status == "completed" else 3)
