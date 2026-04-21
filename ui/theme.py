"""
ST选股工具 - 现代化主题系统 v2.0
美观、专业、简洁的设计系统

设计特点：
- 深色主题配合玻璃拟态效果
- 渐变色彩增加视觉层次
- 精心设计的阴影系统
- 流畅的动画曲线
"""

from typing import Dict, Tuple, List, Optional
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line
from kivy.metrics import dp


# ═══════════════════════════════════════════════════════
# 核心色彩系统
# ═══════════════════════════════════════════════════════

class Colors:
    """现代深色主题色彩系统"""
    
    # 主背景色 - 深邃蓝黑色调
    BG_DEEP = (0.031, 0.039, 0.051, 1)        # #080A0D - 最深背景
    BG_PRIMARY = (0.051, 0.063, 0.082, 1)     # #0D1015 - 主背景
    BG_SECONDARY = (0.075, 0.090, 0.110, 1)   # #13171C - 次级背景
    BG_TERTIARY = (0.098, 0.114, 0.137, 1)    # #191D23 - 第三层背景
    BG_ELEVATED = (0.122, 0.141, 0.165, 1)    # #1F242A - 悬浮背景
    BG_CARD = (0.110, 0.129, 0.153, 0.95)     # 卡片背景带透明
    
    # 文字色 - 精心调配的对比度
    TEXT_PRIMARY = (0.95, 0.96, 0.97, 1)      # #F2F5F8 - 主文字
    TEXT_SECONDARY = (0.70, 0.74, 0.78, 1)    # #B3BCC7 - 次级文字
    TEXT_TERTIARY = (0.52, 0.56, 0.62, 1)     # #858F9E - 第三级文字
    TEXT_MUTED = (0.38, 0.42, 0.48, 1)        # #616B7A - 弱化文字
    TEXT_HINT = (0.28, 0.32, 0.38, 1)         # #485261 - 提示文字
    
    # 强调色 - 活力蓝绿色系
    ACCENT_BLUE = (0.25, 0.65, 1.0, 1)        # #40A6FF - 主强调色
    ACCENT_BLUE_GLOW = (0.25, 0.65, 1.0, 0.3) # 蓝色光晕
    ACCENT_CYAN = (0.20, 0.85, 0.95, 1)       # #33D9F2 - 青色
    ACCENT_GREEN = (0.25, 0.85, 0.50, 1)      # #40D980 - 成功绿
    ACCENT_ORANGE = (1.0, 0.65, 0.20, 1)      # #FFA633 - 警告橙
    ACCENT_RED = (1.0, 0.35, 0.35, 1)         # #FF5A5A - 错误红
    ACCENT_PURPLE = (0.75, 0.45, 1.0, 1)      # #BF73FF - 紫色
    ACCENT_YELLOW = (1.0, 0.85, 0.25, 1)      # #FFD940 - 黄色
    
    # 阶段专用颜色
    STAGE_HOT = (1.0, 0.35, 0.35, 1)          # 最佳介入 - 红色
    STAGE_GOOD = (1.0, 0.65, 0.20, 1)         # 较好 - 橙色  
    STAGE_SAFE = (0.25, 0.85, 0.50, 1)        # 确定性高 - 绿色
    STAGE_INFO = (0.25, 0.65, 1.0, 1)         # 执行/完成 - 蓝色
    STAGE_WARN = (1.0, 0.85, 0.25, 1)         # 早期 - 黄色
    STAGE_MUTED = (0.52, 0.56, 0.62, 1)       # 观察 - 灰色
    
    # 玻璃拟态效果
    GLASS_BG = (0.15, 0.18, 0.22, 0.7)        # 玻璃背景
    GLASS_BORDER = (1, 1, 1, 0.1)             # 玻璃边框
    GLASS_HIGHLIGHT = (1, 1, 1, 0.05)         # 玻璃高光
    
    # 渐变定义 (start_color, end_color, direction)
    GRADIENT_PRIMARY = (ACCENT_BLUE, ACCENT_CYAN)
    GRADIENT_SUCCESS = ((0.20, 0.75, 0.45, 1), (0.30, 0.90, 0.55, 1))
    GRADIENT_WARNING = ((1.0, 0.55, 0.15, 1), (1.0, 0.75, 0.25, 1))
    GRADIENT_DANGER = ((1.0, 0.25, 0.25, 1), (1.0, 0.45, 0.45, 1))
    GRADIENT_CARD = (BG_SECONDARY, BG_TERTIARY)
    
    # 阴影颜色
    SHADOW_LIGHT = (0, 0, 0, 0.15)
    SHADOW_MEDIUM = (0, 0, 0, 0.25)
    SHADOW_HEAVY = (0, 0, 0, 0.40)
    
    # 按钮色
    BTN_PRIMARY = (0.20, 0.55, 0.95, 1)       # 主按钮
    BTN_PRIMARY_HOVER = (0.25, 0.60, 1.0, 1)  # 主按钮悬停
    BTN_SECONDARY = (0.15, 0.18, 0.22, 1)     # 次按钮
    BTN_SUCCESS = (0.20, 0.70, 0.45, 1)       # 成功按钮
    BTN_DANGER = (0.85, 0.30, 0.30, 1)        # 危险按钮
    
    # 分隔线
    DIVIDER = (0.18, 0.22, 0.28, 1)           # 分隔线
    DIVIDER_LIGHT = (1, 1, 1, 0.05)           # 亮色分隔线


