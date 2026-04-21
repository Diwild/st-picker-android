"""
响应式布局工具模块
根据屏幕尺寸自动调整UI元素大小

主流手机屏幕比例参考：
- 小屏手机：360x640 (16:9)
- 标准手机：360x760 (19:9) 
- 大屏手机：400x880 (20:9)
- 平板：600x960 (16:10)
"""

from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.event import EventDispatcher


class ResponsiveHelper(EventDispatcher):
    """响应式布局辅助类 - 单例模式"""
    
    _instance = None
    
    # 屏幕尺寸分类阈值
    SCREEN_SMALL = 360   # 小屏手机 (< 360dp)
    SCREEN_NORMAL = 400  # 标准手机 (360-400dp)
    SCREEN_LARGE = 480   # 大屏手机 (400-480dp)
    SCREEN_XLARGE = 600  # 平板 (>= 600dp)
    
    # 属性
    screen_width = NumericProperty(360)
    screen_height = NumericProperty(760)
    screen_density = NumericProperty(1.0)
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        self._update_dimensions()
        
        # 监听窗口大小变化
        Window.bind(size=self._on_window_resize)
        Clock.schedule_once(self._update_dimensions, 0)
    
    def _on_window_resize(self, instance, size):
        """窗口大小变化时更新"""
        Clock.schedule_once(self._update_dimensions, 0)
    
    def _update_dimensions(self, dt=None):
        """更新屏幕尺寸信息"""
        self.screen_width = Window.width / self.screen_density
        self.screen_height = Window.height / self.screen_density
    
    @property
    def is_small_screen(self):
        """是否小屏手机"""
        return self.screen_width < self.SCREEN_NORMAL
    
    @property
    def is_normal_screen(self):
        """是否标准屏幕"""
        return self.SCREEN_NORMAL <= self.screen_width < self.SCREEN_LARGE
    
    @property
    def is_large_screen(self):
        """是否大屏手机"""
        return self.SCREEN_LARGE <= self.screen_width < self.SCREEN_XLARGE
    
    @property
    def is_xlarge_screen(self):
        """是否平板"""
        return self.screen_width >= self.SCREEN_XLARGE
    
    @property
    def screen_type(self):
        """获取屏幕类型名称"""
        if self.is_small_screen:
            return 'small'
        elif self.is_normal_screen:
            return 'normal'
        elif self.is_large_screen:
            return 'large'
        return 'xlarge'
    
    # ═══════════════════════════════════════════════════════
    # 响应式尺寸计算
    # ═══════════════════════════════════════════════════════
    
    def font_size(self, base_size):
        """
        根据屏幕宽度调整字体大小 - 保守缩放防止溢出
        
        Args:
            base_size: 基础字体大小（标准屏360dp宽度时的值）
        
        Returns:
            调整后的dp值
        """
        # 限制缩放范围：小屏不缩太小（保证可读性），大屏不放大太多（防止溢出）
        scale = min(max(self.screen_width / 360, 0.88), 1.08)
        return dp(base_size * scale)
    
    def spacing(self, base_size):
        """
        根据屏幕宽度调整间距
        
        Args:
            base_size: 基础间距（标准屏360dp宽度时的值）
        """
        scale = min(max(self.screen_width / 360, 0.9), 1.15)
        return dp(base_size * scale)
    
    def height(self, base_size):
        """
        根据屏幕高度调整元素高度
        
        Args:
            base_size: 基础高度（标准屏760dp高度时的值）
        """
        scale = min(max(self.screen_height / 760, 0.92), 1.08)
        return dp(base_size * scale)
    
    def padding(self, base_padding):
        """
        根据屏幕宽度调整内边距 - 保持合理边距防止内容贴边
        
        Args:
            base_padding: 基础内边距元组 (left, top, right, bottom) 或 统一值
        """
        scale = min(max(self.screen_width / 360, 0.9), 1.15)
        
        if isinstance(base_padding, (tuple, list)):
            return tuple(dp(p * scale) for p in base_padding)
        return dp(base_padding * scale)
    
    def card_width(self):
        """计算卡片宽度（列表项）"""
        # 小屏：几乎全宽，大屏：保持合适边距
        if self.is_small_screen:
            return 1.0  # 100% 宽度
        elif self.is_normal_screen:
            return 1.0
        else:
            return 0.95  # 95% 宽度，留出边距
    
    # ═══════════════════════════════════════════════════════
    # 快捷属性
    # ═══════════════════════════════════════════════════════
    
    @property
    def title_font_size(self):
        """标题字体大小 - APP标题"""
        if self.is_small_screen:
            return dp(17)
        elif self.is_normal_screen:
            return dp(19)
        return dp(20)
    
    @property
    def header_font_size(self):
        """头部字体大小 - 卡片标题等"""
        if self.is_small_screen:
            return dp(14)
        elif self.is_normal_screen:
            return dp(15)
        return dp(16)
    
    @property
    def body_font_size(self):
        """正文字体大小"""
        if self.is_small_screen:
            return dp(12)
        elif self.is_normal_screen:
            return dp(13)
        return dp(14)
    
    @property
    def small_font_size(self):
        """小字体大小 - 辅助信息"""
        if self.is_small_screen:
            return dp(10)
        return dp(11)
    
    @property
    def card_title_font_size(self):
        """卡片标题字体 - 股票名称等"""
        if self.is_small_screen:
            return dp(15)
        elif self.is_normal_screen:
            return dp(16)
        return dp(17)
    
    @property
    def card_price_font_size(self):
        """卡片价格字体"""
        if self.is_small_screen:
            return dp(14)
        elif self.is_normal_screen:
            return dp(15)
        return dp(16)
    
    @property
    def nav_height(self):
        """导航栏高度"""
        if self.is_small_screen:
            return dp(44)
        return dp(50)
    
    @property
    def card_height(self):
        """卡片高度"""
        if self.is_small_screen:
            return dp(110)
        elif self.is_normal_screen:
            return dp(120)
        return dp(130)
    
    @property
    def list_spacing(self):
        """列表项间距"""
        if self.is_small_screen:
            return dp(6)
        return dp(8)
    
    @property
    def content_padding(self):
        """内容区域内边距"""
        if self.is_small_screen:
            return dp(8)
        return dp(12)


# 全局响应式帮助实例
responsive = ResponsiveHelper()


# ═══════════════════════════════════════════════════════
# 便捷的响应式函数
# ═══════════════════════════════════════════════════════

def rsp_font(base_size):
    """响应式字体大小"""
    return responsive.font_size(base_size)

def rsp_height(base_size):
    """响应式高度"""
    return responsive.height(base_size)

def rsp_spacing(base_size):
    """响应式间距"""
    return responsive.spacing(base_size)

def rsp_padding(base_padding):
    """响应式内边距"""
    return responsive.padding(base_padding)

# 快捷字体大小
TITLE_FONT = property(lambda self: responsive.title_font_size)
HEADER_FONT = property(lambda self: responsive.header_font_size)
BODY_FONT = property(lambda self: responsive.body_font_size)
SMALL_FONT = property(lambda self: responsive.small_font_size)
