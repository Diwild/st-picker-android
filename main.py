#!/usr/bin/env python3
"""
ST选股工具 - Android版
入口文件

全局异常处理机制：
- 捕获所有未处理的异常，防止应用崩溃
- 记录错误日志到文件
- 显示用户友好的错误提示
"""

import os
import sys
import traceback
import logging
from typing import Any

# 确保项目根目录在 Python 路径中
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# ═══════════════════════════════════════════════════════
# 全局异常处理
# ═══════════════════════════════════════════════════════

def setup_global_exception_handler() -> None:
    """设置全局异常处理器"""
    
    # 确保日志目录存在
    log_dir = os.path.join(app_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # 配置日志
    log_file = os.path.join(log_dir, 'crash.log')
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stderr)
        ]
    )
    
    def handle_exception(exc_type: type, exc_value: Exception, exc_traceback: Any) -> None:
        """全局异常处理函数"""
        # 忽略键盘中断
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # 格式化异常信息
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        # 记录错误日志
        logging.error(f"未捕获的异常:\n{error_msg}")
        
        # 尝试显示错误弹窗（如果UI已初始化）
        try:
            from kivy.app import App
            from kivy.uix.popup import Popup
            from kivy.uix.label import Label
            from kivy.metrics import dp
            from core.constants import Theme
            
            app = App.get_running_app()
            if app and app.root:
                popup = Popup(
                    title='应用错误',
                    content=Label(
                        text=f'发生未预期的错误:\n{str(exc_value)[:100]}\n\n错误已记录到日志文件',
                        color=Theme.TEXT_PRIMARY,
                        font_size=dp(14),
                    ),
                    size_hint=(0.8, 0.4),
                    auto_dismiss=True,
                )
                popup.open()
        except Exception:
            pass  # 如果UI显示失败，至少日志已记录
    
    # 设置全局异常钩子
    sys.excepthook = handle_exception


def setup_thread_exception_handler() -> None:
    """设置线程异常处理器（Python 3.8+）"""
    if hasattr(sys, 'excepthook') and sys.version_info >= (3, 8):
        import threading
        
        def handle_thread_exception(args: Any) -> None:
            """处理线程中的未捕获异常"""
            logging.error(
                f"线程异常 - 线程: {args.thread.name}, "
                f"异常: {args.exc_type.__name__}: {args.exc_value}"
            )
            # 打印完整堆栈
            traceback.print_exception(args.exc_type, args.exc_value, args.exc_traceback)
        
        threading.excepthook = handle_thread_exception


def setup_android_crash_handler() -> None:
    """
    Android 特有的崩溃防护：
    - MonkeyRunner Monkey 针对低内存的 SIGKILL 无法捕获
    - 但通过 Kivy 的 Clock.schedule_once 包裹所有界面操作可以减少崩溃
    - 通过确保 DetailScreen 的 show() 有完整 try-except 防护避免 Python 异常
    """


# ═══════════════════════════════════════════════════════
# 应用启动
# ═══════════════════════════════════════════════════════

def main() -> None:
    """应用主入口"""
    # 设置全局异常处理
    setup_global_exception_handler()
    setup_thread_exception_handler()
    
    try:
        from ui.app import STPickerApp
        from utils.logger import AppLogger
        
        logger = AppLogger()
        logger.info("=" * 50)
        logger.info("ST重整选股工具启动")
        logger.info(f"Python版本: {sys.version}")
        logger.info(f"工作目录: {app_dir}")
        logger.info("=" * 50)
        
        # 启动应用
        STPickerApp().run()
        
    except Exception as e:
        logging.error(f"应用启动失败: {e}")
        raise


if __name__ == '__main__':
    main()
