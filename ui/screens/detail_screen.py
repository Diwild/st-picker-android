"""
ST选股工具 - 股票详情页 v3.0
三Tab结构：重整 / 行情 / 关联
复刻鸿蒙版设计
"""

from typing import Optional, List
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line, Ellipse
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.clock import Clock

from core.constants import Theme, RECOMMENDATIONS, ASSET_INJECTION
from core.favorites import fav_mgr
from ui.widgets.stage_badge import StageBadge
from ui.widgets.score_bar import ScoreBar
from ui.responsive import responsive, rsp_font, rsp_height, rsp_spacing, rsp_padding
from ui.animations import AnimationHelper


class DetailScreen(BoxLayout):
    """股票详情屏幕 v3.0 - 三Tab结构"""

    TAB_NAMES = ['重整', '行情', '关联']

    def __init__(self, on_back=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 0
        self.spacing = 0
        self._on_back = on_back
        self._analysis = None
        self._current_tab = 0

        # 背景
        with self.canvas.before:
            Color(*Theme.BG_PRIMARY)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        # ═══════════════════════════════════════
        #  顶部导航栏（返回 + 标题 + 收藏）
        # ═══════════════════════════════════════
        self.nav_bar = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=rsp_height(50),
            padding=rsp_padding((8, 4)),
        )

        back_btn = Button(
            text='← 返回',
            font_size=rsp_font(16),
            size_hint_x=0.20,
            background_normal='',
            background_color=(0, 0, 0, 0),
            color=Theme.ACCENT_BLUE,
            bold=True,
        )
        back_btn.bind(on_press=self._go_back)

        self.nav_title = Label(
            text='股票详情',
            font_size=rsp_font(18),
            bold=True,
            color=Theme.TEXT_PRIMARY,
            halign='center', valign='middle',
            size_hint_x=0.52,
            text_size=(None, None),
        )

        # 收藏按钮
        self.fav_btn = Button(
            text='☆',
            font_size=rsp_font(22),
            size_hint_x=0.14,
            background_normal='',
            background_color=(0, 0, 0, 0),
            color=Theme.TEXT_MUTED,
        )
        self.fav_btn.bind(on_press=self._toggle_favorite)

        spacer = Widget(size_hint_x=0.14)

        self.nav_bar.add_widget(back_btn)
        self.nav_bar.add_widget(self.nav_title)
        self.nav_bar.add_widget(self.fav_btn)
        self.nav_bar.add_widget(spacer)
        self.add_widget(self.nav_bar)

        # ═══════════════════════════════════════
        #  Tab 导航栏
        # ═══════════════════════════════════════
        self.tab_bar = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=rsp_height(42),
            padding=(rsp_spacing(12), 0),
            spacing=rsp_spacing(8),
        )
        self.tab_buttons: List[Button] = []
        for i, name in enumerate(self.TAB_NAMES):
            btn = Button(
                text=name,
                font_size=rsp_font(15),
                bold=True,
                background_normal='',
                background_color=Theme.BTN_PRIMARY if i == 0 else Theme.BG_ELEVATED,
                color=(1, 1, 1, 1) if i == 0 else Theme.TEXT_SECONDARY,
            )
            btn.bind(on_press=lambda inst, idx=i: self._switch_tab(idx))
            self.tab_buttons.append(btn)
            self.tab_bar.add_widget(btn)
        self.add_widget(self.tab_bar)

        # Tab 指示器条
        self.tab_indicator = Widget(size_hint_y=None, height=dp(2))
        with self.tab_indicator.canvas:
            Color(*Theme.ACCENT_BLUE)
            self._indicator_rect = Rectangle(
                pos=self.tab_indicator.pos,
                size=(self.tab_indicator.width / 3, dp(2)),
            )
        self.tab_indicator.bind(
            pos=self._update_indicator,
            size=self._update_indicator,
        )
        self.add_widget(self.tab_indicator)

        # ═══════════════════════════════════════
        #  内容区域（三Tab共享一个ScrollView）
        # ═══════════════════════════════════════
        self.scroll = ScrollView(
            bar_width=rsp_spacing(3),
            bar_color=(*Theme.ACCENT_BLUE[:3], 0.4),
        )
        self.content = GridLayout(
            cols=1,
            spacing=rsp_spacing(12),
            size_hint_y=None,
            padding=rsp_padding((14, 10, 14, 20)),
        )
        self.content.bind(minimum_height=self.content.setter('height'))
        self.scroll.add_widget(self.content)
        self.add_widget(self.scroll)

    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def _update_indicator(self, *args):
        tab_width = self.tab_indicator.width / 3
        self._indicator_rect.pos = (self.tab_indicator.x + self._current_tab * tab_width, self.tab_indicator.y)
        self._indicator_rect.size = (tab_width, dp(2))

    def _switch_tab(self, index: int):
        """切换Tab"""
        if index == self._current_tab:
            return
        self._current_tab = index
        
        # 更新按钮样式
        for i, btn in enumerate(self.tab_buttons):
            if i == index:
                btn.background_color = Theme.BTN_PRIMARY
                btn.color = (1, 1, 1, 1)
            else:
                btn.background_color = Theme.BG_ELEVATED
                btn.color = Theme.TEXT_SECONDARY
        
        self._update_indicator()
        
        # 重新渲染内容
        if self._analysis:
            self._render_current_tab()

    def show(self, analysis_result):
        """显示股票详情"""
        from utils.logger import AppLogger
        logger = AppLogger()
        
        try:
            self._analysis = analysis_result
            self.nav_title.text = getattr(analysis_result, 'display_name', '未知')
            
            # 更新收藏按钮状态
            code = getattr(analysis_result, 'code', '')
            self._update_fav_btn(code)
            
            self._render_current_tab()
            
            logger.info(f"[Detail] 详情页渲染完成: {self.nav_title.text}")
            Clock.schedule_once(lambda dt: self._animate_entry(), 0.1)
            
        except Exception as e:
            logger.error(f"[Detail] 详情页加载失败: {e}")
            self.content.clear_widgets()
            self._add_error_card('show', f"详情页加载失败: {str(e)[:100]}")
    
    def _update_fav_btn(self, code: str):
        """更新收藏按钮状态"""
        is_fav = fav_mgr.is_favorite(code) if code else False
        self.fav_btn.text = '★' if is_fav else '☆'
        self.fav_btn.color = Theme.ACCENT_ORANGE if is_fav else Theme.TEXT_MUTED
    
    def _toggle_favorite(self, *args):
        """切换收藏状态"""
        if not self._analysis:
            return
        code = getattr(self._analysis, 'code', '')
        name = getattr(self._analysis, 'name', '')
        if not code:
            return
        
        is_fav = fav_mgr.toggle(code, name)
        self._update_fav_btn(code)
        
        # 显示提示
        from kivy.uix.popup import Popup
        popup = Popup(
            title='',
            content=Label(
                text=f"{'已添加' if is_fav else '已移除'}自选: {code}",
                color=Theme.TEXT_PRIMARY,
                font_size=dp(14),
            ),
            size_hint=(0.5, 0.15),
            auto_dismiss=True,
            background_color=(0.1, 0.1, 0.12, 0.9),
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 1.0)

    def _render_current_tab(self):
        """渲染当前Tab内容"""
        self.content.clear_widgets()
        
        if self._current_tab == 0:
            self._build_restructuring_tab()
        elif self._current_tab == 1:
            self._build_quote_tab()
        else:
            self._build_related_tab()

    def _build_restructuring_tab(self):
        """Tab 1: 重整信息"""
        a = self._analysis
        if not a:
            return
        
        builders = [
            self._build_header,
            self._build_risks_section,
            self._build_recommendation,
            self._build_investor_section,
            self._build_timeline,
            self._build_notes,
        ]
        
        for builder in builders:
            try:
                builder(a)
            except Exception as e:
                self._add_error_card(builder.__name__, str(e)[:100])

    def _build_quote_tab(self):
        """Tab 2: 实时行情"""
        a = self._analysis
        if not a:
            return
        
        # 行情概览卡片
        self._build_quote_overview(a)
        
        # 五档盘口
        self._build_market_depth(a)
        
        # 资金流向（简化）
        self._build_fund_flow(a)

    def _build_related_tab(self):
        """Tab 3: 关联股票"""
        a = self._analysis
        if not a:
            return
        
        self._build_related_stocks(a)

    # ═══════════════════════════════════════
    #  Tab 1: 重整内容（从原有代码迁移）
    # ═══════════════════════════════════════

    def _build_header(self, a):
        """头部：价格 + 阶段"""
        card = self._make_card()

        row1 = BoxLayout(orientation='horizontal', size_hint_y=None, height=rsp_height(34))
        name = Label(
            text=getattr(a, 'display_name', '未知'),
            font_size=rsp_font(22), bold=True,
            color=Theme.TEXT_PRIMARY,
            halign='left', valign='middle',
            size_hint_x=0.6,
            text_size=(None, None),
        )

        # 价格颜色：红涨绿跌
        price_color = getattr(a, 'price_color', Theme.ACCENT_GREEN)
        price = Label(
            text=getattr(a, 'price_text', '价格未知'),
            font_size=rsp_font(22), bold=True,
            color=price_color,
            halign='right', valign='middle',
            size_hint_x=0.4,
            text_size=(None, None),
        )

        row1.add_widget(name)
        row1.add_widget(price)
        card.add_widget(row1)

        # 涨跌幅行
        row1_5 = BoxLayout(orientation='horizontal', size_hint_y=None, height=rsp_height(22))
        change_text = getattr(a, 'change_percent_text', '')
        change_color = price_color
        change_label = Label(
            text=change_text,
            font_size=rsp_font(15), bold=True,
            color=change_color,
            halign='left', valign='middle',
            size_hint_x=0.5,
        )
        
        turnover_text = getattr(a, 'turnover_rate_text', '')
        turnover_label = Label(
            text=turnover_text,
            font_size=rsp_font(13),
            color=Theme.TEXT_MUTED,
            halign='right', valign='middle',
            size_hint_x=0.5,
        )
        row1_5.add_widget(change_label)
        row1_5.add_widget(turnover_label)
        card.add_widget(row1_5)

        try:
            row2 = BoxLayout(orientation='horizontal', size_hint_y=None, height=rsp_height(26))
            badge = StageBadge(
                text=getattr(a, 'stage', '未知'),
                stage_type=getattr(a, 'recommendation_type', 'muted'),
            )
            row2.add_widget(badge)

            risk = Label(
                text=f"风险: {getattr(a, 'risk_level', '未知')}",
                font_size=rsp_font(13),
                color=Theme.TEXT_MUTED,
                halign='right', valign='middle',
                text_size=(None, None),
            )
            row2.add_widget(risk)
            card.add_widget(row2)
        except Exception:
            pass

        try:
            if a.market_cap:
                mc = Label(
                    text=f"市值: {a.market_cap:.1f} 亿",
                    font_size=rsp_font(14),
                    color=Theme.TEXT_SECONDARY,
                    halign='left', valign='middle',
                    size_hint_y=None, height=rsp_height(20),
                    text_size=(None, None),
                )
                card.add_widget(mc)
        except Exception:
            pass

        self.content.add_widget(card)

    def _build_risks_section(self, a):
        """严重风险提示区"""
        if getattr(a, 'risk_warnings', None):
            card = self._make_card(bg_color=(0.8, 0.2, 0.2, 0.1))
            self._add_section_title(card, '⚠️ 严重风险提示', color=Theme.ACCENT_RED)
            for warning in a.risk_warnings:
                w_lbl = Label(
                    text=f"• {warning}",
                    font_size=rsp_font(14),
                    color=Theme.ACCENT_RED,
                    halign='left', valign='top',
                    size_hint_y=None,
                    text_size=(None, None),
                )
                w_lbl.bind(texture_size=lambda inst, sz: setattr(inst, 'height', sz[1] + rsp_spacing(4)))
                card.add_widget(w_lbl)
            
            self.content.add_widget(card)

    def _build_recommendation(self, a):
        """投资建议区"""
        card = self._make_card()
        self._add_section_title(card, '投资建议')

        rec_type = getattr(a, 'recommendation_type', 'muted')
        accent = Theme.STAGE_COLORS.get(rec_type, Theme.TEXT_MUTED)

        try:
            rec_label = Label(
                text=getattr(a, 'recommendation', '暂无建议'),
                font_size=rsp_font(18), bold=True,
                color=accent,
                halign='left', valign='middle',
                size_hint_y=None, height=rsp_height(28),
                text_size=(None, None),
            )
            card.add_widget(rec_label)
        except Exception:
            pass

        try:
            score = getattr(a, 'investor_score', 0)
            score_bar = ScoreBar(score=score, label_text='投资人综合评分')
            card.add_widget(score_bar)
        except Exception:
            pass

        try:
            if a.asset_injection:
                inj = Label(
                    text=a.asset_injection,
                    font_size=rsp_font(14),
                    color=Theme.TEXT_SECONDARY,
                    halign='left', valign='middle',
                    size_hint_y=None, height=rsp_height(20),
                    text_size=(None, None),
                )
                card.add_widget(inj)
        except Exception:
            pass

        self.content.add_widget(card)

    def _build_investor_section(self, a):
        """投资人信息"""
        card = self._make_card()
        self._add_section_title(card, '投资人信息')
        
        has_industrial = getattr(a, 'has_industrial', False)
        industrial_name = getattr(a, 'industrial_name', '')
        industrial_background = getattr(a, 'industrial_background', '')
        applicant_count = getattr(a, 'applicant_count', 0)
        investor_summary = getattr(a, 'investor_summary', '')
        
        if has_industrial and industrial_name:
            self._add_kv_row(card, '产业投资人', industrial_name)
            if industrial_background:
                self._add_kv_row(card, '背景', industrial_background)
        else:
            self._add_kv_row(card, '产业投资人', '暂无')
        
        if applicant_count > 0:
            self._add_kv_row(card, '竞争情况', f"{applicant_count} 家申请")
        else:
            self._add_kv_row(card, '竞争情况', '暂无竞争')
        
        if investor_summary:
            try:
                det_lbl = Label(
                    text=f"摘要:\n{investor_summary}",
                    font_size=rsp_font(13),
                    color=Theme.TEXT_SECONDARY,
                    halign='left', valign='top',
                    size_hint_y=None,
                    text_size=(None, None),
                )
                det_lbl.bind(texture_size=lambda inst, sz: setattr(inst, 'height', sz[1] + rsp_spacing(10)))
                card.add_widget(det_lbl)
            except Exception:
                pass
        
        self.content.add_widget(card)

    def _build_timeline(self, a):
        """重整时间线"""
        history = getattr(a, 'history', None)
        if not history:
            return

        try:
            card = self._make_card()
            self._add_section_title(card, '重整历程')

            for i, event in enumerate(history):
                is_last = (i == len(history) - 1)
                event_row = BoxLayout(
                    orientation='horizontal',
                    size_hint_y=None,
                    height=rsp_height(38),
                    spacing=rsp_spacing(8),
                )

                date_label = Label(
                    text=getattr(event, 'date', ''),
                    font_size=rsp_font(12),
                    color=Theme.TEXT_MUTED,
                    size_hint_x=0.20,
                    halign='right', valign='middle',
                    text_size=(None, None),
                )

                dot = Widget(size_hint_x=None, width=rsp_spacing(18))
                dot_color = Theme.ACCENT_BLUE if is_last else Theme.TEXT_MUTED
                with dot.canvas:
                    Color(*dot_color)
                dot.bind(pos=lambda w, v, c=dot_color, last=is_last: self._draw_dot(w, c, last))

                stage_name = getattr(event, 'stage_name', '')
                event_text = getattr(event, 'event', '')
                desc_text = f"{stage_name}"
                if event_text:
                    desc_text += f"\n{event_text}"
                desc = Label(
                    text=desc_text,
                    font_size=rsp_font(13),
                    color=Theme.TEXT_PRIMARY if is_last else Theme.TEXT_SECONDARY,
                    halign='left', valign='middle',
                    size_hint_x=0.70,
                    text_size=(None, None),
                )

                event_row.add_widget(date_label)
                event_row.add_widget(dot)
                event_row.add_widget(desc)
                card.add_widget(event_row)

            self.content.add_widget(card)
        except Exception:
            pass

    def _draw_dot(self, widget, color, is_last):
        widget.canvas.clear()
        cx = widget.x + widget.width / 2
        cy = widget.y + widget.height / 2
        r = rsp_spacing(4) if is_last else dp(3)

        with widget.canvas:
            Color(*color)
            Ellipse(pos=(cx - r, cy - r), size=(r * 2, r * 2))

    def _build_notes(self, a):
        """备注"""
        if not getattr(a, 'notes', None):
            return

        card = self._make_card()
        self._add_section_title(card, '备注')

        notes = Label(
            text=a.notes,
            font_size=rsp_font(14),
            color=Theme.TEXT_SECONDARY,
            halign='left', valign='top',
            size_hint_y=None,
            height=rsp_height(40),
            text_size=(None, None),
        )
        card.add_widget(notes)
        self.content.add_widget(card)

    # ═══════════════════════════════════════
    #  Tab 2: 实时行情
    # ═══════════════════════════════════════

    def _build_quote_overview(self, a):
        """行情概览卡片"""
        card = self._make_card()
        self._add_section_title(card, '实时行情')
        
        price_color = getattr(a, 'price_color', Theme.TEXT_PRIMARY)
        
        # 价格大图
        price_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=rsp_height(40))
        price_label = Label(
            text=getattr(a, 'price_text', '¥0.00'),
            font_size=rsp_font(28), bold=True,
            color=price_color,
            halign='left', valign='middle',
            size_hint_x=0.5,
        )
        change_label = Label(
            text=getattr(a, 'change_percent_text', '0.00%'),
            font_size=rsp_font(18), bold=True,
            color=price_color,
            halign='right', valign='middle',
            size_hint_x=0.5,
        )
        price_row.add_widget(price_label)
        price_row.add_widget(change_label)
        card.add_widget(price_row)
        
        # 详细数据网格
        grid = GridLayout(cols=2, spacing=rsp_spacing(8), size_hint_y=None, height=rsp_height(120))
        
        fields = [
            ('今开', f"{getattr(a, 'open_price', 0):.2f}"),
            ('昨收', f"{getattr(a, 'prev_close', 0):.2f}"),
            ('最高', f"{getattr(a, 'high_price', 0):.2f}"),
            ('最低', f"{getattr(a, 'low_price', 0):.2f}"),
            ('成交量', f"{getattr(a, 'volume', 0):.0f} 手"),
            ('成交额', f"{getattr(a, 'amount', 0):.0f} 万"),
            ('换手率', f"{getattr(a, 'turnover_rate', 0):.2f}%"),
            ('振幅', f"{getattr(a, 'amplitude', 0):.2f}%"),
            ('市盈率', f"{getattr(a, 'pe_ratio', 0):.2f}"),
            ('市净率', f"{getattr(a, 'pb_ratio', 0):.2f}"),
        ]
        
        for label, value in fields:
            item = BoxLayout(orientation='horizontal', size_hint_y=None, height=rsp_height(22))
            item.add_widget(Label(
                text=label, font_size=rsp_font(12),
                color=Theme.TEXT_MUTED, size_hint_x=0.4,
                halign='left', valign='middle',
            ))
            item.add_widget(Label(
                text=value, font_size=rsp_font(13),
                color=Theme.TEXT_PRIMARY, size_hint_x=0.6,
                halign='right', valign='middle',
            ))
            grid.add_widget(item)
        
        card.add_widget(grid)
        self.content.add_widget(card)

    def _build_market_depth(self, a):
        """五档盘口（占位/模拟数据）"""
        card = self._make_card()
        self._add_section_title(card, '五档盘口')
        
        stock = getattr(a, 'stock', None)
        if stock and hasattr(stock, 'market_depth') and stock.market_depth.has_data:
            depth = stock.market_depth
            # 显示买卖五档
            grid = GridLayout(cols=2, spacing=rsp_spacing(6), size_hint_y=None, height=rsp_height(160))
            
            for i in range(5):
                # 卖5到卖1
                si = 4 - i
                if si < len(depth.sell5):
                    price, vol = depth.sell5[si]
                    grid.add_widget(Label(text=f"卖{si+1}", font_size=rsp_font(12), color=Theme.ACCENT_GREEN, halign='left'))
                    grid.add_widget(Label(text=f"{price:.2f}  {vol}", font_size=rsp_font(12), color=Theme.TEXT_PRIMARY, halign='right'))
            
            for i in range(5):
                # 买1到买5
                if i < len(depth.buy5):
                    price, vol = depth.buy5[i]
                    grid.add_widget(Label(text=f"买{i+1}", font_size=rsp_font(12), color=Theme.ACCENT_RED, halign='left'))
                    grid.add_widget(Label(text=f"{price:.2f}  {vol}", font_size=rsp_font(12), color=Theme.TEXT_PRIMARY, halign='right'))
            
            card.add_widget(grid)
        else:
            # 无数据提示
            card.add_widget(Label(
                text='五档盘口数据暂无',
                font_size=rsp_font(13),
                color=Theme.TEXT_MUTED,
                halign='center', valign='middle',
                size_hint_y=None, height=rsp_height(40),
            ))
        
        self.content.add_widget(card)

    def _build_fund_flow(self, a):
        """资金流向（简化展示）"""
        card = self._make_card()
        self._add_section_title(card, '资金流向')
        
        stock = getattr(a, 'stock', None)
        if stock and hasattr(stock, 'fund_flow') and stock.fund_flow.has_data:
            ff = stock.fund_flow
            
            # 主力资金
            main_color = Theme.ACCENT_RED if ff.main_force > 0 else Theme.ACCENT_GREEN
            main_sign = '+' if ff.main_force > 0 else ''
            self._add_kv_row(card, '主力资金', f"{main_sign}{ff.main_force:.0f} 万", value_color=main_color)
            
            self._add_kv_row(card, '大单', f"{ff.large:.0f} 万")
            self._add_kv_row(card, '中单', f"{ff.medium:.0f} 万")
            self._add_kv_row(card, '小单', f"{ff.small:.0f} 万")
        else:
            card.add_widget(Label(
                text='资金流向数据暂无',
                font_size=rsp_font(13),
                color=Theme.TEXT_MUTED,
                halign='center', valign='middle',
                size_hint_y=None, height=rsp_height(40),
            ))
        
        self.content.add_widget(card)

    # ═══════════════════════════════════════
    #  Tab 3: 关联股票
    # ═══════════════════════════════════════

    def _build_related_stocks(self, a):
        """同类股票对比"""
        card = self._make_card()
        self._add_section_title(card, '同类股票对比')
        
        stage_code = getattr(a, 'stage_code', '')
        stage_name = getattr(a, 'stage', '未知')
        
        # 阶段说明
        card.add_widget(Label(
            text=f"当前阶段: {stage_name}",
            font_size=rsp_font(14),
            color=Theme.TEXT_SECONDARY,
            halign='left', valign='middle',
            size_hint_y=None, height=rsp_height(22),
        ))
        
        # 获取同类股票（通过 analyzer，需要从外部传入或全局获取）
        # 这里使用简化的展示：提示用户
        card.add_widget(Label(
            text='同类股票对比功能需要全局股票列表支持\n将在后续版本中完善',
            font_size=rsp_font(13),
            color=Theme.TEXT_MUTED,
            halign='center', valign='middle',
            size_hint_y=None, height=rsp_height(60),
        ))
        
        self.content.add_widget(card)
    
    # ═══════════════════════════════════════
    #  通用辅助方法
    # ═══════════════════════════════════════

    def _animate_entry(self):
        """入场动画"""
        children = list(reversed(self.content.children))
        AnimationHelper.staggered_fade_in(children, base_delay=0.05, duration=0.3)

    def _add_error_card(self, section_name: str, error: str):
        card = self._make_card()
        lbl = Label(
            text=f"[{section_name}] 数据加载异常: {error}",
            font_size=rsp_font(13),
            color=Theme.TEXT_MUTED,
            halign='left', valign='middle',
            size_hint_y=None,
            text_size=(None, None),
        )
        lbl.bind(texture_size=lambda inst, sz: setattr(inst, 'height', sz[1] + rsp_spacing(8)))
        card.add_widget(lbl)
        self.content.add_widget(card)

    def _make_card(self, bg_color=None):
        """创建卡片容器"""
        bg = bg_color or Theme.BG_SECONDARY
        card = GridLayout(
            cols=1,
            size_hint_y=None,
            padding=(rsp_spacing(14), rsp_spacing(12)),
            spacing=rsp_spacing(6),
        )
        card.bind(minimum_height=card.setter('height'))

        with card.canvas.before:
            Color(*bg)
            card._bg = RoundedRectangle(
                pos=card.pos, size=card.size,
                radius=[dp(12)],
            )
            # 阴影
            Color(0, 0, 0, 0.1)
            RoundedRectangle(
                pos=(card.x + dp(1), card.y - dp(2)),
                size=card.size,
                radius=[dp(12)],
            )
        card.bind(
            pos=lambda w, v: setattr(w._bg, 'pos', v),
            size=lambda w, v: setattr(w._bg, 'size', v),
        )
        return card

    def _add_section_title(self, parent, text, color=None):
        title = Label(
            text=text,
            font_size=rsp_font(16),
            bold=True,
            color=color or Theme.ACCENT_BLUE,
            halign='left', valign='middle',
            size_hint_y=None,
            height=rsp_height(24),
            text_size=(None, None),
        )
        parent.add_widget(title)

    def _add_kv_row(self, parent, key, value, value_color=None):
        row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=rsp_height(22),
        )
        key_label = Label(
            text=key,
            font_size=rsp_font(13),
            color=Theme.TEXT_MUTED,
            halign='left', valign='middle',
            size_hint_x=0.35,
            text_size=(None, None),
        )

        val_label = Label(
            text=str(value),
            font_size=rsp_font(13),
            color=value_color or Theme.TEXT_PRIMARY,
            halign='left', valign='middle',
            size_hint_x=0.65,
            text_size=(None, None),
        )

        row.add_widget(key_label)
        row.add_widget(val_label)
        parent.add_widget(row)

    def _go_back(self, *args):
        if self._on_back:
            self._on_back()
