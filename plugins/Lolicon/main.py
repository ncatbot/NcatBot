import asyncio
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp

from ncatbot.core import registrar
from ncatbot.event.qq import MessageEvent, PrivateMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.types import Image, MessageArray
from ncatbot.utils import get_config_manager, get_log

LOG = get_log("Lolicon")


class Lolicon(NcatBotPlugin):
    name = "Lolicon"
    version = "1.0.1"
    author = "FunEnn"
    description = "调用 Lolicon API v2 发送随机二次元图片"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cache_dir: Path | None = None
        self.cache_index_file: Path | None = None
        self.cache_index: Dict = {}

    def _is_root(self, user_id: str) -> bool:
        return str(user_id) == str(get_config_manager().root)

    def _load_cache_index(self) -> Dict:
        if self.cache_index_file and self.cache_index_file.exists():
            try:
                with open(self.cache_index_file, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                LOG.error("加载缓存索引失败: %s", e)
        return {}

    def _save_cache_index(self) -> None:
        if not self.cache_index_file:
            return
        try:
            with open(self.cache_index_file, "w", encoding="utf-8") as f:
                json.dump(self.cache_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            LOG.error("保存缓存索引失败: %s", e)

    def _get_cache_path(self, url: str) -> Path:
        assert self.cache_dir is not None
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.jpg"

    async def _download_image(self, url: str) -> Optional[Path]:
        assert self.cache_dir is not None
        cache_path = self._get_cache_path(url)
        if cache_path.exists():
            return cache_path
        try:
            timeout = aiohttp.ClientTimeout(total=10, connect=3)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        if len(content) > 1000:
                            cache_path.write_bytes(content)
                            self.cache_index[url] = {
                                "path": str(cache_path),
                                "timestamp": time.time(),
                                "size": len(content),
                            }
                            self._save_cache_index()
                            return cache_path
                    else:
                        LOG.warning("下载图片失败: %s, 状态码: %s", url, response.status)
        except Exception as e:
            LOG.error("下载图片异常: %s, 错误: %s", url, e)
        return None

    async def _download_images_concurrent(self, urls: List[str]):
        semaphore = asyncio.Semaphore(5)

        async def download_with_semaphore(url: str) -> Optional[Path]:
            async with semaphore:
                return await self._download_image(url)

        tasks = [download_with_semaphore(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _call_lolicon_api(
        self, count: int = 1, r18: int = 0, tags: Optional[List[str]] = None
    ) -> List[Dict]:
        api_url = "https://api.lolicon.app/setu/v2"
        params: dict = {"r18": r18, "num": count, "size": "regular"}
        if not tags:
            tags = ["萝莉"]
        for tag in tags:
            params["tag"] = tag
        try:
            timeout = aiohttp.ClientTimeout(total=15, connect=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("error") == "":
                            images_data = data.get("data", [])
                            return images_data[:count]
                        LOG.error("API 返回错误: %s", data.get("error"))
                    else:
                        LOG.error("API 请求失败: %s", response.status)
        except Exception as e:
            LOG.error("调用 API 异常: %s", e)
        return []

    async def on_load(self) -> None:
        self.cache_dir = Path(self.workspace) / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_index_file = self.cache_dir / "cache_index.json"
        self.cache_index = self._load_cache_index()
        LOG.info("%s 插件已加载，缓存目录 %s", self.name, self.cache_dir)

    @registrar.qq.on_command("/loli", "/萝莉", "loli", "萝莉")
    async def loli_cmd(
        self, event: MessageEvent, count: int = 1, tag: str = "萝莉"
    ):
        max_count = 10
        count = max(1, min(max_count, count))
        images_data = await self._call_lolicon_api(count=count, r18=0, tags=[tag])
        if not images_data:
            await event.reply("获取图片失败，请稍后重试", at_sender=False)
            return
        await self.send_images(event, images_data)

    @registrar.qq.on_command("/r18", "r18")
    async def r18_cmd(self, event: MessageEvent, count: int = 1, tag: str = ""):
        if not isinstance(event, PrivateMessageEvent):
            await event.reply("R18 内容仅限私聊使用，群聊中无法发送", at_sender=False)
            return
        max_count = 5
        count = max(1, min(max_count, count))
        tags = [tag] if tag else ["萝莉"]
        images_data = await self._call_lolicon_api(count=count, r18=1, tags=tags)
        if not images_data:
            await event.reply("获取图片失败，请稍后重试", at_sender=False)
            return
        await self.send_images(event, images_data)

    @registrar.qq.on_command("/loli_status", "/状态", "loli_status")
    async def status_cmd(self, event: MessageEvent):
        if not self._is_root(event.user_id):
            return
        cache_size = sum(item.get("size", 0) for item in self.cache_index.values())
        cache_count = len(self.cache_index)
        status_text = "Lolicon 插件状态:\n"
        status_text += f"缓存图片数量: {cache_count} 张\n"
        status_text += f"缓存大小: {cache_size / 1024 / 1024:.2f} MB\n"
        api_status = await self._check_api_status()
        status_text += f"API接口状态: {api_status}"
        await event.reply(status_text, at_sender=False)

    @registrar.qq.on_command("/loli_clear", "/清理缓存", "loli_clear")
    async def clear_cache_cmd(self, event: MessageEvent):
        if not self._is_root(event.user_id):
            return
        try:
            if self.cache_dir:
                for cache_path in self.cache_dir.glob("*.jpg"):
                    cache_path.unlink()
            self.cache_index.clear()
            self._save_cache_index()
            await event.reply("缓存清理完成", at_sender=False)
        except Exception as e:
            LOG.error("清理缓存失败: %s", e)
            await event.reply(f"清理缓存失败: {e}", at_sender=False)

    async def _check_api_status(self) -> str:
        try:
            api_url = "https://api.lolicon.app/setu/v2"
            params = {"r18": 0, "num": 1, "size": "regular"}
            start_time = time.time()
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(api_url, params=params) as response:
                    response_time = time.time() - start_time
                    if response.status == 200:
                        data = await response.json()
                        if data.get("error") == "" and data.get("data"):
                            return f"✅ 正常 (响应时间: {response_time:.2f}s)"
                        return f"❌ API返回错误: {data.get('error', '未知错误')}"
                    return f"❌ HTTP错误: {response.status}"
        except Exception as e:
            return f"❌ 连接失败: {e!s}"

    async def send_images(self, event: MessageEvent, images_data: List[Dict]):
        urls = []
        for image_data in images_data:
            url = image_data.get("urls", {}).get("regular", "")
            if url:
                urls.append(url)
        if not urls:
            await event.reply("没有可用的图片链接", at_sender=False)
            return

        await event.reply("正在获取图片，请稍候...", at_sender=False)
        cache_paths = await self._download_images_concurrent(urls)

        images: List[Image] = []
        failed_count = 0
        for cache_path in cache_paths:
            if isinstance(cache_path, Exception):
                LOG.error("下载图片异常: %s", cache_path)
                failed_count += 1
                continue
            if cache_path and cache_path.exists():
                images.append(Image(file=str(cache_path)))
            else:
                failed_count += 1

        if not images:
            await event.reply("所有图片下载失败，请稍后重试", at_sender=False)
            return

        batch_size = min(5, len(images))
        total_sent = 0
        for i in range(0, len(images), batch_size):
            batch = images[i : i + batch_size]
            try:
                rtf = MessageArray()
                for img in batch:
                    rtf = rtf + MessageArray([img])
                await event.reply(rtf=rtf, at_sender=False)
                total_sent += len(batch)
            except Exception as e:
                LOG.error("发送图片失败: %s", e)
            if i + batch_size < len(images):
                await asyncio.sleep(0.2)

        if failed_count > 0:
            await event.reply(
                f"发送完成！成功: {total_sent}张，失败: {failed_count}张",
                at_sender=False,
            )
