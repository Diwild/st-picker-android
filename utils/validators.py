"""
ST选股工具 - 数据校验器
保障数据质量和完整性
"""

import re
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """校验结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    cleaned_data: Optional[Dict[str, Any]] = None


class StockDataValidator:
    """股票数据校验器"""
    
    # 股票代码格式：6位数字，以00/30/60/68/88开头
    STOCK_CODE_PATTERN = re.compile(r'^(00|30|60|68|88)\d{4}$')
    
    # 必填字段
    REQUIRED_FIELDS = ['stock_code', 'stock_name']
    
    # 价格合理范围
    MIN_PRICE = 0.0
    MAX_PRICE = 10000.0
    
    # 市值合理范围（亿）
    MIN_MARKET_CAP = 0.0
    MAX_MARKET_CAP = 100000.0
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        验证股票数据完整性
        
        Returns:
            ValidationResult: 校验结果
        """
        self.errors = []
        self.warnings = []
        
        # 检查必填字段
        self._validate_required_fields(data)
        
        # 检查股票代码格式
        self._validate_stock_code(data.get('stock_code', ''))
        
        # 检查数值范围
        self._validate_price(data.get('current_price'))
        self._validate_market_cap(data.get('market_cap'))
        
        # 清理数据
        cleaned = self.sanitize(data) if not self.errors else None
        
        return ValidationResult(
            is_valid=len(self.errors) == 0,
            errors=self.errors.copy(),
            warnings=self.warnings.copy(),
            cleaned_data=cleaned
        )
    
    def _validate_required_fields(self, data: Dict[str, Any]) -> None:
        """检查必填字段"""
        for field in self.REQUIRED_FIELDS:
            if field not in data or not data[field]:
                self.errors.append(f"缺少必填字段: {field}")
    
    def _validate_stock_code(self, code: Any) -> None:
        """检查股票代码格式"""
        if not code:
            return
        
        code_str = str(code).strip().upper()
        
        # 移除可能的市场前缀
        if code_str.startswith(('SH', 'SZ', 'BJ')):
            code_str = code_str[2:]
        
        if not self.STOCK_CODE_PATTERN.match(code_str):
            self.errors.append(f"股票代码格式错误: {code}")
    
    def _validate_price(self, price: Any) -> None:
        """检查价格范围"""
        if price is None:
            return
        
        try:
            price_val = float(price)
            if price_val < self.MIN_PRICE or price_val > self.MAX_PRICE:
                self.warnings.append(f"价格超出常规范围: {price_val}")
        except (ValueError, TypeError):
            self.errors.append(f"价格格式错误: {price}")
    
    def _validate_market_cap(self, market_cap: Any) -> None:
        """检查市值范围"""
        if market_cap is None:
            return
        
        try:
            cap_val = float(market_cap)
            if cap_val < self.MIN_MARKET_CAP or cap_val > self.MAX_MARKET_CAP:
                self.warnings.append(f"市值超出常规范围: {cap_val}")
        except (ValueError, TypeError):
            self.warnings.append(f"市值格式错误: {market_cap}")
    
    def sanitize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理和标准化数据
        
        Returns:
            Dict[str, Any]: 清理后的数据
        """
        cleaned = {}
        
        # 股票代码：大写、去空格、移除市场前缀
        code = str(data.get('stock_code', '')).strip().upper()
        code = code.replace('SH', '').replace('SZ', '').replace('BJ', '')
        cleaned['stock_code'] = code
        
        # 股票名称：去空格
        cleaned['stock_name'] = str(data.get('stock_name', '')).strip()
        
        # 当前阶段：去空格，设默认值
        stage = data.get('current_stage', '未标记')
        cleaned['current_stage'] = str(stage).strip() if stage else '未标记'
        
        # 价格：转浮点数
        try:
            cleaned['current_price'] = float(data.get('current_price', 0))
        except (ValueError, TypeError):
            cleaned['current_price'] = 0.0
        
        # 市值：转浮点数
        try:
            cleaned['market_cap'] = float(data.get('market_cap', 0))
        except (ValueError, TypeError):
            cleaned['market_cap'] = 0.0
        
        # 保留其他字段
        for key, value in data.items():
            if key not in cleaned:
                cleaned[key] = value
        
        return cleaned
    
    @staticmethod
    def is_valid_stock_code(code: str) -> bool:
        """快速检查股票代码是否有效"""
        if not code:
            return False
        code = str(code).strip().upper()
        if code.startswith(('SH', 'SZ', 'BJ')):
            code = code[2:]
        return bool(StockDataValidator.STOCK_CODE_PATTERN.match(code))


class DataSourceValidator:
    """数据源响应校验器"""
    
    def validate_eastmoney_response(self, data: Dict[str, Any]) -> ValidationResult:
        """校验东方财富API响应"""
        errors = []
        warnings = []
        
        if not isinstance(data, dict):
            errors.append("响应格式错误：应为字典")
            return ValidationResult(False, errors, warnings)
        
        if 'data' not in data:
            errors.append("响应缺少data字段")
            return ValidationResult(False, errors, warnings)
        
        data_obj = data.get('data', {})
        if not data_obj:
            warnings.append("data字段为空")
        
        if 'diff' not in data_obj:
            warnings.append("响应缺少diff字段（股票列表）")
        
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    def validate_tencent_response(self, text: str) -> ValidationResult:
        """校验腾讯财经API响应"""
        errors = []
        warnings = []
        
        if not text or text.strip() == '':
            errors.append("响应为空")
            return ValidationResult(False, errors, warnings)
        
        if 'v_pv_none_match' in text:
            warnings.append("部分股票代码无匹配")
        
        return ValidationResult(len(errors) == 0, errors, warnings)
