"""
交易信号生成模块
基于高低点识别和形态模式生成买卖信号
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SignalType(Enum):
    """信号类型枚举"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    

@dataclass
class TradingSignal:
    """交易信号数据结构"""
    date: datetime
    signal_type: SignalType
    price: float
    confidence: float  # 信号置信度 0-1
    reason: str
    stop_loss: float
    take_profit: float
    position_size: float = 1.0
    

class SignalGenerator:
    """交易信号生成器"""
    
    def __init__(self, config: Dict):
        """
        初始化信号生成器
        
        Parameters:
        -----------
        config: 配置字典，包含交易参数
        """
        self.max_position_pct = config.get('max_position_pct', 0.2)
        self.stop_loss_pct = config.get('stop_loss_pct', 0.02)
        self.atr_stop_factor = config.get('atr_stop_factor', 2)
        self.profit_target_factor = config.get('profit_target_factor', 3)
        self.max_holding_days = config.get('max_holding_days', 20)
        
    def generate_signals(self, data: pd.DataFrame, swing_points: Dict,
                        volatility: pd.Series, atr: pd.Series,
                        patterns: List[Dict] = None) -> List[TradingSignal]:
        """
        生成交易信号
        
        Parameters:
        -----------
        data: OHLCV数据
        swing_points: 高低点字典
        volatility: 波动率序列
        atr: ATR序列
        patterns: 形态列表
        
        Returns:
        --------
        交易信号列表
        """
        signals = []
        
        # 基于高低点突破的信号
        breakout_signals = self._generate_breakout_signals(
            data, swing_points, volatility, atr
        )
        signals.extend(breakout_signals)
        
        # 基于形态的信号
        if patterns:
            pattern_signals = self._generate_pattern_signals(
                data, patterns, atr
            )
            signals.extend(pattern_signals)
        
        # 基于支撑阻力的信号
        support_resistance_signals = self._generate_sr_signals(
            data, swing_points, atr
        )
        signals.extend(support_resistance_signals)
        
        # 去重和优先级排序
        signals = self._filter_signals(signals)
        
        return signals
    
    def _generate_breakout_signals(self, data: pd.DataFrame, swing_points: Dict,
                                 volatility: pd.Series, atr: pd.Series) -> List[TradingSignal]:
        """
        生成突破信号
        """
        signals = []
        highs = swing_points['highs']
        lows = swing_points['lows']
        
        for i in range(len(data)):
            current_date = data.index[i]
            current_close = data['close'].iloc[i]
            current_volume = data['volume'].iloc[i]
            
            # 查找最近的高低点
            recent_high = None
            recent_low = None
            
            for high in reversed(highs):
                if high.index < i and high.confirmed:
                    recent_high = high
                    break
                    
            for low in reversed(lows):
                if low.index < i and low.confirmed:
                    recent_low = low
                    break
            
            # 向上突破信号
            if recent_high and current_close > recent_high.price:
                # 成交量确认
                avg_volume = data['volume'].iloc[i-20:i].mean()
                if current_volume > avg_volume * 1.2:
                    # 计算止损和止盈
                    stop_loss = recent_low.price if recent_low else current_close * (1 - self.stop_loss_pct)
                    atr_stop = current_close - atr.iloc[i] * self.atr_stop_factor
                    stop_loss = max(stop_loss, atr_stop)
                    
                    take_profit = current_close + (current_close - stop_loss) * self.profit_target_factor
                    
                    # 根据波动率调整仓位
                    position_size = self._calculate_position_size(volatility.iloc[i])
                    
                    signal = TradingSignal(
                        date=current_date,
                        signal_type=SignalType.BUY,
                        price=current_close,
                        confidence=0.8,
                        reason=f"突破前高 {recent_high.price:.2f}",
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        position_size=position_size
                    )
                    signals.append(signal)
            
            # 向下突破信号（做空或平仓）
            if recent_low and current_close < recent_low.price:
                signal = TradingSignal(
                    date=current_date,
                    signal_type=SignalType.SELL,
                    price=current_close,
                    confidence=0.8,
                    reason=f"跌破前低 {recent_low.price:.2f}",
                    stop_loss=recent_high.price if recent_high else current_close * (1 + self.stop_loss_pct),
                    take_profit=current_close * 0.95,  # 保守目标
                    position_size=0
                )
                signals.append(signal)
        
        return signals
    
    def _generate_pattern_signals(self, data: pd.DataFrame, 
                                patterns: List[Dict], atr: pd.Series) -> List[TradingSignal]:
        """
        基于形态生成信号
        """
        signals = []
        
        for pattern in patterns:
            pattern_type = pattern['type']
            end_date = pattern['end_date']
            
            # 找到形态完成后的第一个交易日
            pattern_end_idx = data.index.get_loc(end_date)
            if pattern_end_idx < len(data) - 1:
                signal_date = data.index[pattern_end_idx + 1]
                signal_price = data['close'].iloc[pattern_end_idx + 1]
                
                if pattern_type == 'double_bottom':
                    # 双底买入信号
                    stop_loss = pattern['support_level'] * 0.98
                    take_profit = pattern['target']
                    
                    signal = TradingSignal(
                        date=signal_date,
                        signal_type=SignalType.BUY,
                        price=signal_price,
                        confidence=0.85,
                        reason=f"双底形态完成",
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        position_size=self.max_position_pct
                    )
                    signals.append(signal)
                    
                elif pattern_type == 'double_top':
                    # 双顶卖出信号
                    stop_loss = pattern['resistance_level'] * 1.02
                    take_profit = pattern['target']
                    
                    signal = TradingSignal(
                        date=signal_date,
                        signal_type=SignalType.SELL,
                        price=signal_price,
                        confidence=0.85,
                        reason=f"双顶形态完成",
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        position_size=0
                    )
                    signals.append(signal)
        
        return signals
    
    def _generate_sr_signals(self, data: pd.DataFrame, swing_points: Dict,
                           atr: pd.Series) -> List[TradingSignal]:
        """
        基于支撑阻力生成信号
        """
        signals = []
        
        # 获取所有确认的支撑和阻力位
        support_levels = [low.price for low in swing_points['lows'] if low.confirmed]
        resistance_levels = [high.price for high in swing_points['highs'] if high.confirmed]
        
        for i in range(50, len(data)):  # 从50开始确保有足够的历史数据
            current_date = data.index[i]
            current_close = data['close'].iloc[i]
            prev_close = data['close'].iloc[i-1]
            
            # 检查是否接近支撑位
            for support in support_levels:
                if abs(current_close - support) / support < 0.01:  # 接近支撑位1%以内
                    # 如果从上方接近支撑位且有反弹迹象
                    if prev_close > support and current_close > support:
                        stop_loss = support * 0.98
                        take_profit = current_close + atr.iloc[i] * 3
                        
                        signal = TradingSignal(
                            date=current_date,
                            signal_type=SignalType.BUY,
                            price=current_close,
                            confidence=0.7,
                            reason=f"支撑位 {support:.2f} 反弹",
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            position_size=self.max_position_pct * 0.8
                        )
                        signals.append(signal)
                        break
        
        return signals
    
    def _calculate_position_size(self, current_volatility: float) -> float:
        """
        根据波动率计算仓位大小
        
        Parameters:
        -----------
        current_volatility: 当前波动率
        
        Returns:
        --------
        仓位大小（0-1）
        """
        # 波动率越大，仓位越小
        if current_volatility > 0:
            vol_factor = 1 / (1 + current_volatility)
        else:
            vol_factor = 1
            
        position_size = self.max_position_pct * vol_factor
        
        return min(max(position_size, 0.05), self.max_position_pct)
    
    def _filter_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """
        过滤和优先级排序信号
        """
        # 按日期和置信度排序
        signals.sort(key=lambda x: (x.date, -x.confidence))
        
        # 去除同一天的重复信号，保留置信度最高的
        filtered_signals = []
        seen_dates = set()
        
        for signal in signals:
            if signal.date not in seen_dates:
                filtered_signals.append(signal)
                seen_dates.add(signal.date)
        
        return filtered_signals
    
    def calculate_exit_signals(self, positions: List[Dict], current_data: pd.Series,
                             current_date: datetime) -> List[TradingSignal]:
        """
        计算出场信号
        
        Parameters:
        -----------
        positions: 当前持仓列表
        current_data: 当前行情数据
        current_date: 当前日期
        
        Returns:
        --------
        出场信号列表
        """
        exit_signals = []
        
        for position in positions:
            entry_date = position['entry_date']
            entry_price = position['entry_price']
            stop_loss = position['stop_loss']
            take_profit = position['take_profit']
            
            current_price = current_data['close']
            holding_days = (current_date - entry_date).days
            
            # 止损检查
            if current_price <= stop_loss:
                signal = TradingSignal(
                    date=current_date,
                    signal_type=SignalType.SELL,
                    price=current_price,
                    confidence=1.0,
                    reason=f"触发止损 {stop_loss:.2f}",
                    stop_loss=0,
                    take_profit=0,
                    position_size=0
                )
                exit_signals.append(signal)
                
            # 止盈检查
            elif current_price >= take_profit:
                signal = TradingSignal(
                    date=current_date,
                    signal_type=SignalType.SELL,
                    price=current_price,
                    confidence=1.0,
                    reason=f"达到止盈 {take_profit:.2f}",
                    stop_loss=0,
                    take_profit=0,
                    position_size=0
                )
                exit_signals.append(signal)
                
            # 时间止损
            elif holding_days >= self.max_holding_days:
                signal = TradingSignal(
                    date=current_date,
                    signal_type=SignalType.SELL,
                    price=current_price,
                    confidence=0.8,
                    reason=f"持仓超时 {holding_days} 天",
                    stop_loss=0,
                    take_profit=0,
                    position_size=0
                )
                exit_signals.append(signal)
        
        return exit_signals