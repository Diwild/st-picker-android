"""
ST选股工具 - 自选收藏管理器
基于 SQLite 持久化存储
"""

import os
import sqlite3
import threading
from typing import List, Set
from contextlib import contextmanager

from utils.logger import logger


class FavoritesManager:
    """
    自选收藏管理器
    
    特性：
    - SQLite 持久化
    - 线程安全
    - 内存缓存加速
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True

        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(app_dir, 'data', 'favorites.db')
        self._local = threading.local()
        self._cache: Set[str] = set()
        self._cache_dirty = True

        self._ensure_dir()
        self._init_db()

    def _ensure_dir(self):
        dir_path = os.path.dirname(self.db_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

    @contextmanager
    def _get_conn(self):
        conn = getattr(self._local, 'conn', None)
        if conn is None:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn = conn
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS favorites (
                    code TEXT PRIMARY KEY,
                    name TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def _load_cache(self):
        """加载缓存"""
        if not self._cache_dirty:
            return
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT code FROM favorites")
                self._cache = {row[0] for row in cursor.fetchall()}
                self._cache_dirty = False
        except Exception as e:
            logger.error(f"加载自选缓存失败: {e}")

    def add(self, code: str, name: str = '') -> bool:
        """添加自选"""
        code = code.upper().strip()
        if not code:
            return False
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO favorites (code, name) VALUES (?, ?)",
                    (code, name)
                )
                conn.commit()
                self._cache.add(code)
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"添加自选失败: {e}")
            return False

    def remove(self, code: str) -> bool:
        """移除自选"""
        code = code.upper().strip()
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM favorites WHERE code = ?", (code,))
                conn.commit()
                self._cache.discard(code)
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"移除自选失败: {e}")
            return False

    def toggle(self, code: str, name: str = '') -> bool:
        """切换自选状态，返回新的收藏状态"""
        if self.is_favorite(code):
            self.remove(code)
            return False
        else:
            self.add(code, name)
            return True

    def is_favorite(self, code: str) -> bool:
        """是否已收藏"""
        self._load_cache()
        return code.upper().strip() in self._cache

    def get_all(self) -> List[str]:
        """获取所有自选代码"""
        self._load_cache()
        return sorted(list(self._cache))

    def get_count(self) -> int:
        """获取自选数量"""
        self._load_cache()
        return len(self._cache)


# 全局实例
fav_mgr = FavoritesManager()
