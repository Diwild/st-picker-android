"""
ST选股工具 - 筛选面板组件 v2.0
现代化设计，流畅的展开/收起动画
"""

from typing import Optional, Callable
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.properties import BooleanProperty
from kivy.clock import Clock

from core.constants import Theme, FILTER_STAGE_OPTIONS, SORT_OPTIONS
from utils.safe_eval import SafeExpressionEvaluator
from utils.logger import AppLogger
from ui.responsive import responsive, rsp_font, rsp_height, rsp_spacing
from ui.animations import AnimationHelper


logger = AppLogger()
_expr_validator = SafeExpressionEvaluator()


class ToggleButtonWidget(Button):
    """自定义切换按钮 - 确保 toggle 事件可靠触发"""
    filter_panel = None
    _touch_handled = False
    
    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            self._touch_handled = True
            self._trigger_toggle()
            return True
        return super().on_touch_down(touch)
    
    def _trigger_toggle(self):
        if self.filter_panel:
            Clock.schedule_once(lambda dt: self.filter_panel.toggle(), 0)
    
    def on_touch_up(self, touch):
        if self._touch_handled:
            self._touch_handled = False
            return True
        return super().on_touch_up(touch)
    
    def on_press(self):
        self._trigger_toggle()
        return super().on_press()


