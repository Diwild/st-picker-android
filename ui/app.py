"""
ST选股工具 - Kivy App 主类
管理页面切换和全局配置
"""

import os

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.core.text import LabelBase
from kivy.metrics import dp

from core.constants import Theme


# 在模块级设置窗口背景色(需要在 build 之前)
try:
    from kivy.core.window import Window
    if Window is not None:
        Window.clearcolor = Theme.BG_PRIMARY
except Exception:
    Window = None


class MainPage(Screen):
    """主页面包装"""
    pass


class DetailPage(Screen):
    """详情页面包装"""
    pass


class STPickerApp(App):
    """ST选股工具 Kivy 应用"""

    def build(self):
        self.title = 'ST重整选股工具'

        # 延迟导入 screens，确保 Window 已创建
        from ui.screens.main_screen import MainScreen
        from ui.screens.detail_screen import DetailScreen

        # 再次设置窗口背景色(确保 Window 已初始化)
        try:
            from kivy.core.window import Window as Win
            if Win is not None:
                Win.clearcolor = Theme.BG_PRIMARY
        except Exception:
            pass

        # 尝试注册中文字体
        self._register_fonts()

        # 创建屏幕管理器
        self.sm = ScreenManager(transition=SlideTransition(duration=0.25))

        # ── 主页面 ──
        main_page = MainPage(name='main')
        self.main_screen = MainScreen(on_stock_select=self._go_detail)
        main_page.add_widget(self.main_screen)
        self.sm.add_widget(main_page)

        # ── 详情页面 ──
        detail_page = DetailPage(name='detail')
        self.detail_screen = DetailScreen(on_back=self._go_main)
        detail_page.add_widget(self.detail_screen)
        self.sm.add_widget(detail_page)

        return self.sm

    def _register_fonts(self):
        """注册中文字体为全局默认字体"""
        from kivy.core.text import DEFAULT_FONT
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        font_paths = [
            os.path.join(app_dir, 'assets', 'fonts', 'NotoSansSC-Regular.ttf'),
            os.path.join(app_dir, 'assets', 'fonts', 'NotoSansSC-Bold.ttf'),
            # Mac 系统字体
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/Library/Fonts/Arial Unicode.ttf',
            # Android 系统字体
            '/system/fonts/NotoSansCJK-Regular.ttc',
            '/system/fonts/DroidSansFallback.ttf',
        ]

        for path in font_paths:
            if os.path.exists(path):
                try:
                    # 覆盖全局默认字体
                    LabelBase.register(DEFAULT_FONT, fn_regular=path)
                    print(f"[App] 已注册全局默认字体: {path}")
                    return
                except Exception as e:
                    print(f"[App] 字体注册失败 {path}: {e}")

        print("[App] 未找到中文字体，使用系统默认")

    def _go_detail(self, analysis_result):
        """跳转到详情页"""
        from utils.logger import AppLogger
        logger = AppLogger()
        
        try:
            logger.info(f"[NAV] 跳转详情页: {analysis_result.display_name}")
            self.detail_screen.show(analysis_result)
            self.sm.transition.direction = 'left'
            self.sm.current = 'detail'
            logger.info("[NAV] 详情页跳转完成")
        except Exception as e:
            logger.error(f"[NAV] 跳转详情页失败: {e}")
            import traceback
            traceback.print_exc()
            # 显示错误提示但不崩溃
            try:
                from kivy.uix.popup import Popup
                from kivy.uix.label import Label
                from kivy.metrics import dp
                from core.constants import Theme
                popup = Popup(
                    title='页面加载失败',
                    content=Label(
                        text=f'股票详情加载失败:\n{str(e)[:50]}',
                        color=Theme.TEXT_PRIMARY,
                        font_size=dp(14),
                    ),
                    size_hint=(0.8, 0.3),
                    auto_dismiss=True,
                )
                popup.open()
            except:
                pass

    def _go_main(self):
        """返回主页"""
        self.sm.transition.direction = 'right'
        self.sm.current = 'main'
