"""
ST选股工具 - 数据模型 v2.0
复刻鸿蒙版所有数据维度
"""

from typing import Dict, Any, List, Optional, Tuple
from core.constants import STAGE_NAMES


class InvestorInfo:
    """投资人信息"""

    def __init__(self, data: Optional[Dict[str, Any]]):
        self._data: Dict[str, Any] = data or {}

        # 产业投资人
        industrial: Dict[str, Any] = self._data.get('industrial', {})
        self.has_industrial: bool = bool(industrial and industrial.get('name'))
        self.industrial_name: str = industrial.get('name', '')
        self.industrial_background: str = industrial.get('background', '')
        self.industrial_cost: Optional[float] = industrial.get('cost_per_share')
        self.industrial_discount: Optional[float] = industrial.get('discount')
        self.industrial_lockup: Optional[int] = industrial.get('lockup')
        self.industrial_amount: Optional[float] = industrial.get('investment_amount')
        self.industrial_shares: Optional[float] = industrial.get('shares')

        # 财务投资人
        financial: Dict[str, Any] = self._data.get('financial', {})
        self.financial_count: int = financial.get('count', 0)
        self.financial_names: List[str] = financial.get('names', [])
        self.financial_cost: Optional[float] = financial.get('cost_per_share')
        self.financial_lockup: Optional[int] = financial.get('lockup')
        self.financial_amount: Optional[float] = financial.get('investment_amount')

        # 竞争情况
        competition: Dict[str, Any] = self._data.get('competition', {})
        self.applicant_count: int = competition.get('applicant_count', 0)
        self.deposit: Optional[float] = competition.get('deposit')

        # 详细进展与战投方案
        self.progress_detail: str = self._data.get('progress_detail', '')

        # 资产注入预期
        self.asset_injection: str = self._data.get('asset_injection_expectation', 'none')

    def get_summary(self) -> str:
        """获取投资人摘要文本"""
        parts: List[str] = []
        if self.has_industrial:
            parts.append(f"产业: {self.industrial_name}")
            if self.industrial_background:
                parts.append(f"({self.industrial_background})")
        if self.applicant_count > 0:
            parts.append(f"{self.applicant_count}家竞争")
        if not parts:
            return '投资人信息待更新'
        return ' | '.join(parts)


class RestructuringScheme:
    """重整方案信息"""

    def __init__(self, data: Optional[Dict[str, Any]]):
        self._data: Dict[str, Any] = data or {}
        self.pre_capital: Optional[float] = self._data.get('pre_capital')
        self.post_capital: Optional[float] = self._data.get('post_capital')
        self.conversion_ratio: str = self._data.get('conversion_ratio', '')
        self.total_debt: Optional[float] = self._data.get('total_debt')
        self.investment_amount: Optional[float] = self._data.get('investment_amount')
        self.debt_clearance_method: List[str] = self._data.get('debt_clearance_method', [])
        self.scheme_detail: str = self._data.get('scheme_detail', '')

    @property
    def has_info(self) -> bool:
        """是否有方案信息"""
        return bool(self.pre_capital or self.total_debt or self.scheme_detail)


class FutureExpectation:
    """未来预期"""

    def __init__(self, data: Optional[Dict[str, Any]]):
        self._data: Dict[str, Any] = data or {}
        self.new_controller: str = self._data.get('new_controller', '')
        self.new_direction: str = self._data.get('new_direction', '')
        self.asset_injection_plan: str = self._data.get('asset_injection_plan', '')
        self.synergy: str = self._data.get('synergy', '')

    @property
    def has_info(self) -> bool:
        """是否有预期信息"""
        return bool(self.new_controller or self.new_direction)


class StageEvent:
    """阶段历史事件"""

    def __init__(self, data: Dict[str, Any]):
        self.stage: str = data.get('stage', '')
        self.date: str = data.get('date', '')
        self.event: str = data.get('event', '')
        self.stage_name: str = STAGE_NAMES.get(self.stage, self.stage)


