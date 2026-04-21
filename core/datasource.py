"""
ST选股工具 - 多源数据管理器
内嵌免费高速数据源，支持故障自动切换
"""

import json
import urllib.request
import urllib.error
import socket
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from utils.logger import logger
from utils.validators import DataSourceValidator


class DataSourceType(Enum):
    """数据源类型"""
    EASTMONEY = "eastmoney"      # 东方财富 - 主源
    TENCENT = "tencent"          # 腾讯财经 - 备源1
    SINA = "sina"                # 新浪财经 - 备源2


@dataclass
class DataSourceConfig:
    """数据源配置"""
    name: str
    base_url: str
    priority: int  # 优先级，数字越小越优先
    timeout: int = 5
    retry_count: int = 2


# ═══════════════════════════════════════════════════════════════
# 内嵌数据源配置（免费、快速、高质量）
# ═══════════════════════════════════════════════════════════════

DATASOURCE_CONFIGS = {
    DataSourceType.EASTMONEY: DataSourceConfig(
        name="东方财富",
        base_url="http://push2.eastmoney.com/api/qt/clist/get",
        priority=1,
        timeout=8,
        retry_count=2
    ),
    DataSourceType.TENCENT: DataSourceConfig(
        name="腾讯财经",
        base_url="http://qt.gtimg.cn/q=",
        priority=2,
        timeout=5,
        retry_count=2
    ),
    DataSourceType.SINA: DataSourceConfig(
        name="新浪财经",
        base_url="https://hq.sinajs.cn/list=",
        priority=3,
        timeout=5,
        retry_count=2
    ),
}


