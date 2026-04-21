"""
ST选股工具 - SQLite数据库管理器
提供高性能的本地数据持久化存储
"""

import os
import json
import sqlite3
import threading
from typing import List, Optional, Dict, Any, Tuple
from contextlib import contextmanager
from datetime import datetime
from dataclasses import asdict

from utils.logger import logger


class DatabaseManager:
    """
    SQLite数据库管理器
    
    Features:
    - 线程安全连接池
    - 自动建表和索引
    - 增量同步支持
    - 事务保护
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Args:
            db_path: 数据库文件路径，None使用默认路径
        """
        if db_path is None:
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(app_dir, 'data', 'st_picker.db')
        
        self.db_path = db_path
        self._local = threading.local()
        self._ensure_dir()
        self._init_database()
    
    def _ensure_dir(self):
        """确保数据库目录存在"""
        dir_path = os.path.dirname(self.db_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
    
    @contextmanager
    def _get_connection(self):
        """
        获取数据库连接（线程安全）
        
        每个线程使用独立的连接
        """
        conn = getattr(self._local, 'conn', None)
        if conn is None:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            # 启用外键约束
            conn.execute("PRAGMA foreign_keys = ON")
            self._local.conn = conn
        
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
    
    def _init_database(self):
        """初始化数据库表结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 股票主表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stocks (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    stage TEXT DEFAULT '未标记',
                    price REAL DEFAULT 0,
                    market_cap REAL DEFAULT 0,
                    data_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sync_status INTEGER DEFAULT 0
                )
            ''')
            
            # 同步元数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_metadata (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    last_sync TIMESTAMP,
                    last_sync_source TEXT,
                    sync_count INTEGER DEFAULT 0,
                    last_error TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 初始化同步元数据
            cursor.execute('''
                INSERT OR IGNORE INTO sync_metadata (id) VALUES (1)
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_stocks_stage ON stocks(stage)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_stocks_updated ON stocks(updated_at)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_stocks_price ON stocks(price)
            ''')
            
            conn.commit()
            logger.info("数据库初始化完成", 'DATABASE')
    
    # ───────────────────────────────────────────────
    # 股票数据操作
    # ───────────────────────────────────────────────
    
    def get_stock(self, code: str) -> Optional[Dict[str, Any]]:
        """获取单只股票"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM stocks WHERE code = ?",
                (code.upper().strip(),)
            )
            row = cursor.fetchone()
            
            if row:
                return self._row_to_dict(row)
            return None
    
    def get_stocks_by_codes(self, codes: List[str]) -> List[Dict[str, Any]]:
        """批量获取股票"""
        if not codes:
            return []
        
        # 清理代码
        codes = [c.upper().strip() for c in codes]
        placeholders = ','.join(['?' for _ in codes])
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM stocks WHERE code IN ({placeholders})",
                codes
            )
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def get_all_stocks(self) -> List[Dict[str, Any]]:
        """获取所有股票"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM stocks ORDER BY updated_at DESC"
            )
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def get_stocks_by_stage(self, stage: str) -> List[Dict[str, Any]]:
        """按阶段获取股票"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM stocks WHERE stage = ? ORDER BY updated_at DESC",
                (stage,)
            )
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def save_stock(self, stock_data: Dict[str, Any]) -> bool:
        """
        保存或更新股票
        
        Args:
            stock_data: 股票数据字典，必须包含 stock_code
        
        Returns:
            是否成功
        """
        code = stock_data.get('stock_code', '').upper().strip()
        if not code:
            logger.warning("保存股票失败：缺少股票代码", 'DATABASE')
            return False
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 准备数据
            name = stock_data.get('stock_name', '')
            stage = stock_data.get('current_stage', '未标记')
            price = float(stock_data.get('current_price', 0) or 0)
            market_cap = float(stock_data.get('market_cap', 0) or 0)
            data_json = json.dumps(stock_data, ensure_ascii=False)
            
            cursor.execute('''
                INSERT OR REPLACE INTO stocks 
                (code, name, stage, price, market_cap, data_json, updated_at, sync_status)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
            ''', (code, name, stage, price, market_cap, data_json))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def save_stocks_batch(self, stocks_data: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        批量保存股票
        
        Returns:
            (成功数量, 失败数量)
        """
        success = 0
        failed = 0
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            for stock_data in stocks_data:
                try:
                    code = stock_data.get('stock_code', '').upper().strip()
                    if not code:
                        failed += 1
                        continue
                    
                    name = stock_data.get('stock_name', '')
                    stage = stock_data.get('current_stage', '未标记')
                    price = float(stock_data.get('current_price', 0) or 0)
                    market_cap = float(stock_data.get('market_cap', 0) or 0)
                    data_json = json.dumps(stock_data, ensure_ascii=False)
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO stocks 
                        (code, name, stage, price, market_cap, data_json, updated_at, sync_status)
                        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
                    ''', (code, name, stage, price, market_cap, data_json))
                    
                    success += 1
                except Exception as e:
                    logger.error(f"保存股票失败: {e}", 'DATABASE')
                    failed += 1
            
            conn.commit()
        
        return success, failed
    
    def delete_stock(self, code: str) -> bool:
        """删除股票"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM stocks WHERE code = ?",
                (code.upper().strip(),)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_old_stocks(self, days: int = 30) -> int:
        """删除N天前更新的股票"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM stocks 
                WHERE updated_at < datetime('now', '-{} days')
            '''.format(days))
            conn.commit()
            return cursor.rowcount
    
    def search_stocks(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索股票（代码或名称）"""
        keyword = f"%{keyword}%"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM stocks 
                WHERE code LIKE ? OR name LIKE ?
                ORDER BY updated_at DESC
            ''', (keyword, keyword))
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    # ───────────────────────────────────────────────
    # 同步元数据操作
    # ───────────────────────────────────────────────
    
    def get_last_sync(self) -> Optional[Dict[str, Any]]:
        """获取上次同步信息"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sync_metadata WHERE id = 1")
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None
    
    def update_sync_metadata(
        self,
        source: str,
        count: int = 0,
        error: Optional[str] = None
    ):
        """更新同步元数据"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE sync_metadata 
                SET last_sync = CURRENT_TIMESTAMP,
                    last_sync_source = ?,
                    sync_count = sync_count + ?,
                    last_error = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
            ''', (source, count, error))
            conn.commit()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取数据库统计"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 股票总数
            cursor.execute("SELECT COUNT(*) FROM stocks")
            total = cursor.fetchone()[0]
            
            # 各阶段数量
            cursor.execute('''
                SELECT stage, COUNT(*) as count 
                FROM stocks 
                GROUP BY stage
            ''')
            by_stage = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 同步信息
            sync_info = self.get_last_sync()
            
            return {
                'total_stocks': total,
                'by_stage': by_stage,
                'sync_info': sync_info,
            }
    
    # ───────────────────────────────────────────────
    # 工具方法
    # ───────────────────────────────────────────────
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """将行转换为字典"""
        result = dict(row)
        
        # 解析JSON数据
        if result.get('data_json'):
            try:
                parsed = json.loads(result['data_json'])
                result.update(parsed)
            except json.JSONDecodeError:
                pass
        
        return result
    
    def close(self):
        """关闭数据库连接"""
        conn = getattr(self._local, 'conn', None)
        if conn:
            conn.close()
            self._local.conn = None


# 全局数据库实例
db = DatabaseManager()