# ═══════════════════════════════════════════════════════════════
#  新增模型：复刻鸿蒙版数据维度
# ═══════════════════════════════════════════════════════════════

class MarketDepth:
    """五档盘口"""

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        self._data: Dict[str, Any] = data or {}
        # buy5 / sell5: List of (price, volume)
        self.buy5: List[Tuple[float, int]] = []
        self.sell5: List[Tuple[float, int]] = []
        self._parse()

    def _parse(self):
        raw_buy = self._data.get('buy5', [])
        raw_sell = self._data.get('sell5', [])
        if isinstance(raw_buy, list):
            self.buy5 = [(float(b[0]), int(b[1])) for b in raw_buy if len(b) >= 2]
        if isinstance(raw_sell, list):
            self.sell5 = [(float(s[0]), int(s[1])) for s in raw_sell if len(s) >= 2]

    @property
    def has_data(self) -> bool:
        return len(self.buy5) > 0 or len(self.sell5) > 0


class FundFlow:
    """资金流向"""

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        self._data: Dict[str, Any] = data or {}
        self.main_force: float = float(self._data.get('main_force', 0) or 0)
        self.large: float = float(self._data.get('large', 0) or 0)
        self.medium: float = float(self._data.get('medium', 0) or 0)
        self.small: float = float(self._data.get('small', 0) or 0)

    @property
    def has_data(self) -> bool:
        return abs(self.main_force) > 0 or abs(self.large) > 0


class BalanceSheet:
    """资产负债表"""

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        self._data: Dict[str, Any] = data or {}
        self.total_assets: Optional[float] = self._data.get('total_assets')
        self.total_liabilities: Optional[float] = self._data.get('total_liabilities')
        self.equity: Optional[float] = self._data.get('equity')
        self.current_assets: Optional[float] = self._data.get('current_assets')
        self.current_liabilities: Optional[float] = self._data.get('current_liabilities')

    @property
    def has_data(self) -> bool:
        return self.total_assets is not None


class KlineItem:
    """单根K线数据"""

    def __init__(self, data: Dict[str, Any]):
        self.date: str = str(data.get('date', ''))
        self.open_price: float = float(data.get('open', 0) or 0)
        self.high_price: float = float(data.get('high', 0) or 0)
        self.low_price: float = float(data.get('low', 0) or 0)
        self.close_price: float = float(data.get('close', 0) or 0)
        self.volume: float = float(data.get('volume', 0) or 0)
        self.amount: float = float(data.get('amount', 0) or 0)


class KlineData:
    """K线数据集合"""

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        self._data: Dict[str, Any] = data or {}
        self.daily: List[KlineItem] = []
        self.weekly: List[KlineItem] = []
        self.monthly: List[KlineItem] = []
        self._parse()

    def _parse(self):
        for key, target in [('daily', self.daily), ('weekly', self.weekly), ('monthly', self.monthly)]:
            raw = self._data.get(key, [])
            if isinstance(raw, list):
                target.extend([KlineItem(item) for item in raw])

    @property
    def has_data(self) -> bool:
        return len(self.daily) > 0 or len(self.weekly) > 0 or len(self.monthly) > 0


# ═══════════════════════════════════════════════════════════════
#  主模型：RestructuringStock v2
# ═══════════════════════════════════════════════════════════════

