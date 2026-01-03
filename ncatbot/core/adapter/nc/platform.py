"""
平台操作抽象层

使用工厂模式统一 Windows/Linux 平台的 NapCat 安装、启动、停止操作。
"""

import atexit
import json
import os
import platform
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from ....utils import (
    INSTALL_SCRIPT_URL,
    LINUX_NAPCAT_DIR,
    WINDOWS_NAPCAT_DIR,
    gen_url_with_proxy,
    get_json,
    get_log,
    ncatbot_config,
)
from .utils import download_file, unzip_file

LOG = get_log("ncatbot.core.adapter.nc.platform")


class UnsupportedPlatformError(Exception):
    """不支持的操作系统"""

    def __init__(self, system: Optional[str] = None):
        system = system or platform.system()
        super().__init__(f"不支持的操作系统: {system}")


class PlatformOps(ABC):
    """平台操作抽象基类"""

    @staticmethod
    def create() -> "PlatformOps":
        """工厂方法：根据当前系统创建对应的平台操作实例"""
        system = platform.system()
        if system == "Windows":
            return WindowsOps()
        elif system == "Linux":
            return LinuxOps()
        raise UnsupportedPlatformError(system)

    @property
    @abstractmethod
    def napcat_dir(self) -> Path:
        """NapCat 安装目录"""
        ...

    @property
    def config_dir(self) -> Path:
        """NapCat 配置目录"""
        return self.napcat_dir / "config"

    @abstractmethod
    def is_napcat_running(self, uin: Optional[str] = None) -> bool:
        """检查 NapCat 是否正在运行"""
        ...

    @abstractmethod
    def install_napcat(self, install_type: str = "install") -> bool:
        """
        安装 NapCat

        Args:
            install_type: "install" 首次安装, "update" 更新安装

        Returns:
            安装成功返回 True
        """
        ...

    @abstractmethod
    def start_napcat(self, uin: str) -> None:
        """启动 NapCat 服务"""
        ...

    @abstractmethod
    def stop_napcat(self) -> None:
        """停止 NapCat 服务"""
        ...

    def is_napcat_installed(self) -> bool:
        """检查 NapCat 是否已安装"""
        return self.napcat_dir.exists()

    def get_installed_version(self) -> Optional[str]:
        """获取已安装的 NapCat 版本"""
        package_json = self.napcat_dir / "package.json"
        if not package_json.exists():
            return None
        try:
            with open(package_json, "r", encoding="utf-8") as f:
                return json.load(f)["version"]
        except (json.JSONDecodeError, KeyError):
            return None

    @staticmethod
    def get_latest_version() -> Optional[str]:
        """从 GitHub 获取最新版本号"""
        api_url = "https://api.github.com/repos/NapNeko/NapCatQQ/tags"
        LOG.info(f"正在获取版本信息... {api_url}")
        try:
            data = get_json(api_url)
            if data and isinstance(data, list) and len(data) > 0:
                version = data[0].get("name", "").lstrip("v")
                if version:
                    LOG.debug(f"获取最新版本信息成功, 版本号: {version}")
                    return version
            LOG.warning("获取最新版本信息失败: 无法从 tags 中解析版本号")
        except Exception as e:
            LOG.error(f"获取版本信息时发生错误: {e}")
        return None

    def check_and_update(self) -> bool:
        """检查并更新 NapCat（如果有新版本）"""
        if not self.is_napcat_installed():
            return self.install_napcat("install")

        if not ncatbot_config.napcat.check_napcat_update:
            return True

        current = self.get_installed_version()
        latest = self.get_latest_version()

        if current and latest and current != latest:
            LOG.info(f"发现新版本: {latest} (当前: {current})")
            return self.install_napcat("update")

        LOG.info("当前 NapCat 已是最新版本")
        return True

    @staticmethod
    def _confirm_action(prompt: str) -> bool:
        """确认用户输入"""
        return input(prompt).strip().lower() in ["y", "yes"]


