"""
ST选股工具 - 实时行情数据获取
双源容错：东方财富 + 腾讯财经
"""

import json
import urllib.request
import urllib.error
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from utils.logger import logger


@dataclass
class QuoteResult:
    """行情获取结果"""
    success: bool
    message: str
    data: Dict[str, Dict[str, Any]]  # code -> quote_data
    source: str = ""


class RealtimeQuoteFetcher:
    """
    实时行情获取器
    
    数据源优先级：
    1. 东方财富 ST板块API（批量获取，字段丰富）
    2. 腾讯财经 qt.gtimg.cn（单只/批量，稳定）
    """

    # 东方财富：ST板块列表API
    EASTMONEY_ST_URL = (
        "http://push2.eastmoney.com/api/qt/clist/get"
        "?pn=1&pz=5000&po=1&np=1&fltt=2&invt=2"
        "&fid=f12&fs=m:0+t:13,m:1+t:2"
        "&fields=f12,f13,f14,f2,f3,f4,f5,f6,f7,f8,f9,f10,f15,f16,f17,f18,f20,f21,f23,f33,f34,f35,f36,f37,f38,f39,f40,f41,f42,f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f57,f58,f60,f61,f62,f63,f64,f65,f66,f67,f68,f69,f70,f71,f72,f73,f74,f75,f76,f77,f78,f79,f80,f81,f82,f83,f84,f85,f86,f87,f88,f89,f90,f91,f92,f93,f94,f95,f96,f97,f98,f99,f100"
    )

    # 腾讯财经：批量行情API
    TENCENT_BATCH_URL = "http://qt.gtimg.cn/q="

    # 腾讯字段映射（按返回顺序）
    # 返回格式: v_sh600000="1~浦发银行~600000~12.50~..."
    TENCENT_FIELD_MAP = {
        0: 'name',
        1: 'code',
        2: 'price',
        3: 'prev_close',
        4: 'open',
        5: 'volume',
        6: 'bid_volume',  # 外盘
        7: 'ask_volume',  # 内盘
        8: 'bid1', 9: 'bid1_volume',
        10: 'bid2', 11: 'bid2_volume',
        12: 'bid3', 13: 'bid3_volume',
        14: 'bid4', 15: 'bid4_volume',
        16: 'bid5', 17: 'bid5_volume',
        18: 'ask1', 19: 'ask1_volume',
        20: 'ask2', 21: 'ask2_volume',
        22: 'ask3', 23: 'ask3_volume',
        24: 'ask4', 25: 'ask4_volume',
        26: 'ask5', 27: 'ask5_volume',
        32: 'high', 33: 'low',
        34: 'price',  # 重复
        35: 'latest_volume',  # 现量
        36: 'turnover_rate',
        37: 'pe_ratio',
        38: 'amplitude',
        43: 'change_amount',
        44: 'change_percent',
        45: 'volume',  # 总量(手)
        46: 'amount',  # 成交额(万)
        47: 'pb_ratio',
        48: 'market_cap',  # 总市值(万)
        49: 'circulating_market_cap',  # 流通市值(万)
        50: 'turnover_rate',  # 重复
    }

    def __init__(self):
        self.timeout = 10

    def fetch_batch(self, stock_codes: List[str]) -> QuoteResult:
        """
        批量获取实时行情
        
        优先尝试东方财富，失败回退腾讯
        """
        if not stock_codes:
            return QuoteResult(True, "无股票代码", {})

        # 先尝试东方财富（字段最丰富，批量获取）
        result = self._fetch_from_eastmoney(stock_codes)
        if result.success and result.data:
            return result

        # 回退腾讯
        logger.info("东方财富获取失败，回退腾讯财经")
        result = self._fetch_from_tencent(stock_codes)
        return result

    def _fetch_from_eastmoney(self, stock_codes: List[str]) -> QuoteResult:
        """从东方财富获取ST板块行情"""
        try:
            req = urllib.request.Request(
                self.EASTMONEY_ST_URL,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Referer': 'http://quote.eastmoney.com/',
                }
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                raw = response.read().decode('utf-8')

            data = json.loads(raw)
            if data.get('data') is None:
                return QuoteResult(False, "东方财富返回空数据", {})

            items = data['data'].get('diff', [])
            quotes = {}

            for item in items:
                code = str(item.get('f12', ''))
                if not code:
                    continue

                # 东方财富字段映射
                quote = {
                    'code': code,
                    'name': str(item.get('f14', '')),
                    'price': self._safe_float(item.get('f2')),
                    'change_percent': self._safe_float(item.get('f3')),
                    'change_amount': self._safe_float(item.get('f4')),
                    'volume': self._safe_float(item.get('f5')) / 100,  # 股 -> 手
                    'amount': self._safe_float(item.get('f6')) / 10000,  # 元 -> 万
                    'amplitude': self._safe_float(item.get('f7')),
                    'turnover_rate': self._safe_float(item.get('f8')),
                    'pe_ratio': self._safe_float(item.get('f9')),
                    'pb_ratio': self._safe_float(item.get('f23')),
                    'high_price': self._safe_float(item.get('f15')),
                    'low_price': self._safe_float(item.get('f16')),
                    'open_price': self._safe_float(item.get('f17')),
                    'prev_close': self._safe_float(item.get('f18')),
                    'market_cap': self._safe_float(item.get('f20')) / 100000000,  # 万 -> 亿
                    'circulating_market_cap': self._safe_float(item.get('f21')) / 100000000,
                    'source': 'eastmoney',
                }
                quotes[code] = quote

            return QuoteResult(
                True,
                f"东方财富获取成功: {len(quotes)} 只",
                quotes,
                "eastmoney"
            )

        except Exception as e:
            logger.error(f"东方财富行情获取失败: {e}")
            return QuoteResult(False, f"东方财富错误: {str(e)}", {})

    def _fetch_from_tencent(self, stock_codes: List[str]) -> QuoteResult:
        """从腾讯财经获取行情"""
        try:
            # 转换代码格式：sh600000,sz000001
            tencent_codes = []
            for code in stock_codes:
                code = code.strip().upper()
                if code.startswith('6'):
                    tencent_codes.append(f"sh{code}")
                else:
                    tencent_codes.append(f"sz{code}")

            url = self.TENCENT_BATCH_URL + ','.join(tencent_codes)
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Referer': 'http://qt.gtimg.cn/',
                }
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                raw = response.read().decode('gb2312', errors='replace')

            quotes = {}
            for line in raw.strip().split(';'):
                line = line.strip()
                if not line or 'v_' not in line:
                    continue

                # 解析: v_sh600000="1~浦发银行~600000~12.50~...";
                match = re.search(r'v_[^=]+="([^"]*)"', line)
                if not match:
                    continue

                parts = match.group(1).split('~')
                if len(parts) < 35:
                    continue

                code = parts[2] if len(parts) > 2 else ''
                if not code:
                    continue

                price = self._safe_float(parts[3]) if len(parts) > 3 else 0
                prev_close = self._safe_float(parts[4]) if len(parts) > 4 else 0
                change_amount = price - prev_close if price and prev_close else 0
                change_percent = (change_amount / prev_close * 100) if prev_close else 0

                quote = {
                    'code': code,
                    'name': parts[1] if len(parts) > 1 else '',
                    'price': price,
                    'change_percent': change_percent,
                    'change_amount': change_amount,
                    'volume': self._safe_float(parts[5]) / 100 if len(parts) > 5 else 0,  # 股->手
                    'amount': self._safe_float(parts[37]) if len(parts) > 37 else 0,  # 成交额
                    'amplitude': self._safe_float(parts[38]) if len(parts) > 38 else 0,
                    'turnover_rate': self._safe_float(parts[36]) if len(parts) > 36 else 0,
                    'pe_ratio': self._safe_float(parts[37]) if len(parts) > 37 else 0,
                    'pb_ratio': self._safe_float(parts[47]) if len(parts) > 47 else 0,
                    'high_price': self._safe_float(parts[33]) if len(parts) > 33 else 0,
                    'low_price': self._safe_float(parts[34]) if len(parts) > 34 else 0,
                    'open_price': self._safe_float(parts[5]) if len(parts) > 5 else 0,
                    'prev_close': prev_close,
                    'market_cap': self._safe_float(parts[48]) / 100000000 if len(parts) > 48 else 0,
                    'circulating_market_cap': self._safe_float(parts[49]) / 100000000 if len(parts) > 49 else 0,
                    'source': 'tencent',
                }
                quotes[code] = quote

            return QuoteResult(
                True,
                f"腾讯财经获取成功: {len(quotes)} 只",
                quotes,
                "tencent"
            )

        except Exception as e:
            logger.error(f"腾讯财经行情获取失败: {e}")
            return QuoteResult(False, f"腾讯错误: {str(e)}", {})

    @staticmethod
    def _safe_float(value) -> float:
        """安全转换为float"""
        if value is None or value == '' or value == '-':
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0


# 全局实例
quote_fetcher = RealtimeQuoteFetcher()
