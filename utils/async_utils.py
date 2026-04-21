"""
ST选股工具 - 异步任务工具
支持后台数据刷新和UI不阻塞操作
"""

import threading
import queue
from typing import Callable, Any, Optional, Dict
from functools import wraps
from kivy.clock import Clock

from utils.logger import logger


class AsyncTask:
    """异步任务封装"""
    
    def __init__(
        self,
        task_func: Callable,
        on_success: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        on_complete: Optional[Callable] = None
    ):
        self.task_func = task_func
        self.on_success = on_success
        self.on_error = on_error
        self.on_complete = on_complete
        self._thread: Optional[threading.Thread] = None
        self._result: Any = None
        self._error: Optional[Exception] = None
    
    def start(self, *args, **kwargs) -> 'AsyncTask':
        """启动异步任务"""
        self._thread = threading.Thread(
            target=self._run_task,
            args=args,
            kwargs=kwargs,
            daemon=True
        )
        self._thread.start()
        return self
    
    def _run_task(self, *args, **kwargs):
        """在后台线程执行任务"""
        try:
            self._result = self.task_func(*args, **kwargs)
            # 成功回调切换到主线程
            if self.on_success:
                Clock.schedule_once(
                    lambda dt: self._safe_callback(self.on_success, self._result),
                    0
                )
        except Exception as e:
            self._error = e
            logger.error(f"异步任务失败: {e}", 'ASYNC')
            # 错误回调切换到主线程
            if self.on_error:
                Clock.schedule_once(
                    lambda dt: self._safe_callback(self.on_error, e),
                    0
                )
        finally:
            # 完成回调切换到主线程
            if self.on_complete:
                Clock.schedule_once(
                    lambda dt: self._safe_callback(self.on_complete),
                    0
                )
    
    def _safe_callback(self, callback: Callable, *args):
        """安全执行回调"""
        try:
            callback(*args) if args else callback()
        except Exception as e:
            logger.error(f"回调执行失败: {e}", 'ASYNC')
    
    def is_running(self) -> bool:
        """检查任务是否正在运行"""
        return self._thread is not None and self._thread.is_alive()
    
    def join(self, timeout: Optional[float] = None) -> bool:
        """等待任务完成"""
        if self._thread:
            self._thread.join(timeout)
            return not self._thread.is_alive()
        return True


class BackgroundScheduler:
    """后台定时任务调度器"""
    
    def __init__(self):
        self._tasks: Dict[str, Any] = {}
        self._running = False
    
    def schedule_interval(
        self,
        task_id: str,
        callback: Callable,
        interval: float,
        start_immediately: bool = False
    ) -> None:
        """
        安排定时任务
        
        Args:
            task_id: 任务唯一标识
            callback: 任务回调函数
            interval: 间隔时间（秒）
            start_immediately: 是否立即执行一次
        """
        # 取消已有任务
        self.cancel(task_id)
        
        def wrapped_callback(dt):
            try:
                callback()
            except Exception as e:
                logger.error(f"定时任务 {task_id} 失败: {e}", 'SCHEDULER')
        
        event = Clock.schedule_interval(wrapped_callback, interval)
        self._tasks[task_id] = event
        
        if start_immediately:
            wrapped_callback(0)
        
        logger.info(f"定时任务 {task_id} 已安排，间隔 {interval}秒", 'SCHEDULER')
    
    def schedule_once(
        self,
        task_id: str,
        callback: Callable,
        delay: float
    ) -> None:
        """
        安排一次性任务
        
        Args:
            task_id: 任务唯一标识
            callback: 任务回调函数
            delay: 延迟时间（秒）
        """
        self.cancel(task_id)
        
        def wrapped_callback(dt):
            try:
                callback()
            except Exception as e:
                logger.error(f"一次性任务 {task_id} 失败: {e}", 'SCHEDULER')
            finally:
                self._tasks.pop(task_id, None)
        
        event = Clock.schedule_once(wrapped_callback, delay)
        self._tasks[task_id] = event
    
    def cancel(self, task_id: str) -> bool:
        """取消指定任务"""
        if task_id in self._tasks:
            event = self._tasks.pop(task_id)
            Clock.unschedule(event)
            return True
        return False
    
    def cancel_all(self) -> None:
        """取消所有任务"""
        for task_id in list(self._tasks.keys()):
            self.cancel(task_id)
    
    def is_scheduled(self, task_id: str) -> bool:
        """检查任务是否已安排"""
        return task_id in self._tasks


# 全局调度器实例
scheduler = BackgroundScheduler()


def run_in_background(
    on_success: Optional[Callable] = None,
    on_error: Optional[Callable] = None
):
    """后台运行装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            task = AsyncTask(
                task_func=lambda: func(*args, **kwargs),
                on_success=on_success,
                on_error=on_error
            )
            return task.start()
        return wrapper
    return decorator


def debounce(delay: float):
    """防抖装饰器"""
    def decorator(func: Callable):
        _timer = [None]
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            if _timer[0]:
                Clock.unschedule(_timer[0])
            
            def delayed_call(dt):
                func(*args, **kwargs)
                _timer[0] = None
            
            _timer[0] = Clock.schedule_once(delayed_call, delay)
        
        return wrapper
    return decorator


class LoadingState:
    """加载状态管理器"""
    
    def __init__(self):
        self._loading = False
        self._callbacks: List[Callable[[bool], None]] = []
    
    def add_listener(self, callback: Callable[[bool], None]) -> None:
        """添加状态监听器"""
        self._callbacks.append(callback)
    
    def remove_listener(self, callback: Callable[[bool], None]) -> None:
        """移除状态监听器"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def set_loading(self, loading: bool) -> None:
        """设置加载状态"""
        self._loading = loading
        for callback in self._callbacks:
            try:
                callback(loading)
            except Exception as e:
                logger.error(f"加载状态回调失败: {e}", 'LOADING')
    
    def is_loading(self) -> bool:
        """获取加载状态"""
        return self._loading
