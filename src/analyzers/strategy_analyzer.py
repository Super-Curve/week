# -*- coding: utf-8 -*-
"""
策略筛选分析器
用于筛选符合特定策略条件的股票标的池
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from sqlalchemy import text
import warnings

warnings.filterwarnings('ignore')


class StrategyAnalyzer:
    """
    策略筛选分析器
    
    用途:
    - 根据波动率、夏普比率等指标筛选符合策略条件的股票
    - 支持中长期策略和短期波段策略
    - 自动过滤ST股票、U股和上市时间不足的股票
    
    实现方式:
    - 计算年化波动率和夏普比率
    - 从数据库获取股票信息（名称、市值、上市日期）
    - 根据策略条件筛选合格标的
    """
    
    def __init__(self):
        self.risk_free_rate = 0.02  # 无风险利率默认2%
    
    def calculate_volatility_and_sharpe(self, prices: pd.Series, periods: int = 52, 
                                       actual_periods: int = None) -> Tuple[float, float]:
        """
        计算年化波动率和夏普比率
        
        Args:
            prices: 价格序列
            periods: 一年的周期数（周K线=52，日K线=252）
            actual_periods: 实际使用的数据周期数（如果不是全年数据）
            
        Returns:
            (年化波动率, 夏普比率)
        """
        if len(prices) < 2:
            return 0.0, 0.0
        
        # 计算收益率
        returns = prices.pct_change().dropna()
        if len(returns) == 0:
            return 0.0, 0.0
        
        # 如果指定了实际周期数，使用它来计算年化因子
        if actual_periods is not None:
            # 年化因子 = √(年周期数 / 实际周期数)
            annualization_factor = np.sqrt(periods / actual_periods)
            # 年化波动率 = 样本标准差 * 年化因子
            volatility = returns.std() * annualization_factor
        else:
            # 传统方式：假设数据代表完整周期
            volatility = returns.std() * np.sqrt(periods)
        
        # 计算实际的时间跨度（年）
        if actual_periods is not None:
            years = actual_periods / periods
        else:
            years = len(prices) / periods
            
        # 年化收益率
        total_return = (prices.iloc[-1] / prices.iloc[0]) - 1
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        # 夏普比率
        sharpe = (annualized_return - self.risk_free_rate) / volatility if volatility > 0 else 0
        
        return volatility, sharpe
    
    def get_stock_info(self, engine, stock_codes: List[str]) -> Dict[str, Dict]:
        """
        从数据库获取股票信息
        
        Returns:
            {stock_code: {'name': str, 'market_value': float, 'ipo_date': str, 'market_cap_category': str}}
        """
        if not stock_codes:
            return {}
        
        placeholders = ','.join(['%s'] * len(stock_codes))
        query = f"""
        SELECT stock_code, stock_name, total_market_value, ipo_date
        FROM stock_info
        WHERE stock_code IN ({placeholders})
        """
        
        try:
            df = pd.read_sql(query, engine, params=tuple(stock_codes))
            stock_info = {}
            
            for _, row in df.iterrows():
                code = row['stock_code']
                market_value_str = row['total_market_value'] or '0'
                
                # 解析市值（处理各种格式，如"500亿"）
                market_value = self._parse_market_value(market_value_str)
                
                # 分类市值
                if market_value >= 500:
                    category = '大盘股'
                elif market_value >= 100:
                    category = '中盘股'
                else:
                    category = '小盘股'
                
                stock_info[code] = {
                    'name': row['stock_name'] or code,
                    'market_value': market_value,
                    'ipo_date': row['ipo_date'],
                    'market_cap_category': category
                }
            
            return stock_info
            
        except Exception as e:
            print(f"获取股票信息失败: {e}")
            return {}
    
    def _parse_market_value(self, value_str: str) -> float:
        """解析市值字符串，返回亿元为单位的数值"""
        if not value_str or value_str == '0':
            return 0.0
        
        try:
            # 移除空格和逗号
            value_str = value_str.replace(' ', '').replace(',', '')
            
            # 处理不同单位
            if '万亿' in value_str:
                return float(value_str.replace('万亿', '')) * 10000
            elif '亿' in value_str:
                return float(value_str.replace('亿', ''))
            elif '万' in value_str:
                return float(value_str.replace('万', '')) / 10000
            else:
                # 如果是纯数字，假设单位是元
                return float(value_str) / 100000000  # 转换为亿
        except:
            return 0.0
    
    def filter_stocks(self, stock_data: Dict[str, pd.DataFrame], stock_info: Dict[str, Dict], 
                     min_ipo_days: int = 365) -> Dict[str, pd.DataFrame]:
        """
        过滤不符合条件的股票
        
        Args:
            stock_data: 股票数据字典
            stock_info: 股票信息字典
            min_ipo_days: 最小上市天数
            
        Returns:
            过滤后的股票数据
        """
        filtered_data = {}
        today = datetime.now()
        
        # 统计过滤原因
        st_count = 0
        u_count = 0
        hk_count = 0
        ipo_count = 0
        bj_count = 0
        
        for code, df in stock_data.items():
            # 获取股票信息
            info = stock_info.get(code, {})
            name = info.get('name', '')
            ipo_date_str = info.get('ipo_date', '')
            
            # 过滤ST股票
            if 'ST' in name.upper():
                st_count += 1
                continue
            
            # 过滤U股
            if name.endswith('-U'):
                u_count += 1
                continue

            # 过滤港股
            if code.endswith('.HK'):
                hk_count += 1
                continue

            # 过滤北交所
            if code.endswith('.BJ'):
                bj_count += 1
                continue
            
            # 过滤上市时间不足的股票
            if ipo_date_str:
                try:
                    ipo_date = pd.to_datetime(ipo_date_str).to_pydatetime()
                    if (today - ipo_date).days < min_ipo_days:
                        ipo_count += 1
                        continue
                except:
                    pass  # 如果解析失败，不过滤
            
            filtered_data[code] = df
        
        # 输出过滤统计
        total_filtered = st_count + u_count + ipo_count
        if total_filtered > 0:
            print(f"\n🔍 股票过滤统计：")
            print(f"   原始股票数：{len(stock_data)}")
            print(f"   过滤ST股票：{st_count}")
            print(f"   过滤U股：{u_count}")
            print(f"   过滤港股：{hk_count}")
            print(f"   过滤北交所：{bj_count}")
            print(f"   过滤新股（<{min_ipo_days}天）：{ipo_count}")
            print(f"   剩余股票数：{len(filtered_data)}")
            print(f"   过滤比例：{total_filtered/len(stock_data)*100:.1f}%\n")
        
        return filtered_data
    
    def analyze_long_term_strategy(self, stock_data: Dict[str, pd.DataFrame], 
                                  stock_info: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        中长期策略筛选
        条件：
        - 最近一年的年化波动率：40% <= 波动率 < 50%
        - 最近一年的年化夏普率 >= 0.5
        """
        results = {}
        
        # 先过滤股票
        filtered_data = self.filter_stocks(stock_data, stock_info)
        
        for code, df in filtered_data.items():
            if len(df) < 52:  # 至少需要一年数据
                continue
            
            # 使用最近一年数据
            recent_data = df.tail(52)
            prices = recent_data['close']
            
            # 计算指标
            volatility, sharpe = self.calculate_volatility_and_sharpe(prices)
            
            # 判断是否符合条件
            if 0.4 <= volatility < 0.5 and sharpe >= 0.5:
                info = stock_info.get(code, {})
                results[code] = {
                    'volatility': volatility,
                    'sharpe': sharpe,
                    'name': info.get('name', code),
                    'market_cap_category': info.get('market_cap_category', '未知'),
                    'market_value': info.get('market_value', 0),
                    'data': df
                }
        
        return results
    
    def analyze_short_term_strategy(self, stock_data: Dict[str, pd.DataFrame], 
                                   stock_info: Dict[str, Dict], use_daily_data: bool = True) -> Dict[str, Dict]:
        """
        短期波段策略筛选
        条件：
        - 最近6个月的年化波动率 >= 50%
        - 最近6个月的夏普率 > 1
        
        Args:
            stock_data: 股票数据字典（可以是周线或日线）
            stock_info: 股票信息字典
            use_daily_data: 是否使用日线数据（True表示日线，False表示周线）
        """
        results = {}
        
        # 先过滤股票
        filtered_data = self.filter_stocks(stock_data, stock_info)
        
        # 根据数据类型设置参数
        if use_daily_data:
            # 日线数据：6个月约120个交易日
            min_data_points = 120
            data_points_6months = 120
            periods_per_year = 252  # 年化参数
        else:
            # 周线数据：6个月约26周
            min_data_points = 26
            data_points_6months = 26
            periods_per_year = 52  # 年化参数
        
        for code, df in filtered_data.items():
            if len(df) < min_data_points:  # 至少需要6个月数据
                continue
            
            # 使用最近6个月数据
            recent_data = df.tail(data_points_6months)
            prices = recent_data['close']
            
            # 计算指标（传入正确的年化参数和实际周期数）
            if use_daily_data:
                # 日线数据：120天约0.5年
                actual_trading_days = len(prices)
                volatility, sharpe = self.calculate_volatility_and_sharpe(
                    prices, 
                    periods=periods_per_year,
                    actual_periods=actual_trading_days
                )
            else:
                # 周线数据：26周约0.5年
                volatility, sharpe = self.calculate_volatility_and_sharpe(
                    prices, 
                    periods=periods_per_year
                )
            
            # 判断是否符合条件
            if volatility >= 0.5 and sharpe > 1:
                info = stock_info.get(code, {})
                results[code] = {
                    'volatility': volatility,
                    'sharpe': sharpe,
                    'name': info.get('name', code),
                    'market_cap_category': info.get('market_cap_category', '未知'),
                    'market_value': info.get('market_value', 0),
                    'data': df
                }
        
        return results
