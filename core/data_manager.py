"""
ST选股工具 - 数据管理器（重构版）
集成多源API + SQLite + 内存缓存，支持手动/自动刷新
"""

import os
import sys
import json
import time
from typing import List, Optional, Dict, Any, Tuple, Callable, Union

# 类型定义
DataRefreshCallback = Callable[[bool, str], None]
from dataclasses import dataclass
from datetime import datetime

from kivy.clock import Clock

from core.models import RestructuringStock
from core.database import DatabaseManager, db
from core.cache import stock_data_cache, analysis_cache
from core.datasource import datasource_manager, DataSourceType
from core.realtime_quote import RealtimeQuoteFetcher, quote_fetcher
from core.data_updater import data_updater, REMOTE_JSON_URL
from utils.validators import StockDataValidator, ValidationResult
from utils.async_utils import AsyncTask, scheduler, LoadingState
from utils.logger import logger


@dataclass
class SyncResult:
    """同步结果"""
    success: bool
    message: str
    added: int = 0
    updated: int = 0
    failed: int = 0
    source: str = ""


class DataManager:
    """
    统一数据管理器
    
    架构：内存缓存 → SQLite → 多源API
    
    特性：
    - 多级缓存加速
    - 自动故障切换
    - 手动/自动刷新
    - 离线优先
    """
    
    # 类级别共享实例（避免 MainScreen 和 data_manager 全局变量不一致）
    _shared_instance: Optional['DataManager'] = None
    
    def __new__(cls):
        """单例模式：确保整个应用只有一个 DataManager 实例"""
        if cls._shared_instance is None:
            cls._shared_instance = super().__new__(cls)
        return cls._shared_instance
    
    def __init__(self):
        # 避免重复初始化（单例模式下 __init__ 可能被多次调用）
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        
        self.db = db
        self.cache = stock_data_cache
        self.validator = StockDataValidator()
        self.loading_state = LoadingState()
        
        # 自动刷新配置
        self._auto_refresh_enabled = True
        self._auto_refresh_interval = 900  # 15分钟
        self._last_refresh = 0
        
        # 加载状态
        self._is_loading = False
        self._on_loading_changed: Optional[Callable[[bool], None]] = None
        
        # 初始化时从数据库加载
        self._stocks: List[RestructuringStock] = []
        self._load_from_database()

        # 设置热更新缓存目录
        self._setup_updater_cache_dir()

        # 首次启动：如果数据库为空，自动从 JSON 导入（优先缓存）
        if not self._stocks:
            self._import_from_json_if_available()

        # 启动后后台静默检查远程更新（如果已配置 URL）
        self._schedule_background_update_check()
    
    # ═══════════════════════════════════════════════════════════
    # 数据加载
    # ═══════════════════════════════════════════════════════════
    
    def _load_from_database(self) -> None:
        """从数据库加载股票数据"""
        try:
            raw_data = self.db.get_all_stocks()
            self._stocks = [
                RestructuringStock(data) for data in raw_data
            ]
            logger.info(f"从数据库加载 {len(self._stocks)} 只股票", 'DATA_MANAGER')
        except Exception as e:
            logger.error(f"数据库加载失败: {e}", 'DATA_MANAGER')
            self._stocks = []
    
    def load(self) -> List[RestructuringStock]:
        """
        加载股票数据（优先缓存）
        
        Returns:
            股票对象列表
        """
        if not self._stocks:
            self._load_from_database()
        return self._stocks
    
    def reload(self) -> List[RestructuringStock]:
        """重新加载数据（刷新缓存）"""
        self.cache.clear()
        analysis_cache.invalidate_stock('')  # 清除分析缓存
        self._load_from_database()
        return self._stocks
    
    @property
    def stocks(self) -> List[RestructuringStock]:
        """获取股票列表"""
        return self._stocks
    
    # ═══════════════════════════════════════════════════════════
    # 热更新缓存目录设置
    # ═══════════════════════════════════════════════════════════

    def _setup_updater_cache_dir(self) -> None:
        """为热更新管理器设置合适的缓存目录"""
        if 'android' in sys.platform:
            try:
                from kivy.app import App
                app = App.get_running_app()
                if app and app.user_data_dir:
                    data_updater._cache_dir = app.user_data_dir
                    return
            except Exception:
                pass
            data_updater._cache_dir = '/data/data/com.stpicker/files'
        else:
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_updater._cache_dir = os.path.join(app_dir, 'data')

    def _schedule_background_update_check(self) -> None:
        """启动后延迟 3 秒后台静默检查远程更新"""
        if not REMOTE_JSON_URL or not REMOTE_JSON_URL.strip():
            return
        try:
            from kivy.clock import Clock
            Clock.schedule_once(
                lambda dt: self.check_for_updates(silent=True),
                3
            )
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════
    # JSON 自动导入（优先缓存文件，fallback 原始打包 JSON）
    # ═══════════════════════════════════════════════════════════

    def _import_from_json_if_available(self) -> None:
        """首次启动时如果数据库为空，从 JSON 资源文件自动导入数据"""
        # 优先使用缓存文件（热更新后的最新数据）
        cache_path = data_updater._get_cache_path()
        if os.path.exists(cache_path):
            json_path = cache_path
        else:
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            json_path = os.path.join(app_dir, 'data', 'restructuring_watchlist.json')
        
        if not os.path.exists(json_path):
            logger.warning(f"JSON 数据文件不存在: {json_path}", 'DATA_MANAGER')
            return
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            stocks_data = data.get('restructuring_stocks', [])
            if not stocks_data:
                logger.warning("JSON 文件中没有 restructuring_stocks 数据", 'DATA_MANAGER')
                return
            
            # 直接批量保存到数据库（JSON 数据已经是格式化的，跳过 validator）
            success, failed = 0, 0
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                for item in stocks_data:
                    try:
                        code = item.get('stock_code', '').upper().strip()
                        if not code:
                            failed += 1
                            continue
                        
                        name = item.get('stock_name', '')
                        stage = item.get('current_stage', '未标记')
                        price = float(item.get('current_price', 0) or 0)
                        market_cap = float(item.get('market_cap', 0) or 0)
                        data_json = json.dumps(item, ensure_ascii=False)
                        
                        cursor.execute('''
                            INSERT OR REPLACE INTO stocks 
                            (code, name, stage, price, market_cap, data_json, updated_at, sync_status)
                            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
                        ''', (code, name, stage, price, market_cap, data_json))
                        success += 1
                    except Exception as e:
                        logger.error(f"导入股票失败 {item.get('stock_code', '?')}: {e}", 'DATA_MANAGER')
                        failed += 1
                conn.commit()
            
            # 更新同步元数据
            self.db.update_sync_metadata(
                source="本地JSON",
                count=success
            )
            
            # 重新从数据库加载
            self._load_from_database()
            
            logger.info(
                f"从 JSON 导入完成: 成功 {success}, 失败 {failed}, "
                f"数据库共 {len(self._stocks)} 只",
                'DATA_MANAGER'
            )
        except Exception as e:
            logger.error(f"JSON 导入失败: {e}", 'DATA_MANAGER')

    # ═══════════════════════════════════════════════════════════
    # 手动刷新（从网络同步）
    # ═══════════════════════════════════════════════════════════
    
    def refresh(
        self,
        on_success: Optional[Callable[[SyncResult], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        background: bool = False
    ) -> Optional[SyncResult]:
        """
        手动刷新数据（从网络同步）
        
        Args:
            on_success: 成功回调
            on_error: 失败回调
            background: 是否在后台执行
        
        Returns:
            如果不使用后台执行，返回同步结果
        """
        if background:
            AsyncTask(
                task_func=self._do_refresh,
                on_success=on_success,
                on_error=lambda e: on_error(str(e)) if on_error else None
            ).start()
            return None
        else:
            self._set_loading(True)
            try:
                result = self._do_refresh()
                if on_success:
                    on_success(result)
                return result
            except Exception as e:
                logger.error(f"刷新失败: {e}", 'DATA_MANAGER')
                if on_error:
                    on_error(str(e))
                raise
            finally:
                self._set_loading(False)
    
    def _do_refresh(self) -> SyncResult:
        """执行刷新操作"""
        logger.info("开始数据刷新...", 'DATA_MANAGER')
        
        # 从东方财富获取ST股票列表
        stocks = datasource_manager.fetch_all_eastmoney_st()
        
        if not stocks:
            return SyncResult(
                success=False,
                message="获取数据失败，请检查网络连接",
                source="eastmoney"
            )
        
        # 数据校验和清理
        valid_stocks = []
        for stock in stocks:
            result = self.validator.validate(stock)
            if result.is_valid and result.cleaned_data:
                valid_stocks.append(result.cleaned_data)
        
        # 批量保存到数据库
        success, failed = self.db.save_stocks_batch(valid_stocks)
        
        # 更新同步元数据
        self.db.update_sync_metadata(
            source="eastmoney",
            count=success
        )
        
        # 重新加载
        self.reload()
        
        # 更新缓存
        for stock in valid_stocks:
            self.cache.set(stock['stock_code'], stock)
        
        self._last_refresh = time.time()
        
        return SyncResult(
            success=True,
            message=f"同步完成：新增/更新 {success} 只，失败 {failed} 只",
            added=success,
            failed=failed,
            source="东方财富"
        )
    
    def refresh_realtime_quotes(
        self,
        on_success: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ) -> None:
        """
        刷新实时行情（双源容错：东方财富 + 腾讯财经）
        
        更新：价格、涨跌幅、换手率、成交量、市盈率、市净率、振幅等全部字段
        """
        codes = [s.code for s in self._stocks]
        if not codes:
            if on_error:
                on_error("无股票代码")
            return
        
        def task():
            return quote_fetcher.fetch_batch(codes)
        
        def handle_result(result):
            if result.success and result.data:
                self._update_quotes(result.data)
                if on_success:
                    on_success(result.data)
            else:
                logger.warning(f"实时行情获取失败: {result.message}", 'DATA_MANAGER')
                if on_error:
                    on_error(result.message)
        
        AsyncTask(
            task_func=task,
            on_success=handle_result,
            on_error=lambda e: on_error(str(e)) if on_error else None
        ).start()
    
    def _update_quotes(self, quotes: Dict[str, Dict[str, Any]]) -> None:
        """更新股票实时行情数据到内存和数据库"""
        updated_count = 0
        for code, data in quotes.items():
            try:
                # 找到内存中的股票对象
                stock = None
                for s in self._stocks:
                    if s.code == code:
                        stock = s
                        break
                
                if stock is None:
                    continue
                
                # 更新内存对象的所有实时行情字段
                stock.price = data.get('price', stock.price)
                stock.change_percent = data.get('change_percent', 0)
                stock.change_amount = data.get('change_amount', 0)
                stock.turnover_rate = data.get('turnover_rate', 0)
                stock.volume = data.get('volume', 0)
                stock.amount = data.get('amount', 0)
                stock.amplitude = data.get('amplitude', 0)
                stock.pe_ratio = data.get('pe_ratio', 0)
                stock.pb_ratio = data.get('pb_ratio', 0)
                stock.high_price = data.get('high_price', 0)
                stock.low_price = data.get('low_price', 0)
                stock.open_price = data.get('open_price', 0)
                stock.prev_close = data.get('prev_close', 0)
                stock.market_cap = data.get('market_cap', stock.market_cap)
                stock.circulating_market_cap = data.get('circulating_market_cap', stock.circulating_market_cap)
                stock.price_source = data.get('source', 'local')
                
                # 同步更新底层 _data 字典（用于序列化）
                stock._data['current_price'] = stock.price
                stock._data['change_percent'] = stock.change_percent
                stock._data['change_amount'] = stock.change_amount
                stock._data['turnover_rate'] = stock.turnover_rate
                stock._data['volume'] = stock.volume
                stock._data['amount'] = stock.amount
                stock._data['amplitude'] = stock.amplitude
                stock._data['pe_ratio'] = stock.pe_ratio
                stock._data['pb_ratio'] = stock.pb_ratio
                stock._data['high_price'] = stock.high_price
                stock._data['low_price'] = stock.low_price
                stock._data['open_price'] = stock.open_price
                stock._data['prev_close'] = stock.prev_close
                stock._data['market_cap'] = stock.market_cap
                stock._data['circulating_market_cap'] = stock.circulating_market_cap
                stock._data['price_source'] = stock.price_source
                
                # 更新数据库
                db_stock = self.db.get_stock(code)
                if db_stock:
                    db_data = json.loads(db_stock.get('data_json', '{}'))
                    db_data.update(stock._data)
                    self.db.save_stock(db_data)
                
                # 更新缓存
                self.cache.set(code, stock._data)
                updated_count += 1
                
            except Exception as e:
                logger.warning(f"更新行情失败 {code}: {e}", 'DATA_MANAGER')
        
        # 清除分析缓存（因为价格等字段变了）
        analysis_cache.invalidate_stock('')
        
        logger.info(f"实时行情更新完成: {updated_count}/{len(quotes)} 只", 'DATA_MANAGER')

    # ═══════════════════════════════════════════════════════════
    # 远程 JSON 热更新
    # ═══════════════════════════════════════════════════════════

    def check_for_updates(
        self,
        silent: bool = False,
        on_success: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ) -> None:
        """
        手动检查远程 JSON 更新

        Args:
            silent: 静默模式（不弹窗，仅日志）
            on_success: 成功回调，参数为消息文本
            on_error: 失败回调，参数为错误文本
        """
        if not REMOTE_JSON_URL or not REMOTE_JSON_URL.strip():
            msg = '远程更新未配置'
            if not silent and on_error:
                on_error(msg)
            return

        def task():
            return data_updater.check_and_update()

        def handle_result(result):
            if result.success and result.cache_path:
                # 更新成功且写入缓存，重新加载数据
                logger.info(f'热更新成功，重新加载数据: {result.message}', 'DATA_MANAGER')
                self._import_from_json_if_available()
                if not silent and on_success:
                    on_success(f'{result.message}\n已自动重新加载数据')
            elif result.success:
                # 无需更新或其他成功状态
                if not silent and on_success:
                    on_success(result.message)
                else:
                    logger.info(f'热更新检查: {result.message}', 'DATA_MANAGER')
            else:
                # 失败
                if not silent and on_error:
                    on_error(result.message)
                else:
                    logger.warning(f'热更新失败: {result.message}', 'DATA_MANAGER')

        AsyncTask(
            task_func=task,
            on_success=handle_result,
            on_error=lambda e: on_error(str(e)) if (not silent and on_error) else None
        ).start()

    def get_update_status(self) -> Dict[str, Any]:
        """获取热更新状态信息"""
        return {
            'url_configured': bool(REMOTE_JSON_URL and REMOTE_JSON_URL.strip()),
            'url': REMOTE_JSON_URL if REMOTE_JSON_URL else '',
            'has_cache': data_updater.has_valid_cache(),
            'cache_path': data_updater._get_cache_path(),
        }

    # ═══════════════════════════════════════════════════════════
    # 自动刷新
    # ═══════════════════════════════════════════════════════════
    
    def enable_auto_refresh(self, interval: int = 900) -> None:
        """
        启用自动刷新
        
        Args:
            interval: 刷新间隔（秒），默认15分钟
        """
        self._auto_refresh_enabled = True
        self._auto_refresh_interval = interval
        
        # 安排定时任务
        scheduler.schedule_interval(
            'auto_refresh',
            self._auto_refresh_tick,
            interval,
            start_immediately=False
        )
        
        logger.info(f"自动刷新已启用，间隔 {interval} 秒", 'DATA_MANAGER')
    
    def disable_auto_refresh(self) -> None:
        """禁用自动刷新"""
        self._auto_refresh_enabled = False
        scheduler.cancel('auto_refresh')
        logger.info("自动刷新已禁用", 'DATA_MANAGER')
    
    def _auto_refresh_tick(self) -> None:
        """自动刷新 tick"""
        if not self._auto_refresh_enabled:
            return
        
        # 检查是否需要刷新（交易时间）
        if self._is_trading_time():
            logger.info("自动刷新触发", 'DATA_MANAGER')
            self.refresh(background=True)
    
    def _is_trading_time(self) -> bool:
        """检查当前是否为交易时间"""
        now = datetime.now()
        weekday = now.weekday()
        hour = now.hour
        minute = now.minute
        
        # 周末不交易
        if weekday >= 5:
            return False
        
        # 交易时间段：9:30-11:30, 13:00-15:00
        time_val = hour * 100 + minute
        return (930 <= time_val <= 1130) or (1300 <= time_val <= 1500)
    
    # ═══════════════════════════════════════════════════════════
    # 数据导出/导入
    # ═══════════════════════════════════════════════════════════
    
    def import_from_file(self, file_path: str) -> Tuple[bool, str]:
        """
        从JSON文件导入数据
        
        Returns:
            (成功, 消息)
        """
        if not os.path.exists(file_path):
            return False, f"文件不存在: {file_path}"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            stocks_data = data.get('restructuring_stocks', [])
            if not stocks_data:
                return False, "文件中没有找到股票数据"
            
            # 校验和保存
            valid_stocks = []
            for stock in stocks_data:
                result = self.validator.validate(stock)
                if result.is_valid and result.cleaned_data:
                    valid_stocks.append(result.cleaned_data)
            
            success, failed = self.db.save_stocks_batch(valid_stocks)
            self.reload()
            
            return True, f"成功导入 {success} 只股票，失败 {failed} 只"
            
        except json.JSONDecodeError as e:
            return False, f"JSON解析失败: {e}"
        except Exception as e:
            return False, f"导入失败: {e}"
    
    def export_to_csv(
        self,
        results: List[Any],
        filename: str = "st_export.csv"
    ) -> Tuple[bool, str]:
        """
        导出分析结果为CSV
        
        Returns:
            (成功, 消息)
        """
        import csv
        import sys
        
        # 确定保存路径
        if 'android' in sys.platform:
            target_dir = '/sdcard/Download'
        else:
            target_dir = os.path.expanduser('~/Downloads')
        
        if not os.path.exists(target_dir):
            target_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        file_path = os.path.join(target_dir, filename)
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow([
                    '代码', '名称', '当前阶段', '最新价格', '市值(亿)',
                    '得分', '投资人背景', '资产注入预期', '评级建议'
                ])
                
                for r in results:
                    bg = f"{r.industrial_name}-{r.industrial_background}" \
                        if r.has_industrial else '无产业投资人'
                    writer.writerow([
                        r.code, r.name, r.stage, f"{r.price:.2f}",
                        f"{r.market_cap:.1f}" if r.market_cap else '-',
                        r.investor_score, bg, r.asset_injection, r.recommendation
                    ])
            
            return True, f"成功导出至:\n{file_path}"
        except Exception as e:
            return False, f"导出失败: {e}"
    
    # ═══════════════════════════════════════════════════════════
    # 同步状态 / 导出（兼容 main_screen.py 调用）
    # ═══════════════════════════════════════════════════════════

    def get_sync_status(self) -> Dict[str, Any]:
        """获取同步状态信息（供 MainScreen 元数据栏使用）"""
        sync_info = self.db.get_last_sync()
        if sync_info:
            return {
                'source': sync_info.get('last_sync_source', '本地'),
                'last_sync': sync_info.get('last_sync', '未知'),
                'count': sync_info.get('sync_count', 0),
            }
        return {
            'source': '本地',
            'last_sync': '未知',
            'count': len(self._stocks),
        }

    def export_results(
        self,
        results: list,
        filename: str = "st_export.csv",
        fmt: str = "csv",
    ) -> Tuple[bool, str]:
        """
        导出分析结果（供 MainScreen 导出按钮使用）
        
        Args:
            results: AnalysisResult 列表
            filename: 输出文件名
            fmt: 导出格式（仅支持 csv）
        
        Returns:
            (成功, 消息)
        """
        import csv
        import sys

        # 确定保存路径
        if 'android' in sys.platform:
            target_dir = '/sdcard/Download'
        else:
            target_dir = os.path.expanduser('~/Downloads')

        if not os.path.exists(target_dir):
            target_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        file_path = os.path.join(target_dir, filename)

        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow([
                    '代码', '名称', '当前阶段', '最新价格', '市值(亿)',
                    '得分', '投资人背景', '资产注入预期', '评级建议'
                ])

                for r in results:
                    bg = f"{r.industrial_name}-{r.industrial_background}" \
                        if r.has_industrial else '无产业投资人'
                    writer.writerow([
                        r.code, r.name, r.stage, f"{r.price:.2f}",
                        f"{r.market_cap:.1f}" if r.market_cap else '-',
                        r.investor_score, bg, r.asset_injection, r.recommendation
                    ])

            return True, f"成功导出至:\n{file_path}"
        except Exception as e:
            return False, f"导出失败: {e}"

    # ═══════════════════════════════════════════════════════════
    # 属性/统计
    # ═══════════════════════════════════════════════════════════
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """获取数据元信息"""
        return self.db.get_stats()
    
    @property
    def last_updated(self) -> str:
        """最后更新时间"""
        sync_info = self.db.get_last_sync()
        if sync_info and sync_info.get('last_sync'):
            return sync_info['last_sync']
        return '未知'
    
    @property
    def data_source(self) -> str:
        """数据来源"""
        sync_info = self.db.get_last_sync()
        if sync_info and sync_info.get('last_sync_source'):
            return sync_info['last_sync_source']
        return '本地'
    
    # ═══════════════════════════════════════════════════════════
    # 加载状态管理
    # ═══════════════════════════════════════════════════════════
    
    def _set_loading(self, loading: bool) -> None:
        """设置加载状态"""
        self._is_loading = loading
        self.loading_state.set_loading(loading)
        if self._on_loading_changed:
            self._on_loading_changed(loading)
    
    def is_loading(self) -> bool:
        """获取加载状态"""
        return self._is_loading
    
    def set_on_loading_changed(self, callback: Callable[[bool], None]) -> None:
        """设置加载状态变化回调"""
        self._on_loading_changed = callback


# 全局数据管理器实例
data_manager = DataManager()