class RestructuringStock:
    """重整股票数据模型 v2.0 - 复刻鸿蒙版所有字段"""

    def __init__(self, data: Dict[str, Any]):
        self._data: Dict[str, Any] = data
        self.code: str = data.get('stock_code', '')
        self.name: str = data.get('stock_name', '')
        self.stage: str = data.get('current_stage', '')
        self.price: float = float(data.get('current_price', 0) or 0)
        self.price_source: str = 'local'  # 'local' | 'eastmoney' | 'tencent'
        self.market_cap: Optional[float] = data.get('market_cap')
        self.notes: str = data.get('notes', '')

        # === 实时行情字段（复刻鸿蒙版）===
        self.change_percent: float = float(data.get('change_percent', 0) or 0)
        self.change_amount: float = float(data.get('change_amount', 0) or 0)
        self.turnover_rate: float = float(data.get('turnover_rate', 0) or 0)
        self.volume: float = float(data.get('volume', 0) or 0)
        self.amount: float = float(data.get('amount', 0) or 0)
        self.amplitude: float = float(data.get('amplitude', 0) or 0)
        self.pe_ratio: float = float(data.get('pe_ratio', 0) or 0)
        self.pb_ratio: float = float(data.get('pb_ratio', 0) or 0)
        self.high_price: float = float(data.get('high_price', 0) or 0)
        self.low_price: float = float(data.get('low_price', 0) or 0)
        self.open_price: float = float(data.get('open_price', 0) or 0)
        self.prev_close: float = float(data.get('prev_close', 0) or 0)
        self.circulating_market_cap: Optional[float] = data.get('circulating_market_cap')

        # 复合对象
        self.investor: InvestorInfo = InvestorInfo(data.get('investor_info'))
        self.scheme: RestructuringScheme = RestructuringScheme(data.get('scheme'))
        self.future: FutureExpectation = FutureExpectation(data.get('future_expectation'))

        # 新增维度
        self.timeline: Dict[str, Any] = data.get('timeline_dates', {})

        # 风险
        risks: Dict[str, Any] = data.get('risks', {})
        self.has_audit_risk: bool = risks.get('audit_issue', False)
        self.has_financial_risk: bool = risks.get('financial_issue', False)
        self.has_illegal_guarantee: bool = risks.get('illegal_guarantee', False)
        self.has_delisting_risk: bool = risks.get('delisting_risk', False)
        self.risk_warnings: List[str] = risks.get('warnings', [])

        # 阶段历史
        self.history: List[StageEvent] = [
            StageEvent(h) for h in data.get('stage_history', [])
        ]

        # 新增数据维度（复刻鸿蒙版）
        self.market_depth: MarketDepth = MarketDepth(data.get('market_depth'))
        self.fund_flow: FundFlow = FundFlow(data.get('fund_flow'))
        self.balance_sheet: BalanceSheet = BalanceSheet(data.get('balance_sheet'))
        self.kline_data: KlineData = KlineData(data.get('kline_data'))

    # ── 属性方法 ──

    @property
    def stage_name(self) -> str:
        """获取当前阶段中文名"""
        return STAGE_NAMES.get(self.stage, self.stage)

    @property
    def display_name(self) -> str:
        """显示名称：代码 + 名称"""
        return f"{self.code} {self.name}"

    @property
    def price_text(self) -> str:
        """价格文本"""
        if self.price:
            return f"¥{self.price:.2f}"
        return "价格未知"

    @property
    def change_percent_text(self) -> str:
        """涨跌幅文本"""
        if self.change_percent != 0:
            sign = '+' if self.change_percent > 0 else ''
            return f"{sign}{self.change_percent:.2f}%"
        return ""

    @property
    def turnover_rate_text(self) -> str:
        """换手率文本"""
        if self.turnover_rate > 0:
            return f"换手 {self.turnover_rate:.2f}%"
        return ""

    @property
    def is_up(self) -> bool:
        """是否上涨"""
        return self.change_percent > 0

    @property
    def is_down(self) -> bool:
        """是否下跌"""
        return self.change_percent < 0

    @property
    def price_color(self) -> Tuple[float, float, float, float]:
        """价格颜色（中国红涨绿跌）"""
        if self.change_percent > 0:
            return (1.0, 0.35, 0.35, 1)  # 红色
        elif self.change_percent < 0:
            return (0.25, 0.85, 0.50, 1)  # 绿色
        return (0.70, 0.74, 0.78, 1)  # 灰色

    def to_dict(self) -> Dict[str, Any]:
        """序列化回字典"""
        return self._data

    def clone(self) -> 'RestructuringStock':
        """深拷贝（用于 @State 引用更新）"""
        import copy
        return RestructuringStock(copy.deepcopy(self._data))
