#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import argrelextrema
from scipy.optimize import minimize
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("Warning: TA-Lib not available. Using basic implementation.")

class UptrendChannelAnalyzer:
    """专业上升通道分析器 - 量化架构师优化版"""
    
    def __init__(self):
        self.talib_available = TALIB_AVAILABLE
    
    def detect_uptrend_channel(self, prices, high_prices=None, low_prices=None, 
                              min_points=20, min_channel_width=0.03, 
                              min_duration_weeks=8, r2_threshold=0.6, 
                              recent_focus=True, volatility_filter=True):
        """
        专业上升通道识别算法 - 智能波动率过滤版
        
        Args:
            prices: 收盘价序列
            high_prices: 最高价序列（可选）
            low_prices: 最低价序列（可选）
            min_points: 最小数据点数
            min_channel_width: 最小通道宽度
            min_duration_weeks: 最小持续时间
            r2_threshold: 趋势线拟合度阈值
            recent_focus: 是否专注最近趋势
            volatility_filter: 是否启用智能波动率过滤
            
        Returns:
            dict: 上升通道分析结果
        """
        if len(prices) < min_points:
            return None
        
        # 转换为numpy数组
        prices = np.array(prices, dtype=np.float64)
        if high_prices is not None:
            high_prices = np.array(high_prices, dtype=np.float64)
        else:
            high_prices = prices
        if low_prices is not None:
            low_prices = np.array(low_prices, dtype=np.float64)
        else:
            low_prices = prices
        
        # 0. 智能波动率过滤（优化版）
        if volatility_filter:
            filtered_data = self._apply_intelligent_volatility_filter(prices, high_prices, low_prices)
            if filtered_data is None:
                return None
            
            prices = filtered_data['prices']
            high_prices = filtered_data['high_prices']
            low_prices = filtered_data['low_prices']
            volatility_stats = filtered_data['volatility_stats']
        else:
            volatility_stats = None
        
        # 1. 专业关键点识别
        if recent_focus:
            # 专注最近趋势：只分析最近60%的数据
            recent_start = int(len(prices) * 0.4)
            recent_high_prices = high_prices[recent_start:]
            recent_low_prices = low_prices[recent_start:]
            
            peaks, troughs = self._find_professional_key_points(recent_high_prices, recent_low_prices)
            
            # 调整索引到原始数据位置
            peaks = [(idx + recent_start, price) for idx, price in peaks]
            troughs = [(idx + recent_start, price) for idx, price in troughs]
        else:
            peaks, troughs = self._find_professional_key_points(high_prices, low_prices)
        
        if len(peaks) < 2 or len(troughs) < 2:
            return None
        
        # 2. 专业通道线识别
        upper_channel = self._identify_professional_upper_channel(peaks, high_prices)
        if not upper_channel:
            return None
        
        lower_channel = self._identify_professional_lower_channel(troughs, low_prices)
        if not lower_channel:
            return None
        
        # 3. 专业通道质量验证
        channel_quality = self._validate_professional_channel_quality(
            upper_channel, lower_channel, prices, high_prices, low_prices,
            min_channel_width, min_duration_weeks
        )
        if not channel_quality:
            return None
        
        # 4. 专业通道特征分析
        channel_features = self._analyze_professional_channel_features(
            upper_channel, lower_channel, prices, high_prices, low_prices
        )
        
        # 5. TA-Lib增强分析
        enhanced_analysis = None
        if self.talib_available:
            enhanced_analysis = self._analyze_with_talib_indicators(
                prices, high_prices, low_prices, upper_channel, lower_channel
            )
        
        # 6. 专业质量评分
        quality_score = self._calculate_professional_quality_score(
            channel_quality, channel_features, enhanced_analysis
        )
        
        enhanced_quality_score = self._calculate_enhanced_quality_score(
            quality_score, enhanced_analysis
        )
        
        # 7. 智能波动率过滤质量提升（优化版）
        if volatility_filter and volatility_stats:
            enhanced_quality_score = self._apply_intelligent_volatility_boost(
                enhanced_quality_score, volatility_stats, channel_quality
            )
        
        return {
            'type': 'professional_uptrend_channel',
            'upper_channel': upper_channel,
            'lower_channel': lower_channel,
            'channel_quality': channel_quality,
            'channel_features': channel_features,
            'quality_score': quality_score,
            'enhanced_quality_score': enhanced_quality_score,
            'talib_analysis': enhanced_analysis,
            'volatility_filter': volatility_stats,
            'recommendation': self._generate_professional_recommendation(
                enhanced_quality_score, channel_features, enhanced_analysis
            )
        }
    
    def _find_professional_key_points(self, high_prices, low_prices):
        """专业关键点识别 - 考虑价格重要性和趋势连续性"""
        # 1. 基础极值点识别
        peaks = argrelextrema(high_prices, np.greater, order=3)[0]
        troughs = argrelextrema(low_prices, np.less, order=3)[0]
        
        # 2. 价格重要性过滤
        significant_peaks = []
        for peak_idx in peaks:
            peak_price = high_prices[peak_idx]
            # 计算局部重要性（与周围价格的差异）
            left_range = max(0, peak_idx - 5)
            right_range = min(len(high_prices), peak_idx + 6)
            local_avg = np.mean(high_prices[left_range:right_range])
            importance = (peak_price - local_avg) / local_avg
            
            if importance > 0.02:  # 2%以上的重要性
                significant_peaks.append((peak_idx, peak_price))
        
        significant_troughs = []
        for trough_idx in troughs:
            trough_price = low_prices[trough_idx]
            left_range = max(0, trough_idx - 5)
            right_range = min(len(low_prices), trough_idx + 6)
            local_avg = np.mean(low_prices[left_range:right_range])
            importance = (local_avg - trough_price) / local_avg
            
            if importance > 0.02:  # 2%以上的重要性
                significant_troughs.append((trough_idx, trough_price))
        
        # 3. 趋势连续性过滤
        filtered_peaks = self._filter_trend_continuity(significant_peaks, 'peak')
        filtered_troughs = self._filter_trend_continuity(significant_troughs, 'trough')
        
        return filtered_peaks, filtered_troughs
    
    def _filter_trend_continuity(self, points, point_type):
        """过滤趋势连续性 - 确保关键点形成合理的趋势"""
        if len(points) < 2:
            return points
        
        filtered = []
        for i, (idx, price) in enumerate(points):
            if i == 0:
                filtered.append((idx, price))
                continue
            
            # 检查与前一个点的趋势连续性
            prev_idx, prev_price = filtered[-1]
            
            if point_type == 'peak':
                # 高点应该形成上升趋势
                if price > prev_price and (idx - prev_idx) >= 3:
                    filtered.append((idx, price))
            else:
                # 低点应该形成上升趋势
                if price > prev_price and (idx - prev_idx) >= 3:
                    filtered.append((idx, price))
        
        return filtered
    
    def _identify_professional_upper_channel(self, peaks, high_prices):
        """专业上轨线识别 - 使用优化算法"""
        if len(peaks) < 2:
            return None
        
        # 使用最小二乘法优化通道线拟合
        best_fit = None
        best_score = 0
        
        for i in range(len(peaks) - 1):
            for j in range(i + 1, len(peaks)):
                point1 = peaks[i]
                point2 = peaks[j]
                
                # 计算基础线性回归
                x = np.array([point1[0], point2[0]])
                y = np.array([point1[1], point2[1]])
                
                try:
                    slope, intercept, r_value, _, _ = stats.linregress(x, y)
                    r2 = r_value ** 2
                    
                    if slope > 0:
                        # 优化通道线参数
                        optimized_params = self._optimize_channel_line(
                            peaks, slope, intercept, 'upper'
                        )
                        
                        if optimized_params:
                            score = self._calculate_channel_line_score(
                                peaks, optimized_params['slope'], 
                                optimized_params['intercept'], 'upper'
                            )
                            
                            if score > best_score:
                                best_score = score
                                best_fit = {
                                    'slope': optimized_params['slope'],
                                    'intercept': optimized_params['intercept'],
                                    'r2': r2,
                                    'score': score,
                                    'start_idx': point1[0],
                                    'end_idx': point2[0],
                                    'fit_quality': optimized_params['fit_quality']
                                }
                except:
                    continue
        
        return best_fit
    
    def _identify_professional_lower_channel(self, troughs, low_prices):
        """专业下轨线识别 - 使用优化算法"""
        if len(troughs) < 2:
            return None
        
        best_fit = None
        best_score = 0
        
        for i in range(len(troughs) - 1):
            for j in range(i + 1, len(troughs)):
                point1 = troughs[i]
                point2 = troughs[j]
                
                x = np.array([point1[0], point2[0]])
                y = np.array([point1[1], point2[1]])
                
                try:
                    slope, intercept, r_value, _, _ = stats.linregress(x, y)
                    r2 = r_value ** 2
                    
                    if slope > 0:
                        optimized_params = self._optimize_channel_line(
                            troughs, slope, intercept, 'lower'
                        )
                        
                        if optimized_params:
                            score = self._calculate_channel_line_score(
                                troughs, optimized_params['slope'], 
                                optimized_params['intercept'], 'lower'
                            )
                            
                            if score > best_score:
                                best_score = score
                                best_fit = {
                                    'slope': optimized_params['slope'],
                                    'intercept': optimized_params['intercept'],
                                    'r2': r2,
                                    'score': score,
                                    'start_idx': point1[0],
                                    'end_idx': point2[0],
                                    'fit_quality': optimized_params['fit_quality']
                                }
                except:
                    continue
        
        return best_fit
    
    def _optimize_channel_line(self, points, initial_slope, initial_intercept, line_type):
        """优化通道线参数"""
        def objective(params):
            slope, intercept = params
            total_error = 0
            
            for idx, price in points:
                predicted_price = slope * idx + intercept
                error = abs(price - predicted_price) / price
                total_error += error
            
            return total_error / len(points)
        
        try:
            result = minimize(objective, [initial_slope, initial_intercept], 
                            method='Nelder-Mead', bounds=[(0, None), (None, None)])
            
            if result.success:
                optimized_slope, optimized_intercept = result.x
                fit_quality = 1 - result.fun  # 转换为质量分数
                
                return {
                    'slope': optimized_slope,
                    'intercept': optimized_intercept,
                    'fit_quality': fit_quality
                }
        except:
            pass
        
        return None
    
    def _calculate_channel_line_score(self, points, slope, intercept, line_type):
        """计算通道线质量评分"""
        if len(points) < 2:
            return 0
        
        # 计算拟合误差
        errors = []
        for idx, price in points:
            predicted_price = slope * idx + intercept
            error = abs(price - predicted_price) / price
            errors.append(error)
        
        avg_error = np.mean(errors)
        fit_score = max(0, 1 - avg_error)
        
        # 计算趋势强度
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        
        try:
            _, _, r_value, _, _ = stats.linregress(x_coords, y_coords)
            trend_score = r_value ** 2
        except:
            trend_score = 0
        
        # 综合评分
        score = fit_score * 0.6 + trend_score * 0.4
        return score
    
    def _validate_professional_channel_quality(self, upper_channel, lower_channel, 
                                             prices, high_prices, low_prices,
                                             min_channel_width, min_duration_weeks):
        """专业通道质量验证"""
        if not upper_channel or not lower_channel:
            return None
        
        # 1. 持续时间检查
        channel_start = min(upper_channel['start_idx'], lower_channel['start_idx'])
        channel_end = max(upper_channel['end_idx'], lower_channel['end_idx'])
        duration = channel_end - channel_start
        
        if duration < min_duration_weeks:
            return None
        
        # 2. 通道宽度检查
        channel_width_pct = self._calculate_professional_channel_width(
            upper_channel, lower_channel, prices
        )
        
        if channel_width_pct < min_channel_width:
            return None
        
        # 3. 平行性检查
        slope_diff = abs(upper_channel['slope'] - lower_channel['slope'])
        if slope_diff > 0.02:
            return None
        
        # 4. 价格在通道内的分布检查
        price_distribution = self._analyze_price_distribution_in_channel(
            upper_channel, lower_channel, prices, channel_start, channel_end
        )
        
        if price_distribution['outside_ratio'] > 0.3:  # 超过30%的价格在通道外
            return None
        
        return {
            'duration': duration,
            'channel_width_pct': channel_width_pct,
            'slope_diff': slope_diff,
            'start_idx': channel_start,
            'end_idx': channel_end,
            'price_distribution': price_distribution
        }
    
    def _calculate_professional_channel_width(self, upper_channel, lower_channel, prices):
        """计算专业通道宽度"""
        # 计算整个通道的平均宽度
        channel_start = min(upper_channel['start_idx'], lower_channel['start_idx'])
        channel_end = max(upper_channel['end_idx'], lower_channel['end_idx'])
        
        widths = []
        for i in range(channel_start, channel_end + 1):
            if i < len(prices):
                upper_price = upper_channel['slope'] * i + upper_channel['intercept']
                lower_price = lower_channel['slope'] * i + lower_channel['intercept']
                
                if upper_price > lower_price:
                    avg_price = (upper_price + lower_price) / 2
                    width = (upper_price - lower_price) / avg_price
                    widths.append(width)
        
        return np.mean(widths) if widths else 0
    
    def _analyze_price_distribution_in_channel(self, upper_channel, lower_channel, 
                                             prices, start_idx, end_idx):
        """分析价格在通道内的分布"""
        inside_count = 0
        total_count = 0
        
        for i in range(start_idx, end_idx + 1):
            if i < len(prices):
                price = prices[i]
                upper_price = upper_channel['slope'] * i + upper_channel['intercept']
                lower_price = lower_channel['slope'] * i + lower_channel['intercept']
                
                if lower_price <= price <= upper_price:
                    inside_count += 1
                total_count += 1
        
        inside_ratio = inside_count / total_count if total_count > 0 else 0
        outside_ratio = 1 - inside_ratio
        
        return {
            'inside_ratio': inside_ratio,
            'outside_ratio': outside_ratio,
            'inside_count': inside_count,
            'total_count': total_count
        }
    
    def _analyze_professional_channel_features(self, upper_channel, lower_channel, 
                                             prices, high_prices, low_prices):
        """专业通道特征分析"""
        channel_start = min(upper_channel['start_idx'], lower_channel['start_idx'])
        channel_end = max(upper_channel['end_idx'], lower_channel['end_idx'])
        
        # 计算通道强度
        channel_strength = self._calculate_professional_channel_strength(
            upper_channel, lower_channel, prices
        )
        
        # 计算突破尝试
        breakout_attempts = self._count_professional_breakout_attempts(
            prices, high_prices, low_prices, upper_channel, lower_channel
        )
        
        # 计算价格位置
        current_price = prices[-1]
        current_upper = upper_channel['slope'] * (len(prices) - 1) + upper_channel['intercept']
        current_lower = lower_channel['slope'] * (len(prices) - 1) + lower_channel['intercept']
        
        if current_upper > current_lower:
            price_position = (current_price - current_lower) / (current_upper - current_lower)
        else:
            price_position = 0.5
        
        return {
            'channel_strength': channel_strength,
            'breakout_attempts': breakout_attempts,
            'price_position': price_position,
            'current_price': current_price,
            'upper_price': current_upper,
            'lower_price': current_lower
        }
    
    def _calculate_professional_channel_strength(self, upper_channel, lower_channel, prices):
        """计算专业通道强度"""
        # 基于通道的稳定性和价格分布计算强度
        channel_start = min(upper_channel['start_idx'], lower_channel['start_idx'])
        channel_end = max(upper_channel['end_idx'], lower_channel['end_idx'])
        
        # 计算通道宽度的一致性
        widths = []
        for i in range(channel_start, channel_end + 1, 5):  # 每5个点采样一次
            if i < len(prices):
                upper_price = upper_channel['slope'] * i + upper_channel['intercept']
                lower_price = lower_channel['slope'] * i + lower_channel['intercept']
                
                if upper_price > lower_price:
                    avg_price = (upper_price + lower_price) / 2
                    width = (upper_price - lower_price) / avg_price
                    widths.append(width)
        
        if not widths:
            return 0
        
        # 宽度一致性（标准差越小越好）
        width_std = np.std(widths)
        width_consistency = max(0, 1 - width_std / np.mean(widths))
        
        # 趋势强度
        trend_strength = min(1, (upper_channel['slope'] + lower_channel['slope']) / 2 / 0.01)
        
        # 综合强度
        strength = width_consistency * 0.6 + trend_strength * 0.4
        return strength
    
    def _count_professional_breakout_attempts(self, prices, high_prices, low_prices, 
                                           upper_channel, lower_channel):
        """计算专业突破尝试次数"""
        breakout_count = 0
        
        for i in range(len(prices)):
            upper_price = upper_channel['slope'] * i + upper_channel['intercept']
            lower_price = lower_channel['slope'] * i + lower_channel['intercept']
            
            # 检查是否突破上轨
            if high_prices[i] > upper_price * 1.02:
                breakout_count += 1
            
            # 检查是否突破下轨
            if low_prices[i] < lower_price * 0.98:
                breakout_count += 1
        
        return breakout_count
    
    def _calculate_professional_quality_score(self, channel_quality, channel_features, enhanced_analysis):
        """计算专业质量评分"""
        score = 0
        
        # 通道质量 (40%)
        if channel_quality:
            duration_score = min(1, channel_quality['duration'] / 20)  # 20周为满分
            width_score = min(1, channel_quality['channel_width_pct'] / 0.1)  # 10%为满分
            distribution_score = channel_quality['price_distribution']['inside_ratio']
            
            quality_score = (duration_score * 0.3 + width_score * 0.3 + distribution_score * 0.4)
            score += quality_score * 0.4
        
        # 通道特征 (35%)
        if channel_features:
            strength_score = channel_features['channel_strength']
            breakout_score = max(0, 1 - channel_features['breakout_attempts'] / 10)  # 突破次数越少越好
            position_score = 1 - abs(channel_features['price_position'] - 0.5)  # 价格位置居中最好
            
            feature_score = (strength_score * 0.5 + breakout_score * 0.3 + position_score * 0.2)
            score += feature_score * 0.35
        
        # 拟合质量 (25%)
        fit_score = 0
        if channel_quality and channel_features:
            # 基于价格分布和通道强度计算拟合质量
            fit_score = (channel_quality['price_distribution']['inside_ratio'] * 0.6 + 
                        channel_features['channel_strength'] * 0.4)
        
        score += fit_score * 0.25
        
        return min(1, score)
    
    def _generate_professional_recommendation(self, quality_score, channel_features, enhanced_analysis):
        """生成专业投资建议"""
        if quality_score >= 0.8:
            return "强烈推荐 - 高质量上升通道，建议买入"
        elif quality_score >= 0.6:
            return "推荐 - 良好上升通道，可考虑买入"
        elif quality_score >= 0.4:
            return "关注 - 一般上升通道，谨慎操作"
        else:
            return "观望 - 通道质量较低，建议观望"
    
    def _analyze_with_talib_indicators(self, prices, high_prices, low_prices, 
                                     upper_channel, lower_channel):
        """TA-Lib技术指标分析"""
        if not self.talib_available:
            return None
        
        try:
            # 趋势强度分析
            trend_strength = self._analyze_trend_strength(prices, high_prices, low_prices)
            
            # 动量分析
            momentum = self._analyze_momentum(prices, high_prices, low_prices)
            
            # 波动率分析
            volatility = self._analyze_volatility(prices, high_prices, low_prices)
            
            return {
                'trend_strength': trend_strength,
                'momentum': momentum,
                'volatility': volatility
            }
        except:
            return None
    
    def _analyze_trend_strength(self, prices, high_prices, low_prices):
        """分析趋势强度"""
        try:
            # ADX指标
            adx = talib.ADX(high_prices, low_prices, prices, timeperiod=14)
            current_adx = adx[-1] if not np.isnan(adx[-1]) else 0
            
            # +DI/-DI指标
            plus_di = talib.PLUS_DI(high_prices, low_prices, prices, timeperiod=14)
            minus_di = talib.MINUS_DI(high_prices, low_prices, prices, timeperiod=14)
            
            current_plus_di = plus_di[-1] if not np.isnan(plus_di[-1]) else 0
            current_minus_di = minus_di[-1] if not np.isnan(minus_di[-1]) else 0
            
            return {
                'trend_strength': 'strong' if current_adx > 25 else 'weak',
                'trend_direction': 'bullish' if current_plus_di > current_minus_di else 'bearish',
                'adx_value': current_adx,
                'plus_di': current_plus_di,
                'minus_di': current_minus_di
            }
        except:
            return {'trend_strength': 'unknown', 'trend_direction': 'unknown'}
    
    def _analyze_momentum(self, prices, high_prices, low_prices):
        """分析动量指标"""
        try:
            # RSI指标
            rsi = talib.RSI(prices, timeperiod=14)
            current_rsi = rsi[-1] if not np.isnan(rsi[-1]) else 50
            
            # MACD指标
            macd, macd_signal, macd_hist = talib.MACD(prices)
            macd_bullish = macd[-1] > macd_signal[-1] if not np.isnan(macd[-1]) else False
            
            return {
                'rsi': current_rsi,
                'macd_bullish': macd_bullish,
                'rsi_signal': 'oversold' if current_rsi < 30 else 'overbought' if current_rsi > 70 else 'normal'
            }
        except:
            return {'rsi': 50, 'macd_bullish': False, 'rsi_signal': 'unknown'}
    
    def _analyze_volatility(self, prices, high_prices, low_prices):
        """分析波动率"""
        try:
            # ATR指标
            atr = talib.ATR(high_prices, low_prices, prices, timeperiod=14)
            current_atr = atr[-1] if not np.isnan(atr[-1]) else 0
            
            # 布林带
            upper, middle, lower = talib.BBANDS(prices, timeperiod=20)
            current_price = prices[-1]
            bb_position = (current_price - lower[-1]) / (upper[-1] - lower[-1]) if upper[-1] > lower[-1] else 0.5
            
            return {
                'atr': current_atr,
                'bb_position': bb_position,
                'volatility_level': 'high' if current_atr > np.mean(atr[-20:]) else 'low'
            }
        except:
            return {'atr': 0, 'bb_position': 0.5, 'volatility_level': 'unknown'}
    
    def _calculate_enhanced_quality_score(self, base_score, enhanced_analysis):
        """计算增强质量评分"""
        if not enhanced_analysis:
            return base_score
        
        enhancement = 0
        
        # 趋势强度增强
        if enhanced_analysis.get('trend_strength'):
            trend = enhanced_analysis['trend_strength']
            if trend.get('trend_strength') == 'strong':
                enhancement += 0.1
            if trend.get('trend_direction') == 'bullish':
                enhancement += 0.1
        
        # 动量增强
        if enhanced_analysis.get('momentum'):
            momentum = enhanced_analysis['momentum']
            if momentum.get('macd_bullish'):
                enhancement += 0.05
            rsi = momentum.get('rsi', 50)
            if 30 <= rsi <= 70:
                enhancement += 0.05
        
        # 波动率增强
        if enhanced_analysis.get('volatility'):
            volatility = enhanced_analysis['volatility']
            if volatility.get('volatility_level') == 'low':
                enhancement += 0.05
        
        enhanced_score = min(1, base_score + enhancement)
        return enhanced_score
    
    def detect_entry_signal(self, prices, high_prices=None, low_prices=None, 
                           recent_weeks=12, min_slope=0.01):
        """检测入场信号"""
        if len(prices) < recent_weeks:
            return None
        
        # 只分析最近的数据
        recent_prices = prices[-recent_weeks:]
        recent_high = high_prices[-recent_weeks:] if high_prices is not None else recent_prices
        recent_low = low_prices[-recent_weeks:] if low_prices is not None else recent_prices
        
        # 1. 检查最近趋势
        x = np.arange(len(recent_prices))
        try:
            slope, intercept, r_value, _, _ = stats.linregress(x, recent_prices)
            r2 = r_value ** 2 if isinstance(r_value, (int, float)) else 0
        except:
            slope = 0
            r2 = 0
        
        # 2. 检查是否满足基本上升趋势
        if slope < min_slope or r2 < 0.2:  # 降低R²要求到0.2
            return None
        
        # 3. 寻找最近的关键点
        peaks, troughs = self._find_professional_key_points(recent_high, recent_low)
        
        if len(peaks) < 2 or len(troughs) < 2:
            return None
        
        # 4. 分析通道特征
        channel_analysis = self._analyze_recent_channel(peaks, troughs, recent_prices, recent_high, recent_low)
        
        if not channel_analysis:
            return None
        
        # 5. 计算入场信号强度
        entry_strength = self._calculate_entry_strength(
            slope, r2, channel_analysis, recent_prices
        )
        
        # 6. 生成入场建议
        entry_recommendation = self._generate_entry_recommendation(entry_strength, channel_analysis)
        
        return {
            'type': 'entry_signal',
            'entry_strength': entry_strength,
            'recommendation': entry_recommendation,
            'recent_trend': {
                'slope': slope,
                'r2': r2,
                'price_change': (recent_prices[-1] - recent_prices[0]) / recent_prices[0] if recent_prices[0] > 0 else 0
            },
            'channel_analysis': channel_analysis,
            'analysis_period': recent_weeks,
            'current_price': recent_prices[-1],
            'signal_time': 'recent'
        }
    
    def _analyze_recent_channel(self, peaks, troughs, prices, high_prices, low_prices):
        """分析最近的通道特征"""
        try:
            # 计算通道宽度
            price_ranges = []
            for i in range(len(prices)):
                if i < len(high_prices) and i < len(low_prices):
                    price_range = (high_prices[i] - low_prices[i]) / prices[i] if prices[i] > 0 else 0
                    price_ranges.append(price_range)
            
            if not price_ranges:
                return None
            
            avg_range = np.mean(price_ranges)
            
            # 检查通道质量
            if avg_range < 0.02 or avg_range > 0.15:  # 2%-15%的合理范围
                return None
            
            # 计算价格在通道中的位置
            current_price = prices[-1]
            recent_high = max(high_prices[-5:]) if len(high_prices) >= 5 else max(high_prices)
            recent_low = min(low_prices[-5:]) if len(low_prices) >= 5 else min(low_prices)
            
            price_position = (current_price - recent_low) / (recent_high - recent_low) if (recent_high - recent_low) > 0 else 0.5
            
            return {
                'channel_width': avg_range,
                'price_position': price_position,
                'recent_high': recent_high,
                'recent_low': recent_low,
                'peaks_count': len(peaks),
                'troughs_count': len(troughs)
            }
        except:
            return None
    
    def _calculate_entry_strength(self, slope, r2, channel_analysis, prices):
        """计算入场信号强度"""
        strength = 0.0
        
        # 趋势强度 (40%)
        trend_score = min(slope / 0.02, 1.0) * r2  # 2%周涨幅为满分
        strength += trend_score * 0.4
        
        # 通道质量 (30%)
        if channel_analysis:
            width_score = 1.0 if 0.03 <= channel_analysis['channel_width'] <= 0.12 else 0.5
            position_score = 1.0 if 0.3 <= channel_analysis['price_position'] <= 0.7 else 0.5
            channel_score = width_score * position_score
            strength += channel_score * 0.3
        
        # 价格动量 (30%)
        if len(prices) >= 3:
            recent_momentum = (prices[-1] - prices[-3]) / prices[-3] if prices[-3] > 0 else 0
            momentum_score = min(recent_momentum / 0.05, 1.0)  # 5%涨幅为满分
            strength += momentum_score * 0.3
        
        return min(strength, 1.0)
    
    def _generate_entry_recommendation(self, entry_strength, channel_analysis):
        """生成入场建议"""
        if entry_strength >= 0.8:
            return "强烈买入 - 上升通道明确，趋势强劲"
        elif entry_strength >= 0.6:
            return "买入 - 上升通道形成，趋势向好"
        elif entry_strength >= 0.4:
            return "关注 - 上升趋势初现，等待确认"
        else:
            return "观望 - 上升趋势不明显"
    
    def calculate_channel_similarity(self, prices, high_prices=None, low_prices=None, min_points=30):
        """计算通道相似度"""
        if len(prices) < min_points:
            return {
                'similarity_score': 0.0,
                'reason': 'insufficient_data',
                'details': {}
            }
        
        similarity_factors = {}
        total_score = 0.0
        
        # 1. 上升趋势分析（权重30%）
        trend_analysis = self._analyze_uptrend_similarity(prices)
        similarity_factors['trend'] = trend_analysis
        total_score += trend_analysis['score'] * 0.30
        
        # 2. 通道宽度分析（权重25%）
        width_analysis = self._analyze_channel_width_similarity(prices, high_prices, low_prices)
        similarity_factors['width'] = width_analysis
        total_score += width_analysis['score'] * 0.25
        
        # 3. 价格波动分析（权重20%）
        volatility_analysis = self._analyze_volatility_similarity(prices)
        similarity_factors['volatility'] = volatility_analysis
        total_score += volatility_analysis['score'] * 0.20
        
        # 4. 持续时间分析（权重15%）
        duration_analysis = self._analyze_duration_similarity(prices)
        similarity_factors['duration'] = duration_analysis
        total_score += duration_analysis['score'] * 0.15
        
        # 5. 技术指标分析（权重10%）
        if self.talib_available:
            tech_analysis = self._analyze_tech_indicators_similarity(prices, high_prices, low_prices)
            similarity_factors['technical'] = tech_analysis
            total_score += tech_analysis['score'] * 0.10
        else:
            similarity_factors['technical'] = {'score': 0.5, 'reason': 'no_talib'}
            total_score += 0.05
        
        # 生成推荐
        recommendation = self._generate_similarity_recommendation(total_score, similarity_factors)
        
        return {
            'similarity_score': total_score,
            'recommendation': recommendation,
            'factors': similarity_factors,
            'details': {
                'trend_score': trend_analysis['score'],
                'width_score': width_analysis['score'],
                'volatility_score': volatility_analysis['score'],
                'duration_score': duration_analysis['score']
            }
        }
    
    def _analyze_uptrend_similarity(self, prices):
        """分析上升趋势相似度"""
        if len(prices) < 10:
            return {'score': 0.0, 'reason': 'insufficient_data'}
        
        # 计算整体趋势
        x = np.arange(len(prices))
        try:
            slope, _, r_value, _, _ = stats.linregress(x, prices)
            
            # 上升斜率评分
            if slope > 0:
                slope_score = min(slope / (np.mean(prices) * 0.01), 1.0)  # 1%周涨幅为满分
            else:
                slope_score = 0
            
            # 趋势一致性评分
            consistency_score = abs(r_value) if isinstance(r_value, (int, float)) else 0
            
            # 价格变化幅度
            price_change = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0
            change_score = min(price_change / 0.5, 1.0)  # 50%涨幅为满分
            
            overall_score = (slope_score * 0.4 + consistency_score * 0.4 + change_score * 0.2)
            
            return {
                'score': overall_score,
                'slope': slope,
                'r_squared': r_value ** 2 if isinstance(r_value, (int, float)) else 0,
                'price_change': price_change
            }
        except:
            return {'score': 0.0, 'reason': 'calculation_error'}
    
    def _analyze_channel_width_similarity(self, prices, high_prices, low_prices):
        """分析通道宽度相似度"""
        if high_prices is None or low_prices is None:
            return {'score': 0.5, 'reason': 'no_ohlc_data'}
        
        # 计算价格波动范围
        price_ranges = []
        for i in range(len(prices)):
            if i < len(high_prices) and i < len(low_prices):
                price_range = (high_prices[i] - low_prices[i]) / prices[i] if prices[i] > 0 else 0
                price_ranges.append(price_range)
        
        if not price_ranges:
            return {'score': 0.0, 'reason': 'no_valid_data'}
        
        # 计算平均波动范围
        avg_range = np.mean(price_ranges)
        
        # 理想通道宽度在5%-15%之间
        if 0.05 <= avg_range <= 0.15:
            width_score = 1.0
        elif avg_range < 0.05:
            width_score = avg_range / 0.05
        else:
            width_score = max(0, 1 - (avg_range - 0.15) / 0.15)
        
        return {
            'score': width_score,
            'avg_range': avg_range,
            'ideal_range': '5%-15%'
        }
    
    def _analyze_volatility_similarity(self, prices):
        """分析波动率相似度"""
        if len(prices) < 10:
            return {'score': 0.0, 'reason': 'insufficient_data'}
        
        # 计算价格变化率
        returns = np.diff(prices) / prices[:-1]
        
        # 计算波动率
        volatility = np.std(returns)
        
        # 理想波动率在2%-8%之间
        if 0.02 <= volatility <= 0.08:
            vol_score = 1.0
        elif volatility < 0.02:
            vol_score = volatility / 0.02
        else:
            vol_score = max(0, 1 - (volatility - 0.08) / 0.08)
        
        return {
            'score': vol_score,
            'volatility': volatility,
            'ideal_volatility': '2%-8%'
        }
    
    def _analyze_duration_similarity(self, prices):
        """分析持续时间相似度"""
        duration = len(prices)
        
        # 理想持续时间在12-52周之间
        if 12 <= duration <= 52:
            duration_score = 1.0
        elif duration < 12:
            duration_score = duration / 12
        else:
            duration_score = max(0, 1 - (duration - 52) / 52)
        
        return {
            'score': duration_score,
            'duration': duration,
            'ideal_duration': '12-52周'
        }
    
    def _analyze_tech_indicators_similarity(self, prices, high_prices, low_prices):
        """分析技术指标相似度"""
        try:
            # 简化的技术指标分析
            tech_score = 0.5
            
            # 移动平均线分析
            if len(prices) >= 20:
                ma20 = np.mean(prices[-20:])
                current_price = prices[-1]
                if current_price > ma20:
                    tech_score += 0.2
            
            # 价格位置分析
            price_range = np.max(prices) - np.min(prices)
            current_position = (current_price - np.min(prices)) / price_range if price_range > 0 else 0.5
            
            if 0.3 <= current_position <= 0.7:
                tech_score += 0.3
            else:
                tech_score += 0.1
            
            return {
                'score': min(tech_score, 1.0),
                'ma20_above': current_price > ma20 if 'ma20' in locals() else False,
                'price_position': current_position
            }
        except:
            return {'score': 0.5, 'reason': 'calculation_error'}
    
    def _generate_similarity_recommendation(self, total_score, factors):
        """生成相似度推荐"""
        if total_score >= 0.8:
            return "强烈推荐 - 高度符合上升通道特征"
        elif total_score >= 0.6:
            return "推荐 - 基本符合上升通道特征"
        elif total_score >= 0.4:
            return "关注 - 部分符合上升通道特征"
        else:
            return "观望 - 不符合上升通道特征" 

    def _apply_volatility_filter(self, prices, high_prices, low_prices):
        """
        应用波动率智能过滤，去除毛刺和噪声
        
        Args:
            prices: 收盘价序列
            high_prices: 最高价序列
            low_prices: 最低价序列
            
        Returns:
            dict: 过滤后的数据和波动率统计
        """
        try:
            # 1. 计算基础波动率指标
            volatility_stats = self._calculate_volatility_statistics(prices, high_prices, low_prices)
            
            # 2. 识别异常波动点
            outlier_indices = self._identify_volatility_outliers(prices, high_prices, low_prices, volatility_stats)
            
            # 3. 智能平滑处理
            smoothed_data = self._apply_intelligent_smoothing(prices, high_prices, low_prices, outlier_indices, volatility_stats)
            
            # 4. 验证过滤效果
            if not self._validate_filtered_data(smoothed_data, volatility_stats):
                return None
            
            return {
                'prices': smoothed_data['prices'],
                'high_prices': smoothed_data['high_prices'],
                'low_prices': smoothed_data['low_prices'],
                'volatility_stats': volatility_stats,
                'filtered_points': len(outlier_indices),
                'smoothing_method': smoothed_data['method']
            }
            
        except Exception as e:
            print(f"波动率过滤失败: {e}")
            return None
    
    def _calculate_volatility_statistics(self, prices, high_prices, low_prices):
        """计算波动率统计指标"""
        # 1. 计算收益率
        returns = np.diff(prices) / prices[:-1]
        
        # 2. 计算滚动波动率（20期）
        window = min(20, len(returns))
        rolling_vol = np.array([np.std(returns[max(0, i-window+1):i+1]) for i in range(len(returns))])
        
        # 3. 计算真实波动率（TR）
        tr_values = []
        for i in range(1, len(prices)):
            high_low = high_prices[i] - low_prices[i]
            high_close = abs(high_prices[i] - prices[i-1])
            low_close = abs(low_prices[i] - prices[i-1])
            tr = max(high_low, high_close, low_close)
            tr_values.append(tr / prices[i-1])  # 标准化
        
        tr_values = np.array(tr_values)
        
        # 4. 计算ATR（平均真实波动率）
        atr_period = min(14, len(tr_values))
        atr = np.array([np.mean(tr_values[max(0, i-atr_period+1):i+1]) for i in range(len(tr_values))])
        
        # 5. 计算波动率分位数
        vol_percentiles = np.percentile(rolling_vol, [25, 50, 75, 90, 95])
        tr_percentiles = np.percentile(tr_values, [25, 50, 75, 90, 95])
        
        return {
            'returns': returns,
            'rolling_volatility': rolling_vol,
            'true_range': tr_values,
            'atr': atr,
            'vol_percentiles': vol_percentiles,
            'tr_percentiles': tr_percentiles,
            'mean_vol': np.mean(rolling_vol),
            'std_vol': np.std(rolling_vol),
            'mean_tr': np.mean(tr_values),
            'std_tr': np.std(tr_values)
        }
    
    def _identify_volatility_outliers(self, prices, high_prices, low_prices, volatility_stats):
        """识别波动率异常点"""
        outlier_indices = []
        
        # 1. 基于滚动波动率的异常检测
        vol_threshold = volatility_stats['vol_percentiles'][3]  # 90分位数
        vol_outliers = np.where(volatility_stats['rolling_volatility'] > vol_threshold)[0]
        outlier_indices.extend(vol_outliers)
        
        # 2. 基于真实波动率的异常检测
        tr_threshold = volatility_stats['tr_percentiles'][3]  # 90分位数
        tr_outliers = np.where(volatility_stats['true_range'] > tr_threshold)[0]
        outlier_indices.extend(tr_outliers)
        
        # 3. 基于价格跳跃的异常检测
        price_jumps = np.abs(np.diff(prices)) / prices[:-1]
        jump_threshold = np.percentile(price_jumps, 95)  # 95分位数
        jump_outliers = np.where(price_jumps > jump_threshold)[0]
        outlier_indices.extend(jump_outliers)
        
        # 4. 基于高低价差的异常检测
        price_spreads = (high_prices - low_prices) / prices
        spread_threshold = np.percentile(price_spreads, 95)  # 95分位数
        spread_outliers = np.where(price_spreads > spread_threshold)[0]
        outlier_indices.extend(spread_outliers)
        
        # 去重并排序
        outlier_indices = sorted(list(set(outlier_indices)))
        
        # 限制过滤点数量（不超过总数据的20%）
        max_filtered = int(len(prices) * 0.2)
        if len(outlier_indices) > max_filtered:
            outlier_indices = outlier_indices[:max_filtered]
        
        return outlier_indices
    
    def _apply_intelligent_smoothing(self, prices, high_prices, low_prices, outlier_indices, volatility_stats):
        """应用智能平滑处理"""
        smoothed_prices = prices.copy()
        smoothed_high = high_prices.copy()
        smoothed_low = low_prices.copy()
        
        # 1. 对异常点进行平滑处理
        for idx in outlier_indices:
            if idx == 0:
                # 第一个点，使用下一个点的值
                if len(prices) > 1:
                    smoothed_prices[idx] = prices[1]
                    smoothed_high[idx] = high_prices[1]
                    smoothed_low[idx] = low_prices[1]
            elif idx == len(prices) - 1:
                # 最后一个点，使用前一个点的值
                smoothed_prices[idx] = prices[idx-1]
                smoothed_high[idx] = high_prices[idx-1]
                smoothed_low[idx] = low_prices[idx-1]
            else:
                # 中间点，使用前后点的加权平均
                weight = 0.5
                smoothed_prices[idx] = weight * prices[idx-1] + (1-weight) * prices[idx+1]
                smoothed_high[idx] = weight * high_prices[idx-1] + (1-weight) * high_prices[idx+1]
                smoothed_low[idx] = weight * low_prices[idx-1] + (1-weight) * low_prices[idx+1]
        
        # 2. 应用移动平均平滑（可选）
        if len(outlier_indices) > len(prices) * 0.1:  # 如果过滤点超过10%，应用额外平滑
            window = 3
            for i in range(window, len(smoothed_prices) - window):
                smoothed_prices[i] = np.mean(smoothed_prices[i-window:i+window+1])
                smoothed_high[i] = np.mean(smoothed_high[i-window:i+window+1])
                smoothed_low[i] = np.mean(smoothed_low[i-window:i+window+1])
        
        return {
            'prices': smoothed_prices,
            'high_prices': smoothed_high,
            'low_prices': smoothed_low,
            'method': 'intelligent_smoothing'
        }
    
    def _validate_filtered_data(self, smoothed_data, volatility_stats):
        """验证过滤后的数据质量"""
        # 1. 检查数据完整性
        if np.any(np.isnan(smoothed_data['prices'])) or np.any(np.isinf(smoothed_data['prices'])):
            return False
        
        # 2. 检查价格逻辑性
        for i in range(len(smoothed_data['prices'])):
            if (smoothed_data['high_prices'][i] < smoothed_data['low_prices'][i] or
                smoothed_data['prices'][i] > smoothed_data['high_prices'][i] or
                smoothed_data['prices'][i] < smoothed_data['low_prices'][i]):
                return False
        
        # 3. 检查波动率改善
        original_vol = volatility_stats['mean_vol']
        filtered_returns = np.diff(smoothed_data['prices']) / smoothed_data['prices'][:-1]
        filtered_vol = np.std(filtered_returns)
        
        # 波动率应该有所改善
        if filtered_vol >= original_vol:
            return False
        
        return True
    
    def _apply_intelligent_volatility_filter(self, prices, high_prices, low_prices):
        """
        智能波动率过滤 - 根据波动率特征自动调整过滤强度
        
        Args:
            prices: 收盘价序列
            high_prices: 最高价序列
            low_prices: 最低价序列
            
        Returns:
            dict: 过滤后的数据和波动率统计
        """
        try:
            # 1. 计算基础波动率指标
            volatility_stats = self._calculate_volatility_statistics(prices, high_prices, low_prices)
            
            # 2. 智能确定过滤策略
            filter_strategy = self._determine_intelligent_filter_strategy(volatility_stats)
            
            # 3. 根据策略应用过滤
            if filter_strategy['apply_filter']:
                outlier_indices = self._identify_intelligent_outliers(
                    prices, high_prices, low_prices, volatility_stats, filter_strategy
                )
                
                smoothed_data = self._apply_intelligent_smoothing(
                    prices, high_prices, low_prices, outlier_indices, volatility_stats, filter_strategy
                )
                
                # 4. 验证过滤效果
                if not self._validate_filtered_data(smoothed_data, volatility_stats):
                    return None
                
                # 更新波动率统计
                volatility_stats.update({
                    'filter_strategy': filter_strategy,
                    'filtered_points': len(outlier_indices),
                    'smoothing_method': smoothed_data['method']
                })
                
                return {
                    'prices': smoothed_data['prices'],
                    'high_prices': smoothed_data['high_prices'],
                    'low_prices': smoothed_data['low_prices'],
                    'volatility_stats': volatility_stats
                }
            else:
                # 不应用过滤，但记录策略
                volatility_stats.update({
                    'filter_strategy': filter_strategy,
                    'filtered_points': 0,
                    'smoothing_method': 'no_filter'
                })
                
                return {
                    'prices': prices,
                    'high_prices': high_prices,
                    'low_prices': low_prices,
                    'volatility_stats': volatility_stats
                }
            
        except Exception as e:
            print(f"智能波动率过滤失败: {e}")
            return None
    
    def _determine_intelligent_filter_strategy(self, volatility_stats):
        """
        智能确定波动率过滤策略
        
        基于测试结果：
        - 低波动率股票 (<3%): 轻微过滤，主要提升信号质量
        - 中波动率股票 (3-5%): 标准过滤，显著提升检测准确性
        - 高波动率股票 (≥5%): 关闭过滤或极轻微过滤
        """
        mean_vol = volatility_stats['mean_vol']
        
        if mean_vol < 0.03:
            # 低波动率股票：轻微过滤
            return {
                'apply_filter': True,
                'filter_intensity': 'light',
                'vol_threshold_percentile': 95,  # 95分位数
                'tr_threshold_percentile': 95,   # 95分位数
                'jump_threshold_percentile': 98, # 98分位数
                'spread_threshold_percentile': 98, # 98分位数
                'max_filter_ratio': 0.05,  # 最多过滤5%
                'smoothing_window': 2,     # 小窗口平滑
                'reason': 'low_volatility_light_filter'
            }
        elif mean_vol < 0.05:
            # 中波动率股票：标准过滤
            return {
                'apply_filter': True,
                'filter_intensity': 'standard',
                'vol_threshold_percentile': 90,  # 90分位数
                'tr_threshold_percentile': 90,   # 90分位数
                'jump_threshold_percentile': 95, # 95分位数
                'spread_threshold_percentile': 95, # 95分位数
                'max_filter_ratio': 0.15,  # 最多过滤15%
                'smoothing_window': 3,     # 标准窗口平滑
                'reason': 'medium_volatility_standard_filter'
            }
        else:
            # 高波动率股票：关闭过滤
            return {
                'apply_filter': False,
                'filter_intensity': 'none',
                'reason': 'high_volatility_no_filter'
            }
    
    def _identify_intelligent_outliers(self, prices, high_prices, low_prices, volatility_stats, strategy):
        """智能识别异常点"""
        if not strategy['apply_filter']:
            return []
        
        outlier_indices = []
        
        # 1. 基于滚动波动率的异常检测
        vol_threshold = np.percentile(volatility_stats['rolling_volatility'], strategy['vol_threshold_percentile'])
        vol_outliers = np.where(volatility_stats['rolling_volatility'] > vol_threshold)[0]
        outlier_indices.extend(vol_outliers)
        
        # 2. 基于真实波动率的异常检测
        tr_threshold = np.percentile(volatility_stats['true_range'], strategy['tr_threshold_percentile'])
        tr_outliers = np.where(volatility_stats['true_range'] > tr_threshold)[0]
        outlier_indices.extend(tr_outliers)
        
        # 3. 基于价格跳跃的异常检测
        price_jumps = np.abs(np.diff(prices)) / prices[:-1]
        jump_threshold = np.percentile(price_jumps, strategy['jump_threshold_percentile'])
        jump_outliers = np.where(price_jumps > jump_threshold)[0]
        outlier_indices.extend(jump_outliers)
        
        # 4. 基于高低价差的异常检测
        price_spreads = (high_prices - low_prices) / prices
        spread_threshold = np.percentile(price_spreads, strategy['spread_threshold_percentile'])
        spread_outliers = np.where(price_spreads > spread_threshold)[0]
        outlier_indices.extend(spread_outliers)
        
        # 去重并排序
        outlier_indices = sorted(list(set(outlier_indices)))
        
        # 限制过滤点数量
        max_filtered = int(len(prices) * strategy['max_filter_ratio'])
        if len(outlier_indices) > max_filtered:
            outlier_indices = outlier_indices[:max_filtered]
        
        return outlier_indices
    
    def _apply_intelligent_smoothing(self, prices, high_prices, low_prices, outlier_indices, volatility_stats, strategy):
        """智能平滑处理"""
        smoothed_prices = prices.copy()
        smoothed_high = high_prices.copy()
        smoothed_low = low_prices.copy()
        
        # 1. 对异常点进行平滑处理
        for idx in outlier_indices:
            if idx == 0:
                # 第一个点，使用下一个点的值
                if len(prices) > 1:
                    smoothed_prices[idx] = prices[1]
                    smoothed_high[idx] = high_prices[1]
                    smoothed_low[idx] = low_prices[1]
            elif idx == len(prices) - 1:
                # 最后一个点，使用前一个点的值
                smoothed_prices[idx] = prices[idx-1]
                smoothed_high[idx] = high_prices[idx-1]
                smoothed_low[idx] = low_prices[idx-1]
            else:
                # 中间点，使用前后点的加权平均
                weight = 0.5
                smoothed_prices[idx] = weight * prices[idx-1] + (1-weight) * prices[idx+1]
                smoothed_high[idx] = weight * high_prices[idx-1] + (1-weight) * high_prices[idx+1]
                smoothed_low[idx] = weight * low_prices[idx-1] + (1-weight) * low_prices[idx+1]
        
        # 2. 根据策略应用移动平均平滑
        if len(outlier_indices) > len(prices) * 0.05:  # 如果过滤点超过5%
            window = strategy['smoothing_window']
            for i in range(window, len(smoothed_prices) - window):
                smoothed_prices[i] = np.mean(smoothed_prices[i-window:i+window+1])
                smoothed_high[i] = np.mean(smoothed_high[i-window:i+window+1])
                smoothed_low[i] = np.mean(smoothed_low[i-window:i+window+1])
        
        return {
            'prices': smoothed_prices,
            'high_prices': smoothed_high,
            'low_prices': smoothed_low,
            'method': f'intelligent_smoothing_{strategy["filter_intensity"]}'
        }
    
    def _apply_intelligent_volatility_boost(self, base_score, volatility_stats, channel_quality):
        """智能波动率过滤质量提升"""
        boost = 0
        
        strategy = volatility_stats.get('filter_strategy', {})
        filter_intensity = strategy.get('filter_intensity', 'none')
        
        # 1. 基于过滤策略的质量提升
        if filter_intensity == 'light':
            boost += 0.02  # 轻微过滤提升
        elif filter_intensity == 'standard':
            boost += 0.05  # 标准过滤提升
        elif filter_intensity == 'none':
            # 高波动率股票，基于波动率稳定性给予奖励
            if volatility_stats['std_vol'] < volatility_stats['mean_vol'] * 0.6:
                boost += 0.03  # 高波动率但稳定性好
        
        # 2. 波动率与通道质量的匹配度
        channel_width = channel_quality['channel_width_pct']
        mean_vol = volatility_stats['mean_vol']
        
        if channel_width < 0.15:  # 窄通道
            if mean_vol < 0.03:  # 低波动率
                boost += 0.05  # 窄通道配低波动率，质量更高
        elif channel_width > 0.3:  # 宽通道
            if mean_vol > 0.04:  # 中高波动率
                boost += 0.05  # 宽通道配中高波动率，质量更高
        
        # 3. 价格分布质量
        inside_ratio = channel_quality['price_distribution']['inside_ratio']
        if inside_ratio > 0.85 and mean_vol < 0.04:
            boost += 0.05  # 高内分布率配低中波动率
        
        # 4. 过滤效果奖励
        filtered_points = volatility_stats.get('filtered_points', 0)
        if filtered_points > 0:
            filter_ratio = filtered_points / len(volatility_stats['returns'])
            if 0.02 <= filter_ratio <= 0.1:  # 适度的过滤比例
                boost += 0.03
        
        enhanced_score = min(1.0, base_score + boost)
        return enhanced_score 