# ═══════════════════════════════════════════════════════
# 尺寸系统
# ═══════════════════════════════════════════════════════

class Dimensions:
    """统一尺寸系统"""
    
    # 圆角
    RADIUS_SMALL = 6
    RADIUS_MEDIUM = 10
    RADIUS_LARGE = 16
    RADIUS_XLARGE = 20
    RADIUS_FULL = 999  # 完全圆角
    
    # 间距
    SPACING_XS = 4
    SPACING_SM = 8
    SPACING_MD = 12
    SPACING_LG = 16
    SPACING_XL = 20
    SPACING_XXL = 24
    
    # 内边距
    PADDING_CARD = (12, 12)
    PADDING_SECTION = (16, 14)
    PADDING_SCREEN = (16, 12)
    
    # 高度
    HEIGHT_BUTTON = 40
    HEIGHT_INPUT = 42
    HEIGHT_CARD_SMALL = 100
    HEIGHT_CARD_MEDIUM = 120
    HEIGHT_CARD_LARGE = 140
    HEIGHT_NAV = 52
    
    # 字体大小
    FONT_H1 = 24
    FONT_H2 = 20
    FONT_H3 = 17
    FONT_BODY = 14
    FONT_SMALL = 12
    FONT_TINY = 10


# ═══════════════════════════════════════════════════════
# 动画曲线
# ═══════════════════════════════════════════════════════

class AnimationCurves:
    """动画缓动曲线"""
    EASE = 'out_quad'
    EASE_OUT = 'out_cubic'
    EASE_IN = 'in_cubic'
    EASE_IN_OUT = 'in_out_cubic'
    BOUNCE = 'out_bounce'
    ELASTIC = 'out_elastic'
    SPRING = 'out_back'
    
    # 时长
    DURATION_FAST = 0.15
    DURATION_NORMAL = 0.25
    DURATION_SLOW = 0.4
    DURATION_SLOWER = 0.6


# ═══════════════════════════════════════════════════════
# 向后兼容的 Theme 类
# ═══════════════════════════════════════════════════════

class Theme:
    """向后兼容的主题类 - 映射到新色彩系统"""
    
    # 背景色
    BG_PRIMARY = Colors.BG_PRIMARY
    BG_SECONDARY = Colors.BG_SECONDARY
    BG_TERTIARY = Colors.BG_TERTIARY
    BG_ELEVATED = Colors.BG_ELEVATED
    
    # 文字色
    TEXT_PRIMARY = Colors.TEXT_PRIMARY
    TEXT_SECONDARY = Colors.TEXT_SECONDARY
    TEXT_MUTED = Colors.TEXT_MUTED
    
    # 强调色
    ACCENT_BLUE = Colors.ACCENT_BLUE
    ACCENT_RED = Colors.ACCENT_RED
    ACCENT_GREEN = Colors.ACCENT_GREEN
    ACCENT_ORANGE = Colors.ACCENT_ORANGE
    ACCENT_PURPLE = Colors.ACCENT_PURPLE
    ACCENT_YELLOW = Colors.ACCENT_YELLOW
    
    # 阶段颜色
    STAGE_COLORS = {
        'hot': Colors.STAGE_HOT,
        'good': Colors.STAGE_GOOD,
        'safe': Colors.STAGE_SAFE,
        'info': Colors.STAGE_INFO,
        'warn': Colors.STAGE_WARN,
        'muted': Colors.STAGE_MUTED,
    }
    
    # 按钮色
    BTN_PRIMARY = Colors.BTN_PRIMARY
    BTN_SUCCESS = Colors.BTN_SUCCESS
    BTN_DANGER = Colors.BTN_DANGER
    
    # 分隔线
    DIVIDER = Colors.DIVIDER
    
    # 圆角
    CARD_RADIUS = Dimensions.RADIUS_MEDIUM
    BADGE_RADIUS = Dimensions.RADIUS_SMALL
    BUTTON_RADIUS = Dimensions.RADIUS_SMALL


# ═══════════════════════════════════════════════════════
# 实用函数
# ═══════════════════════════════════════════════════════

def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> Tuple[float, ...]:
    """十六进制颜色转RGBA元组"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return (r, g, b, alpha)


def get_stage_color(stage_type: str) -> Tuple[float, ...]:
    """获取阶段类型对应的颜色"""
    return Theme.STAGE_COLORS.get(stage_type, Colors.TEXT_MUTED)


def darken(color: Tuple[float, ...], factor: float = 0.8) -> Tuple[float, ...]:
    """加深颜色"""
    return (color[0] * factor, color[1] * factor, color[2] * factor, color[3])


def lighten(color: Tuple[float, ...], factor: float = 1.2) -> Tuple[float, ...]:
    """减淡颜色"""
    return (
        min(color[0] * factor, 1.0),
        min(color[1] * factor, 1.0),
        min(color[2] * factor, 1.0),
        color[3]
    )


def with_alpha(color: Tuple[float, ...], alpha: float) -> Tuple[float, ...]:
    """修改颜色透明度"""
    return (color[0], color[1], color[2], alpha)
