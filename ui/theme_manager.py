"""
ST选股工具 - 主题管理器 v2.0
支持深色/浅色主题动态切换
"""

from typing import Dict, Tuple, Optional, Callable
from kivy.properties import BooleanProperty
from kivy.event import EventDispatcher


class ThemeManager(EventDispatcher):
    """
    主题管理器
    
    特性：
    - 支持深色/浅色主题
    - 动态切换
    - 全局通知
    """

    is_dark = BooleanProperty(True)

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        super().__init__()
        self._initialized = True
        self._listeners: list = []
        self._current_theme: Dict[str, Tuple[float, float, float, float]] = {}
        self._init_themes()
        self.apply_theme(True)

    def _init_themes(self):
        """初始化两套主题配色"""
        # 深色主题
        self._dark_theme = {
            'bg_primary': (0.051, 0.063, 0.082, 1),
            'bg_secondary': (0.075, 0.090, 0.110, 1),
            'bg_tertiary': (0.098, 0.114, 0.137, 1),
            'bg_elevated': (0.122, 0.141, 0.165, 1),
            'card_bg': (0.110, 0.129, 0.153, 0.95),
            'text_primary': (0.95, 0.96, 0.97, 1),
            'text_secondary': (0.70, 0.74, 0.78, 1),
            'text_tertiary': (0.52, 0.56, 0.62, 1),
            'text_muted': (0.38, 0.42, 0.48, 1),
            'accent_primary': (0.25, 0.65, 1.0, 1),
            'accent_red': (1.0, 0.35, 0.35, 1),
            'accent_green': (0.25, 0.85, 0.50, 1),
            'accent_orange': (1.0, 0.65, 0.20, 1),
            'accent_purple': (0.75, 0.45, 1.0, 1),
            'accent_yellow': (1.0, 0.85, 0.25, 1),
            'divider': (0.18, 0.22, 0.28, 1),
            'border': (0.18, 0.22, 0.28, 1),
            'btn_primary': (0.20, 0.55, 0.95, 1),
            'bg_secondary_alpha': (0.075, 0.090, 0.110, 0.8),
            'risk_high': (1.0, 0.35, 0.35, 1),
            'risk_bg': (1.0, 0.35, 0.35, 0.08),
            'risk_border': (1.0, 0.35, 0.35, 0.2),
            'price_up': (1.0, 0.35, 0.35, 1),    # 中国红涨
            'price_down': (0.25, 0.85, 0.50, 1), # 中国绿跌
        }

        # 浅色主题
        self._light_theme = {
            'bg_primary': (0.97, 0.97, 0.98, 1),      # #F8F8F9
            'bg_secondary': (1.0, 1.0, 1.0, 1),        # #FFFFFF
            'bg_tertiary': (0.94, 0.94, 0.95, 1),      # #F0F0F2
            'bg_elevated': (1.0, 1.0, 1.0, 1),         # #FFFFFF
            'card_bg': (1.0, 1.0, 1.0, 1),
            'text_primary': (0.10, 0.10, 0.12, 1),     # #1A1A1F
            'text_secondary': (0.35, 0.35, 0.40, 1),   # #5A5A66
            'text_tertiary': (0.55, 0.55, 0.60, 1),    # #8C8C99
            'text_muted': (0.65, 0.65, 0.70, 1),       # #A6A6B3
            'accent_primary': (0.20, 0.55, 0.95, 1),
            'accent_red': (0.90, 0.25, 0.25, 1),
            'accent_green': (0.20, 0.75, 0.40, 1),
            'accent_orange': (0.95, 0.55, 0.15, 1),
            'accent_purple': (0.70, 0.40, 0.95, 1),
            'accent_yellow': (0.95, 0.75, 0.15, 1),
            'divider': (0.88, 0.88, 0.90, 1),
            'border': (0.88, 0.88, 0.90, 1),
            'btn_primary': (0.20, 0.55, 0.95, 1),
            'bg_secondary_alpha': (1.0, 1.0, 1.0, 0.9),
            'risk_high': (0.90, 0.25, 0.25, 1),
            'risk_bg': (0.90, 0.25, 0.25, 0.06),
            'risk_border': (0.90, 0.25, 0.25, 0.15),
            'price_up': (0.90, 0.25, 0.25, 1),
            'price_down': (0.20, 0.75, 0.40, 1),
        }

    def apply_theme(self, is_dark: bool):
        """应用主题"""
        self.is_dark = is_dark
        self._current_theme = self._dark_theme if is_dark else self._light_theme

    def toggle_theme(self):
        """切换主题"""
        self.apply_theme(not self.is_dark)

    def color(self, key: str) -> Tuple[float, float, float, float]:
        """获取颜色值"""
        return self._current_theme.get(key, (0.5, 0.5, 0.5, 1))

    def get_theme(self) -> Dict[str, Tuple[float, float, float, float]]:
        """获取完整主题字典"""
        return self._current_theme.copy()


# 全局主题管理器
theme_mgr = ThemeManager()
