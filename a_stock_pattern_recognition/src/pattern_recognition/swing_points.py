"""
基于波动率过滤的高低点识别模块
核心算法：通过动态波动率阈值过滤噪音，识别真正的高低点
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SwingPoint:
    """摆动点数据结构"""
    index: int
    date: datetime
    price: float
    point_type: str  # 'high' or 'low'
    volume: float
    volatility: float
    confirmed: bool = False
    
    
class SwingPointDetector:
    """基于波动率过滤的高低点检测器"""
    
    def __init__(self, lookback_window: int = 50, 
                 volatility_factor: float = 1.5,
                 time_confirm: int = 3,
                 volume_factor: float = 1.2):
        """
        初始化检测器
        
        Parameters:
        -----------
        lookback_window: 回看窗口大小
        volatility_factor: 波动率过滤倍数
        time_confirm: 时间确认周期
        volume_factor: 成交量确认倍数
        """
        self.lookback_window = lookback_window
        self.volatility_factor = volatility_factor
        self.time_confirm = time_confirm
        self.volume_factor = volume_factor
        
    def detect_swing_points(self, data: pd.DataFrame, 
                          volatility: pd.Series) -> Dict[str, List[SwingPoint]]:
        """
        检测高低点
        
        Parameters:
        -----------
        data: 包含OHLCV的DataFrame
        volatility: 波动率序列
        
        Returns:
        --------
        {'highs': [SwingPoint], 'lows': [SwingPoint]}
        """
        # 初步识别局部极值点
        raw_highs, raw_lows = self._find_local_extremes(data)
        
        # 波动率过滤
        filtered_highs = self._volatility_filter(raw_highs, data, volatility, 'high')
        filtered_lows = self._volatility_filter(raw_lows, data, volatility, 'low')
        
        # 时间和成交量确认
        confirmed_highs = self._confirm_swing_points(filtered_highs, data, 'high')
        confirmed_lows = self._confirm_swing_points(filtered_lows, data, 'low')
        
        return {
            'highs': confirmed_highs,
            'lows': confirmed_lows
        }
    
    def _find_local_extremes(self, data: pd.DataFrame) -> Tuple[List[int], List[int]]:
        """
        查找局部极值点
        
        Returns:
        --------
        (高点索引列表, 低点索引列表)
        """
        high_prices = data['high'].values
        low_prices = data['low'].values
        
        highs = []
        lows = []
        
        # 使用滚动窗口查找局部极值
        for i in range(self.lookback_window, len(data) - self.lookback_window):
            # 局部最高点
            window_high = high_prices[i-self.lookback_window//2:i+self.lookback_window//2+1]
            if high_prices[i] == np.max(window_high):
                highs.append(i)
            
            # 局部最低点
            window_low = low_prices[i-self.lookback_window//2:i+self.lookback_window//2+1]
            if low_prices[i] == np.min(window_low):
                lows.append(i)
        
        return highs, lows
    
    def _volatility_filter(self, indices: List[int], data: pd.DataFrame,
                         volatility: pd.Series, point_type: str) -> List[SwingPoint]:
        """
        波动率过滤
        
        Parameters:
        -----------
        indices: 极值点索引列表
        data: 价格数据
        volatility: 波动率序列
        point_type: 'high' or 'low'
        
        Returns:
        --------
        过滤后的SwingPoint列表
        """
        filtered_points = []
        
        for i, idx in enumerate(indices):
            # 获取当前点的波动率
            current_vol = volatility.iloc[idx]
            median_vol = volatility.iloc[idx-20:idx].median()
            
            # 动态阈值
            threshold = median_vol * self.volatility_factor
            
            # 价格条件
            if point_type == 'high':
                price = data['high'].iloc[idx]
                # 查找前一个高点
                prev_high_idx = indices[i-1] if i > 0 else idx - self.lookback_window
                prev_high = data['high'].iloc[prev_high_idx]
                
                # 过滤条件：当前高点必须显著高于前高点
                if price > prev_high + threshold * data['close'].iloc[idx] / 100:
                    point = SwingPoint(
                        index=idx,
                        date=data.index[idx],
                        price=price,
                        point_type='high',
                        volume=data['volume'].iloc[idx],
                        volatility=current_vol
                    )
                    filtered_points.append(point)
                    
            else:  # low
                price = data['low'].iloc[idx]
                # 查找前一个低点
                prev_low_idx = indices[i-1] if i > 0 else idx - self.lookback_window
                prev_low = data['low'].iloc[prev_low_idx]
                
                # 过滤条件：当前低点必须显著低于前低点
                if price < prev_low - threshold * data['close'].iloc[idx] / 100:
                    point = SwingPoint(
                        index=idx,
                        date=data.index[idx],
                        price=price,
                        point_type='low',
                        volume=data['volume'].iloc[idx],
                        volatility=current_vol
                    )
                    filtered_points.append(point)
        
        return filtered_points
    
    def _confirm_swing_points(self, points: List[SwingPoint], 
                            data: pd.DataFrame, point_type: str) -> List[SwingPoint]:
        """
        时间和成交量确认
        
        Parameters:
        -----------
        points: SwingPoint列表
        data: 价格数据
        point_type: 'high' or 'low'
        
        Returns:
        --------
        确认后的SwingPoint列表
        """
        confirmed_points = []
        
        for point in points:
            idx = point.index
            
            # 时间确认：在后续N个周期内价格没有突破
            time_confirmed = True
            for j in range(1, min(self.time_confirm + 1, len(data) - idx)):
                if point_type == 'high':
                    if data['high'].iloc[idx + j] > point.price:
                        time_confirmed = False
                        break
                else:  # low
                    if data['low'].iloc[idx + j] < point.price:
                        time_confirmed = False
                        break
            
            # 成交量确认：伴随成交量放大
            avg_volume = data['volume'].iloc[idx-20:idx].mean()
            volume_confirmed = point.volume > avg_volume * self.volume_factor
            
            # 两个条件都满足才确认
            if time_confirmed and volume_confirmed:
                point.confirmed = True
                confirmed_points.append(point)
        
        return confirmed_points
    
    def get_swing_levels(self, swing_points: Dict[str, List[SwingPoint]], 
                        current_idx: int) -> Dict[str, float]:
        """
        获取当前的支撑和阻力位
        
        Parameters:
        -----------
        swing_points: 高低点字典
        current_idx: 当前索引
        
        Returns:
        --------
        {'resistance': float, 'support': float}
        """
        # 找到最近的确认高点作为阻力
        resistance = None
        for high in reversed(swing_points['highs']):
            if high.index < current_idx and high.confirmed:
                resistance = high.price
                break
        
        # 找到最近的确认低点作为支撑
        support = None
        for low in reversed(swing_points['lows']):
            if low.index < current_idx and low.confirmed:
                support = low.price
                break
        
        return {
            'resistance': resistance,
            'support': support
        }
    
    def identify_patterns(self, swing_points: Dict[str, List[SwingPoint]]) -> List[Dict]:
        """
        识别形态模式
        
        Parameters:
        -----------
        swing_points: 高低点字典
        
        Returns:
        --------
        形态列表
        """
        patterns = []
        highs = swing_points['highs']
        lows = swing_points['lows']
        
        # 双底形态
        if len(lows) >= 2:
            for i in range(len(lows) - 1):
                low1, low2 = lows[i], lows[i + 1]
                # 两个低点价格相近（误差在2%以内）
                if abs(low1.price - low2.price) / low1.price < 0.02:
                    # 中间有高点
                    middle_highs = [h for h in highs if low1.index < h.index < low2.index]
                    if middle_highs:
                        patterns.append({
                            'type': 'double_bottom',
                            'start_date': low1.date,
                            'end_date': low2.date,
                            'support_level': (low1.price + low2.price) / 2,
                            'target': middle_highs[0].price + (middle_highs[0].price - low1.price)
                        })
        
        # 双顶形态
        if len(highs) >= 2:
            for i in range(len(highs) - 1):
                high1, high2 = highs[i], highs[i + 1]
                # 两个高点价格相近（误差在2%以内）
                if abs(high1.price - high2.price) / high1.price < 0.02:
                    # 中间有低点
                    middle_lows = [l for l in lows if high1.index < l.index < high2.index]
                    if middle_lows:
                        patterns.append({
                            'type': 'double_top',
                            'start_date': high1.date,
                            'end_date': high2.date,
                            'resistance_level': (high1.price + high2.price) / 2,
                            'target': middle_lows[0].price - (high1.price - middle_lows[0].price)
                        })
        
        return patterns