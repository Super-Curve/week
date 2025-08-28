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
        
        # 年化波动率的计算：日/周收益率标准差 × √年周期数
        # 这个计算与实际使用多少数据无关，只与数据频率有关
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
                market_value = self._parse_market_value(row['total_market_value'])
                
                # 计算市值分类
                if market_value >= 500:
                    category = '大盘股'
                elif market_value >= 100:
                    category = '中盘股'
                else:
                    category = '小盘股'
                
                stock_info[code] = {
                    'name': row['stock_name'],
                    'market_value': market_value,
                    'ipo_date': row['ipo_date'],
                    'market_cap_category': category
                }
            
            return stock_info
            
        except Exception as e:
            print(f"获取股票信息失败: {e}")
            return {}
    
    def _parse_market_value(self, value_str: str) -> float:
        """解析市值字符串（处理'亿'等单位）"""
        if pd.isna(value_str) or value_str == '':
            return 0.0
        
        # 转换为字符串并去除空格
        value_str = str(value_str).strip()
        
        # 如果包含'亿'，直接返回数字部分
        if '亿' in value_str:
            try:
                return float(value_str.replace('亿', '').strip())
            except:
                return 0.0
        
        # 尝试直接转换
        try:
            return float(value_str)/100000000
        except:
            return 0.0
    
    def filter_stocks(self, codes: List[str], stock_info: Dict[str, Dict], 
                     min_ipo_days: int = 365) -> List[str]:
        """
        过滤股票（排除ST、U股、上市时间不足的股票）
        
        Args:
            codes: 股票代码列表
            stock_info: 股票信息字典
            min_ipo_days: 最少上市天数要求
            
        Returns:
            过滤后的股票代码列表
        """
        filtered_codes = []
        today = datetime.now()
        
        for code in codes:
            # 检查是否是ST或U股
            info = stock_info.get(code, {})
            name = info.get('name', '')
            
            if 'ST' in name or name.endswith('-U'):
                continue

            # 过滤港股和北交所
            if code.endswith('HK') or code.endswith('BJ'):
                continue
            
            # 检查上市时间
            if min_ipo_days > 0:
                ipo_date_str = info.get('ipo_date')
                if ipo_date_str:
                    try:
                        ipo_date = pd.to_datetime(ipo_date_str)
                        days_listed = (today - ipo_date).days
                        if days_listed < min_ipo_days:
                            continue
                    except:
                        pass
            
            filtered_codes.append(code)
        
        return filtered_codes
    
    def long_term_strategy(self, stock_data_dict: Dict[str, pd.DataFrame], 
                          stock_info: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        中长期策略筛选
        条件：最近一年的年化波动率40%-50%，年化夏普率≥0.5
        """
        results = {}
        
        for code, df in stock_data_dict.items():
            # 使用最近一年数据（52周）
            recent_data = df.tail(52)
            if len(recent_data) < 52:
                continue
            
            prices = recent_data['close']
            
            # 计算指标
            volatility, sharpe = self.calculate_volatility_and_sharpe(prices)
            
            # 判断是否符合条件
            if 0.4 <= volatility <= 0.5 and sharpe >= 0.5:
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
    
    def recommend_strategy(self, volatility: float, sharpe: float) -> str:
        """
        根据指标推荐策略类型
        
        Returns:
            'long_term' 或 'short_term'
        """
        # 中长期策略：波动率适中(40%-50%)，夏普比率较高(≥0.5)
        if 0.4 <= volatility <= 0.5 and sharpe >= 0.5:
            return 'long_term'
        # 短期策略：波动率较高(≥50%)，夏普比率>1
        elif volatility >= 0.5 and sharpe > 1:
            return 'short_term'
        else:
            return 'long_term'
    
    def short_term_strategy(self, stock_data_dict: Dict[str, pd.DataFrame], 
                           stock_info: Dict[str, Dict], use_daily_data: bool = False) -> Dict[str, Dict]:
        """
        短期波段策略筛选
        条件：最近6个月的年化波动率≥50%，夏普比率>1
        
        Args:
            stock_data_dict: 股票数据字典
            stock_info: 股票信息字典  
            use_daily_data: 是否使用日线数据（True）还是周线数据（False）
        """
        results = {}

        print(f"开始执行短期波段策略筛选，使用{use_daily_data}数据")
        
        # 根据数据类型设置参数
        if use_daily_data:
            # 日线：6个月约120个交易日
            data_points_6months = 120
            periods_per_year = 252
        else:
            # 周线：6个月约26周
            data_points_6months = 26
            periods_per_year = 52
        
        for code, df in stock_data_dict.items():
            # 检查数据是否足够
            if len(df) < data_points_6months:
                print(f"股票 {code}: 数据不足，跳过")
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


            print(f"股票 {code}: 波动率={volatility:.1%}, 夏普={sharpe:.2f}")
            
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
    
    def find_t2_and_entry_point(self, data: pd.DataFrame, pivot_result: dict) -> dict:
        """
        查找T2和入场点
        
        Args:
            data: 股票数据
            pivot_result: 高低点分析结果
            
        Returns:
            包含T2和入场点信息的字典
        """
        try:
            # 获取过滤后的高低点
            filtered_lows = pivot_result.get('filtered_pivot_lows', [])
            filtered_highs = pivot_result.get('filtered_pivot_highs', [])
            
            if not filtered_lows or not filtered_highs:
                return {}
            
            # 找到T1（最低点）
            lows = data['low'].values
            valid_lows = [idx for idx in filtered_lows if 0 <= idx < len(lows)]
            if not valid_lows:
                return {}
            
            t1_idx = min(valid_lows, key=lambda i: lows[i])
            t1_date = data.index[t1_idx]
            t1_price = lows[t1_idx]
            
            # 找到T2（T1之后的第一个高点）
            t2_candidates = [idx for idx in filtered_highs if idx > t1_idx]
            if not t2_candidates:
                return {'t1_date': t1_date, 't1_price': t1_price}
            
            t2_idx = min(t2_candidates)
            t2_date = data.index[t2_idx]
            t2_price = data['high'].iloc[t2_idx]
            
            # 找入场点（T2后半年第一个高于T2的点）
            half_year_later_idx = t2_idx + 26  # 26周约等于半年
            
            entry_date = None
            entry_price = None
            entry_idx = None
            
            if half_year_later_idx < len(data):
                for idx in range(half_year_later_idx, len(data)):
                    if data['high'].iloc[idx] > t2_price:
                        entry_idx = idx
                        entry_date = data.index[idx]
                        entry_price = data['close'].iloc[idx]  # 使用收盘价作为入场价
                        break
            
            result = {
                't1_date': t1_date,
                't1_price': t1_price,
                't1_idx': t1_idx,
                't2_date': t2_date,
                't2_price': t2_price,
                't2_idx': t2_idx
            }
            
            if entry_date is not None:
                result.update({
                    'entry_date': entry_date,
                    'entry_price': entry_price,
                    'entry_idx': entry_idx,
                    'wait_periods': entry_idx - t2_idx  # 等待周期数
                })
            
            return result
            
        except Exception as e:
            print(f"计算T2和入场点时出错: {e}")
            return {}