class FilterPanel(BoxLayout):
    """可折叠筛选面板 v2.0"""

    is_expanded = BooleanProperty(False)

    def __init__(self, on_filter_apply=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.spacing = rsp_spacing(8)
        self.padding = 0
        self._on_filter_apply = on_filter_apply
        self._target_height = rsp_height(340)

        self.height = rsp_height(46)
        self.opacity = 1

        # ── 折叠头部按钮 ──
        self.toggle_btn = ToggleButtonWidget(
            text='▼  筛选条件',
            font_size=rsp_font(15),
            size_hint_y=None,
            height=rsp_height(46),
            background_normal='',
            background_color=Theme.BG_ELEVATED,
            color=Theme.ACCENT_BLUE,
            bold=True,
        )
        self.toggle_btn.filter_panel = self
        self.add_widget(self.toggle_btn)

        self.content = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=0,
            opacity=0,
            disabled=True,
            padding=(rsp_spacing(14), rsp_spacing(10), rsp_spacing(14), rsp_spacing(10)),
            spacing=rsp_spacing(10),
        )

        # 阶段筛选
        stage_row = self._make_row('重整阶段')
        self.stage_spinner = Spinner(
            text='最佳介入点',
            values=list(FILTER_STAGE_OPTIONS.keys()),
            size_hint_x=0.65,
            height=rsp_height(38),
            size_hint_y=None,
            background_normal='',
            background_color=Theme.BG_ELEVATED,
            color=Theme.TEXT_PRIMARY,
        )
        stage_row.add_widget(self.stage_spinner)
        self.content.add_widget(stage_row)

        # 价格区间
        price_row = self._make_row('价格区间')
        self.min_price = TextInput(
            text='0', multiline=False,
            input_filter='float',
            size_hint_x=0.25,
            height=rsp_height(38), size_hint_y=None,
            background_color=Theme.BG_ELEVATED,
            foreground_color=Theme.TEXT_PRIMARY,
            cursor_color=Theme.ACCENT_BLUE,
            padding=(rsp_spacing(8), rsp_spacing(8)),
        )
        dash_label = Label(
            text='—', color=Theme.TEXT_MUTED,
            size_hint_x=0.1, font_size=rsp_font(15),
        )
        self.max_price = TextInput(
            text='50', multiline=False,
            input_filter='float',
            size_hint_x=0.25,
            height=rsp_height(38), size_hint_y=None,
            background_color=Theme.BG_ELEVATED,
            foreground_color=Theme.TEXT_PRIMARY,
            cursor_color=Theme.ACCENT_BLUE,
            padding=(rsp_spacing(8), rsp_spacing(8)),
        )
        price_row.add_widget(self.min_price)
        price_row.add_widget(dash_label)
        price_row.add_widget(self.max_price)
        self.content.add_widget(price_row)

        # 涨跌幅区间
        change_row = self._make_row('涨跌幅(%)')
        self.min_change = TextInput(
            text='-20', multiline=False,
            input_filter='float',
            size_hint_x=0.25,
            height=rsp_height(38), size_hint_y=None,
            background_color=Theme.BG_ELEVATED,
            foreground_color=Theme.TEXT_PRIMARY,
            cursor_color=Theme.ACCENT_BLUE,
            padding=(rsp_spacing(8), rsp_spacing(8)),
        )
        dash_label2 = Label(
            text='—', color=Theme.TEXT_MUTED,
            size_hint_x=0.1, font_size=rsp_font(15),
        )
        self.max_change = TextInput(
            text='20', multiline=False,
            input_filter='float',
            size_hint_x=0.25,
            height=rsp_height(38), size_hint_y=None,
            background_color=Theme.BG_ELEVATED,
            foreground_color=Theme.TEXT_PRIMARY,
            cursor_color=Theme.ACCENT_BLUE,
            padding=(rsp_spacing(8), rsp_spacing(8)),
        )
        change_row.add_widget(self.min_change)
        change_row.add_widget(dash_label2)
        change_row.add_widget(self.max_change)
        self.content.add_widget(change_row)

        # 换手率区间
        turnover_row = self._make_row('换手率(%)')
        self.min_turnover = TextInput(
            text='0', multiline=False,
            input_filter='float',
            size_hint_x=0.25,
            height=rsp_height(38), size_hint_y=None,
            background_color=Theme.BG_ELEVATED,
            foreground_color=Theme.TEXT_PRIMARY,
            cursor_color=Theme.ACCENT_BLUE,
            padding=(rsp_spacing(8), rsp_spacing(8)),
        )
        dash_label3 = Label(
            text='—', color=Theme.TEXT_MUTED,
            size_hint_x=0.1, font_size=rsp_font(15),
        )
        self.max_turnover = TextInput(
            text='30', multiline=False,
            input_filter='float',
            size_hint_x=0.25,
            height=rsp_height(38), size_hint_y=None,
            background_color=Theme.BG_ELEVATED,
            foreground_color=Theme.TEXT_PRIMARY,
            cursor_color=Theme.ACCENT_BLUE,
            padding=(rsp_spacing(8), rsp_spacing(8)),
        )
        turnover_row.add_widget(self.min_turnover)
        turnover_row.add_widget(dash_label3)
        turnover_row.add_widget(self.max_turnover)
        self.content.add_widget(turnover_row)

        # 产业投资人 + 自选（同一行）
        check_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=rsp_height(38),
            spacing=rsp_spacing(8),
        )
        
        # 产业投资人
        inv_label = Label(
            text='仅产业投资人',
            font_size=rsp_font(14),
            color=Theme.TEXT_SECONDARY,
            size_hint_x=0.28,
            halign='left', valign='middle',
            text_size=(None, None),
        )
        inv_check_container = BoxLayout(size_hint_x=0.12, padding=(rsp_spacing(4), 0))
        with inv_check_container.canvas.before:
            Color(*Theme.BG_ELEVATED)
            inv_check_container._bg = RoundedRectangle(
                pos=inv_check_container.pos,
                size=(rsp_height(28), rsp_height(28)),
                radius=[dp(6)],
            )
        inv_check_container.bind(
            pos=lambda w, v: setattr(w._bg, 'pos', (v[0] + rsp_spacing(4), v[1] + (w.height - rsp_height(28)) / 2)),
            size=lambda w, v: setattr(w._bg, 'size', (rsp_height(28), rsp_height(28))),
        )
        self.investor_check = CheckBox(
            active=False,
            size_hint=(None, None),
            size=(rsp_height(28), rsp_height(28)),
            color=Theme.ACCENT_BLUE,
        )
        inv_check_container.add_widget(self.investor_check)
        
        # 自选
        fav_label = Label(
            text='仅自选',
            font_size=rsp_font(14),
            color=Theme.TEXT_SECONDARY,
            size_hint_x=0.20,
            halign='right', valign='middle',
            text_size=(None, None),
        )
        fav_check_container = BoxLayout(size_hint_x=0.12, padding=(rsp_spacing(4), 0))
        with fav_check_container.canvas.before:
            Color(*Theme.BG_ELEVATED)
            fav_check_container._bg = RoundedRectangle(
                pos=fav_check_container.pos,
                size=(rsp_height(28), rsp_height(28)),
                radius=[dp(6)],
            )
        fav_check_container.bind(
            pos=lambda w, v: setattr(w._bg, 'pos', (v[0] + rsp_spacing(4), v[1] + (w.height - rsp_height(28)) / 2)),
            size=lambda w, v: setattr(w._bg, 'size', (rsp_height(28), rsp_height(28))),
        )
        self.favorite_check = CheckBox(
            active=False,
            size_hint=(None, None),
            size=(rsp_height(28), rsp_height(28)),
            color=Theme.ACCENT_BLUE,
        )
        fav_check_container.add_widget(self.favorite_check)
        
        check_row.add_widget(inv_label)
        check_row.add_widget(inv_check_container)
        check_row.add_widget(fav_label)
        check_row.add_widget(fav_check_container)
        self.content.add_widget(check_row)

        # 关键字搜索
        keyword_row = self._make_row('搜索')
        self.keyword_input = TextInput(
            hint_text='代码/名称',
            multiline=False,
            size_hint_x=0.65,
            height=rsp_height(38), size_hint_y=None,
            background_color=Theme.BG_ELEVATED,
            foreground_color=Theme.TEXT_PRIMARY,
            cursor_color=Theme.ACCENT_BLUE,
            hint_text_color=Theme.TEXT_MUTED,
            padding=(rsp_spacing(8), rsp_spacing(8)),
        )
        keyword_row.add_widget(self.keyword_input)
        self.content.add_widget(keyword_row)

        # 快捷策略
        preset_row = BoxLayout(
            orientation='horizontal', 
            size_hint_y=None, 
            height=rsp_height(38), 
            spacing=rsp_spacing(8)
        )
        preset_label = Label(
            text='快捷规则', 
            font_size=rsp_font(14), 
            color=Theme.TEXT_SECONDARY, 
            size_hint_x=0.22, 
            halign='left', valign='middle', 
            text_size=(None, None)
        )
        preset_row.add_widget(preset_label)
        
        preset_grid = GridLayout(cols=4, size_hint_x=0.78, spacing=rsp_spacing(5))
        
        presets = [
            ("无硬伤", "not has_audit_risk and not has_financial_risk and not has_delisting_risk"),
            ("无违规", "not has_illegal_guarantee"),
            ("有产业大佬", "has_industrial"),
            ("竞争热拍", "applicants >= 3")
        ]
        
        for name, expr in presets:
            btn = Button(
                text=name, size_hint_y=None, height=rsp_height(38),
                background_normal='', background_color=Theme.BG_ELEVATED, 
                color=Theme.ACCENT_BLUE, font_size=rsp_font(12)
            )
            btn.bind(on_press=lambda inst, expr=expr: self._apply_preset_expr(expr))
            preset_grid.add_widget(btn)
            
        preset_row.add_widget(preset_grid)
        self.content.add_widget(preset_row)

        # 高级表达式搜索
        expr_row = self._make_row('策略公式')
        
        expr_input_container = BoxLayout(
            orientation='horizontal',
            size_hint_x=0.65,
            spacing=rsp_spacing(4),
        )
        
        self.expr_input = TextInput(
            hint_text='例: price < 3 and score > 50',
            multiline=False,
            size_hint_x=0.85,
            height=rsp_height(38), size_hint_y=None,
            background_color=Theme.BG_ELEVATED,
            foreground_color=Theme.TEXT_PRIMARY,
            cursor_color=Theme.ACCENT_BLUE,
            hint_text_color=Theme.TEXT_MUTED,
            padding=(rsp_spacing(8), rsp_spacing(8)),
        )
        self.expr_input.bind(text=self._on_expr_text_changed)
        
        self.expr_status = Label(
            text='',
            font_size=rsp_font(13),
            size_hint_x=0.15,
            halign='center', valign='middle',
        )
        
        expr_input_container.add_widget(self.expr_input)
        expr_input_container.add_widget(self.expr_status)
        expr_row.add_widget(expr_input_container)
        self.content.add_widget(expr_row)
        
        # 表达式帮助文本
        help_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=rsp_height(18),
            padding=(rsp_spacing(4), 0),
        )
        self.expr_help = Label(
            text='可用: price, score, change_percent, turnover_rate, pe_ratio, has_industrial...',
            font_size=rsp_font(11),
            color=Theme.TEXT_MUTED,
            halign='left', valign='middle',
            text_size=(None, None),
        )
        help_row.add_widget(Label(size_hint_x=0.35))
        help_row.add_widget(self.expr_help)
        self.content.add_widget(help_row)

        # 按钮行
        btn_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=rsp_height(44),
            spacing=rsp_spacing(10),
        )
        apply_btn = Button(
            text='应用筛选',
            font_size=rsp_font(15),
            bold=True,
            background_normal='',
            background_color=Theme.BTN_PRIMARY,
            color=(1, 1, 1, 1),
        )
        apply_btn.bind(on_press=self._apply)

        reset_btn = Button(
            text='重置',
            font_size=rsp_font(15),
            background_normal='',
            background_color=Theme.BG_ELEVATED,
            color=Theme.TEXT_SECONDARY,
        )
        reset_btn.bind(on_press=self._reset)

        btn_row.add_widget(apply_btn)
        btn_row.add_widget(reset_btn)
        self.content.add_widget(btn_row)

        # 重要：先添加content，再重新添加toggle_btn到最上层
        self.add_widget(self.content)
        self.remove_widget(self.toggle_btn)
        self.add_widget(self.toggle_btn)

        # 绘制背景
        self.content.bind(pos=self._draw_content_bg, size=self._draw_content_bg)

    def _make_row(self, label_text):
        row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=rsp_height(38),
            spacing=rsp_spacing(8),
        )
        label = Label(
            text=label_text,
            font_size=rsp_font(14),
            color=Theme.TEXT_SECONDARY,
            size_hint_x=0.35,
            halign='left', valign='middle',
            text_size=(None, None),
        )
        row.add_widget(label)
        return row

    def toggle(self, *args):
        """展开/收起筛选面板"""
        if self.is_expanded:
            self._collapse()
        else:
            self._expand()
        self.is_expanded = not self.is_expanded

    def _expand(self):
        """展开 - 增强动画"""
        self.content.disabled = False
        content_h = self._target_height
        
        anim_self = Animation(
            height=rsp_height(46) + content_h, 
            duration=0.35, 
            t='out_back'
        )
        anim_self.start(self)

        anim_content = Animation(
            height=content_h, 
            opacity=1, 
            duration=0.3, 
            t='out_quad'
        )
        anim_content.start(self.content)
        
        Clock.schedule_once(lambda dt: self._animate_children_appear(), 0.05)

        self.toggle_btn.text = '▲  收起筛选条件'
        self.toggle_btn.background_color = Theme.BG_TERTIARY

    def _animate_children_appear(self):
        """子元素依次出现动画"""
        children = list(reversed(self.content.children))
        for i, child in enumerate(children):
            if hasattr(child, 'opacity'):
                child.opacity = 0
                anim = Animation(opacity=1, duration=0.2, t='out_quad')
                Clock.schedule_once(lambda dt, c=child, a=anim: a.start(c), i * 0.02)

    def _collapse(self):
        """收起 - 增强动画"""
        self.content.disabled = True
        
        anim_content = Animation(
            height=0, 
            opacity=0, 
            duration=0.25, 
            t='in_quad'
        )
        anim_content.start(self.content)
        
        anim_self = Animation(
            height=rsp_height(46), 
            duration=0.3, 
            t='in_out_quad'
        )
        anim_self.start(self)

        self.toggle_btn.text = '▼  筛选条件'
        self.toggle_btn.background_color = Theme.BG_ELEVATED

    def _draw_content_bg(self, *args):
        if self.content.height <= 0:
            return
        self.content.canvas.before.clear()
        with self.content.canvas.before:
            Color(*Theme.BG_SECONDARY)
            RoundedRectangle(
                pos=self.content.pos,
                size=self.content.size,
                radius=[0, 0, dp(12), dp(12)],
            )

    def get_filters(self) -> dict:
        """获取当前筛选条件"""
        stage_key = self.stage_spinner.text
        stage_value = FILTER_STAGE_OPTIONS.get(stage_key, 'all')

        filters = {'stage': stage_value}

        # 价格区间
        try:
            min_p = float(self.min_price.text) if self.min_price.text else None
            if min_p is not None and min_p > 0:
                filters['min_price'] = min_p
        except ValueError:
            pass

        try:
            max_p = float(self.max_price.text) if self.max_price.text else None
            if max_p is not None:
                filters['max_price'] = max_p
        except ValueError:
            pass

        # 涨跌幅区间
        try:
            min_c = float(self.min_change.text) if self.min_change.text else None
            if min_c is not None:
                filters['min_change_percent'] = min_c
        except ValueError:
            pass

        try:
            max_c = float(self.max_change.text) if self.max_change.text else None
            if max_c is not None:
                filters['max_change_percent'] = max_c
        except ValueError:
            pass

        # 换手率区间
        try:
            min_t = float(self.min_turnover.text) if self.min_turnover.text else None
            if min_t is not None and min_t > 0:
                filters['min_turnover_rate'] = min_t
        except ValueError:
            pass

        try:
            max_t = float(self.max_turnover.text) if self.max_turnover.text else None
            if max_t is not None:
                filters['max_turnover_rate'] = max_t
        except ValueError:
            pass

        # 产业投资人
        if self.investor_check.active:
            filters['has_industrial'] = True

        # 自选
        if self.favorite_check.active:
            filters['only_favorites'] = True
            from core.favorites import fav_mgr
            filters['favorite_codes'] = fav_mgr.get_all()

        keyword = self.keyword_input.text.strip()
        if keyword:
            filters['keyword'] = keyword

        strategy_expr = self.expr_input.text.strip()
        if strategy_expr:
            is_valid, error = self._validate_with_context(strategy_expr)
            if is_valid:
                filters['strategy_expr'] = strategy_expr
            else:
                filters['strategy_expr'] = strategy_expr
                filters['_expr_error'] = error
                logger.warning(f"策略表达式验证失败: {error}")

        return filters

    def _on_expr_text_changed(self, instance, value):
        if not value.strip():
            self.expr_status.text = ''
            self.expr_input.foreground_color = Theme.TEXT_PRIMARY
            return
        Clock.unschedule(self._validate_expr)
        Clock.schedule_once(self._validate_expr, 0.5)
    
    def _validate_expr(self, dt):
        expr = self.expr_input.text.strip()
        if not expr:
            return
        is_valid, error = self._validate_with_context(expr)
        if is_valid:
            self.expr_status.text = '✓'
            self.expr_status.color = Theme.ACCENT_GREEN
            self.expr_input.foreground_color = Theme.TEXT_PRIMARY
        else:
            self.expr_status.text = '✗'
            self.expr_status.color = Theme.ACCENT_RED
            self.expr_input.foreground_color = Theme.ACCENT_RED
    
    def _validate_with_context(self, expr: str) -> tuple:
        is_valid, error = _expr_validator.validate_expression(expr)
        if not is_valid:
            return (False, error)
        
        allowed_vars = {
            'price', 'score', 'market_cap', 'stage', 'stage_code', 'risk',
            'has_industrial', 'has_industry', 'applicants',
            'has_audit_risk', 'has_financial_risk', 'has_illegal_guarantee', 'has_delisting_risk',
            'True', 'False', 'None'
        }
        
        try:
            import ast
            tree = ast.parse(expr.strip(), mode='eval')
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    if node.id not in allowed_vars:
                        return (False, f"未知变量: {node.id}")
        except SyntaxError as e:
            return (False, f"语法错误: {e}")
        except Exception as e:
            return (False, str(e))
        
        return (True, None)
    
    def _show_message(self, title: str, message: str) -> None:
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        from kivy.metrics import dp
        
        popup = Popup(
            title=title,
            content=Label(text=str(message), color=Theme.TEXT_PRIMARY, font_size=dp(15)),
            size_hint=(0.8, 0.3),
            auto_dismiss=True,
            separator_color=Theme.DIVIDER,
            title_color=Theme.TEXT_PRIMARY,
        )
        popup.open()

    def _apply_preset_expr(self, expr):
        self.expr_input.text = expr
        is_valid, error = self._validate_with_context(expr)
        if not is_valid:
            logger.warning(f"预设表达式验证失败: {error}")
            self.expr_status.text = '✗'
            self.expr_status.color = Theme.ACCENT_RED
            self.expr_input.foreground_color = Theme.ACCENT_RED
            self._show_message("策略公式错误", f"表达式验证失败:\n{error}")
            return
        
        self.expr_status.text = '✓'
        self.expr_status.color = Theme.ACCENT_GREEN
        self.expr_input.foreground_color = Theme.TEXT_PRIMARY
        
        if '全部' in FILTER_STAGE_OPTIONS:
            self.stage_spinner.text = '全部'
        else:
            self.stage_spinner.text = list(FILTER_STAGE_OPTIONS.keys())[0]
        self.min_price.text = '0'
        self.max_price.text = '50'
        self.min_change.text = '-20'
        self.max_change.text = '20'
        self.min_turnover.text = '0'
        self.max_turnover.text = '30'
        self.investor_check.active = False
        self.favorite_check.active = False
        self.keyword_input.text = ''
        self._apply()

    def _apply(self, *args):
        if self._on_filter_apply:
            self._on_filter_apply(self.get_filters())

    def _reset(self, *args):
        if '全部' in FILTER_STAGE_OPTIONS:
            self.stage_spinner.text = '全部'
        else:
            self.stage_spinner.text = list(FILTER_STAGE_OPTIONS.keys())[0]
        self.min_price.text = '0'
        self.max_price.text = '50'
        self.min_change.text = '-20'
        self.max_change.text = '20'
        self.min_turnover.text = '0'
        self.max_turnover.text = '30'
        self.investor_check.active = False
        self.favorite_check.active = False
        self.keyword_input.text = ''
        self.expr_input.text = ''
        self.expr_status.text = ''
        self.expr_input.foreground_color = Theme.TEXT_PRIMARY
        if self._on_filter_apply:
            self._on_filter_apply({'stage': 'all'})
