# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from scipy import stats
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("Warning: TA-Lib not available. Using basic implementation.")

class PatternAnalyzer:
    def __init__(self):
        self.talib_available = TALIB_AVAILABLE
    
    def detect_major_arc_bottom_enhanced(self, prices, high_prices=None, low_prices=None, volume=None, min_points=30, r2_threshold=0.6):
        """
        使用TA-Lib增强的大弧底检测算法
        
        Args:
            prices: 收盘价序列
            high_prices: 最高价序列（可选，用于支撑阻力分析）
            low_prices: 最低价序列（可选，用于支撑阻力分析）
            volume: 成交量序列（可选，用于成交量确认）
            min_points: 最小数据点数
            r2_threshold: R²拟合度阈值
            
        Returns:
            dict: 增强的大弧底分析结果
        """
        # 如果没有TA-Lib，回退到基本方法
        if not self.talib_available:
            return self.detect_major_arc_bottom(prices, min_points, r2_threshold)
        
        if len(prices) < min_points:
            return None
        
        # 转换为numpy数组
        prices = np.array(prices, dtype=np.float64)
        if high_prices is not None:
            high_prices = np.array(high_prices, dtype=np.float64)
        if low_prices is not None:
            low_prices = np.array(low_prices, dtype=np.float64)
        if volume is not None:
            volume = np.array(volume, dtype=np.float64)
        
        # 1. 基础大弧底检测
        basic_result = self.detect_major_arc_bottom(prices, min_points, r2_threshold)
        if not basic_result:
            return None
        
        # 2. TA-Lib技术指标增强分析
        enhanced_analysis = self._analyze_with_talib_indicators(
            prices, high_prices, low_prices, volume, basic_result
        )
        
        # 3. 合并结果
        enhanced_result = basic_result.copy()
        enhanced_result['talib_analysis'] = enhanced_analysis
        enhanced_result['enhanced_quality_score'] = self._calculate_enhanced_quality_score(
            basic_result, enhanced_analysis
        )
        
        return enhanced_result
    
    def _analyze_with_talib_indicators(self, prices, high_prices, low_prices, volume, basic_result):
        """使用TA-Lib指标进行增强分析"""
        analysis = {}
        
        # 1. 移动平均线分析
        analysis['moving_averages'] = self._analyze_moving_averages(prices)
        
        # 2. 动量指标分析
        analysis['momentum'] = self._analyze_momentum_indicators(prices, high_prices, low_prices)
        
        # 3. 趋势指标分析
        analysis['trend'] = self._analyze_trend_indicators(prices, high_prices, low_prices)
        
        # 4. 成交量分析（如果有成交量数据）
        if volume is not None:
            analysis['volume'] = self._analyze_volume_indicators(prices, volume)
        
        # 5. 支撑阻力位分析
        if high_prices is not None and low_prices is not None:
            analysis['support_resistance'] = self._analyze_support_resistance(
                prices, high_prices, low_prices, basic_result
            )
        
        # 6. 波动率分析
        analysis['volatility'] = self._analyze_volatility_indicators(prices, high_prices, low_prices)
        
        return analysis
    
    def _analyze_moving_averages(self, prices):
        """移动平均线分析"""
        ma_analysis = {}
        
        try:
            # 短期、中期、长期移动平均
            ma20 = talib.SMA(prices, timeperiod=20)
            ma50 = talib.SMA(prices, timeperiod=50)
            ma200 = talib.EMA(prices, timeperiod=min(200, len(prices)//2))
            
            # 当前价格与移动平均线的关系
            current_vs_ma20 = (prices[-1] - ma20[-1]) / ma20[-1] if not np.isnan(ma20[-1]) else 0
            current_vs_ma50 = (prices[-1] - ma50[-1]) / ma50[-1] if not np.isnan(ma50[-1]) else 0
            current_vs_ma200 = (prices[-1] - ma200[-1]) / ma200[-1] if not np.isnan(ma200[-1]) else 0
            
            # 移动平均线排列（多头/空头排列）
            ma_arrangement = self._check_ma_arrangement(ma20, ma50, ma200)
            
            ma_analysis = {
                'ma20_slope': self._calculate_slope(ma20[-10:]) if len(ma20) >= 10 else 0,
                'ma50_slope': self._calculate_slope(ma50[-10:]) if len(ma50) >= 10 else 0,
                'current_vs_ma20': current_vs_ma20,
                'current_vs_ma50': current_vs_ma50,
                'current_vs_ma200': current_vs_ma200,
                'arrangement': ma_arrangement,
                'score': self._score_moving_averages(current_vs_ma20, current_vs_ma50, current_vs_ma200, ma_arrangement)
            }
        except Exception as e:
            ma_analysis = {'error': str(e), 'score': 0}
        
        return ma_analysis
    
    def _analyze_momentum_indicators(self, prices, high_prices, low_prices):
        """动量指标分析"""
        momentum_analysis = {}
        
        try:
            # RSI - 相对强弱指标
            rsi = talib.RSI(prices, timeperiod=14)
            current_rsi = rsi[-1] if not np.isnan(rsi[-1]) else 50
            
            # MACD - 指数平滑移动平均收敛发散
            macd, macd_signal, macd_hist = talib.MACD(prices)
            macd_bullish = macd[-1] > macd_signal[-1] if not (np.isnan(macd[-1]) or np.isnan(macd_signal[-1])) else False
            
            # 威廉指标
            if high_prices is not None and low_prices is not None:
                willr = talib.WILLR(high_prices, low_prices, prices, timeperiod=14)
                current_willr = willr[-1] if not np.isnan(willr[-1]) else -50
            else:
                current_willr = -50
            
            # CCI - 商品通道指数
            if high_prices is not None and low_prices is not None:
                cci = talib.CCI(high_prices, low_prices, prices, timeperiod=14)
                current_cci = cci[-1] if not np.isnan(cci[-1]) else 0
            else:
                current_cci = 0
            
            momentum_analysis = {
                'rsi': current_rsi,
                'rsi_oversold': current_rsi < 30,
                'rsi_overbought': current_rsi > 70,
                'macd_bullish': macd_bullish,
                'willr': current_willr,
                'cci': current_cci,
                'score': self._score_momentum_indicators(current_rsi, macd_bullish, current_willr, current_cci)
            }
        except Exception as e:
            momentum_analysis = {'error': str(e), 'score': 0}
        
        return momentum_analysis
    
    def _analyze_trend_indicators(self, prices, high_prices, low_prices):
        """趋势指标分析"""
        trend_analysis = {}
        
        try:
            # ADX - 平均趋向指数（趋势强度）
            if high_prices is not None and low_prices is not None:
                adx = talib.ADX(high_prices, low_prices, prices, timeperiod=14)
                plus_di = talib.PLUS_DI(high_prices, low_prices, prices, timeperiod=14)
                minus_di = talib.MINUS_DI(high_prices, low_prices, prices, timeperiod=14)
                
                current_adx = adx[-1] if not np.isnan(adx[-1]) else 0
                current_plus_di = plus_di[-1] if not np.isnan(plus_di[-1]) else 0
                current_minus_di = minus_di[-1] if not np.isnan(minus_di[-1]) else 0
                
                trend_strength = 'strong' if current_adx > 25 else 'weak'
                trend_direction = 'bullish' if current_plus_di > current_minus_di else 'bearish'
            else:
                current_adx = 0
                trend_strength = 'unknown'
                trend_direction = 'unknown'
            
            # 抛物线SAR
            if high_prices is not None and low_prices is not None:
                sar = talib.SAR(high_prices, low_prices)
                sar_bullish = prices[-1] > sar[-1] if not np.isnan(sar[-1]) else False
            else:
                sar_bullish = False
            
            trend_analysis = {
                'adx': current_adx,
                'trend_strength': trend_strength,
                'trend_direction': trend_direction,
                'sar_bullish': sar_bullish,
                'score': self._score_trend_indicators(current_adx, trend_direction, sar_bullish)
            }
        except Exception as e:
            trend_analysis = {'error': str(e), 'score': 0}
        
        return trend_analysis
    
    def _analyze_volume_indicators(self, prices, volume):
        """成交量指标分析"""
        volume_analysis = {}
        
        try:
            # OBV - 能量潮指标
            obv = talib.OBV(prices, volume)
            obv_trend = self._calculate_slope(obv[-20:]) if len(obv) >= 20 else 0
            
            # 成交量移动平均
            volume_ma = talib.SMA(volume, timeperiod=20)
            volume_vs_ma = volume[-1] / volume_ma[-1] if not np.isnan(volume_ma[-1]) and volume_ma[-1] > 0 else 1
            
            volume_analysis = {
                'obv_trend': obv_trend,
                'volume_vs_ma': volume_vs_ma,
                'volume_surge': volume_vs_ma > 1.5,
                'score': self._score_volume_indicators(obv_trend, volume_vs_ma)
            }
        except Exception as e:
            volume_analysis = {'error': str(e), 'score': 0}
        
        return volume_analysis
    
    def _analyze_support_resistance(self, prices, high_prices, low_prices, basic_result):
        """支撑阻力位分析"""
        sr_analysis = {}
        
        try:
            # 使用基础结果中的低位区信息
            low_zone = basic_result.get('low_zone_analysis', {})
            low_zone_max = low_zone.get('low_zone_max', np.min(prices) * 1.35)
            
            # 计算低位区内的支撑强度
            low_zone_prices = prices[prices <= low_zone_max]
            support_tests = len(low_zone_prices)
            
            # 使用最低价计算支撑位强度
            support_level = np.min(low_prices) if low_prices is not None else np.min(prices)
            prices_near_support = np.sum(np.abs(low_prices - support_level) < (support_level * 0.02)) if low_prices is not None else 0
            
            sr_analysis = {
                'support_level': support_level,
                'support_tests': support_tests,
                'prices_near_support': prices_near_support,
                'support_strength': min(support_tests / 10, 1.0),  # 标准化到0-1
                'score': min((support_tests + prices_near_support) / 20, 1.0)
            }
        except Exception as e:
            sr_analysis = {'error': str(e), 'score': 0}
        
        return sr_analysis
    
    def _analyze_volatility_indicators(self, prices, high_prices, low_prices):
        """波动率指标分析"""
        volatility_analysis = {}
        
        try:
            # ATR - 真实波幅
            if high_prices is not None and low_prices is not None:
                atr = talib.ATR(high_prices, low_prices, prices, timeperiod=14)
                current_atr = atr[-1] if not np.isnan(atr[-1]) else 0
                atr_pct = current_atr / prices[-1] if prices[-1] > 0 else 0
            else:
                current_atr = 0
                atr_pct = 0
            
            # 布林带
            bb_upper, bb_middle, bb_lower = talib.BBANDS(prices, timeperiod=20)
            bb_position = (prices[-1] - bb_lower[-1]) / (bb_upper[-1] - bb_lower[-1]) if not (np.isnan(bb_upper[-1]) or np.isnan(bb_lower[-1])) else 0.5
            
            volatility_analysis = {
                'atr': current_atr,
                'atr_percentage': atr_pct,
                'bb_position': bb_position,
                'low_volatility': atr_pct < 0.02,  # 低波动率有利于盘整
                'score': self._score_volatility_indicators(atr_pct, bb_position)
            }
        except Exception as e:
            volatility_analysis = {'error': str(e), 'score': 0}
        
        return volatility_analysis
    
    def detect_major_arc_bottom(self, prices, min_points=30, r2_threshold=0.6):
        """
        识别大弧底形态：寻找3-5年低位区间的有力支撑位
        
        投资策略核心：
        1. 确定3-5年的价格低位区间（如最高价10元，低位区3.5元以内）
        2. 箱体最高点在低位区的0.8-1.2倍之间
        3. 箱体盘整周期大于6个月（约26周）
        4. 整体形态：初期高位 → 长期下跌 → 箱体盘整 → 末尾升高趋势
        
        Args:
            prices: 价格序列（周K线数据）
            min_points: 最小数据点数（建议至少78周=1.5年）
            r2_threshold: R²拟合度阈值
            
        Returns:
            dict: 大弧底分析结果，如果不满足则返回None
        """
        if len(prices) < min_points:
            return None
        
        # 1. 确定3-5年的价格低位区间
        low_zone_analysis = self._analyze_low_price_zone(prices)
        if not low_zone_analysis:
            return None
        
        # 2. 检查初期高位特征（必须远高于低位区）
        initial_high = self._check_initial_high_vs_low_zone(prices, low_zone_analysis)
        if not initial_high:
            return None
        
        # 3. 检查长期下跌趋势（从高位到低位区）
        decline_analysis = self._analyze_decline_to_low_zone(prices, initial_high, low_zone_analysis)
        if not decline_analysis:
            return None
        
        # 4. 检查箱体盘整特征（在低位区内，持续6个月以上）
        box_analysis = self._analyze_low_zone_consolidation(prices, low_zone_analysis, decline_analysis['first_low_zone_entry'])
        if not box_analysis:
            return None
        
        # 5. 检查末尾升高趋势
        uptrend_analysis = self._check_recent_uptrend(prices, box_analysis)
        if not uptrend_analysis:
            return None
        
        # 6. 整体形态拟合验证
        x = np.arange(len(prices))
        coeffs = np.polyfit(x, prices, 2)
        y_fit = np.polyval(coeffs, x)
        r2 = 1 - np.sum((prices - y_fit) ** 2) / np.sum((prices - np.mean(prices)) ** 2)
        
        if r2 < r2_threshold:
            return None
        
        # 7. 计算综合质量评分
        quality_score = self._calculate_strategic_arc_quality(
            prices, coeffs, r2, low_zone_analysis, initial_high, 
            decline_analysis, box_analysis, uptrend_analysis
        )
        
        return {
            'type': 'strategic_major_arc_bottom',
            'r2': r2,
            'quality_score': quality_score,
            'coeffs': coeffs,
            'low_zone_analysis': low_zone_analysis,
            'initial_high': initial_high,
            'decline_analysis': decline_analysis,
            'box_analysis': box_analysis,
            'uptrend_analysis': uptrend_analysis,
            'total_points': len(prices),
            'consolidation_weeks': box_analysis['duration'],
            'support_strength': box_analysis['support_strength'],
            'price_range': {
                'start': prices[0],
                'end': prices[-1],
                'min': np.min(prices),
                'max': np.max(prices),
                'low_zone_max': low_zone_analysis['low_zone_max'],
                'box_range': f"{box_analysis['box_low']:.2f}-{box_analysis['box_high']:.2f}"
            }
        }
    
    def calculate_arc_similarity(self, prices, min_points=30):
        """
        计算股票与理想大弧底形态的相似度得分
        即使不完全符合条件，也给出相似度评分
        
        Returns:
            dict: 包含相似度得分和各项评分的详细信息
        """
        if len(prices) < min_points:
            return {
                'similarity_score': 0.0,
                'reason': 'insufficient_data',
                'details': {}
            }
        
        similarity_factors = {}
        total_score = 0.0
        
        # 1. 低位区分析（权重25%）
        low_zone_analysis = self._analyze_low_price_zone_flexible(prices)
        similarity_factors['low_zone'] = low_zone_analysis
        total_score += low_zone_analysis['score'] * 0.25
        
        # 2. 初期高位分析（权重15%）
        if low_zone_analysis['score'] > 0:
            initial_high_analysis = self._analyze_initial_high_flexible(prices, low_zone_analysis['data'])
            similarity_factors['initial_high'] = initial_high_analysis
            total_score += initial_high_analysis['score'] * 0.15
        else:
            similarity_factors['initial_high'] = {'score': 0.0, 'reason': 'no_low_zone'}
        
        # 3. 下跌趋势分析（权重20%）
        decline_analysis = self._analyze_decline_flexible(prices)
        similarity_factors['decline'] = decline_analysis
        total_score += decline_analysis['score'] * 0.20
        
        # 4. 盘整分析（权重30%）- 最重要的因素
        consolidation_analysis = self._analyze_consolidation_flexible(prices)
        similarity_factors['consolidation'] = consolidation_analysis
        total_score += consolidation_analysis['score'] * 0.30
        
        # 5. 上升趋势分析（权重10%）
        uptrend_analysis = self._analyze_uptrend_flexible(prices)
        similarity_factors['uptrend'] = uptrend_analysis
        total_score += uptrend_analysis['score'] * 0.10
        
        return {
            'similarity_score': total_score,
            'factors': similarity_factors,
            'recommendation': self._get_similarity_recommendation(total_score),
            'details': {
                'total_weeks': len(prices),
                'price_range': f"{np.min(prices):.2f}-{np.max(prices):.2f}",
                'current_price': prices[-1],
                'decline_from_high': (np.max(prices) - prices[-1]) / np.max(prices)
            }
        }
    
    def _analyze_low_price_zone(self, prices):
        """
        分析3-5年的价格低位区间
        
        策略：找到历史最高价，然后确定低位区间（通常是最高价的30-40%）
        """
        max_price = np.max(prices)
        min_price = np.min(prices)
        
        # 计算价格区间
        price_range = max_price - min_price
        
        # 低位区定义：最高价的35%以内（可调整）
        low_zone_threshold_ratio = 0.35
        low_zone_max = min_price + (price_range * low_zone_threshold_ratio)
        
        # 找到低位区内的所有价格点
        low_zone_indices = np.where(prices <= low_zone_max)[0]
        
        if len(low_zone_indices) < 26:  # 至少6个月的数据在低位区
            return None
        
        # 分析低位区的特征
        low_zone_prices = prices[low_zone_indices]
        low_zone_duration = len(low_zone_indices)
        
        return {
            'max_price': max_price,
            'min_price': min_price,
            'low_zone_max': low_zone_max,
            'low_zone_threshold_ratio': low_zone_threshold_ratio,
            'low_zone_indices': low_zone_indices,
            'low_zone_prices': low_zone_prices,
            'low_zone_duration': low_zone_duration,
            'low_zone_avg': np.mean(low_zone_prices),
            'low_zone_std': np.std(low_zone_prices)
        }
    
    def _check_initial_high_vs_low_zone(self, prices, low_zone_analysis):
        """
        检查初期高位特征，确保初期价格远高于低位区
        """
        # 前20%时期的最高价应该接近历史最高价
        initial_period = max(5, len(prices) // 5)
        initial_prices = prices[:initial_period]
        initial_max = np.max(initial_prices)
        
        max_price = low_zone_analysis['max_price']
        low_zone_max = low_zone_analysis['low_zone_max']
        
        # 初期最高价应该至少是低位区上限的2.5倍
        if initial_max < low_zone_max * 2.5:
            return None
        
        # 初期最高价应该至少是历史最高价的85%
        if initial_max < max_price * 0.85:
            return None
        
        max_idx = np.argmax(prices)
        
        return {
            'max_idx': max_idx,
            'max_price': max_price,
            'initial_max': initial_max,
            'initial_period': initial_period,
            'high_to_low_ratio': initial_max / low_zone_max
        }
    
    def _analyze_decline_to_low_zone(self, prices, initial_high, low_zone_analysis):
        """
        分析从高位到低位区的下跌趋势
        """
        max_idx = initial_high['max_idx']
        low_zone_indices = low_zone_analysis['low_zone_indices']
        
        # 找到第一次进入低位区的时间点
        first_low_zone_entry = None
        for idx in low_zone_indices:
            if idx > max_idx:
                first_low_zone_entry = idx
                break
        
        if first_low_zone_entry is None:
            return None
        
        # 分析下跌阶段
        decline_prices = prices[max_idx:first_low_zone_entry+1]
        decline_duration = len(decline_prices)
        
        # 下跌幅度计算
        decline_amplitude = (prices[max_idx] - prices[first_low_zone_entry]) / prices[max_idx]
        
        # 下跌应该显著（至少50%）且持续时间合理
        if decline_amplitude < 0.5:
            return None
        
        if decline_duration < len(prices) * 0.2:  # 下跌至少占总时间的20%
            return None
        
        return {
            'max_idx': max_idx,
            'first_low_zone_entry': first_low_zone_entry,
            'decline_duration': decline_duration,
            'decline_amplitude': decline_amplitude,
            'decline_start_price': prices[max_idx],
            'decline_end_price': prices[first_low_zone_entry]
        }
    
    def _analyze_low_zone_consolidation(self, prices, low_zone_analysis, decline_end_idx):
        """
        分析低位区的箱体盘整特征
        
        关键要求：
        1. 箱体最高点在低位区的0.8-1.2倍之间
        2. 盘整周期大于6个月（26周）
        3. 价格波动相对稳定
        """
        low_zone_max = low_zone_analysis['low_zone_max']
        low_zone_indices = low_zone_analysis['low_zone_indices']
        
        # 找到进入低位区后的盘整阶段
        consolidation_start = decline_end_idx
        
        # 筛选盘整阶段的价格（从decline_end_idx开始的低位区价格）
        consolidation_indices = [idx for idx in low_zone_indices if idx >= consolidation_start]
        
        if len(consolidation_indices) < 26:  # 盘整期至少6个月
            return None
        
        # 连续性检查：确保盘整期基本连续
        consolidation_indices = np.array(consolidation_indices)
        gaps = np.diff(consolidation_indices)
        
        # 如果有太多间隔，说明不是连续的盘整
        if np.sum(gaps > 4) > len(gaps) * 0.2:  # 允许20%的间隔
            return None
        
        consolidation_prices = prices[consolidation_indices]
        box_high = np.max(consolidation_prices)
        box_low = np.min(consolidation_prices)
        box_center = (box_high + box_low) / 2
        
        # 验证箱体高点要求：0.8-1.2倍低位区上限
        if box_high < low_zone_max * 0.8 or box_high > low_zone_max * 1.2:
            return None
        
        # 计算支撑强度（价格在箱体下半部分停留的时间）
        lower_half_threshold = box_low + (box_high - box_low) * 0.4
        support_touches = np.sum(consolidation_prices <= lower_half_threshold)
        support_strength = support_touches / len(consolidation_prices)
        
        # 支撑强度应该足够（至少30%的时间在下半部分）
        if support_strength < 0.3:
            return None
        
        # 计算盘整期的波动率
        volatility = np.std(consolidation_prices) / box_center
        
        # 波动率应该相对稳定（不超过15%）
        if volatility > 0.15:
            return None
        
        return {
            'consolidation_start': consolidation_start,
            'consolidation_indices': consolidation_indices,
            'duration': len(consolidation_indices),
            'duration_months': len(consolidation_indices) / 4.33,  # 周转月
            'box_high': box_high,
            'box_low': box_low,
            'box_center': box_center,
            'box_range_pct': (box_high - box_low) / box_center,
            'support_strength': support_strength,
            'volatility': volatility,
            'low_zone_ratio': box_high / low_zone_max,
            'consolidation_prices': consolidation_prices
        }
    
    def _check_recent_uptrend(self, prices, box_analysis):
        """
        检查末尾的升高趋势
        """
        consolidation_indices = box_analysis['consolidation_indices']
        last_consolidation_idx = consolidation_indices[-1]
        
        # 获取盘整结束后的价格数据
        recent_start = last_consolidation_idx + 1
        if recent_start >= len(prices) - 3:  # 至少需要3个数据点
            return None
        
        recent_prices = prices[recent_start:]
        
        if len(recent_prices) < 3:
            return None
        
        # 计算最近趋势
        x = np.arange(len(recent_prices))
        if len(recent_prices) > 1:
            slope, _, r_value, _, _ = stats.linregress(x, recent_prices)
        else:
            slope = 0
            r_value = 0
        
        # 应该有明显的上升趋势
        if slope <= 0:
            return None
        
        # 最新价格应该高于箱体中位数
        if recent_prices[-1] <= box_analysis['box_center']:
            return None
        
        uptrend_strength = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        
        return {
            'recent_start': recent_start,
            'recent_duration': len(recent_prices),
            'uptrend_slope': slope,
            'uptrend_r2': r_value ** 2 if isinstance(r_value, (int, float)) else 0,
            'uptrend_strength': uptrend_strength,
            'recent_high': np.max(recent_prices),
            'breakthrough_box': recent_prices[-1] > box_analysis['box_high']
        }
    
    def _calculate_strategic_arc_quality(self, prices, coeffs, r2, low_zone_analysis, 
                                       initial_high, decline_analysis, box_analysis, uptrend_analysis):
        """
        计算基于投资策略的大弧底质量评分
        """
        quality_factors = []
        
        # 1. 低位区质量（25%）- 低位区越明确越好
        low_zone_quality = min(low_zone_analysis['low_zone_duration'] / 52, 1.0)  # 理想：1年在低位区
        low_zone_quality *= (1.0 - low_zone_analysis['low_zone_std'] / low_zone_analysis['low_zone_avg'])  # 稳定性
        quality_factors.append(low_zone_quality * 0.25)
        
        # 2. 盘整质量（35%）- 最重要的因素
        consolidation_quality = min(box_analysis['duration'] / 52, 1.0)  # 理想：1年盘整
        consolidation_quality *= box_analysis['support_strength']  # 支撑强度
        consolidation_quality *= (1.0 - box_analysis['volatility'])  # 稳定性
        quality_factors.append(consolidation_quality * 0.35)
        
        # 3. 下跌质量（20%）- 从高位到低位的有效下跌
        decline_quality = min(decline_analysis['decline_amplitude'] / 0.7, 1.0)  # 理想下跌70%
        decline_quality *= min(decline_analysis['decline_duration'] / (len(prices) * 0.3), 1.0)
        quality_factors.append(decline_quality * 0.20)
        
        # 4. 上升趋势质量（15%）- 末尾的突破能力
        uptrend_quality = min(uptrend_analysis['uptrend_strength'] / 0.2, 1.0)  # 理想上涨20%
        if uptrend_analysis['breakthrough_box']:
            uptrend_quality *= 1.5  # 突破箱体加分
        quality_factors.append(min(uptrend_quality, 1.0) * 0.15)
        
        # 5. 整体拟合质量（5%）
        quality_factors.append(r2 * 0.05)
        
        return sum(quality_factors)
    
    def detect_arc_bottom(self, data, min_points=20):
        """检测圆弧底形态"""
        if len(data) < min_points:
            return None
        
        # 获取收盘价数据
        prices = data['close'].to_numpy() if hasattr(data['close'], 'to_numpy') else data['close'].values
        dates = np.arange(len(prices))
        
        # 标准化价格
        prices_normalized = (prices - np.min(prices)) / (np.max(prices) - np.min(prices))
        
        # 尝试拟合圆弧
        arc_score = self._fit_arc(prices_normalized, dates)
        
        # 如果圆弧拟合度不够好，返回None
        if arc_score < 0.3:  # 降低拟合度要求
            return None
        
        # 分析三阶段
        stages = self._analyze_three_stages(prices, dates)
        
        if stages:
            return {
                'type': 'arc_bottom',
                'score': arc_score,
                'stages': stages,
                'data': data
            }
        
        return None
    
    def _fit_arc(self, prices, dates):
        """拟合圆弧并计算拟合度"""
        try:
            # 尝试拟合二次函数（圆弧近似）
            coeffs = np.polyfit(dates, prices, 2)
            fitted_prices = np.polyval(coeffs, dates)
            
            # 计算R²值
            ss_res = np.sum((prices - fitted_prices) ** 2)
            ss_tot = np.sum((prices - np.mean(prices)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)
            
            # 检查是否为向上开口的抛物线（圆弧底）
            if coeffs[0] > 0:  # 二次项系数为正，向上开口
                return r_squared
            else:
                return 0
                
        except:
            return 0
    
    def _analyze_three_stages(self, prices, dates):
        """分析三阶段：下降、横向、上涨"""
        n = len(prices)
        if n < 15:
            return None
        
        # 计算移动平均线
        ma_short = pd.Series(prices).rolling(window=3).mean().to_numpy()
        ma_long = pd.Series(prices).rolling(window=7).mean().to_numpy()
        
        # 寻找转折点
        turning_points = self._find_turning_points(prices, ma_short, ma_long)
        
        if len(turning_points) < 2:
            return None
        
        # 分析三个阶段
        stages = self._identify_stages(prices, dates, turning_points)
        
        return stages
    
    def _find_turning_points(self, prices, ma_short, ma_long):
        """寻找转折点"""
        turning_points = []
        
        for i in range(5, len(prices) - 5):
            # 检查是否为局部最低点
            if (prices[i] <= prices[i-1] and prices[i] <= prices[i-2] and 
                prices[i] <= prices[i+1] and prices[i] <= prices[i+2]):
                turning_points.append(i)
            
            # 检查是否为局部最高点
            elif (prices[i] >= prices[i-1] and prices[i] >= prices[i-2] and 
                  prices[i] >= prices[i+1] and prices[i] >= prices[i+2]):
                turning_points.append(i)
        
        return turning_points
    
    def _identify_stages(self, prices, dates, turning_points):
        """识别三个阶段"""
        if len(turning_points) < 2:
            return None
        
        # 找到最低点
        min_idx = np.argmin(prices)
        
        # 在最低点之前找下降阶段
        decline_start = 0
        decline_end = min_idx
        
        # 在最低点之后找上涨阶段
        rise_start = min_idx
        rise_end = len(prices) - 1
        
        # 横向阶段（如果有的话）
        flat_start = decline_end
        flat_end = rise_start
        
        # 分析各阶段特征 - 传递全局索引
        decline_stage = self._analyze_stage(prices[decline_start:decline_end+1], 
                                          np.arange(decline_start, decline_end+1), 'decline')
        
        flat_stage = None
        if flat_end > flat_start:
            flat_stage = self._analyze_stage(prices[flat_start:flat_end+1], 
                                           np.arange(flat_start, flat_end+1), 'flat')
        
        rise_stage = self._analyze_stage(prices[rise_start:rise_end+1], 
                                        np.arange(rise_start, rise_end+1), 'rise')
        
        return {
            'decline': decline_stage,
            'flat': flat_stage,
            'rise': rise_stage,
            'min_point': min_idx,
            'min_price': prices[min_idx]
        }
    
    def _analyze_stage(self, stage_prices, stage_dates, stage_type):
        """分析单个阶段的特征"""
        if len(stage_prices) < 3:
            return None
        
        # 计算趋势
        if len(stage_dates) > 1:
            slope, intercept, r_value, p_value, std_err = stats.linregress(stage_dates, stage_prices)
        else:
            slope = 0
            r_value = 0
        
        # 计算波动性
        volatility = np.std(stage_prices)
        
        # 计算价格变化
        price_change = stage_prices[-1] - stage_prices[0]
        price_change_pct = (price_change / stage_prices[0]) * 100 if stage_prices[0] != 0 else 0
        
        return {
            'type': stage_type,
            'start_price': stage_prices[0],
            'end_price': stage_prices[-1],
            'price_change': price_change,
            'price_change_pct': price_change_pct,
            'slope': slope,
            'r_squared': r_value ** 2 if isinstance(r_value, (int, float)) else 0,
            'volatility': volatility,
            'duration': len(stage_prices),
            'prices': stage_prices,
            'dates': stage_dates  # 直接使用全局索引
        }
    
    def is_valid_arc_bottom(self, stages):
        """验证是否为有效的圆弧底形态"""
        if not stages or not stages['decline'] or not stages['rise']:
            return False
        
        decline = stages['decline']
        rise = stages['rise']
        
        # 下降阶段应该向下倾斜
        if decline['slope'] > -0.005:  # 降低斜率要求
            return False
        
        # 上涨阶段应该向上倾斜
        if rise['slope'] < 0.005:  # 降低斜率要求
            return False
        
        # 下降和上涨阶段都应该有足够的持续时间
        if decline['duration'] < 3 or rise['duration'] < 3:  # 降低持续时间要求
            return False
        
        # 价格变化应该足够显著
        if abs(decline['price_change_pct']) < 5 or abs(rise['price_change_pct']) < 5:  # 降低价格变化要求
            return False
        
        return True 
    
    # TA-Lib增强功能的评分方法
    def _score_moving_averages(self, vs_ma20, vs_ma50, vs_ma200, arrangement):
        """移动平均线评分"""
        score = 0.5  # 基础分
        
        # 当前价格高于移动平均线加分
        if vs_ma20 > 0: score += 0.1
        if vs_ma50 > 0: score += 0.15
        if vs_ma200 > 0: score += 0.2
        
        # 多头排列加分
        if arrangement == 'bullish': score += 0.2
        elif arrangement == 'bearish': score -= 0.2
        
        return max(0, min(1, score))
    
    def _score_momentum_indicators(self, rsi, macd_bullish, willr, cci):
        """动量指标评分"""
        score = 0.5
        
        # RSI在合理范围内加分
        if 30 <= rsi <= 70: score += 0.2
        elif rsi < 30: score += 0.3  # 超卖更有利
        
        # MACD多头信号
        if macd_bullish: score += 0.2
        
        # 威廉指标
        if willr < -80: score += 0.2  # 超卖
        elif willr > -20: score -= 0.1  # 超买
        
        # CCI
        if -100 <= cci <= 100: score += 0.1
        
        return max(0, min(1, score))
    
    def _score_trend_indicators(self, adx, trend_direction, sar_bullish):
        """趋势指标评分"""
        score = 0.5
        
        # ADX趋势强度
        if adx > 25: score += 0.2  # 有明确趋势
        elif adx < 15: score += 0.1  # 盘整期
        
        # 趋势方向
        if trend_direction == 'bullish': score += 0.2
        
        # SAR信号
        if sar_bullish: score += 0.1
        
        return max(0, min(1, score))
    
    def _score_volume_indicators(self, obv_trend, volume_vs_ma):
        """成交量指标评分"""
        score = 0.5
        
        # OBV趋势
        if obv_trend > 0: score += 0.3  # 资金流入
        
        # 成交量相对于平均值
        if 1.2 <= volume_vs_ma <= 2.0: score += 0.2  # 适度放量
        elif volume_vs_ma > 2.0: score += 0.1  # 大幅放量
        
        return max(0, min(1, score))
    
    def _score_volatility_indicators(self, atr_pct, bb_position):
        """波动率指标评分"""
        score = 0.5
        
        # 低波动率有利于盘整
        if atr_pct < 0.02: score += 0.3
        elif atr_pct < 0.03: score += 0.2
        
        # 布林带位置
        if bb_position < 0.3: score += 0.2  # 接近下轨
        elif bb_position > 0.7: score -= 0.1  # 接近上轨
        
        return max(0, min(1, score))
    
    def _calculate_enhanced_quality_score(self, basic_result, talib_analysis):
        """计算增强质量评分"""
        basic_score = basic_result.get('quality_score', 0.5)
        
        # 收集TA-Lib各项评分
        scores = []
        weights = []
        
        if 'moving_averages' in talib_analysis:
            scores.append(talib_analysis['moving_averages'].get('score', 0))
            weights.append(0.2)
        
        if 'momentum' in talib_analysis:
            scores.append(talib_analysis['momentum'].get('score', 0))
            weights.append(0.25)
        
        if 'trend' in talib_analysis:
            scores.append(talib_analysis['trend'].get('score', 0))
            weights.append(0.2)
        
        if 'volume' in talib_analysis:
            scores.append(talib_analysis['volume'].get('score', 0))
            weights.append(0.15)
        
        if 'support_resistance' in talib_analysis:
            scores.append(talib_analysis['support_resistance'].get('score', 0))
            weights.append(0.1)
        
        if 'volatility' in talib_analysis:
            scores.append(talib_analysis['volatility'].get('score', 0))
            weights.append(0.1)
        
        # 计算加权平均
        if scores and weights:
            talib_score = np.average(scores, weights=weights)
            # 基础评分占60%，TA-Lib评分占40%
            enhanced_score = basic_score * 0.6 + talib_score * 0.4
        else:
            enhanced_score = basic_score
        
        return enhanced_score
    
    def _check_ma_arrangement(self, ma20, ma50, ma200):
        """检查移动平均线排列"""
        try:
            current_ma20 = ma20[-1]
            current_ma50 = ma50[-1]
            current_ma200 = ma200[-1]
            
            if np.isnan(current_ma20) or np.isnan(current_ma50) or np.isnan(current_ma200):
                return 'unknown'
            
            if current_ma20 > current_ma50 > current_ma200:
                return 'bullish'
            elif current_ma20 < current_ma50 < current_ma200:
                return 'bearish'
            else:
                return 'mixed'
        except:
            return 'unknown'
    
    def _calculate_slope(self, values):
        """计算数值序列的斜率"""
        if len(values) < 2:
            return 0
        
        # 过滤NaN值
        clean_values = values[~np.isnan(values)]
        if len(clean_values) < 2:
            return 0
        
        x = np.arange(len(clean_values))
        slope, _ = np.polyfit(x, clean_values, 1)
        return slope
    
    def get_talib_analysis_summary(self, enhanced_result):
        """获取TA-Lib分析摘要"""
        if not enhanced_result or 'talib_analysis' not in enhanced_result:
            return "TA-Lib分析不可用"
        
        talib_data = enhanced_result['talib_analysis']
        summary = []
        
        # 移动平均线
        if 'moving_averages' in talib_data:
            ma_data = talib_data['moving_averages']
            if 'arrangement' in ma_data:
                if ma_data['arrangement'] == 'bullish':
                    summary.append("✓ 移动平均线呈多头排列")
                elif ma_data['arrangement'] == 'bearish':
                    summary.append("✗ 移动平均线呈空头排列")
        
        # 动量指标
        if 'momentum' in talib_data:
            momentum_data = talib_data['momentum']
            if momentum_data.get('rsi_oversold'):
                summary.append("✓ RSI显示超卖状态")
            if momentum_data.get('macd_bullish'):
                summary.append("✓ MACD金叉信号")
        
        # 趋势指标
        if 'trend' in talib_data:
            trend_data = talib_data['trend']
            if trend_data.get('trend_direction') == 'bullish':
                summary.append("✓ 趋势指标显示上升趋势")
            if trend_data.get('sar_bullish'):
                summary.append("✓ SAR发出看涨信号")
        
        # 成交量
        if 'volume' in talib_data:
            volume_data = talib_data['volume']
            if volume_data.get('volume_surge'):
                summary.append("✓ 成交量明显放大")
            if volume_data.get('obv_trend', 0) > 0:
                summary.append("✓ 资金呈流入趋势")
        
        # 波动率
        if 'volatility' in talib_data:
            vol_data = talib_data['volatility']
            if vol_data.get('low_volatility'):
                summary.append("✓ 波动率较低，有利于盘整")
        
        return "\n".join(summary) if summary else "技术指标分析中性" 
    
    def _analyze_low_price_zone_flexible(self, prices):
        """灵活的低位区分析，给出评分而不是严格判断"""
        max_price = np.max(prices)
        min_price = np.min(prices)
        current_price = prices[-1]
        
        # 计算当前价格在价格区间中的位置
        price_range = max_price - min_price
        current_position = (current_price - min_price) / price_range if price_range > 0 else 0
        
        # 计算低位区的质量
        low_zone_threshold = 0.35  # 35%作为低位区标准
        
        # 如果当前价格在低位区内，得分较高
        if current_position <= low_zone_threshold:
            position_score = 1.0 - (current_position / low_zone_threshold)
        else:
            # 超出低位区，按距离递减
            position_score = max(0, 1.0 - (current_position - low_zone_threshold) / (1.0 - low_zone_threshold))
        
        # 计算在低位区停留的时间
        low_zone_max = min_price + (price_range * low_zone_threshold)
        low_zone_weeks = np.sum(prices <= low_zone_max)
        low_zone_ratio = low_zone_weeks / len(prices)
        
        # 时间评分：在低位区停留越久得分越高
        time_score = min(low_zone_ratio / 0.3, 1.0)  # 30%时间在低位区为满分
        
        overall_score = (position_score * 0.6 + time_score * 0.4)
        
        return {
            'score': overall_score,
            'current_position': current_position,
            'low_zone_weeks': low_zone_weeks,
            'low_zone_ratio': low_zone_ratio,
            'low_zone_max': low_zone_max,
            'data': {
                'max_price': max_price,
                'min_price': min_price,
                'low_zone_max': low_zone_max,
                'low_zone_threshold_ratio': low_zone_threshold
            }
        }
    
    def _analyze_initial_high_flexible(self, prices, low_zone_data):
        """灵活的初期高位分析"""
        initial_period = max(5, len(prices) // 5)
        initial_prices = prices[:initial_period]
        initial_max = np.max(initial_prices)
        
        max_price = low_zone_data['max_price']
        low_zone_max = low_zone_data['low_zone_max']
        
        # 评分标准
        # 1. 初期最高价与历史最高价的比例
        high_ratio = initial_max / max_price
        high_score = min(high_ratio / 0.85, 1.0)  # 85%为满分
        
        # 2. 高位与低位区的比例
        if low_zone_max > 0:
            elevation_ratio = initial_max / low_zone_max
            elevation_score = min(elevation_ratio / 2.5, 1.0)  # 2.5倍为满分
        else:
            elevation_score = 0
        
        overall_score = (high_score * 0.4 + elevation_score * 0.6)
        
        return {
            'score': overall_score,
            'initial_max': initial_max,
            'high_ratio': high_ratio,
            'elevation_ratio': elevation_ratio if low_zone_max > 0 else 0,
            'initial_period': initial_period
        }
    
    def _analyze_decline_flexible(self, prices):
        """灵活的下跌趋势分析"""
        max_idx = np.argmax(prices)
        max_price = prices[max_idx]
        current_price = prices[-1]
        
        # 总下跌幅度
        total_decline = (max_price - current_price) / max_price if max_price > 0 else 0
        decline_score = min(total_decline / 0.5, 1.0)  # 50%下跌为满分
        
        # 下跌持续性
        decline_period = len(prices) - max_idx
        decline_ratio = decline_period / len(prices)
        persistence_score = min(decline_ratio / 0.6, 1.0)  # 60%时间为满分
        
        # 下跌趋势的一致性（通过线性回归检查）
        if decline_period > 3:
            decline_prices = prices[max_idx:]
            x = np.arange(len(decline_prices))
            try:
                slope, _, r_value, _, _ = stats.linregress(x, decline_prices)
                trend_score = max(0, -slope / abs(slope)) if slope != 0 else 0
                trend_score *= abs(r_value) if isinstance(r_value, (int, float)) else 0
            except:
                trend_score = 0
        else:
            trend_score = 0
        
        overall_score = (decline_score * 0.5 + persistence_score * 0.3 + trend_score * 0.2)
        
        return {
            'score': overall_score,
            'total_decline': total_decline,
            'decline_period': decline_period,
            'decline_ratio': decline_ratio,
            'max_idx': max_idx,
            'trend_score': trend_score
        }
    
    def _analyze_consolidation_flexible(self, prices):
        """灵活的盘整分析 - 最重要的评分因素"""
        min_price = np.min(prices)
        max_price = np.max(prices)
        price_range = max_price - min_price
        
        # 计算低位区阈值（与其他方法保持一致）
        low_zone_threshold = 0.35
        low_zone_max = min_price + (price_range * low_zone_threshold)
        
        # 找到所有在低位区内的价格点
        low_zone_indices = np.where(prices <= low_zone_max)[0]
        
        if len(low_zone_indices) < 6:
            return {'score': 0.0, 'reason': 'insufficient_low_zone_data'}
        
        # 找到最后的连续盘整区间
        consolidation_indices = self._find_consolidation_period(low_zone_indices)
        
        if len(consolidation_indices) < 6:
            return {'score': 0.0, 'reason': 'insufficient_consolidation_data'}
        
        # 基于实际盘整区间计算指标
        consolidation_prices = prices[consolidation_indices]
        recent_mean = np.mean(consolidation_prices)
        recent_std = np.std(consolidation_prices)
        stability_ratio = recent_std / recent_mean if recent_mean > 0 else 1.0
        
        # 稳定性评分：波动率越低得分越高
        stability_score = max(0, 1.0 - stability_ratio / 0.15)  # 15%波动率为零分
        
        # 盘整时长评分
        consolidation_weeks = len(consolidation_indices)
        duration_score = min(consolidation_weeks / 26, 1.0)  # 26周为满分
        
        # 价格位置评分：盘整位置应该在低位
        position_in_range = (recent_mean - min_price) / price_range if price_range > 0 else 0
        position_score = max(0, 1.0 - position_in_range / 0.4)  # 40%位置以上扣分
        
        # 支撑强度：价格多次触及低位
        support_level = min_price + price_range * 0.1  # 底部10%区域作为支撑
        support_touches = np.sum(prices <= support_level)
        support_ratio = support_touches / len(prices)
        support_score = min(support_ratio / 0.2, 1.0)  # 20%时间触及支撑为满分
        
        overall_score = (stability_score * 0.3 + duration_score * 0.3 + 
                        position_score * 0.2 + support_score * 0.2)
        
        return {
            'score': overall_score,
            'stability_score': stability_score,
            'duration_score': duration_score,
            'position_score': position_score,
            'support_score': support_score,
            'consolidation_weeks': consolidation_weeks,
            'recent_volatility': stability_ratio,
            'support_touches': support_touches,
            'consolidation_indices': consolidation_indices.tolist(),  # 添加实际的盘整索引
            'consolidation_start': int(consolidation_indices[0]) if len(consolidation_indices) > 0 else 0,
            'consolidation_end': int(consolidation_indices[-1]) if len(consolidation_indices) > 0 else 0,
            'box_high': float(np.max(consolidation_prices)),
            'box_low': float(np.min(consolidation_prices))
        }
    
    def _find_consolidation_period(self, low_zone_indices):
        """找到最后的连续盘整区间"""
        if len(low_zone_indices) == 0:
            return np.array([])
        
        low_zone_indices = sorted(low_zone_indices)
        
        # 从后往前找最长的连续区间
        current_end = len(low_zone_indices) - 1
        best_start = current_end
        best_length = 1
        
        # 寻找最长的连续区间
        for start in range(len(low_zone_indices)):
            for end in range(start, len(low_zone_indices)):
                # 检查这个区间是否相对连续（允许少量间隔）
                segment = low_zone_indices[start:end+1]
                if len(segment) <= 1:
                    continue
                
                # 计算间隔
                gaps = np.diff(segment)
                large_gaps = np.sum(gaps > 4)  # 间隔超过4周的数量
                
                # 如果大间隔太多，跳过这个区间
                if large_gaps > len(gaps) * 0.2:  # 超过20%的间隔太大
                    continue
                
                # 记录最好的（最长的）区间
                if len(segment) > best_length:
                    best_length = len(segment)
                    best_start = start
                    current_end = end
        
        # 返回最佳区间的实际索引
        best_indices = low_zone_indices[best_start:current_end+1]
        
        # 如果区间太短，尝试扩展到至少10个点
        if len(best_indices) < 10 and len(low_zone_indices) >= 10:
            # 取最后10个点
            best_indices = low_zone_indices[-10:]
        
        return np.array(best_indices)
    
    def _analyze_uptrend_flexible(self, prices):
        """灵活的上升趋势分析"""
        if len(prices) < 10:
            return {'score': 0.0, 'reason': 'insufficient_data'}
        
        # 分析最近的价格走势
        recent_period = min(13, len(prices) // 4)  # 最近13周或25%的数据
        recent_prices = prices[-recent_period:]
        
        if len(recent_prices) < 3:
            return {'score': 0.0, 'reason': 'insufficient_recent_data'}
        
        # 计算最近趋势
        x = np.arange(len(recent_prices))
        try:
            slope, _, r_value, _, _ = stats.linregress(x, recent_prices)
            
            # 上升斜率评分
            if slope > 0:
                slope_score = min(slope / (np.mean(recent_prices) * 0.02), 1.0)  # 2%周涨幅为满分
            else:
                slope_score = 0
            
            # 趋势一致性评分
            consistency_score = abs(r_value) if isinstance(r_value, (int, float)) else 0
            
        except:
            slope_score = 0
            consistency_score = 0
        
        # 突破评分：最新价格相对于历史低位的表现
        min_price = np.min(prices)
        current_price = prices[-1]
        breakthrough_ratio = (current_price - min_price) / min_price if min_price > 0 else 0
        breakthrough_score = min(breakthrough_ratio / 0.3, 1.0)  # 30%反弹为满分
        
        overall_score = (slope_score * 0.4 + consistency_score * 0.3 + breakthrough_score * 0.3)
        
        return {
            'score': overall_score,
            'slope_score': slope_score,
            'consistency_score': consistency_score,
            'breakthrough_score': breakthrough_score,
            'recent_slope': slope if 'slope' in locals() else 0,
            'recent_period': recent_period
        }
    
    def _get_similarity_recommendation(self, score):
        """根据相似度得分给出推荐级别"""
        if score >= 0.8:
            return "强烈推荐 - 高度符合大弧底特征"
        elif score >= 0.6:
            return "推荐 - 较好符合大弧底特征"
        elif score >= 0.4:
            return "关注 - 部分符合大弧底特征"
        elif score >= 0.2:
            return "观察 - 少量符合大弧底特征"
        else:
            return "不推荐 - 不符合大弧底特征" 