class WindowsOps(PlatformOps):
    """Windows 平台操作"""

    @property
    def napcat_dir(self) -> Path:
        return Path(WINDOWS_NAPCAT_DIR)

    def is_napcat_running(self, uin: Optional[str] = None) -> bool:
        # Windows 暂未实现精确检测
        return True

    def install_napcat(self, install_type: str = "install") -> bool:
        prompt = (
            "未找到 napcat，是否要自动安装？\n输入 Y 继续安装或 N 退出: "
            if install_type == "install"
            else "输入 Y 继续更新或 N 跳过更新: "
        )
        if not self._confirm_action(prompt):
            return False

        version = self.get_latest_version()
        if not version:
            return False

        try:
            download_url = gen_url_with_proxy(
                f"https://github.com/NapNeko/NapCatQQ/releases/download/v{version}/NapCat.Shell.zip"
            )
            LOG.info(f"下载链接: {download_url}")
            LOG.info("正在下载 napcat 客户端...")

            zip_path = f"{WINDOWS_NAPCAT_DIR}.zip"
            download_file(download_url, zip_path)
            unzip_file(zip_path, WINDOWS_NAPCAT_DIR, remove=True)
            return True
        except Exception as e:
            LOG.error(f"安装失败: {e}")
            return False

    def start_napcat(self, uin: str) -> None:
        launcher = self._get_launcher_name()
        launcher_path = self.napcat_dir / launcher

        if not launcher_path.exists():
            raise FileNotFoundError(f"找不到启动文件: {launcher_path}")

        LOG.info(f"正在启动 QQ, 启动器路径: {launcher_path}")
        subprocess.Popen(
            f'"{launcher_path}" {uin}',
            shell=True,
            cwd=str(self.napcat_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop_napcat(self) -> None:
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "QQ.exe"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            LOG.info("已成功停止 QQ.exe 进程")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode(errors="ignore") if e.stderr else ""
            LOG.error(f"停止 NapCat 服务失败: {stderr}")
            raise RuntimeError(f"无法停止 QQ.exe 进程: {stderr}")

    def _get_launcher_name(self) -> str:
        """获取对应系统的 launcher 名称"""
        platform_info = platform.platform()

        # 检测 Server 版本
        try:
            edition = platform.win32_edition()
            is_server = "Server" in edition
        except AttributeError:
            is_server = "Server" in platform_info

        if is_server:
            if any(ver in platform_info for ver in ["2016", "2019", "2022"]):
                LOG.info("当前操作系统: Windows Server (旧版本)")
                return "launcher-win10.bat"
            elif "2025" in platform_info:
                LOG.info("当前操作系统: Windows Server 2025")
                return "launcher.bat"
            LOG.warning("不支持的 Windows Server 版本，按 Windows 10 内核启动")
            return "launcher-win10.bat"

        # 桌面版 Windows
        release = platform.release()
        if release == "11":
            LOG.info("当前操作系统: Windows 11")
            return "launcher.bat"

        LOG.info("当前操作系统: Windows 10")
        return "launcher-win10.bat"


class LinuxOps(PlatformOps):
    """Linux 平台操作"""

    @property
    def napcat_dir(self) -> Path:
        target = Path(LINUX_NAPCAT_DIR)
        if target.exists():
            return target
        return Path.home() / "Napcat/opt/QQ/resources/app/app_launcher/napcat"

    def is_napcat_running(self, uin: Optional[str] = None) -> bool:
        process = subprocess.Popen(["bash", "napcat", "status"], stdout=subprocess.PIPE)
        process.wait()
        stdout = process.stdout
        if stdout is None:
            return False
        output = stdout.read().decode(encoding="utf-8")

        if uin is None:
            return "PID" in output
        return str(uin) in output

    def install_napcat(self, install_type: str = "install") -> bool:
        prompt = (
            "未找到 napcat，是否要使用一键安装脚本安装？\n输入 Y 继续安装或 N 退出: "
            if install_type == "install"
            else "是否要更新 napcat 客户端？\n输入 Y 继续更新或 N 跳过更新: "
        )
        if not self._confirm_action(prompt):
            return False

        if not self._check_root():
            LOG.error("请使用 root 权限运行 ncatbot")
            return False

        try:
            LOG.info("正在下载一键安装脚本...")
            cmd = f"sudo bash -c 'curl -sS {INSTALL_SCRIPT_URL} -o install && printf \"n\\ny\\n\" | sudo bash install'"
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
            process.wait()

            if process.returncode == 0:
                LOG.info("napcat 客户端安装完成")
                return True
            LOG.error("执行一键安装脚本失败")
            return False
        except Exception as e:
            LOG.error(f"执行一键安装脚本失败: {e}")
            raise

    def start_napcat(self, uin: str) -> None:
        if self.is_napcat_running(uin):
            LOG.info("NapCat 已启动")
            return

        if self.is_napcat_running():
            LOG.warning("NapCat 正在运行, 但运行的不是该 QQ 号")
            if input("按 y 强制结束当前进程并继续, 按其他键退出: ") == "y":
                self.stop_napcat()
            else:
                raise RuntimeError("NapCat 正在运行, 但运行的不是该 QQ 号")

        # 检查工作目录
        if os.path.exists("napcat"):
            LOG.error("工作目录下存在 napcat 目录")
            raise FileExistsError("工作目录下存在 napcat 目录")

        LOG.info("正在启动 NapCat 服务")
        process = subprocess.Popen(
            ["sudo", "bash", "napcat", "start", uin],
            stdout=subprocess.PIPE,
        )
        process.wait()

        if process.returncode != 0:
            LOG.error(f"启动失败，请检查目录 {LINUX_NAPCAT_DIR}")
            raise FileNotFoundError("napcat cli 可能没有被正确安装")

        # 注册退出清理
        if ncatbot_config.napcat.stop_napcat:
            atexit.register(self.stop_napcat)

        if not self.is_napcat_running(uin):
            raise RuntimeError("napcat 启动失败")

        time.sleep(0.5)
        LOG.info("napcat 启动成功")

    def stop_napcat(self) -> None:
        try:
            process = subprocess.Popen(
                ["bash", "napcat", "stop"], stdout=subprocess.PIPE
            )
            process.wait()
            if process.returncode != 0:
                raise RuntimeError("停止 napcat 失败")
            LOG.info("已成功停止 napcat")
        except Exception as e:
            LOG.error(f"停止 napcat 失败: {e}")
            raise

    @staticmethod
    def _check_root() -> bool:
        """检查是否有 root 权限"""
        try:
            result = subprocess.run(
                ["sudo", "whoami"],
                check=True,
                text=True,
                capture_output=True,
            )
            return result.stdout.strip() == "root"
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
