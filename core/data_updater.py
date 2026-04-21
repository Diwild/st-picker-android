"""
ST选股工具 - 远程 JSON 热更新管理器
复刻鸿蒙版 DataUpdateManager 核心逻辑

流程：
1. 启动时检查远程版本（对比 data_version）
2. 有新版本则下载完整 JSON
3. 校验格式后写入缓存目录
4. DataManager 加载时优先使用缓存文件
"""

import os
import sys
import json
import urllib.request
import urllib.error
import re
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from utils.logger import logger


# ═══════════════════════════════════════════════════════════════
# 远程 JSON URL 配置（用户可修改）
# 支持 GitHub Raw / Gitee Raw / CDN 等公开可访问的 HTTPS URL
# ═══════════════════════════════════════════════════════════════

REMOTE_JSON_URL: str = ''


@dataclass
class UpdateCheckResult:
    """版本检查结果"""
    has_update: bool
    message: str
    remote_version: Optional[str] = None
    local_version: Optional[str] = None


@dataclass
class DownloadResult:
    """下载结果"""
    success: bool
    message: str
    cache_path: Optional[str] = None


class DataUpdateManager:
    """
    远程 JSON 热更新管理器

    特性：
    - 基于 data_version 字段判断是否需要更新
    - 支持完整 GET + 前 2KB 版本号提取（不依赖 Range）
    - 下载后格式/结构双重校验
    - 缓存到应用私有目录（Android）或项目目录（桌面）
    """

    CACHE_FILE_NAME = 'restructuring_watchlist_cache.json'
    HTTP_TIMEOUT = 15
    MAX_VERSION_CHECK_SIZE = 2048  # 只读取前 2KB 提取版本号

    def __init__(self, cache_dir: Optional[str] = None):
        self._cache_dir = cache_dir
        self._is_updating = False

    # ─── 缓存路径 ──────────────────────────────────────────────

    def _get_cache_dir(self) -> str:
        """获取缓存目录"""
        if self._cache_dir:
            return self._cache_dir

        # Android: 使用 Kivy 应用私有目录
        if 'android' in sys.platform:
            try:
                from kivy.app import App
                app = App.get_running_app()
                if app and app.user_data_dir:
                    return app.user_data_dir
            except Exception:
                pass
            # fallback（包名: com.stockpicker.stpicker）
            return '/data/data/com.stockpicker.stpicker/files'

        # 桌面: 使用项目 data 目录
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(app_dir, 'data')

    def _get_cache_path(self) -> str:
        """获取缓存文件完整路径"""
        return os.path.join(self._get_cache_dir(), self.CACHE_FILE_NAME)

    def _get_original_json_path(self) -> str:
        """获取原始打包 JSON 路径"""
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(app_dir, 'data', 'restructuring_watchlist.json')

    def has_valid_cache(self) -> bool:
        """检查缓存文件是否存在且可读"""
        path = self._get_cache_path()
        return os.path.exists(path) and os.path.getsize(path) > 100

    # ─── 版本检查 ──────────────────────────────────────────────

    def check_remote_version(self) -> UpdateCheckResult:
        """
        异步检查远程是否有新版本

        若 REMOTE_JSON_URL 未配置，直接跳过
        """
        if not REMOTE_JSON_URL or not REMOTE_JSON_URL.strip():
            return UpdateCheckResult(has_update=False, message='远程更新未配置')

        try:
            req = urllib.request.Request(
                REMOTE_JSON_URL,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            with urllib.request.urlopen(req, timeout=self.HTTP_TIMEOUT) as response:
                text = response.read().decode('utf-8', errors='replace')

            if response.status != 200:
                return UpdateCheckResult(
                    has_update=False, message=f'HTTP {response.status}'
                )

            # 只取前 2KB 提取版本号，避免大文件解析开销
            head_text = text[:self.MAX_VERSION_CHECK_SIZE]
            remote_version = self._extract_data_version(head_text)
            if not remote_version:
                return UpdateCheckResult(
                    has_update=False, message='远程 JSON 无版本信息'
                )

            local_version = self._read_local_version()

            if not local_version:
                return UpdateCheckResult(
                    has_update=True,
                    message='本地无缓存，建议下载',
                    remote_version=remote_version,
                    local_version=local_version
                )

            # 版本号对比：尝试按 ISO 时间戳解析
            has_update = self._compare_versions(remote_version, local_version)

            return UpdateCheckResult(
                has_update=has_update,
                message='发现新版本' if has_update else '已是最新',
                remote_version=remote_version,
                local_version=local_version
            )

        except Exception as e:
            logger.error(f'检查远程版本失败: {e}', 'DATA_UPDATER')
            return UpdateCheckResult(has_update=False, message=f'网络错误: {e}')

    # ─── 下载缓存 ──────────────────────────────────────────────

    def download_and_cache(self) -> DownloadResult:
        """下载完整远程 JSON 并写入缓存"""
        if not REMOTE_JSON_URL or not REMOTE_JSON_URL.strip():
            return DownloadResult(
                success=False, message='远程更新未配置，无法下载'
            )

        try:
            req = urllib.request.Request(
                REMOTE_JSON_URL,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            with urllib.request.urlopen(req, timeout=self.HTTP_TIMEOUT * 2) as response:
                text = response.read().decode('utf-8', errors='replace')

            if response.status != 200:
                return DownloadResult(
                    success=False, message=f'HTTP {response.status}'
                )

            text_stripped = text.strip()

            # 简单校验：必须是 JSON 且包含 restructuring_stocks
            if not text_stripped.startswith('{') or '"restructuring_stocks"' not in text_stripped:
                return DownloadResult(success=False, message='远程 JSON 格式异常')

            # 结构校验：确保能解析且包含数组
            try:
                parsed = json.loads(text_stripped)
                arr = parsed.get('restructuring_stocks')
                if not isinstance(arr, list):
                    return DownloadResult(
                        success=False,
                        message='远程 JSON 结构异常，缺少 restructuring_stocks 数组'
                    )
            except json.JSONDecodeError:
                return DownloadResult(
                    success=False, message='远程 JSON 解析失败'
                )

            # 写入缓存
            cache_path = self._get_cache_path()
            cache_dir = os.path.dirname(cache_path)
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)

            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(text_stripped)

            logger.info(f'JSON 缓存更新成功: {cache_path}', 'DATA_UPDATER')
            return DownloadResult(
                success=True,
                message='下载并缓存成功',
                cache_path=cache_path
            )

        except Exception as e:
            logger.error(f'下载失败: {e}', 'DATA_UPDATER')
            return DownloadResult(success=False, message=f'网络错误: {e}')

    # ─── 一键检查并更新 ────────────────────────────────────────

    def check_and_update(self) -> DownloadResult:
        """一键检查并更新：有更新则下载，无更新则跳过"""
        if self._is_updating:
            return DownloadResult(success=False, message='更新检查正在进行中')

        self._is_updating = True
        try:
            check = self.check_remote_version()
            if not check.has_update:
                return DownloadResult(success=True, message=check.message)

            logger.info(
                f'发现更新: {check.local_version} -> {check.remote_version}',
                'DATA_UPDATER'
            )
            return self.download_and_cache()
        finally:
            self._is_updating = False

    # ─── 内部方法 ──────────────────────────────────────────────

    def _read_local_version(self) -> Optional[str]:
        """读取本地缓存中的 data_version，优先缓存文件，fallback 原始 JSON"""
        # 优先读取缓存文件（从末尾 4KB 读取，data_version 通常在文件尾部）
        cache_path = self._get_cache_path()
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    f.seek(0, 2)
                    size = f.tell()
                    f.seek(max(0, size - 4096), 0)
                    text = f.read()
                version = self._extract_data_version(text)
                if version:
                    return version
            except Exception:
                pass

        # fallback 到原始打包 JSON
        orig_path = self._get_original_json_path()
        if os.path.exists(orig_path):
            try:
                with open(orig_path, 'r', encoding='utf-8') as f:
                    f.seek(0, 2)
                    size = f.tell()
                    f.seek(max(0, size - 4096), 0)
                    text = f.read()
                return self._extract_data_version(text)
            except Exception:
                pass

        return None

    @staticmethod
    def _extract_data_version(text: str) -> Optional[str]:
        """从 JSON 文本中提取 data_version 字段值"""
        match = re.search(r'"data_version"\s*:\s*"([^"]+)"', text)
        return match.group(1) if match else None

    @staticmethod
    def _compare_versions(remote: str, local: str) -> bool:
        """对比版本号，尝试按 ISO 时间戳解析"""
        try:
            remote_dt = datetime.fromisoformat(remote.replace('Z', '+00:00'))
            local_dt = datetime.fromisoformat(local.replace('Z', '+00:00'))
            return remote_dt > local_dt
        except (ValueError, TypeError):
            # 无法解析时保守认为有更新
            return remote != local


# 全局实例（cache_dir 由 DataManager 初始化时传入）
data_updater = DataUpdateManager()
