"""
ST选股工具 - 动画系统
提供流畅、专业的动画效果
"""

from typing import Optional, Callable, Any, List
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.metrics import dp


class AnimationConfig:
    """动画配置常量"""
    DURATION_INSTANT = 0.1
    DURATION_FAST = 0.15
    DURATION_NORMAL = 0.25
    DURATION_SLOW = 0.4
    
    EASE = 'out_quad'
    EASE_OUT = 'out_cubic'
    SPRING = 'out_back'
    STAGGER_DELAY = 0.05


class AnimationHelper:
    """动画辅助类"""
    
    @staticmethod
    def fade_in(widget: Widget, duration: float = None, delay: float = 0):
        duration = duration or AnimationConfig.DURATION_NORMAL
        widget.opacity = 0
        anim = Animation(opacity=1, duration=duration, t=AnimationConfig.EASE)
        if delay > 0:
            Clock.schedule_once(lambda dt: anim.start(widget), delay)
        else:
            anim.start(widget)
        return anim
    
    @staticmethod
    def fade_out(widget: Widget, duration: float = None):
        duration = duration or AnimationConfig.DURATION_FAST
        anim = Animation(opacity=0, duration=duration, t=AnimationConfig.EASE)
        anim.start(widget)
        return anim
    
    @staticmethod
    def slide_in_from_bottom(widget: Widget, distance: float = None, 
                             duration: float = None, delay: float = 0):
        duration = duration or AnimationConfig.DURATION_NORMAL
        distance = distance or dp(30)
        original_y = widget.y
        widget.y = original_y - distance
        widget.opacity = 0
        anim = Animation(y=original_y, opacity=1, duration=duration, t=AnimationConfig.SPRING)
        if delay > 0:
            Clock.schedule_once(lambda dt: anim.start(widget), delay)
        else:
            anim.start(widget)
        return anim
    
    @staticmethod
    def press_effect(widget: Widget, scale: float = 0.97):
        anim = Animation(opacity=0.7, duration=AnimationConfig.DURATION_INSTANT, t=AnimationConfig.EASE)
        anim.start(widget)
        return anim
    
    @staticmethod
    def release_effect(widget: Widget):
        anim = Animation(opacity=1, duration=AnimationConfig.DURATION_FAST, t=AnimationConfig.SPRING)
        anim.start(widget)
        return anim
    
    @staticmethod
    def staggered_fade_in(widgets: List[Widget], base_delay: float = None, duration: float = None):
        base_delay = base_delay or AnimationConfig.STAGGER_DELAY
        duration = duration or AnimationConfig.DURATION_NORMAL
        for i, widget in enumerate(widgets):
            widget.opacity = 0
            Clock.schedule_once(lambda dt, w=widget: AnimationHelper.fade_in(w, duration), i * base_delay)
    
    @staticmethod
    def expand_height(widget: Widget, target_height: float, duration: float = None):
        duration = duration or AnimationConfig.DURATION_SLOW
        anim = Animation(height=target_height, duration=duration, t=AnimationConfig.SPRING)
        anim.start(widget)
        return anim
    
    @staticmethod
    def collapse_height(widget: Widget, duration: float = None):
        duration = duration or AnimationConfig.DURATION_NORMAL
        anim = Animation(height=0, duration=duration, t=AnimationConfig.EASE)
        anim.start(widget)
        return anim
