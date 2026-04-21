"""
ST选股工具 - 评分进度条组件 v2.0
现代化设计，带渐变效果
"""

from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp
from kivy.properties import NumericProperty, ListProperty

from core.constants import Theme
from ui.responsive import rsp_font, rsp_height, rsp_spacing


class ScoreBar(BoxLayout):
    """投资人评分进度条 v2.0"""

    score = NumericProperty(0)
    bar_color = ListProperty(Theme.ACCENT_BLUE)

    def __init__(self, score=0, label_text='评分', **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = rsp_height(18)
        self.spacing = rsp_spacing(6)

        self.label = Label(
            text=label_text,
            font_size=rsp_font(12),
            color=Theme.TEXT_TERTIARY,
            size_hint_x=0.22,
            halign='left', valign='center',
        )
        self.add_widget(self.label)

        self.bar_container = Widget(size_hint_x=0.53)
        self.add_widget(self.bar_container)

        self.score_label = Label(
            text=str(int(score)),
            font_size=rsp_font(13),
            bold=True,
            color=Theme.TEXT_PRIMARY,
            size_hint_x=0.25,
            halign='right', valign='center',
        )
        self.add_widget(self.score_label)

        self.bar_container.bind(pos=self._draw_bar, size=self._draw_bar)
        self.bind(score=self._on_score_change)
        
        # 设置初始分数
        self.score = score

    def _determine_color(self):
        if self.score >= 70:
            self.bar_color = list(Theme.ACCENT_GREEN)
        elif self.score >= 40:
            self.bar_color = list(Theme.ACCENT_ORANGE)
        else:
            self.bar_color = list(Theme.ACCENT_RED)

    def _on_score_change(self, *args):
        self._determine_color()
        self.score_label.text = str(int(self.score))
        self._draw_bar()

    def _draw_bar(self, *args):
        container = self.bar_container
        container.canvas.clear()

        with container.canvas:
            # 背景轨道
            Color(*Theme.BG_ELEVATED)
            RoundedRectangle(
                pos=(container.x, container.center_y - rsp_spacing(3)),
                size=(container.width, rsp_spacing(6)),
                radius=[rsp_spacing(3)],
            )

            # 填充进度
            fill_width = max(rsp_spacing(4), container.width * (self.score / 100))
            Color(*self.bar_color[:3], 0.9)
            RoundedRectangle(
                pos=(container.x, container.center_y - rsp_spacing(3)),
                size=(fill_width, rsp_spacing(6)),
                radius=[rsp_spacing(3)],
            )
            
            # 进度条高光
            Color(1, 1, 1, 0.2)
            RoundedRectangle(
                pos=(container.x, container.center_y - rsp_spacing(1)),
                size=(fill_width, rsp_spacing(2)),
                radius=[rsp_spacing(1)],
            )
