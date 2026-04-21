"""
ST选股工具 - 股票分析器（优化版）
添加类型注解、安全表达式解析、分析结果缓存
"""

from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field

from core.constants import (
    Stage, STAGE_NAMES, STAGE_PRIORITY, BEST_ENTRY_STAGES,
    RECOMMENDATIONS, RISK_LEVELS, ASSET_INJECTION,
)
from core.models import RestructuringStock, InvestorInfo, StageEvent
from core.cache import analysis_cache
from utils.safe_eval import safe_eval
from utils.logger import logger, log_performance


@dataclass
class AnalysisResult:
    """分析结果数据类 v2.0 - 复刻鸿蒙版所有字段"""
    # 基本信息
    code: str
    name: str
    display_name: str
    stage: str
    stage_code: str
    price: float
    price_text: str
    market_cap: Optional[float]
    notes: str
    
    # 分析指标
    investor_score: int
    stage_priority: int
    
    # 推荐和风险
    recommendation: str
    recommendation_type: str
    risk_level: str
    
    # 扩展风险标志
    has_audit_risk: bool = False
    has_financial_risk: bool = False
    has_illegal_guarantee: bool = False
    has_delisting_risk: bool = False
    risk_warnings: List[str] = field(default_factory=list)
    
    # 投资人概要
    has_industrial: bool = False
    industrial_name: str = ""
    industrial_background: str = ""
    applicant_count: int = 0
    investor_summary: str = ""
    
    # 资产注入
    asset_injection: str = ""
    
    # 历史和方案
    history: List[StageEvent] = field(default_factory=list)
    scheme: Optional[Any] = None
    future: Optional[Any] = None
    
    # === 实时行情字段（复刻鸿蒙版）===
    change_percent: float = 0.0
    change_amount: float = 0.0
    turnover_rate: float = 0.0
    volume: float = 0.0
    amount: float = 0.0
    amplitude: float = 0.0
    pe_ratio: float = 0.0
    pb_ratio: float = 0.0
    high_price: float = 0.0
    low_price: float = 0.0
    open_price: float = 0.0
    prev_close: float = 0.0
    price_source: str = 'local'
    is_up: bool = False
    is_down: bool = False
    
    # 原始数据引用
    stock: Optional[RestructuringStock] = None
    
    @property
    def price_color(self) -> Tuple[float, float, float, float]:
        """价格颜色（中国红涨绿跌）"""
        if self.change_percent > 0:
            return (1.0, 0.35, 0.35, 1)
        elif self.change_percent < 0:
            return (0.25, 0.85, 0.50, 1)
        return (0.70, 0.74, 0.78, 1)
    
    @property
    def change_percent_text(self) -> str:
        """涨跌幅文本"""
        if self.change_percent != 0:
            sign = '+' if self.change_percent > 0 else ''
            return f"{sign}{self.change_percent:.2f}%"
        return "0.00%"
    
    @property
    def turnover_rate_text(self) -> str:
        """换手率文本"""
        if self.turnover_rate > 0:
            return f"换手 {self.turnover_rate:.2f}%"
        return ""


