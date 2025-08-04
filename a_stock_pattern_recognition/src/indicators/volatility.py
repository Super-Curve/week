"""
波动率指标计算模块
包含ATR、历史波动率、Bollinger Bands等指标
"""

import numpy as np
import pandas as pd
from typing import Union, Tuple


class VolatilityIndicators:
    """波动率指标计算类"""
    
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, 
                     period: int = 14) -> pd.Series:
        """
        计算平均真实波幅(ATR)
        
        Parameters:
        -----------
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        period: ATR周期
        
        Returns:
        --------
        ATR序列
        """
        # 计算真实波幅
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # 计算ATR
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    @staticmethod
    def calculate_atr_percent(high: pd.Series, low: pd.Series, close: pd.Series, 
                            period: int = 14) -> pd.Series:
        """
        计算ATR百分比
        
        Returns:
        --------
        ATR百分比序列
        """
        atr = VolatilityIndicators.calculate_atr(high, low, close, period)
        atr_percent = (atr / close) * 100
        
        return atr_percent
    
    @staticmethod
    def calculate_historical_volatility(close: pd.Series, period: int = 20, 
                                      annualize: bool = True) -> pd.Series:
        """
        计算历史波动率
        
        Parameters:
        -----------
        close: 收盘价序列
        period: 计算周期
        annualize: 是否年化
        
        Returns:
        --------
        历史波动率序列
        """
        # 计算对数收益率
        log_returns = np.log(close / close.shift(1))
        
        # 计算滚动标准差
        hv = log_returns.rolling(window=period).std()
        
        # 年化处理（假设一年250个交易日）
        if annualize:
            hv = hv * np.sqrt(250)
        
        return hv
    
    @staticmethod
    def calculate_bollinger_bands(close: pd.Series, period: int = 20, 
                                num_std: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        计算布林带
        
        Parameters:
        -----------
        close: 收盘价序列
        period: 移动平均周期
        num_std: 标准差倍数
        
        Returns:
        --------
        (中轨, 上轨, 下轨)
        """
        # 计算中轨（移动平均）
        middle_band = close.rolling(window=period).mean()
        
        # 计算标准差
        std = close.rolling(window=period).std()
        
        # 计算上下轨
        upper_band = middle_band + (std * num_std)
        lower_band = middle_band - (std * num_std)
        
        return middle_band, upper_band, lower_band
    
    @staticmethod
    def calculate_bollinger_width(close: pd.Series, period: int = 20, 
                                num_std: float = 2) -> pd.Series:
        """
        计算布林带宽度
        
        Returns:
        --------
        布林带宽度序列
        """
        _, upper_band, lower_band = VolatilityIndicators.calculate_bollinger_bands(
            close, period, num_std
        )
        
        # 计算带宽百分比
        bb_width = ((upper_band - lower_band) / close) * 100
        
        return bb_width
    
    @staticmethod
    def calculate_dynamic_volatility(high: pd.Series, low: pd.Series, close: pd.Series,
                                   atr_period: int = 14, hv_period: int = 20,
                                   bb_period: int = 20, weights: list = None) -> pd.Series:
        """
        计算综合动态波动率
        
        Parameters:
        -----------
        high, low, close: 价格序列
        atr_period: ATR周期
        hv_period: 历史波动率周期
        bb_period: 布林带周期
        weights: 各指标权重 [atr_weight, hv_weight, bb_weight]
        
        Returns:
        --------
        综合波动率序列
        """
        if weights is None:
            weights = [0.4, 0.3, 0.3]  # 默认权重
        
        # 计算各波动率指标
        atr_pct = VolatilityIndicators.calculate_atr_percent(high, low, close, atr_period)
        hv = VolatilityIndicators.calculate_historical_volatility(close, hv_period, False) * 100
        bb_width = VolatilityIndicators.calculate_bollinger_width(close, bb_period)
        
        # 标准化处理
        atr_norm = (atr_pct - atr_pct.rolling(50).mean()) / atr_pct.rolling(50).std()
        hv_norm = (hv - hv.rolling(50).mean()) / hv.rolling(50).std()
        bb_norm = (bb_width - bb_width.rolling(50).mean()) / bb_width.rolling(50).std()
        
        # 加权计算
        dynamic_vol = (weights[0] * atr_norm + 
                      weights[1] * hv_norm + 
                      weights[2] * bb_norm)
        
        return dynamic_vol
    
    @staticmethod
    def get_volatility_regime(volatility: pd.Series, 
                            thresholds: list = None) -> pd.Series:
        """
        判断波动率状态
        
        Parameters:
        -----------
        volatility: 波动率序列
        thresholds: 阈值列表 [低, 中, 高]
        
        Returns:
        --------
        波动率状态序列 (1: 低波动, 2: 中波动, 3: 高波动)
        """
        if thresholds is None:
            # 使用分位数作为默认阈值
            thresholds = [
                volatility.quantile(0.33),
                volatility.quantile(0.67)
            ]
        
        regime = pd.Series(index=volatility.index, dtype=int)
        regime[volatility <= thresholds[0]] = 1  # 低波动
        regime[(volatility > thresholds[0]) & (volatility <= thresholds[1])] = 2  # 中波动
        regime[volatility > thresholds[1]] = 3  # 高波动
        
        return regime