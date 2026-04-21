"""
ST选股工具 - 内存LRU缓存管理器
提供高性能的内存缓存，减少重复计算
"""

import time
import threading
from typing import Dict, Optional, Any, Callable
from collections import OrderedDict
from dataclasses import dataclass, field
from functools import wraps

from utils.logger import logger


@dataclass
class CacheEntry:
    """缓存条目"""
    value: Any
    expire_at: Optional[float] = None
    access_count: int = field(default=0)
    last_access: float = field(default_factory=time.time)


class LRUCache:
    """
    线程安全的LRU缓存
    
    Features:
    - 固定容量，超出自动淘汰最久未使用
    - 支持TTL过期
    - 线程安全
    - 命中率统计
    """
    
    def __init__(self, capacity: int = 128, default_ttl: Optional[int] = None):
        """
        Args:
            capacity: 最大缓存条目数
            default_ttl: 默认过期时间（秒），None表示永不过期
        """
        self._capacity = max(1, capacity)
        self._default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        
        # 统计
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
        
        Returns:
            缓存值或None
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                return None
            
            # 检查是否过期
            if entry.expire_at is not None and time.time() > entry.expire_at:
                del self._cache[key]
                self._misses += 1
                return None
            
            # 更新访问信息
            entry.access_count += 1
            entry.last_access = time.time()
            
            # 移到末尾（最新使用）
            self._cache.move_to_end(key)
            
            self._hits += 1
            return entry.value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None使用默认值
        """
        with self._lock:
            # 计算过期时间
            expire_at = None
            if ttl is not None:
                expire_at = time.time() + ttl
            elif self._default_ttl is not None:
                expire_at = time.time() + self._default_ttl
            
            # 如果key已存在，更新值
            if key in self._cache:
                self._cache[key] = CacheEntry(
                    value=value,
                    expire_at=expire_at,
                    access_count=self._cache[key].access_count + 1,
                    last_access=time.time()
                )
                self._cache.move_to_end(key)
                return
            
            # 容量检查：淘汰最久未使用的
            while len(self._cache) >= self._capacity:
                self._evict_oldest()
            
            # 添加新条目
            self._cache[key] = CacheEntry(
                value=value,
                expire_at=expire_at,
                last_access=time.time()
            )
    
    def delete(self, key: str) -> bool:
        """删除缓存条目"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def _evict_oldest(self) -> None:
        """淘汰最久未使用的条目"""
        if self._cache:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            return {
                'size': len(self._cache),
                'capacity': self._capacity,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': f"{hit_rate:.1%}",
            }
    
    def keys(self) -> list:
        """获取所有键"""
        with self._lock:
            return list(self._cache.keys())
    
    def __contains__(self, key: str) -> bool:
        """检查键是否存在"""
        return self.get(key) is not None
    
    def __len__(self) -> int:
        """获取缓存大小"""
        with self._lock:
            return len(self._cache)


class AnalysisCache:
    """
    股票分析结果专用缓存
    
    缓存分析结果，避免重复计算
    """
    
    def __init__(self, maxsize: int = 256):
        self._cache = LRUCache(capacity=maxsize, default_ttl=300)  # 5分钟过期
    
    def get_analysis_key(self, stock_code: str, filters_hash: str = '') -> str:
        """生成分析结果缓存键"""
        return f"analysis:{stock_code}:{filters_hash}"
    
    def get(self, stock_code: str, filters_hash: str = ''):
        """获取分析结果"""
        key = self.get_analysis_key(stock_code, filters_hash)
        return self._cache.get(key)
    
    def set(self, stock_code: str, result, filters_hash: str = ''):
        """缓存分析结果"""
        key = self.get_analysis_key(stock_code, filters_hash)
        self._cache.set(key, result)
    
    def invalidate_stock(self, stock_code: str):
        """使某只股票的所有分析结果失效"""
        prefix = f"analysis:{stock_code}:"
        for key in self._cache.keys():
            if key.startswith(prefix):
                self._cache.delete(key)
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
    
    def get_stats(self):
        """获取统计"""
        return self._cache.get_stats()


class StockDataCache:
    """
    股票原始数据缓存
    
    缓存从数据库/API获取的原始股票数据
    """
    
    def __init__(self, maxsize: int = 512):
        # 股票数据缓存15分钟
        self._cache = LRUCache(capacity=maxsize, default_ttl=900)
    
    def get(self, stock_code: str):
        """获取股票数据"""
        return self._cache.get(f"stock:{stock_code}")
    
    def set(self, stock_code: str, data):
        """缓存股票数据"""
        self._cache.set(f"stock:{stock_code}", data)
    
    def get_batch(self, stock_codes: list):
        """批量获取"""
        result = {}
        for code in stock_codes:
            data = self.get(code)
            if data:
                result[code] = data
        return result
    
    def set_batch(self, stocks_data: dict):
        """批量缓存"""
        for code, data in stocks_data.items():
            self.set(code, data)
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
    
    def get_stats(self):
        """获取统计"""
        return self._cache.get_stats()


def cached(cache: LRUCache, key_func: Optional[Callable] = None):
    """
    缓存装饰器
    
    Usage:
        cache = LRUCache(capacity=100)
        
        @cached(cache)
        def expensive_function(x, y):
            return x + y
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试从缓存获取
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            cache.set(cache_key, result)
            
            return result
        
        return wrapper
    return decorator


# 全局缓存实例
analysis_cache = AnalysisCache(maxsize=256)
stock_data_cache = StockDataCache(maxsize=512)