class StockAnalyzer:
    """股票分析器 - 优化版（带缓存）"""

    def __init__(self, stocks: List[RestructuringStock]):
        """
        初始化分析器
        
        Args:
            stocks: RestructuringStock 对象列表
        """
        self.stocks = stocks
        self._cache = analysis_cache
    
    @log_performance('ANALYZER')
    def analyze(self, stock: RestructuringStock) -> AnalysisResult:
        """
        分析单只股票（带缓存）
        
        Args:
            stock: 股票对象
        
        Returns:
            分析结果
        """
        # 尝试从缓存获取
        cached = self._cache.get(stock.code)
        if cached is not None:
            return cached
        
        # 计算分析结果
        result = self._compute_analysis(stock)
        
        # 缓存结果
        self._cache.set(stock.code, result)
        
        return result
    
    def _compute_analysis(self, stock: RestructuringStock) -> AnalysisResult:
        """计算分析结果（内部方法）"""
        investor_score = self._calc_investor_score(stock)
        stage_priority = STAGE_PRIORITY.get(stock.stage, 99)
        
        # 推荐和风险
        rec_tuple = RECOMMENDATIONS.get(stock.stage, ('👀 观察中', 'muted'))
        recommendation = rec_tuple[0]
        recommendation_type = rec_tuple[1]
        risk_level = RISK_LEVELS.get(stock.stage, '中')
        
        # 资产注入
        asset_injection = ASSET_INJECTION.get(stock.investor.asset_injection, '')
        
        return AnalysisResult(
            code=stock.code,
            name=stock.name,
            display_name=stock.display_name,
            stage=stock.stage_name,
            stage_code=stock.stage,
            price=stock.price,
            price_text=stock.price_text,
            market_cap=stock.market_cap,
            notes=stock.notes,
            investor_score=investor_score,
            stage_priority=stage_priority,
            recommendation=recommendation,
            recommendation_type=recommendation_type,
            risk_level=risk_level,
            has_audit_risk=stock.has_audit_risk,
            has_financial_risk=stock.has_financial_risk,
            has_illegal_guarantee=stock.has_illegal_guarantee,
            has_delisting_risk=stock.has_delisting_risk,
            risk_warnings=stock.risk_warnings,
            has_industrial=stock.investor.has_industrial,
            industrial_name=stock.investor.industrial_name,
            industrial_background=stock.investor.industrial_background,
            applicant_count=stock.investor.applicant_count,
            investor_summary=stock.investor.get_summary(),
            asset_injection=asset_injection,
            history=stock.history,
            scheme=stock.scheme,
            future=stock.future,
            # === 实时行情字段 ===
            change_percent=stock.change_percent,
            change_amount=stock.change_amount,
            turnover_rate=stock.turnover_rate,
            volume=stock.volume,
            amount=stock.amount,
            amplitude=stock.amplitude,
            pe_ratio=stock.pe_ratio,
            pb_ratio=stock.pb_ratio,
            high_price=stock.high_price,
            low_price=stock.low_price,
            open_price=stock.open_price,
            prev_close=stock.prev_close,
            price_source=stock.price_source,
            is_up=stock.is_up,
            is_down=stock.is_down,
            stock=stock,
        )
    
    def _calc_investor_score(self, stock: RestructuringStock) -> int:
        """计算投资人综合评分 (0-100)"""
        score = 0
        inv = stock.investor

        # 有产业投资人 +30
        if inv.has_industrial:
            score += 30
            # 背景含"龙头"或"上市" +15
            bg = inv.industrial_background
            if '龙头' in bg or '上市' in bg:
                score += 15
            # 有明确成本价 +5
            if inv.industrial_cost:
                score += 5

        # 竞争激烈度
        if inv.applicant_count >= 5:
            score += 20
        elif inv.applicant_count >= 3:
            score += 15
        elif inv.applicant_count >= 1:
            score += 8

        # 有财务投资人 +5
        if inv.financial_count > 0:
            score += 5

        # 资产注入预期
        injection = inv.asset_injection
        if injection == 'confirmed_plan':
            score += 15
        elif injection == 'strong_expectation':
            score += 10
        elif injection == 'possible':
            score += 5

        return min(score, 100)

    def analyze_all(
        self,
        stocks: Optional[List[RestructuringStock]] = None
    ) -> List[AnalysisResult]:
        """
        分析全部或指定股票
        
        Args:
            stocks: 指定股票列表，None则分析全部
        
        Returns:
            分析结果列表
        """
        target = stocks if stocks is not None else self.stocks
        return [self.analyze(s) for s in target]

    def filter_stocks(self, **kwargs) -> List[RestructuringStock]:
        """
        多维度筛选股票 v2.0 - 复刻鸿蒙版所有筛选维度

        支持参数:
        - stage: 'all' | 'best' | 具体阶段代码
        - min_price / max_price: 价格区间
        - min_change_percent / max_change_percent: 涨跌幅区间(%)
        - min_turnover_rate / max_turnover_rate: 换手率区间(%)
        - has_industrial: 是否有产业投资人 (bool)
        - only_favorites: 仅显示自选 (bool) - 需要传入 favorite_codes
        - favorite_codes: 自选代码列表 (List[str])
        - min_applicants: 最小报名家数
        - keyword: 关键字搜索（代码/名称）
        - strategy_expr: 高级策略表达式
        """
        result: List[RestructuringStock] = list(self.stocks)

        # 按阶段筛选
        stage = kwargs.get('stage', 'all')
        if stage != 'all':
            if stage == 'best':
                result = [s for s in result if s.stage in BEST_ENTRY_STAGES]
            else:
                result = [s for s in result if s.stage == stage]

        # 按价格区间
        min_price = kwargs.get('min_price')
        if min_price is not None and str(min_price).strip() != '':
            try:
                mp = float(min_price)
                result = [s for s in result if s.price >= mp]
            except ValueError:
                pass

        max_price = kwargs.get('max_price')
        if max_price is not None and str(max_price).strip() != '':
            try:
                mp = float(max_price)
                result = [s for s in result if s.price <= mp]
            except ValueError:
                pass

        # 按涨跌幅区间
        min_change = kwargs.get('min_change_percent')
        if min_change is not None and str(min_change).strip() != '':
            try:
                mc = float(min_change)
                result = [s for s in result if s.change_percent >= mc]
            except ValueError:
                pass

        max_change = kwargs.get('max_change_percent')
        if max_change is not None and str(max_change).strip() != '':
            try:
                mc = float(max_change)
                result = [s for s in result if s.change_percent <= mc]
            except ValueError:
                pass

        # 按换手率区间
        min_turnover = kwargs.get('min_turnover_rate')
        if min_turnover is not None and str(min_turnover).strip() != '':
            try:
                mt = float(min_turnover)
                result = [s for s in result if s.turnover_rate >= mt]
            except ValueError:
                pass

        max_turnover = kwargs.get('max_turnover_rate')
        if max_turnover is not None and str(max_turnover).strip() != '':
            try:
                mt = float(max_turnover)
                result = [s for s in result if s.turnover_rate <= mt]
            except ValueError:
                pass

        # 产业投资人筛选
        has_industrial = kwargs.get('has_industrial')
        if has_industrial is not None and has_industrial:
            result = [s for s in result if s.investor.has_industrial]

        # 自选筛选
        only_favorites = kwargs.get('only_favorites')
        favorite_codes = kwargs.get('favorite_codes', [])
        if only_favorites and favorite_codes:
            fav_set = {c.upper().strip() for c in favorite_codes}
            result = [s for s in result if s.code.upper().strip() in fav_set]

        # 最小报名家数
        min_applicants = kwargs.get('min_applicants')
        if min_applicants is not None:
            result = [s for s in result
                      if s.investor.applicant_count >= min_applicants]

        # 关键字搜索
        keyword = kwargs.get('keyword')
        if keyword:
            kw = keyword.lower()
            result = [s for s in result
                      if kw in s.code.lower() or kw in s.name.lower()]

        # 高级策略表达式过滤
        strategy_expr = kwargs.get('strategy_expr')
        if strategy_expr and strategy_expr.strip():
            result = self._apply_strategy_filter(result, strategy_expr.strip())

        return result
    
    def _apply_strategy_filter(
        self,
        stocks: List[RestructuringStock],
        expr: str
    ) -> List[RestructuringStock]:
        """
        应用策略表达式过滤
        
        Args:
            stocks: 股票列表
            expr: 表达式字符串
        
        Returns:
            过滤后的股票列表
        
        Raises:
            ValueError: 表达式解析失败
        """
        filtered: List[RestructuringStock] = []
        
        for stock in stocks:
            # 获取分析结果（用于表达式变量）
            analysis = self.analyze(stock)
            
            # 构建变量上下文
            # 注意：同时提供 has_industry 和 has_industrial 以兼容不同写法
            context = {
                'price': analysis.price,
                'score': analysis.investor_score,
                'market_cap': analysis.market_cap or 0,
                'stage': analysis.stage,
                'stage_code': analysis.stage_code,
                'risk': analysis.risk_level,
                'has_industrial': analysis.has_industrial,
                'has_industry': analysis.has_industrial,  # 别名
                'applicants': analysis.applicant_count or 0,
                'has_audit_risk': stock.has_audit_risk,
                'has_financial_risk': stock.has_financial_risk,
                'has_illegal_guarantee': stock.has_illegal_guarantee,
                'has_delisting_risk': stock.has_delisting_risk,
                # === 实时行情变量（复刻鸿蒙版）===
                'change_percent': analysis.change_percent,
                'change_amount': analysis.change_amount,
                'turnover_rate': analysis.turnover_rate,
                'volume': analysis.volume,
                'amount': analysis.amount,
                'amplitude': analysis.amplitude,
                'pe_ratio': analysis.pe_ratio,
                'pb_ratio': analysis.pb_ratio,
                'high_price': analysis.high_price,
                'low_price': analysis.low_price,
                'open_price': analysis.open_price,
                'prev_close': analysis.prev_close,
            }
            
            # 使用安全表达式解析器
            try:
                if safe_eval(expr, context):
                    filtered.append(stock)
            except Exception as e:
                logger.error(f"策略表达式错误: {e}", 'ANALYZER')
                raise ValueError(f"策略公式解析失败: {e}")
        
        return filtered

    def sort_stocks(
        self,
        stocks: List[RestructuringStock],
        sort_by: str = 'priority'
    ) -> List[RestructuringStock]:
        """
        排序股票列表
        
        Args:
            stocks: 股票列表
            sort_by: 排序方式
                - 'priority': 阶段优先级 + 评分
                - 'price_asc': 价格升序
                - 'price_desc': 价格降序
                - 'score_desc': 评分降序
        
        Returns:
            排序后的股票列表
        """
        if sort_by == 'priority':
            return sorted(
                stocks,
                key=lambda s: (
                    STAGE_PRIORITY.get(s.stage, 99),
                    -self.analyze(s).investor_score
                )
            )
        elif sort_by == 'price_asc':
            return sorted(stocks, key=lambda s: s.price)
        elif sort_by == 'price_desc':
            return sorted(stocks, key=lambda s: s.price, reverse=True)
        elif sort_by == 'score_desc':
            return sorted(
                stocks,
                key=lambda s: self.analyze(s).investor_score,
                reverse=True
            )
        return stocks

    def get_filtered_analysis(
        self,
        sort_by: str = 'priority',
        **filters
    ) -> List[AnalysisResult]:
        """
        筛选 + 排序 + 分析 一站式
        
        Args:
            sort_by: 排序方式
            **filters: 筛选条件
        
        Returns:
            分析结果列表
        """
        filtered = self.filter_stocks(**filters)
        sorted_stocks = self.sort_stocks(filtered, sort_by)
        return self.analyze_all(sorted_stocks)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self.stocks)
        by_stage: Dict[str, int] = {}
        
        for s in self.stocks:
            stage_name = STAGE_NAMES.get(s.stage, s.stage)
            by_stage[stage_name] = by_stage.get(stage_name, 0) + 1

        best_count = len([s for s in self.stocks if s.stage in BEST_ENTRY_STAGES])

        return {
            'total': total,
            'best_entry': best_count,
            'by_stage': by_stage,
        }
    
    def invalidate_cache(self, stock_code: Optional[str] = None) -> None:
        """
        使缓存失效
        
        Args:
            stock_code: 指定股票代码，None则全部失效
        """
        if stock_code:
            self._cache.invalidate_stock(stock_code)
        else:
            self._cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return self._cache.get_stats()