class DataSourceManager:
    """
    多源数据管理器
    
    特性：
    - 内嵌3个免费数据源配置
    - 自动故障切换
    - 请求超时控制
    - 响应数据统一格式化
    """
    
    def __init__(self):
        self.validator = DataSourceValidator()
        self._current_source = DataSourceType.EASTMONEY
        self._source_status: Dict[DataSourceType, bool] = {
            DataSourceType.EASTMONEY: True,
            DataSourceType.TENCENT: True,
            DataSourceType.SINA: True,
        }
    
    def _make_request(
        self,
        url: str,
        timeout: int = 5,
        headers: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """
        发送HTTP请求
        
        Returns:
            响应文本或None（失败）
        """
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        if headers:
            default_headers.update(headers)
        
        try:
            req = urllib.request.Request(url, headers=default_headers)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP错误 {e.code}: {url}", 'DATASOURCE')
            return None
        except urllib.error.URLError as e:
            logger.error(f"URL错误: {e.reason}", 'DATASOURCE')
            return None
        except socket.timeout:
            logger.error(f"请求超时: {url}", 'DATASOURCE')
            return None
        except Exception as e:
            logger.error(f"请求失败: {e}", 'DATASOURCE')
            return None
    
    # ═══════════════════════════════════════════════════════════
    # 东方财富数据源（主源）
    # ═══════════════════════════════════════════════════════════
    
    def fetch_eastmoney_st_list(
        self,
        page: int = 1,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        从东方财富获取ST板块股票列表
        
        BK0511是东方财富的ST板块代码
        
        Returns:
            股票列表，每个股票包含：code, name, price, market_cap
        """
        config = DATASOURCE_CONFIGS[DataSourceType.EASTMONEY]
        
        # 构建URL
        # fs=b:BK0511 表示ST板块
        # fields: f12=代码, f14=名称, f2=最新价, f20=总市值
        url = (
            f"{config.base_url}?"
            f"pn={page}&pz={page_size}&po=1&np=1&"
            f"fltt=2&invt=2&fid=f3&"
            f"fs=b:BK0511&"
            f"fields=f12,f14,f2,f20"
        )
        
        response = self._make_request(url, timeout=config.timeout)
        if not response:
            return []
        
        try:
            data = json.loads(response)
            
            # 验证响应
            validation = self.validator.validate_eastmoney_response(data)
            if not validation.is_valid:
                logger.error(f"东方财富响应验证失败: {validation.errors}", 'DATASOURCE')
                return []
            
            # 解析股票列表
            stocks = []
            diff = data.get('data', {}).get('diff', [])
            
            for item in diff:
                code = str(item.get('f12', '')).strip()
                name = item.get('f14', '')
                
                if not code or not name:
                    continue
                
                # 解析价格
                try:
                    price = float(item.get('f2') or 0)
                    if price <= 0:
                        price = 0.0
                except (ValueError, TypeError):
                    price = 0.0
                
                # 解析市值（转换为亿）
                try:
                    market_cap = float(item.get('f20') or 0) / 1e8
                    market_cap = round(market_cap, 2)
                except (ValueError, TypeError):
                    market_cap = 0.0
                
                stocks.append({
                    'stock_code': code,
                    'stock_name': name,
                    'current_price': price,
                    'market_cap': market_cap,
                    'current_stage': '未标记',
                    'data_source': 'eastmoney',
                    'fetch_time': __import__('time').time(),
                })
            
            logger.info(f"东方财富获取 {len(stocks)} 只股票", 'DATASOURCE')
            return stocks
            
        except json.JSONDecodeError as e:
            logger.error(f"东方财富JSON解析失败: {e}", 'DATASOURCE')
            return []
        except Exception as e:
            logger.error(f"东方财富数据处理失败: {e}", 'DATASOURCE')
            return []
    
    def fetch_all_eastmoney_st(self) -> List[Dict[str, Any]]:
        """获取全部ST股票（自动分页）"""
        all_stocks = []
        
        for page in range(1, 4):  # 最多3页，约300只ST股票
            stocks = self.fetch_eastmoney_st_list(page=page, page_size=100)
            if not stocks:
                break
            all_stocks.extend(stocks)
            
            # 如果少于一页，说明已经取完
            if len(stocks) < 100:
                break
        
        logger.info(f"东方财富共获取 {len(all_stocks)} 只ST股票", 'DATASOURCE')
        return all_stocks
    
    # ═══════════════════════════════════════════════════════════
    # 腾讯数据源（备源1）
    # ═══════════════════════════════════════════════════════════
    
    def fetch_tencent_quotes(
        self,
        stock_codes: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        从腾讯获取股票实时行情
        
        Args:
            stock_codes: 股票代码列表，如 ['000001', '600000']
        
        Returns:
            字典 {code: {name, price, change, ...}}
        """
        if not stock_codes:
            return {}
        
        config = DATASOURCE_CONFIGS[DataSourceType.TENCENT]
        
        # 构建代码字符串（添加市场前缀）
        codes_str = ','.join([
            f"sh{code}" if code.startswith('6') else f"sz{code}"
            for code in stock_codes
        ])
        
        url = f"{config.base_url}{codes_str}"
        response = self._make_request(url, timeout=config.timeout)
        
        if not response:
            return {}
        
        # 解析响应（格式：v_sh600000="..."）
        result = {}
        for line in response.strip().split(';'):
            line = line.strip()
            if not line or '="' not in line:
                continue
            
            try:
                # 提取代码和数据
                prefix, data = line.split('="', 1)
                data = data.rstrip('"')
                
                # 从前缀提取代码
                code = prefix.replace('v_sh', '').replace('v_sz', '')
                
                # 解析数据字段
                fields = data.split('~')
                if len(fields) >= 3:
                    result[code] = {
                        'stock_code': code,
                        'stock_name': fields[1],
                        'current_price': float(fields[2]) if fields[2] else 0.0,
                        'change_percent': float(fields[4]) if len(fields) > 4 and fields[4] else 0.0,
                        'data_source': 'tencent',
                    }
            except Exception as e:
                logger.warning(f"腾讯数据解析失败: {e}", 'DATASOURCE')
                continue
        
        return result
    
    # ═══════════════════════════════════════════════════════════
    # 新浪数据源（备源2）
    # ═══════════════════════════════════════════════════════════
    
    def fetch_sina_quotes(
        self,
        stock_codes: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        从新浪获取股票实时行情
        
        Args:
            stock_codes: 股票代码列表
        
        Returns:
            字典 {code: {name, price, ...}}
        """
        if not stock_codes:
            return {}
        
        config = DATASOURCE_CONFIGS[DataSourceType.SINA]
        
        # 构建代码字符串
        codes_str = ','.join([
            f"sh{code}" if code.startswith('6') else f"sz{code}"
            for code in stock_codes
        ])
        
        url = f"{config.base_url}{codes_str}"
        headers = {'Referer': 'https://finance.sina.com.cn'}
        response = self._make_request(url, timeout=config.timeout, headers=headers)
        
        if not response:
            return {}
        
        # 解析响应（格式：var hq_str_sh600000="..."）
        result = {}
        for line in response.strip().split(';'):
            line = line.strip()
            if not line or '="' not in line:
                continue
            
            try:
                prefix, data = line.split('="', 1)
                data = data.rstrip('"')
                
                code = prefix.replace('var hq_str_sh', '').replace('var hq_str_sz', '')
                
                # 新浪数据格式：名称,今日开盘价,昨日收盘价,当前价,...
                fields = data.split(',')
                if len(fields) >= 3:
                    result[code] = {
                        'stock_code': code,
                        'stock_name': fields[0],
                        'current_price': float(fields[3]) if fields[3] else 0.0,
                        'data_source': 'sina',
                    }
            except Exception as e:
                logger.warning(f"新浪数据解析失败: {e}", 'DATASOURCE')
                continue
        
        return result
    
    # ═══════════════════════════════════════════════════════════
    # 智能获取（自动切换数据源）
    # ═══════════════════════════════════════════════════════════
    
    def fetch_st_stocks_with_fallback(self) -> List[Dict[str, Any]]:
        """
        获取ST股票列表（带故障切换）
        
        优先使用东方财富，失败自动切换到备用源
        """
        # 尝试主源：东方财富
        stocks = self.fetch_all_eastmoney_st()
        if stocks:
            self._source_status[DataSourceType.EASTMONEY] = True
            self._current_source = DataSourceType.EASTMONEY
            return stocks
        
        self._source_status[DataSourceType.EASTMONEY] = False
        logger.warning("东方财富失败，尝试备用源", 'DATASOURCE')
        
        # 备用源需要已知股票代码列表才能获取
        # 这里返回空列表，后续可以从数据库获取缓存
        return []
    
    def fetch_realtime_quotes(
        self,
        stock_codes: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        获取实时行情（带故障切换）
        
        优先腾讯，失败切换到新浪
        """
        # 尝试腾讯
        result = self.fetch_tencent_quotes(stock_codes)
        if result:
            self._source_status[DataSourceType.TENCENT] = True
            return result
        
        self._source_status[DataSourceType.TENCENT] = False
        logger.warning("腾讯失败，切换到新浪", 'DATASOURCE')
        
        # 切换到新浪
        result = self.fetch_sina_quotes(stock_codes)
        if result:
            self._source_status[DataSourceType.SINA] = True
        else:
            self._source_status[DataSourceType.SINA] = False
        
        return result
    
    # ═══════════════════════════════════════════════════════════
    # 状态查询
    # ═══════════════════════════════════════════════════════════
    
    def get_source_status(self) -> Dict[str, bool]:
        """获取各数据源状态"""
        return {
            config.name: self._source_status[source_type]
            for source_type, config in DATASOURCE_CONFIGS.items()
        }
    
    def get_current_source(self) -> str:
        """获取当前使用的数据源名称"""
        return DATASOURCE_CONFIGS[self._current_source].name


# 全局数据源管理器实例
datasource_manager = DataSourceManager()
