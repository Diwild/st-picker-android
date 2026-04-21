"""
ST选股工具 - 主屏幕 v2.0
现代化设计，带流畅动画和优化布局
"""

from typing import Optional, Callable, Any
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import BooleanProperty, StringProperty, NumericProperty
from kivy.core.window import Window

from core.constants import Theme, REMOTE_JSON_URL
from core.analyzer import StockAnalyzer
from core.data_manager import DataManager
from core.favorites import fav_mgr
from ui.theme_manager import theme_mgr
from utils.logger import AppLogger as _AppLogger
logger = _AppLogger()
from ui.widgets.stock_card import StockCard
from ui.widgets.filter_panel import FilterPanel
from ui.responsive import responsive, rsp_font, rsp_height, rsp_spacing, rsp_padding
from ui.animations import AnimationHelper


class PullToRefreshScrollView(RelativeLayout):
    """支持下拉刷新的滚动容器"""
    refresh_trigger_distance = NumericProperty(dp(80))
    
    SCROLLVIEW_PROPS = {
        'bar_width', 'bar_color', 'bar_inactive_color', 'bar_margin',
        'scroll_distance', 'scroll_timeout', 'scroll_type',
        'effect_cls', 'effect_x', 'effect_y',
        'do_scroll_x', 'do_scroll_y', 'scroll_x', 'scroll_y',
    }
    
    def __init__(self, on_refresh=None, **kwargs):
        self.on_refresh = on_refresh
        self._is_refreshing = False
        self._refresh_indicator = None
        
        scrollview_kwargs = {'pos_hint': {'x': 0, 'y': 0}, 'size_hint': (1, 1)}
        for prop in self.SCROLLVIEW_PROPS:
            if prop in kwargs:
                scrollview_kwargs[prop] = kwargs.pop(prop)
        
        super().__init__(**kwargs)
        
        self._scroll_view = ScrollView(**scrollview_kwargs)
        super().add_widget(self._scroll_view)
    
    @property
    def scroll_y(self):
        return self._scroll_view.scroll_y
    
    def add_widget(self, widget, index=0):
        self._scroll_view.add_widget(widget, index)
    
    def remove_widget(self, widget):
        self._scroll_view.remove_widget(widget)
    
    def clear_widgets(self):
        self._scroll_view.clear_widgets()
    
    def finish_refresh(self):
        self._is_refreshing = False


