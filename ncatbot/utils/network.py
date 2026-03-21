"""通用网络工具 — JSON 请求、文件下载、GitHub 代理。"""

import json
import socket
import urllib
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from .logger import get_log

_log = get_log()

# 模块级缓存，替代 legacy 中 status.current_github_proxy
_cached_github_proxy: Optional[str] = None
_proxy_resolved: bool = False


def post_json(
    url: str,
    payload: Optional[dict] = None,
    headers: Optional[dict] = None,
    timeout: float = 5.0,
) -> dict:
    """发送 JSON POST 请求并返回解析后的字典。"""
    body = None
    req_headers = {
        "User-Agent": "ncatbot/1.0",
        "Accept": "application/json",
    }
    if headers:
        req_headers.update(headers)
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", resp.getcode())
            if status != 200:
                raise urllib.error.HTTPError(
                    url, status, "Non-200 response", hdrs=resp.headers, fp=None
                )
            data = resp.read()
            return json.loads(data.decode("utf-8"))
    except socket.timeout as e:
        raise TimeoutError("request timed out") from e
    except urllib.error.URLError as e:
        if isinstance(getattr(e, "reason", None), socket.timeout):
            raise TimeoutError("request timed out") from e
        raise


def get_json(url: str, headers: Optional[dict] = None, timeout: float = 5.0) -> dict:
    """发送 JSON GET 请求并返回解析后的字典。"""
    req_headers = {
        "User-Agent": "ncatbot/1.0",
        "Accept": "application/json",
    }
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", resp.getcode())
            if status != 200:
                raise urllib.error.HTTPError(
                    url, status, "Non-200 response", hdrs=resp.headers, fp=None
                )
            data = resp.read()
            return json.loads(data.decode("utf-8"))
    except socket.timeout as e:
        raise TimeoutError("request timed out") from e
    except urllib.error.URLError as e:
        if isinstance(getattr(e, "reason", None), socket.timeout):
            raise TimeoutError("request timed out") from e
        raise


def download_file(url: str, file_name: str) -> None:
    """下载文件（带进度条）。"""
    import requests
    from tqdm import tqdm

    r = requests.get(url, stream=True)
    total_size = int(r.headers.get("content-length", 0))
    progress_bar = tqdm(
        total=total_size,
        unit="iB",
        unit_scale=True,
        desc=f"Downloading {file_name}",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
        colour="green",
        dynamic_ncols=True,
        smoothing=0.3,
        mininterval=0.1,
        maxinterval=1.0,
    )
    with open(file_name, "wb") as f:
        for data in r.iter_content(chunk_size=1024):
            progress_bar.update(len(data))
            f.write(data)
    progress_bar.close()


def get_proxy_url() -> str:
    """获取 GitHub 代理 URL（结果会缓存）。"""
    import requests

    global _cached_github_proxy, _proxy_resolved
    if _proxy_resolved:
        return _cached_github_proxy or ""

    github_proxy_urls = [
        "https://ghfast.top/",
    ]

    for proxy in github_proxy_urls:
        try:
            response = requests.get(proxy, timeout=10)
            if response.status_code == 200:
                _cached_github_proxy = proxy
                _proxy_resolved = True
                return proxy
        except TimeoutError:
            _log.warning(f"代理请求超时: {proxy}")
        except Exception:
            pass

    _log.warning("无法连接到任何 GitHub 代理, 将直接连接 GitHub")
    _cached_github_proxy = None
    _proxy_resolved = True
    return ""


def gen_url_with_proxy(original_url: str) -> str:
    """生成带 GitHub 代理前缀的 URL。"""
    proxy_url = get_proxy_url()
    return (
        f"{proxy_url.strip('/')}/{original_url.strip('/')}"
        if proxy_url
        else original_url
    )


# ==================== 异步 HTTP 工具 ====================


async def async_download_to_file(
    url: str,
    dest_dir: str | Path,
    *,
    filename: Optional[str] = None,
    proxy: Optional[str] = None,
) -> Path:
    """异步下载 URL 到目录，返回文件路径。

    Parameters
    ----------
    url : str
        下载地址。
    dest_dir : str | Path
        目标目录，不存在时自动创建。
    filename : str, optional
        文件名。省略则从 URL 路径推断。
    proxy : str, optional
        HTTP/SOCKS5 代理地址（如 ``"http://127.0.0.1:7890"``）。
    """
    from urllib.parse import unquote, urlparse

    import httpx

    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    if filename is None:
        filename = unquote(urlparse(url).path.rsplit("/", 1)[-1]) or "download"
    filepath = dest / filename

    async with httpx.AsyncClient(
        proxy=proxy, follow_redirects=True, timeout=120
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        filepath.write_bytes(resp.content)

    return filepath


async def async_download_to_bytes(
    url: str,
    *,
    proxy: Optional[str] = None,
) -> bytes:
    """异步下载 URL 到内存，返回原始字节。

    Parameters
    ----------
    url : str
        下载地址。
    proxy : str, optional
        HTTP/SOCKS5 代理地址。
    """
    import httpx

    async with httpx.AsyncClient(
        proxy=proxy, follow_redirects=True, timeout=120
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


async def async_http_get(
    url: str,
    *,
    headers: Optional[dict] = None,
    proxy: Optional[str] = None,
    timeout: float = 10.0,
) -> bytes:
    """异步 GET 请求，返回响应体字节。

    Parameters
    ----------
    url : str
        请求地址。
    headers : dict, optional
        额外请求头。
    proxy : str, optional
        HTTP/SOCKS5 代理地址。
    timeout : float
        超时秒数，默认 10。
    """
    import httpx

    req_headers = {"User-Agent": "ncatbot/1.0"}
    if headers:
        req_headers.update(headers)

    async with httpx.AsyncClient(
        proxy=proxy, follow_redirects=True, timeout=timeout
    ) as client:
        resp = await client.get(url, headers=req_headers)
        resp.raise_for_status()
        return resp.content


async def async_check_proxy(proxy_url: str) -> bool:
    """检查 HTTP/SOCKS5 代理是否可用。

    通过代理请求 ``https://www.google.com/generate_204`` 验证连通性。

    Parameters
    ----------
    proxy_url : str
        代理地址（如 ``"http://127.0.0.1:7890"``）。

    Returns
    -------
    bool
        代理可用返回 ``True``，否则 ``False``。
    """
    import httpx

    test_url = "https://www.google.com/generate_204"
    try:
        async with httpx.AsyncClient(
            proxy=proxy_url, follow_redirects=True, timeout=5
        ) as client:
            resp = await client.get(test_url)
            return resp.status_code in (200, 204)
    except Exception:
        return False
