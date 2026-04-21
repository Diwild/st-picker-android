"""
ST选股工具 - 阶段标签组件 v2.0
现代化设计，带渐变背景效果
"""

from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty

from core.constants import Theme, RECOMMENDATIONS
from ui.responsive import rsp_font, rsp_spacing


class StageBadge(Label):
    """阶段标签 Badge v2.0"""

    stage_type = StringProperty('muted')
    badge_color = ListProperty(Theme.TEXT_MUTED)

    def __init__(self, text='', stage_type='muted', **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.stage_type = stage_type
        self.badge_color = list(Theme.STAGE_COLORS.get(stage_type, Theme.TEXT_MUTED))

        self.font_size = rsp_font(12)
        self.size_hint = (None, None)
        self.padding = (rsp_spacing(10), rsp_spacing(4))
        self.color = (1, 1, 1, 1)
        self.bold = True
        self.halign = 'center'
        self.valign = 'middle'

        self.bind(texture_size=self._update_size)
        self.bind(pos=self._draw_bg)
        self.bind(badge_color=self._draw_bg)

    def _update_size(self, *args):
        new_width = self.texture_size[0] + rsp_spacing(14)
        new_height = self.texture_size[1] + rsp_spacing(6)
        if abs(self.width - new_width) > 0.5 or abs(self.height - new_height) > 0.5:
            self.size = (new_width, new_height)
            self._draw_bg()

    def _draw_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # 徽章背景 - 使用带透明度的颜色
            Color(*self.badge_color[:3], 0.2)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[rsp_spacing(6)],
            )
            # 边框
            Color(*self.badge_color[:3], 0.4)
            RoundedRectangle(
                pos=self.pos,
                size=(self.width, dp(1)),
                radius=[rsp_spacing(6)],
            )

    @staticmethod
    def from_stage_code(stage_code):
        from core.constants import STAGE_NAMES
        rec_tuple = RECOMMENDATIONS.get(stage_code, ('观察', 'muted'))
        name = STAGE_NAMES.get(stage_code, stage_code)
        return StageBadge(text=name, stage_type=rec_tuple[1])
