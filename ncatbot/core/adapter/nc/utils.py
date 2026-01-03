"""
通用工具函数

提供文件下载、解压、版本检查等通用功能。
"""

import os
import site
import subprocess
import sys
import zipfile
from typing import Optional

import requests
import urllib.parse
from tqdm import tqdm

from ....utils import PYPI_URL, get_log

LOG = get_log("ncatbot.core.adapter.nc.utils")


# ==================== 文件操作 ====================


def download_file(url: str, file_name: str) -> None:
    """
    下载文件（带进度条）

    Args:
        url: 下载地址
        file_name: 保存的文件名
    """
    try:
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
    except Exception as e:
        LOG.error(f"从 {url} 下载 {file_name} 失败: {e}")
        raise


def unzip_file(file_name: str, extract_path: str, remove: bool = False) -> None:
    """
    解压 ZIP 文件

    Args:
        file_name: ZIP 文件路径
        extract_path: 解压目标路径
        remove: 解压后是否删除 ZIP 文件
    """
    try:
        with zipfile.ZipFile(file_name, "r") as zip_ref:
            zip_ref.extractall(extract_path)
            LOG.info(f"解压 {file_name} 成功")

        if remove:
            os.remove(file_name)
    except Exception as e:
        LOG.error(f"解压 {file_name} 失败: {e}")
        raise


# ==================== 版本检查 ====================


def get_local_package_version(package_name: str) -> Optional[str]:
    """
    获取已安装包的版本

    Args:
        package_name: 包名

    Returns:
        版本号字符串，未安装返回 None
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for line in result.stdout.splitlines():
            if line.lower().startswith(package_name.lower()):
                parts = line.split()
                if len(parts) >= 2:
                    return parts[1]
        return None
    except subprocess.CalledProcessError:
        return None


def get_pypi_latest_version(package_name: str) -> Optional[str]:
    """
    获取 PyPI 上的最新版本

    Args:
        package_name: 包名

    Returns:
        最新版本号，获取失败返回 None
    """
    try:
        url = urllib.parse.urljoin(PYPI_URL, f"{package_name}/json")
        response = requests.get(url, timeout=3)
        response.raise_for_status()
        return response.json()["info"]["version"]
    except Exception:
        return None


def is_package_installed(package_name: str) -> bool:
    """
    检查包是否已安装

    Args:
        package_name: 包名

    Returns:
        是否已安装
    """
    all_paths = site.getsitepackages() + [site.getusersitepackages()]

    for path in all_paths:
        # 检查包目录
        if os.path.exists(os.path.join(path, package_name)):
            return True
        # 检查 egg-info
        if os.path.exists(os.path.join(path, f"{package_name}.egg-info")):
            return True

    return False


def check_self_package_version() -> bool:
    """
    检查当前包的版本

    Returns:
        True 如果包已正确安装
    """
    package_name = "ncatbot"

    if not is_package_installed(package_name):
        LOG.error(f"包 {package_name} 未使用 pip 安装")
        return False

    local_version = get_local_package_version(package_name)
    if not local_version:
        LOG.error(f"包 {package_name} 未使用 pip 安装")
        return False

    latest_version = get_pypi_latest_version(package_name)
    if not latest_version:
        LOG.warning("获取 NcatBot 最新版本失败")
        return True

    if local_version != latest_version:
        LOG.warning("NcatBot 有可用更新！")
        LOG.info("若使用 main.exe 或 NcatBot CLI 启动, CLI 输入 update 即可更新")
        LOG.info("若手动安装, 推荐使用: pip install --upgrade ncatbot")

    return True
