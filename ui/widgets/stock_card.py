"""
ST选股工具 - 股票卡片组件 v2.0
现代化设计，带阴影、渐变效果和流畅动画
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp
from kivy.properties import ObjectProperty
from kivy.animation import Animation
from kivy.clock import Clock

from core.constants import Theme, RECOMMENDATIONS
from ui.widgets.stage_badge import StageBadge
from ui.widgets.score_bar import ScoreBar
from ui.responsive import responsive, rsp_font, rsp_height, rsp_spacing, rsp_padding
from ui.animations import AnimationHelper


class StockCard(BoxLayout):
    """股票卡片 - 现代化设计 v2.0"""

    on_card_press = ObjectProperty(None)

    def __init__(self, analysis_result, on_press=None, **kwargs):
        super().__init__(**kwargs)
        self.analysis = analysis_result
        self.on_card_press = on_press
        self.orientation = 'horizontal'
        self.size_hint_y = None
        # 增加卡片高度，解决文字溢出问题
        self.height = rsp_height(125)
        self.padding = 0
        self.spacing = 0
        
        # 动画状态
        self._is_pressed = False
        self._press_start_time = 0

        # 获取阶段颜色
        rec_type = analysis_result.recommendation_type
        accent_color = Theme.STAGE_COLORS.get(rec_type, Theme.TEXT_MUTED)

        # ── 左侧彩色竖条 ──
        self.accent_bar = BoxLayout(size_hint_x=None, width=rsp_spacing(4))
        self.add_widget(self.accent_bar)

        # ── 主内容区 ──
        content = BoxLayout(
            orientation='vertical',
            padding=rsp_padding((12, 8, 12, 6)),  # 减小顶部padding到8，底部6
            spacing=rsp_spacing(2),  # 减小行间距到2
        )

        # 第一行：阶段标签 + 名称 + 价格（同一行，水平对齐，垂直居中）
        row1 = BoxLayout(
            orientation='horizontal', 
            size_hint_y=None, 
            height=rsp_height(26),  # 减小行高到26
        )
        
        # 阶段标签 - 使用AnchorLayout包装确保垂直居中
        badge_container = AnchorLayout(
            anchor_x='left', 
            anchor_y='center',
            size_hint_x=0.25
        )
        badge = StageBadge(text=analysis_result.stage, stage_type=rec_type)
        badge_container.add_widget(badge)
        row1.add_widget(badge_container)
        
        # 股票名称
        name_label = Label(
            text=analysis_result.display_name,
            font_size=rsp_font(17),  # 稍微减小字体
            bold=True,
            color=Theme.TEXT_PRIMARY,
            halign='left', valign='center',
            size_hint_x=0.45,
        )
        row1.add_widget(name_label)
        
        # 股价（中国红涨绿跌）
        price_color = getattr(analysis_result, 'price_color', None)
        if price_color is None:
            if getattr(analysis_result, 'is_up', False):
                price_color = (1.0, 0.35, 0.35, 1)  # 红涨
            elif getattr(analysis_result, 'is_down', False):
                price_color = (0.25, 0.85, 0.50, 1)  # 绿跌
            else:
                price_color = Theme.TEXT_SECONDARY
        
        price_label = Label(
            text=analysis_result.price_text,
            font_size=rsp_font(16),
            bold=True,
            color=price_color,
            halign='right', valign='center',
            size_hint_x=0.30,
        )
        row1.add_widget(price_label)
        content.add_widget(row1)

        # 第二行：涨跌幅(颜色) + 换手率 + 推荐
        row2 = BoxLayout(orientation='horizontal', size_hint_y=None, height=rsp_height(20))
        
        # 涨跌幅
        change_text = getattr(analysis_result, 'change_percent_text', '')
        if not change_text and getattr(analysis_result, 'change_percent', 0) != 0:
            sign = '+' if analysis_result.change_percent > 0 else ''
            change_text = f"{sign}{analysis_result.change_percent:.2f}%"
        
        change_color = price_color  # 与价格同色
        
        change_label = Label(
            text=change_text,
            font_size=rsp_font(13),
            bold=True,
            color=change_color,
            halign='left', valign='center',
            size_hint_x=0.28,
        )
        row2.add_widget(change_label)
        
        # 换手率
        turnover_text = getattr(analysis_result, 'turnover_rate_text', '')
        if not turnover_text and getattr(analysis_result, 'turnover_rate', 0) > 0:
            turnover_text = f"换手 {analysis_result.turnover_rate:.2f}%"
        
        turnover_label = Label(
            text=turnover_text,
            font_size=rsp_font(11),
            color=Theme.TEXT_MUTED,
            halign='left', valign='center',
            size_hint_x=0.30,
        )
        row2.add_widget(turnover_label)
        
        # 推荐
        rec_label = Label(
            text=analysis_result.recommendation,
            font_size=rsp_font(12),
            color=accent_color,
            halign='right', valign='center',
            size_hint_x=0.42,
        )
        row2.add_widget(rec_label)
        content.add_widget(row2)

        # 第三行：投资人摘要
        row3 = BoxLayout(orientation='horizontal', size_hint_y=None, height=rsp_height(16))
        investor_label = Label(
            text=analysis_result.investor_summary or '暂无投资人信息',
            font_size=rsp_font(11),
            color=Theme.TEXT_SECONDARY,
            halign='left', valign='center',
            shorten=True, shorten_from='right',
        )
        row3.add_widget(investor_label)
        content.add_widget(row3)

        # 第四行：评分进度条
        score_bar = ScoreBar(score=analysis_result.investor_score, label_text='评分')
        content.add_widget(score_bar)

        # 第五行：风险 + 资产注入
        row5 = BoxLayout(orientation='horizontal', size_hint_y=None, height=rsp_height(15))
        risk_label = Label(
            text=f"风险: {analysis_result.risk_level}",
            font_size=rsp_font(10),
            color=Theme.TEXT_MUTED,
            halign='left', valign='center',
            size_hint_x=0.4,
        )
        row5.add_widget(risk_label)
        if analysis_result.asset_injection:
            injection_label = Label(
                text=analysis_result.asset_injection,
                font_size=rsp_font(10),
                color=Theme.TEXT_MUTED,
                halign='right', valign='center',
                size_hint_x=0.6,
            )
            row5.add_widget(injection_label)
        content.add_widget(row5)

        self.add_widget(content)

        # 绑定绘制
        self._accent_color = accent_color
        self.bind(pos=self._draw, size=self._draw)
        
        # 入场动画
        Clock.schedule_once(lambda dt: AnimationHelper.fade_in(self), 0.05)

    def _draw(self, *args):
        """绘制卡片背景和阴影"""
        self.canvas.before.clear()
        with self.canvas.before:
            # 阴影效果
            Color(0, 0, 0, 0.15)
            RoundedRectangle(
                pos=(self.x + dp(1), self.y - dp(2)),
                size=self.size,
                radius=[dp(12)],
            )
            # 卡片背景
            Color(*Theme.BG_SECONDARY)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(12)],
            )
            # 顶部高光
            Color(1, 1, 1, 0.03)
            RoundedRectangle(
                pos=(self.x, self.top - dp(2)),
                size=(self.width, dp(2)),
                radius=[dp(12), dp(12), 0, 0],
            )

        # 左侧竖条
        self.accent_bar.canvas.clear()
        with self.accent_bar.canvas:
            Color(*self._accent_color)
            RoundedRectangle(
                pos=self.accent_bar.pos,
                size=self.accent_bar.size,
                radius=[dp(12), 0, 0, dp(12)],
            )

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._is_pressed = True
            self._touch_start_pos = touch.pos
            self._press_start_time = Clock.get_time()
            AnimationHelper.press_effect(self)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._is_pressed:
            dx = abs(touch.x - self._touch_start_pos[0])
            dy = abs(touch.y - self._touch_start_pos[1])
            if dx > dp(10) or dy > dp(10):
                self._cancel_press()
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self._is_pressed:
            was_inside = self.collide_point(*touch.pos)
            self._cancel_press()
            
            if was_inside and self.on_card_press:
                dx = abs(touch.x - self._touch_start_pos[0])
                dy = abs(touch.y - self._touch_start_pos[1])
                if dx < dp(10) and dy < dp(10):
                    # 点击反馈动画
                    anim = Animation(opacity=0.6, duration=0.05)
                    anim += Animation(opacity=1.0, duration=0.1)
                    anim.start(self)
                    try:
                        self.on_card_press(self.analysis)
                    except Exception as e:
                        from utils.logger import AppLogger
                        logger = AppLogger()
                        logger.error(f"[StockCard] 点击回调异常: {e}")
            return True
        return super().on_touch_up(touch)
    
    def _cancel_press(self):
        self._is_pressed = False
        AnimationHelper.release_effect(self)
