"""
ST选股工具 - 统一日志管理
提供分级日志记录和性能监控
"""

import sys
import logging
from typing import Optional
from functools import wraps
from datetime import datetime


class AppLogger:
    """应用日志管理器"""
    
    _instance: Optional['AppLogger'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._logger = logging.getLogger('STPicker')
        self._logger.setLevel(logging.DEBUG)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # 格式化
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # 避免重复添加
        if not self._logger.handlers:
            self._logger.addHandler(console_handler)
    
    def debug(self, msg: str, tag: str = '') -> None:
        """调试日志"""
        self._log(logging.DEBUG, msg, tag)
    
    def info(self, msg: str, tag: str = '') -> None:
        """信息日志"""
        self._log(logging.INFO, msg, tag)
    
    def warning(self, msg: str, tag: str = '') -> None:
        """警告日志"""
        self._log(logging.WARNING, msg, tag)
    
    def error(self, msg: str, tag: str = '', exc_info: bool = False) -> None:
        """错误日志"""
        self._log(logging.ERROR, msg, tag, exc_info)
    
    def _log(self, level: int, msg: str, tag: str, exc_info: bool = False) -> None:
        """内部日志方法"""
        prefix = f"[{tag}] " if tag else ""
        self._logger.log(level, f"{prefix}{msg}", exc_info=exc_info)


# 全局日志实例
logger = AppLogger()


def log_performance(tag: str = ''):
    """性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = datetime.now()
            try:
                result = func(*args, **kwargs)
                elapsed = (datetime.now() - start).total_seconds() * 1000
                logger.debug(f"{func.__name__} 耗时 {elapsed:.2f}ms", tag or 'PERF')
                return result
            except Exception as e:
                elapsed = (datetime.now() - start).total_seconds() * 1000
                logger.error(f"{func.__name__} 失败 ({elapsed:.2f}ms): {e}", tag or 'PERF')
                raise
        return wrapper
    return decorator


def log_method(tag: str = ''):
    """方法调用日志装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug(f"调用 {func.__name__}", tag or 'CALL')
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{func.__name__} 异常: {e}", tag or 'CALL')
                raise
        return wrapper
    return decorator