class MainScreen(BoxLayout):
    """主屏幕 - 股票列表 v2.0"""
    
    is_refreshing = BooleanProperty(False)
    refresh_status = StringProperty('')

    def __init__(self, on_stock_select: Optional[Callable] = None, **kwargs: Any):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = (rsp_spacing(12), rsp_spacing(8), rsp_spacing(12), rsp_spacing(8))
        self.spacing = rsp_spacing(10)
        self._on_stock_select = on_stock_select

        # 数据层
        self.data_manager = DataManager()
        self._init_data_layer()
        
        self.current_filters = {'stage': 'best'}
        self._refresh_timer = None

        # 绘制背景
        with self.canvas.before:
            Color(*Theme.BG_PRIMARY)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        # ══════════════════════════════════════
        #  标题栏
        # ══════════════════════════════════════
        title_bar = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=rsp_height(48),
            padding=(rsp_spacing(4), 0),
        )
        title_label = Label(
            text='ST重整选股工具',
            font_size=rsp_font(22),
            bold=True,
            color=Theme.TEXT_PRIMARY,
            halign='left', valign='middle',
            size_hint_x=0.40,
            text_size=(None, None),
        )

        self.loading_spinner = Label(
            text='',
            font_size=rsp_font(12),
            color=Theme.ACCENT_BLUE,
            halign='center', valign='middle',
            size_hint_x=0.18,
            text_size=(None, None),
        )

        # 自选数量徽章
        self.fav_badge = Button(
            text=f'★ {fav_mgr.get_count()}',
            font_size=rsp_font(12),
            size_hint_x=0.13,
            background_normal='',
            background_color=(0, 0, 0, 0),
            color=Theme.ACCENT_ORANGE,
        )
        self.fav_badge.bind(on_press=self._show_favorites_filter)

        # 主题切换按钮
        self.theme_btn = Button(
            text='🌙',
            font_size=rsp_font(16),
            size_hint_x=0.09,
            background_normal='',
            background_color=(0, 0, 0, 0),
            color=Theme.TEXT_MUTED,
        )
        self.theme_btn.bind(on_press=self._toggle_theme)

        # 数据更新按钮
        self.update_btn = Button(
            text='🔄',
            font_size=rsp_font(14),
            size_hint_x=0.09,
            background_normal='',
            background_color=(0, 0, 0, 0),
            color=Theme.ACCENT_GREEN,
        )
        self.update_btn.bind(on_press=self._on_data_update_click)

        self.stats_badge = Label(
            text='',
            font_size=rsp_font(13),
            color=Theme.ACCENT_BLUE,
            halign='right', valign='middle',
            size_hint_x=0.11,
            text_size=(None, None),
        )

        title_bar.add_widget(title_label)
        title_bar.add_widget(self.loading_spinner)
        title_bar.add_widget(self.fav_badge)
        title_bar.add_widget(self.theme_btn)
        title_bar.add_widget(self.update_btn)
        title_bar.add_widget(self.stats_badge)
        self.add_widget(title_bar)

        # 数据来源状态栏
        meta_bar = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=rsp_height(18),
        )
        self.meta_label = Label(
            text=self._get_meta_text(),
            font_size=rsp_font(12),
            color=Theme.TEXT_MUTED,
            halign='left', valign='middle',
            text_size=(None, None),
        )
        meta_bar.add_widget(self.meta_label)
        self.add_widget(meta_bar)

        # ══════════════════════════════════════
        #  筛选面板
        # ══════════════════════════════════════
        self.filter_panel = FilterPanel(on_filter_apply=self._on_filter_apply)
        self.add_widget(self.filter_panel)

        # ══════════════════════════════════════
        #  统计信息条
        # ══════════════════════════════════════
        self.stats_bar = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=rsp_height(26),
            padding=(rsp_spacing(4), 0),
        )
        self.stats_label = Label(
            text='加载中...',
            font_size=rsp_font(14),
            color=Theme.TEXT_SECONDARY,
            halign='left', valign='middle',
            text_size=(None, None),
        )
        self.stats_bar.add_widget(self.stats_label)
        self.add_widget(self.stats_bar)

        # ══════════════════════════════════════
        #  股票列表
        # ══════════════════════════════════════
        self.scroll_view = PullToRefreshScrollView(
            on_refresh=self._on_pull_refresh,
            bar_width=rsp_spacing(3),
            bar_color=(*Theme.ACCENT_BLUE[:3], 0.4),
            bar_inactive_color=(*Theme.ACCENT_BLUE[:3], 0.15),
            scroll_type=['bars', 'content'],
            effect_cls='ScrollEffect',
            scroll_distance=rsp_spacing(20),
        )

        self.list_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=rsp_height(100),
        )
        self.list_container.bind(minimum_height=self.list_container.setter('height'))

        self.stock_list = GridLayout(
            cols=1,
            spacing=rsp_spacing(10),
            size_hint_y=None,
            padding=(0, dp(4)),
        )
        self.stock_list.bind(minimum_height=self.stock_list.setter('height'))
        
        self.list_container.add_widget(self.stock_list)
        self.scroll_view.add_widget(self.list_container)
        self.add_widget(self.scroll_view)

        # ── 底部操作栏 ──
        bottom_bar = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=rsp_height(44),
            spacing=rsp_spacing(10),
            padding=(rsp_spacing(4), 0),
        )

        self.refresh_btn = Button(
            text='🔄 行情刷新',
            font_size=rsp_font(13),
            bold=True,
            background_normal='',
            background_color=Theme.BTN_PRIMARY,
            color=(1, 1, 1, 1),
        )
        self.refresh_btn.bind(on_press=self._on_quote_refresh_click)

        self.auto_refresh_btn = Button(
            text='⏸ 自动',
            font_size=rsp_font(13),
            background_normal='',
            background_color=Theme.BG_ELEVATED,
            color=Theme.TEXT_SECONDARY,
        )
        self.auto_refresh_btn.bind(on_press=self._toggle_auto_refresh)
        self._auto_refresh_enabled = False

        export_btn = Button(
            text='⬇ 导出',
            font_size=rsp_font(13),
            background_normal='',
            background_color=Theme.BG_ELEVATED,
            color=Theme.TEXT_PRIMARY,
        )
        export_btn.bind(on_press=self._export_data)

        bottom_bar.add_widget(self.refresh_btn)
        bottom_bar.add_widget(self.auto_refresh_btn)
        bottom_bar.add_widget(export_btn)

        self.add_widget(bottom_bar)

        # ══════════════════════════════════════
        #  风险提示
        # ══════════════════════════════════════
        risk_bar = BoxLayout(
            size_hint_y=None,
            height=rsp_height(26),
            padding=(rsp_spacing(8), rsp_spacing(3)),
        )
        with risk_bar.canvas.before:
            Color(0.85, 0.25, 0.25, 0.08)
            self._risk_bg = RoundedRectangle(
                pos=risk_bar.pos,
                size=risk_bar.size,
                radius=[dp(8)],
            )
        risk_bar.bind(
            pos=lambda w, v: setattr(self._risk_bg, 'pos', v),
            size=lambda w, v: setattr(self._risk_bg, 'size', v),
        )

        risk_label = Label(
            text='⚠️ ST股票投资风险极高，本工具仅供学习研究参考',
            font_size=dp(12),
            color=Theme.ACCENT_RED,
            halign='center', valign='middle',
            text_size=(None, None),
        )
        risk_bar.add_widget(risk_label)
        self.add_widget(risk_bar)

        # 首次加载
        Clock.schedule_once(lambda dt: self._load_stocks(), 0.1)

    def _init_data_layer(self) -> None:
        try:
            stocks = self.data_manager.load()
            self.analyzer = StockAnalyzer(stocks)
            logger.info(f"数据层初始化完成，加载 {len(stocks)} 只股票")
        except Exception as e:
            logger.error(f"数据层初始化失败: {e}")
            self.analyzer = StockAnalyzer([])
            self._show_message("初始化错误", f"数据加载失败: {str(e)}")

    def _get_meta_text(self) -> str:
        try:
            sync_info = self.data_manager.get_sync_status()
            source = sync_info.get('source', '本地')
            time_str = sync_info.get('last_sync', '未知')
            return f"数据: {time_str} | {source}"
        except:
            return "数据: 未知"

    def _update_meta_display(self) -> None:
        self.meta_label.text = self._get_meta_text()

    def _set_loading_state(self, is_loading: bool, message: str = '') -> None:
        self.is_refreshing = is_loading
        if is_loading:
            self.loading_spinner.text = f'⟳ {message}' if message else '⟳ 加载中...'
            self.refresh_btn.disabled = True
            self.refresh_btn.text = '⏳ 刷新中...'
        else:
            self.loading_spinner.text = ''
            self.refresh_btn.disabled = False
            self.refresh_btn.text = '🔄 刷新'

    def _on_window_resize(self, instance, size):
        pass

    def _update_bg(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def _on_filter_apply(self, filters: dict) -> None:
        if '_expr_error' in filters:
            error_msg = filters.pop('_expr_error')
            self._show_message("策略公式错误", f"表达式验证失败:\n{error_msg}")
        self.current_filters = filters
        self._load_stocks()

    def _on_pull_refresh(self):
        logger.info("下拉刷新触发")
        
        def on_refresh_complete():
            Clock.schedule_once(lambda dt: self._load_stocks(), 0)
            Clock.schedule_once(lambda dt: self.scroll_view.finish_refresh(), 0.5)
        
        def do_refresh(dt):
            try:
                stocks = self.data_manager.reload()
                self.analyzer = StockAnalyzer(stocks)
                Clock.schedule_once(lambda dt: on_refresh_complete(), 0.1)
                logger.info(f"下拉刷新完成，共 {len(stocks)} 只股票")
            except Exception as e:
                logger.error(f"下拉刷新失败: {e}")
                Clock.schedule_once(lambda dt: self.scroll_view.finish_refresh(), 0)
                Clock.schedule_once(lambda dt: self._show_message("刷新失败", str(e)), 0)
        
        Clock.schedule_once(do_refresh, 0.1)

    def _on_refresh_click(self, *args) -> None:
        self._refresh_local()

    def _on_quote_refresh_click(self, *args) -> None:
        """点击实时行情刷新按钮"""
        self._set_loading_state(True, '刷新实时行情...')
        logger.info("手动触发实时行情刷新")
        
        def on_success(quotes):
            self._set_loading_state(False)
            self._load_stocks()
            self._update_meta_display()
            count = len(quotes) if quotes else 0
            logger.info(f"实时行情刷新成功: {count} 只")
        
        def on_error(msg):
            self._set_loading_state(False)
            logger.warning(f"实时行情刷新失败: {msg}")
            self._show_message("行情刷新失败", msg)
        
        self.data_manager.refresh_realtime_quotes(
            on_success=on_success,
            on_error=on_error
        )

    def _toggle_theme(self, *args) -> None:
        """切换明暗主题"""
        theme_mgr.toggle_theme()
        is_dark = theme_mgr.is_dark
        self.theme_btn.text = '🌙' if is_dark else '☀️'
        self.theme_btn.color = Theme.ACCENT_BLUE if is_dark else Theme.ACCENT_ORANGE
        # 主题切换后需要重新加载以应用新颜色
        self._load_stocks()
        logger.info(f"主题切换: {'深色' if is_dark else '浅色'}")

    def _on_data_update_click(self, *args) -> None:
        """点击数据更新按钮 - 一键更新全部数据（行情 + 重整）"""
        self._set_loading_state(True, "更新全部数据中...")

        # 第一步：刷新实时行情
        def on_quote_success(quote_data: Dict[str, Any]) -> None:
            quote_count = len(quote_data) if quote_data else 0
            # 第二步：检查重整数据远程更新
            if not REMOTE_JSON_URL or not REMOTE_JSON_URL.strip():
                self._set_loading_state(False)
                self._show_message(
                    "更新完成",
                    f"实时行情已刷新 ({quote_count}只)\n\n"
                    "远程重整数据更新未配置\n"
                    "如需配置，请修改 core/constants.py 中的 REMOTE_JSON_URL"
                )
                self._load_stocks()
                return

            def on_update_success(msg: str) -> None:
                self._set_loading_state(False)
                self._show_message(
                    "全部数据更新完成",
                    f"实时行情已刷新 ({quote_count}只)\n\n重整数据: {msg}"
                )
                self._load_stocks()

            def on_update_error(msg: str) -> None:
                self._set_loading_state(False)
                self._show_message(
                    "部分更新完成",
                    f"实时行情已刷新 ({quote_count}只)\n\n重整数据更新失败: {msg}"
                )
                self._load_stocks()

            self.data_manager.check_for_updates(
                silent=False,
                on_success=on_update_success,
                on_error=on_update_error
            )

        def on_quote_error(msg: str) -> None:
            # 行情刷新失败，仍尝试重整数据更新
            if not REMOTE_JSON_URL or not REMOTE_JSON_URL.strip():
                self._set_loading_state(False)
                self._show_message("更新失败", f"行情刷新失败: {msg}\n\n远程重整数据更新未配置")
                return

            def on_update_success(msg2: str) -> None:
                self._set_loading_state(False)
                self._show_message(
                    "部分更新完成",
                    f"行情刷新失败: {msg}\n\n重整数据: {msg2}"
                )
                self._load_stocks()

            def on_update_error(msg2: str) -> None:
                self._set_loading_state(False)
                self._show_message("全部更新失败", f"行情: {msg}\n重整: {msg2}")

            self.data_manager.check_for_updates(
                silent=False,
                on_success=on_update_success,
                on_error=on_update_error
            )

        self.data_manager.refresh_realtime_quotes(
            on_success=on_quote_success,
            on_error=on_quote_error
        )

    def _show_favorites_filter(self, *args) -> None:
        """显示自选筛选"""
        fav_count = fav_mgr.get_count()
        if fav_count == 0:
            self._show_message("自选", "暂无自选股票\n在详情页点击 ☆ 收藏")
            return
        
        # 切换自选筛选
        if self.current_filters.get('only_favorites'):
            # 取消自选筛选，恢复默认
            self.current_filters = {'stage': 'best'}
            self.filter_panel.favorite_check.active = False
        else:
            # 启用自选筛选
            self.current_filters = {
                'stage': 'all',
                'only_favorites': True,
                'favorite_codes': fav_mgr.get_all(),
            }
            self.filter_panel.favorite_check.active = True
        
        self._load_stocks()

    def _load_stocks(self, *args) -> None:
        self.stock_list.clear_widgets()

        try:
            results = self.analyzer.get_filtered_analysis(**self.current_filters)
        except ValueError as e:
            self._show_message("策略错误", str(e))
            results = []
        except Exception as e:
            self._show_message("筛选错误", f"执行筛选时出错:\n{str(e)}")
            results = []

        total = len(self.analyzer.stocks)
        showing = len(results)
        self.stats_label.text = f'显示 {showing} / {total} 只股票'
        self.stats_badge.text = f'{total} 只'
        self.fav_badge.text = f'★ {fav_mgr.get_count()}'
        
        if showing == 0 and total > 0:
            empty_label = Label(
                text='没有符合条件的股票\n请尝试调整筛选条件',
                color=Theme.TEXT_SECONDARY,
                font_size=dp(15),
                halign='center', valign='middle',
                text_size=(None, None),
            )
            self.stock_list.add_widget(empty_label)

        # 添加卡片（带交错淡入动画）
        cards = []
        for result in results:
            card = StockCard(result, on_press=self._on_card_press)
            card.opacity = 0
            self.stock_list.add_widget(card)
            cards.append(card)
        
        # 交错动画
        AnimationHelper.staggered_fade_in(cards, base_delay=0.03, duration=0.25)

        if not results:
            empty_label = Label(
                text='没有符合条件的股票\n尝试调整筛选条件',
                font_size=dp(15),
                color=Theme.TEXT_MUTED,
                halign='center', valign='middle',
                size_hint_y=None, height=dp(200),
                text_size=(None, None),
            )
            self.stock_list.add_widget(empty_label)

    def _on_card_press(self, analysis_result):
        if self._on_stock_select:
            self._on_stock_select(analysis_result)

    def _refresh_local(self, *args) -> None:
        self._set_loading_state(True, '加载本地数据...')
        logger.info("开始本地数据刷新")
        
        def _do_refresh(dt):
            try:
                stocks = self.data_manager.reload()
                self.analyzer = StockAnalyzer(stocks)
                Clock.schedule_once(lambda dt: self._load_stocks(), 0)
                Clock.schedule_once(lambda dt: self._set_loading_state(False), 0)
                logger.info(f"本地刷新完成，共 {len(stocks)} 只股票")
            except Exception as e:
                logger.error(f"本地刷新失败: {e}")
                Clock.schedule_once(lambda dt: self._set_loading_state(False), 0)
                Clock.schedule_once(lambda dt: self._show_message("刷新失败", str(e)), 0)
        
        Clock.schedule_once(_do_refresh, 0.1)

    def _toggle_auto_refresh(self, *args) -> None:
        self._auto_refresh_enabled = not self._auto_refresh_enabled

        if self._auto_refresh_enabled:
            self.auto_refresh_btn.text = '▶ 自动'
            self.auto_refresh_btn.background_color = Theme.BTN_PRIMARY
            self.auto_refresh_btn.color = (1, 1, 1, 1)
            self._start_auto_refresh()
            logger.info("自动刷新已开启")
        else:
            self.auto_refresh_btn.text = '⏸ 自动'
            self.auto_refresh_btn.background_color = Theme.BG_ELEVATED
            self.auto_refresh_btn.color = Theme.TEXT_SECONDARY
            self._stop_auto_refresh()
            logger.info("自动刷新已关闭")

    def _start_auto_refresh(self) -> None:
        self._stop_auto_refresh()
        self._refresh_timer = Clock.schedule_interval(lambda dt: self._auto_refresh_callback(), 900)
    
    def _stop_auto_refresh(self) -> None:
        if self._refresh_timer:
            self._refresh_timer.cancel()
            self._refresh_timer = None
    
    def _auto_refresh_callback(self) -> None:
        """自动刷新回调 - 刷新实时行情"""
        logger.info("自动行情刷新触发")
        try:
            def on_success(quotes):
                Clock.schedule_once(lambda dt: self._load_stocks(), 0)
                Clock.schedule_once(lambda dt: self._update_meta_display(), 0)
                count = len(quotes) if quotes else 0
                logger.info(f"自动行情刷新完成: {count} 只")
            
            def on_error(msg):
                logger.warning(f"自动行情刷新失败: {msg}")
            
            self.data_manager.refresh_realtime_quotes(
                on_success=on_success,
                on_error=on_error
            )
        except Exception as e:
            logger.error(f"自动刷新失败: {e}")

    def _export_data(self, *args) -> None:
        try:
            results = self.analyzer.get_filtered_analysis(**self.current_filters)
        except ValueError:
            self._show_message("导出失败", "当前的策略公式存在错误，请先修正")
            return
            
        if not results:
            self._show_message("提示", "当前筛选结果为空，没有可导出的数据")
            return
            
        success, msg = self.data_manager.export_results(results, filename="st_export.csv", fmt="csv")
        if success:
            logger.info(f"数据导出成功: {msg}")
        else:
            logger.error(f"数据导出失败: {msg}")
        self._show_message("导出结果", msg)

    def _show_message(self, title: str, message: str) -> None:
        popup = Popup(
            title=title,
            content=Label(
                text=str(message),
                color=Theme.TEXT_PRIMARY,
                font_size=dp(15),
            ),
            size_hint=(0.8, 0.3),
            auto_dismiss=True,
            separator_color=Theme.DIVIDER,
            title_color=Theme.TEXT_PRIMARY,
        )
        popup.open()
    
    def on_leave(self) -> None:
        self._stop_auto_refresh()
        logger.info("主屏幕离开，已清理资源")
