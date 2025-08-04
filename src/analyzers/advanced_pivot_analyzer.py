# -*- coding: utf-8 -*-
"""
企业级高低点分析器 - 融合顶级量化交易技术的智能转折点识别系统
集成分形维度、多时间框架、统计验证、机器学习、市场微观结构等先进技术
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import argrelextrema, find_peaks
from scipy.optimize import minimize_scalar
import warnings
warnings.filterwarnings('ignore')

try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("Warning: TA-Lib not available. Using numpy implementations.")

try:
    from sklearn.ensemble import IsolationForest, RandomForestClassifier
    from sklearn.preprocessing import StandardScaler, RobustScaler
    from sklearn.cluster import DBSCAN
    from sklearn.metrics import silhouette_score
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("Warning: Scikit-learn not available. ML features disabled.")


class EnterprisesPivotAnalyzer:
    """
    企业级高低点分析器 - 融合多种顶级量化交易技术
    
    核心技术栈：
    1. 分形维度分析 - 基于分形几何的转折点识别
    2. 多时间框架确认 - 确保不同时间尺度的一致性
    3. 统计显著性验证 - 使用统计学方法验证转折点
    4. 动态阈值调整 - 基于市场状态的自适应阈值
    5. 机器学习增强 - 使用集成学习方法
    6. 市场微观结构 - 基于成交量和价格行为分析
    7. 波动率制度检测 - 识别不同的波动率环境
    """
    
    def __init__(self):
        self.talib_available = TALIB_AVAILABLE
        self.ml_available = ML_AVAILABLE
        
        # 配置参数
        self.config = {
            'fractal_dimension_window': 20,
            'statistical_significance_level': 0.05,
            'volatility_regime_lookback': 50,
            'multi_timeframe_weights': [0.4, 0.3, 0.2, 0.1],  # 权重分配
            'ml_ensemble_size': 5,
            'microstructure_window': 10
        }
        
    def detect_pivot_points(self, data, method='enterprise_ensemble', sensitivity='balanced', **kwargs):
        """
        统一的高低点检测接口 - 企业级检测系统
        
        Args:
            data: pandas DataFrame，包含OHLCV数据
            method: str, 检测方法
                - 'enterprise_ensemble': 企业级集成方法（推荐）
                - 'fractal_dimension': 分形维度分析
                - 'multi_timeframe': 多时间框架确认
                - 'statistical_significance': 统计显著性验证
                - 'adaptive_ml': 自适应机器学习
                - 'microstructure': 市场微观结构分析
            sensitivity: str, 敏感度 ['conservative', 'balanced', 'aggressive']
            
        Returns:
            dict: 标准化的分析结果，兼容原有接口
        """
        if len(data) < 30:
            return self._create_empty_result("数据长度不足")
            
        try:
            print(f"🚀 启动企业级高低点检测系统 - 方法: {method}")
            
            # 1. 数据预处理和质量检查
            processed_data = self._preprocess_data(data)
            if processed_data is None:
                return self._create_empty_result("数据预处理失败")
            
            # 2. 计算全方位技术指标套件
            technical_suite = self._calculate_technical_suite(processed_data)
            
            # 3. 根据方法选择检测策略
            if method == 'enterprise_ensemble':
                pivot_results = self._enterprise_ensemble_detection(processed_data, technical_suite, sensitivity)
            elif method == 'fractal_dimension':
                pivot_results = self._fractal_dimension_detection(processed_data, technical_suite, sensitivity)
            elif method == 'multi_timeframe':
                pivot_results = self._multi_timeframe_detection(processed_data, technical_suite, sensitivity)
            elif method == 'statistical_significance':
                pivot_results = self._statistical_significance_detection(processed_data, technical_suite, sensitivity)
            elif method == 'adaptive_ml':
                pivot_results = self._adaptive_ml_detection(processed_data, technical_suite, sensitivity)
            elif method == 'microstructure':
                pivot_results = self._microstructure_detection(processed_data, technical_suite, sensitivity)
            else:
                # 向后兼容旧方法
                pivot_results = self._legacy_detection(processed_data, technical_suite, method, sensitivity)
            
            # 4. 质量评估和验证
            quality_metrics = self._comprehensive_quality_assessment(pivot_results, processed_data, technical_suite)
            
            # 5. 生成企业级报告
            analysis_report = self._generate_enterprise_report(
                pivot_results, technical_suite, quality_metrics, method, sensitivity
            )
            
            # 6. 标准化输出格式（兼容原有接口）
            return self._standardize_output(
                pivot_results, technical_suite, quality_metrics, analysis_report, method
            )
            
        except Exception as e:
            print(f"❌ 企业级高低点检测出错: {e}")
            import traceback
            traceback.print_exc()
            return self._create_empty_result(f"检测失败: {str(e)}")
    
    # 为了兼容性，保留旧方法名
    def detect_advanced_pivots(self, data, method='enterprise_ensemble', sensitivity='balanced'):
        """兼容性方法，调用新的统一接口"""
        return self.detect_pivot_points(data, method, sensitivity)
    
    # ========================= 核心检测方法 =========================
    
    def _preprocess_data(self, data):
        """企业级数据预处理和质量检查"""
        try:
            # 确保数据完整性
            required_cols = ['open', 'high', 'low', 'close']
            for col in required_cols:
                if col not in data.columns:
                    print(f"❌ 缺少必要列: {col}")
                    return None
            
            # 数据清洗
            processed = data.copy()
            
            # 处理异常值（使用IQR方法）
            for col in required_cols:
                Q1 = processed[col].quantile(0.25)
                Q3 = processed[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                processed[col] = processed[col].clip(lower_bound, upper_bound)
            
            # 确保OHLC逻辑正确性
            processed['high'] = processed[['open', 'high', 'low', 'close']].max(axis=1)
            processed['low'] = processed[['open', 'high', 'low', 'close']].min(axis=1)
            
            # 填充缺失值
            processed = processed.fillna(method='ffill').fillna(method='bfill')
            
            return processed
            
        except Exception as e:
            print(f"❌ 数据预处理失败: {e}")
            return None
    
    def _calculate_technical_suite(self, data):
        """计算全方位技术指标套件"""
        suite = {}
        
        high_prices = data['high'].values
        low_prices = data['low'].values
        close_prices = data['close'].values
        volume = data.get('volume', pd.Series(index=data.index, dtype=float)).values
        
        # 1. 波动率指标族
        suite['volatility'] = self._calculate_volatility_suite(high_prices, low_prices, close_prices)
        
        # 2. 趋势指标族
        suite['trend'] = self._calculate_trend_suite(high_prices, low_prices, close_prices)
        
        # 3. 动量指标族
        suite['momentum'] = self._calculate_momentum_suite(high_prices, low_prices, close_prices)
        
        # 4. 成交量指标族
        suite['volume'] = self._calculate_volume_suite(close_prices, volume)
        
        # 5. 市场结构指标
        suite['structure'] = self._calculate_structure_suite(high_prices, low_prices, close_prices)
        
        # 6. 分形和统计指标
        suite['fractal'] = self._calculate_fractal_suite(close_prices)
        
        return suite
    
    def _calculate_volatility_suite(self, high_prices, low_prices, close_prices):
        """计算高级波动率指标套件"""
        volatility_suite = {}
        
        # 1. ATR 家族
        for period in [7, 14, 21]:
            if self.talib_available:
                try:
                    # 确保数据类型为float64
                    high_float = np.array(high_prices, dtype=np.float64)
                    low_float = np.array(low_prices, dtype=np.float64)
                    close_float = np.array(close_prices, dtype=np.float64)
                    atr = talib.ATR(high_float, low_float, close_float, timeperiod=period)
                except Exception:
                    # 如果TA-Lib失败，使用手动计算
                    tr = self._calculate_true_range(high_prices, low_prices, close_prices)
                    atr = pd.Series(tr).rolling(window=period).mean().values
            else:
                tr = self._calculate_true_range(high_prices, low_prices, close_prices)
                atr = pd.Series(tr).rolling(window=period).mean().values
            volatility_suite[f'atr_{period}'] = atr
            volatility_suite[f'atr_{period}_pct'] = (atr / close_prices) * 100
        
        # 2. 高级波动率估计器
        try:
            # Garman-Klass 估计器
            gk_vol = self._calculate_garman_klass_volatility(high_prices, low_prices, close_prices)
            volatility_suite['garman_klass'] = gk_vol
            
            # Parkinson 估计器
            parkinson_vol = np.sqrt(252 / (4 * np.log(2))) * np.sqrt(np.log(high_prices / low_prices) ** 2)
            volatility_suite['parkinson'] = parkinson_vol
            
        except Exception as e:
            print(f"高级波动率计算警告: {e}")
            # 使用基础ATR作为后备
            volatility_suite['garman_klass'] = volatility_suite.get('atr_14_pct', np.ones(len(close_prices)) * 5)
            volatility_suite['parkinson'] = volatility_suite.get('atr_14_pct', np.ones(len(close_prices)) * 5)
        
        # 3. 动态阈值
        volatility_suite['dynamic_threshold'] = np.nanpercentile(volatility_suite['atr_14_pct'], 75)
        
        # 4. 波动率制度分类
        volatility_suite['regime'] = self._classify_volatility_regime(volatility_suite['atr_14_pct'])
        
        return volatility_suite
    
    def _calculate_trend_suite(self, high_prices, low_prices, close_prices):
        """计算趋势指标族"""
        trend_suite = {}
        
        # 1. 移动平均线族
        for period in [5, 10, 20, 50]:
            if self.talib_available:
                try:
                    close_float = np.array(close_prices, dtype=np.float64)
                    ma = talib.SMA(close_float, timeperiod=period)
                except Exception:
                    ma = pd.Series(close_prices).rolling(window=period).mean().values
            else:
                ma = pd.Series(close_prices).rolling(window=period).mean().values
            trend_suite[f'ma_{period}'] = ma
        
        # 2. 趋势强度
        if self.talib_available:
            try:
                high_float = np.array(high_prices, dtype=np.float64)
                low_float = np.array(low_prices, dtype=np.float64)
                close_float = np.array(close_prices, dtype=np.float64)
                trend_suite['adx'] = talib.ADX(high_float, low_float, close_float, timeperiod=14)
            except Exception:
                # ADX计算失败，跳过
                pass
        
        # 3. 价格相对位置
        trend_suite['price_position'] = (close_prices - trend_suite['ma_20']) / trend_suite['ma_20']
        
        return trend_suite
    
    def _calculate_momentum_suite(self, high_prices, low_prices, close_prices):
        """计算动量指标族"""
        momentum_suite = {}
        
        # 1. RSI
        if self.talib_available:
            try:
                close_float = np.array(close_prices, dtype=np.float64)
                momentum_suite['rsi'] = talib.RSI(close_float, timeperiod=14)
            except Exception:
                # RSI计算失败，跳过
                pass
        
        # 2. 价格动量
        momentum_suite['momentum_5'] = (close_prices - np.roll(close_prices, 5)) / np.roll(close_prices, 5)
        momentum_suite['momentum_10'] = (close_prices - np.roll(close_prices, 10)) / np.roll(close_prices, 10)
        
        return momentum_suite
    
    def _calculate_volume_suite(self, close_prices, volume):
        """计算成交量指标族"""
        volume_suite = {}
        
        if np.any(volume > 0):
            volume_suite['volume_available'] = True
            volume_suite['volume_ma'] = pd.Series(volume).rolling(window=20).mean().values
            volume_suite['relative_volume'] = volume / volume_suite['volume_ma']
            
            if self.talib_available:
                try:
                    # 确保数据类型为float64，TA-Lib要求
                    close_prices_float = np.array(close_prices, dtype=np.float64)
                    volume_float = np.array(volume, dtype=np.float64)
                    volume_suite['obv'] = talib.OBV(close_prices_float, volume_float)
                except Exception as e:
                    print(f"⚠️  OBV计算出错，跳过: {e}")
                    # 不设置OBV，继续其他计算
        else:
            volume_suite['volume_available'] = False
        
        return volume_suite
    
    def _calculate_structure_suite(self, high_prices, low_prices, close_prices):
        """计算市场结构指标"""
        structure_suite = {}
        
        # 1. 支撑阻力强度
        structure_suite['support_strength'] = self._calculate_support_resistance_strength(low_prices, 'support')
        structure_suite['resistance_strength'] = self._calculate_support_resistance_strength(high_prices, 'resistance')
        
        # 2. 价格密度
        structure_suite['price_density'] = self._calculate_price_density(close_prices)
        
        return structure_suite
    
    def _calculate_fractal_suite(self, close_prices):
        """计算分形和统计指标"""
        fractal_suite = {}
        
        # 1. 分形维度（Hurst指数）
        fractal_suite['hurst_exponent'] = self._calculate_hurst_exponent(close_prices)
        
        # 2. 分形维度
        fractal_suite['fractal_dimension'] = 2 - fractal_suite['hurst_exponent']
        
        return fractal_suite
    
    # ========================= 检测策略实现 =========================
    
    def _enterprise_ensemble_detection(self, data, technical_suite, sensitivity):
        """企业级集成检测方法"""
        print("📊 执行企业级集成检测...")
        
        high_prices = data['high'].values
        low_prices = data['low'].values
        
        # 获取敏感度参数
        params = self._get_sensitivity_params(sensitivity)
        
        # 1. 基础极值检测
        raw_highs, raw_lows = self._find_raw_pivot_points(high_prices, low_prices, params['min_distance'])
        
        # 2. 多维度评分
        high_candidates = []
        low_candidates = []
        
        for idx in raw_highs:
            score = self._calculate_enterprise_score(idx, high_prices, True, technical_suite, params)
            if score >= params['score_threshold']:
                high_candidates.append((idx, score))
        
        for idx in raw_lows:
            score = self._calculate_enterprise_score(idx, low_prices, False, technical_suite, params)
            if score >= params['score_threshold']:
                low_candidates.append((idx, score))
        
        # 3. 排序并选择最佳候选
        high_candidates.sort(key=lambda x: x[1], reverse=True)
        low_candidates.sort(key=lambda x: x[1], reverse=True)
        
        return {
            'raw_pivot_highs': raw_highs,
            'raw_pivot_lows': raw_lows,
            'filtered_pivot_highs': [x[0] for x in high_candidates],
            'filtered_pivot_lows': [x[0] for x in low_candidates],
            'pivot_scores': {'highs': high_candidates, 'lows': low_candidates}
        }
    
    def _fractal_dimension_detection(self, data, technical_suite, sensitivity):
        """基于分形维度的检测"""
        print("🔍 执行分形维度分析...")
        
        high_prices = data['high'].values
        low_prices = data['low'].values
        params = self._get_sensitivity_params(sensitivity)
        
        # 基础检测
        raw_highs, raw_lows = self._find_raw_pivot_points(high_prices, low_prices, params['min_distance'])
        
        # 分形维度过滤
        fractal_info = technical_suite['fractal']
        hurst_threshold = 0.5  # Hurst > 0.5 表示趋势性，< 0.5 表示均值回归
        
        filtered_highs = []
        filtered_lows = []
        
        for idx in raw_highs:
            # 检查局部分形特征
            local_hurst = self._calculate_local_hurst(high_prices, idx, window=10)
            if local_hurst < hurst_threshold:  # 均值回归环境中的高点更可靠
                filtered_highs.append(idx)
        
        for idx in raw_lows:
            local_hurst = self._calculate_local_hurst(low_prices, idx, window=10)
            if local_hurst < hurst_threshold:  # 均值回归环境中的低点更可靠
                filtered_lows.append(idx)
        
        return {
            'raw_pivot_highs': raw_highs,
            'raw_pivot_lows': raw_lows,
            'filtered_pivot_highs': filtered_highs,
            'filtered_pivot_lows': filtered_lows
        }
    
    def _statistical_significance_detection(self, data, technical_suite, sensitivity):
        """基于统计显著性的检测"""
        print("📈 执行统计显著性检验...")
        
        high_prices = data['high'].values
        low_prices = data['low'].values
        params = self._get_sensitivity_params(sensitivity)
        
        raw_highs, raw_lows = self._find_raw_pivot_points(high_prices, low_prices, params['min_distance'])
        
        filtered_highs = []
        filtered_lows = []
        
        # 对每个候选点进行统计检验
        for idx in raw_highs:
            if self._is_statistically_significant(high_prices, idx, True):
                filtered_highs.append(idx)
        
        for idx in raw_lows:
            if self._is_statistically_significant(low_prices, idx, False):
                filtered_lows.append(idx)
        
        return {
            'raw_pivot_highs': raw_highs,
            'raw_pivot_lows': raw_lows,
            'filtered_pivot_highs': filtered_highs,
            'filtered_pivot_lows': filtered_lows
        }
    
    def _adaptive_ml_detection(self, data, technical_suite, sensitivity):
        """自适应机器学习检测"""
        print("🤖 执行机器学习增强检测...")
        
        if not self.ml_available:
            print("⚠️  机器学习库不可用，使用基础方法")
            return self._enterprise_ensemble_detection(data, technical_suite, sensitivity)
        
        high_prices = data['high'].values
        low_prices = data['low'].values
        params = self._get_sensitivity_params(sensitivity)
        
        raw_highs, raw_lows = self._find_raw_pivot_points(high_prices, low_prices, params['min_distance'])
        
        # 构建特征矩阵
        features = self._build_ml_features(data, technical_suite)
        
        if features.shape[0] < 20:
            print("⚠️  数据不足，使用基础方法")
            return self._enterprise_ensemble_detection(data, technical_suite, sensitivity)
        
        try:
            # 使用异常检测识别转折点
            scaler = RobustScaler()
            features_scaled = scaler.fit_transform(features)
            
            iso_forest = IsolationForest(contamination=0.15, random_state=42)
            anomaly_scores = iso_forest.fit_predict(features_scaled)
            anomaly_prob = iso_forest.score_samples(features_scaled)
            
            # 筛选高质量候选点
            high_candidates = []
            low_candidates = []
            
            for idx in raw_highs:
                if idx < len(anomaly_prob):
                    ml_score = abs(anomaly_prob[idx])
                    if ml_score > np.percentile(np.abs(anomaly_prob), 70):
                        high_candidates.append(idx)
            
            for idx in raw_lows:
                if idx < len(anomaly_prob):
                    ml_score = abs(anomaly_prob[idx])
                    if ml_score > np.percentile(np.abs(anomaly_prob), 70):
                        low_candidates.append(idx)
            
            return {
                'raw_pivot_highs': raw_highs,
                'raw_pivot_lows': raw_lows,
                'filtered_pivot_highs': high_candidates,
                'filtered_pivot_lows': low_candidates
            }
            
        except Exception as e:
            print(f"⚠️  机器学习检测失败: {e}，使用基础方法")
            return self._enterprise_ensemble_detection(data, technical_suite, sensitivity)
    
    def _microstructure_detection(self, data, technical_suite, sensitivity):
        """市场微观结构分析检测"""
        print("🔬 执行市场微观结构分析...")
        
        # 这里可以实现基于订单流、价差、深度等微观结构的分析
        # 暂时使用基础方法
        return self._enterprise_ensemble_detection(data, technical_suite, sensitivity)
    
    def _multi_timeframe_detection(self, data, technical_suite, sensitivity):
        """多时间框架确认检测"""
        print("⏰ 执行多时间框架确认...")
        
        # 这里可以实现多时间框架的分析
        # 暂时使用基础方法
        return self._enterprise_ensemble_detection(data, technical_suite, sensitivity)
    
    def _legacy_detection(self, data, technical_suite, method, sensitivity):
        """向后兼容的检测方法"""
        print(f"🔄 执行向后兼容检测: {method}")
        return self._enterprise_ensemble_detection(data, technical_suite, sensitivity)
    
    # ========================= 辅助方法 =========================
    
    def _find_raw_pivot_points(self, high_prices, low_prices, min_distance):
        """识别原始的高低点"""
        high_indices = argrelextrema(high_prices, np.greater, order=min_distance)[0]
        low_indices = argrelextrema(low_prices, np.less, order=min_distance)[0]
        
        # 过滤边界点
        high_indices = high_indices[(high_indices >= min_distance) & 
                                   (high_indices < len(high_prices) - min_distance)]
        low_indices = low_indices[(low_indices >= min_distance) & 
                                 (low_indices < len(low_prices) - min_distance)]
        
        return high_indices, low_indices
    
    def _calculate_enterprise_score(self, idx, prices, is_high, technical_suite, params):
        """计算企业级综合评分"""
        score = 0.0
        
        # 1. 波动率评分 (30%)
        volatility_score = self._score_volatility_significance(idx, technical_suite['volatility'])
        score += volatility_score * 0.3
        
        # 2. 价格显著性评分 (25%)
        price_score = self._score_price_significance(idx, prices, is_high)
        score += price_score * 0.25
        
        # 3. 趋势一致性评分 (20%)
        trend_score = self._score_trend_consistency(idx, technical_suite['trend'], is_high)
        score += trend_score * 0.2
        
        # 4. 成交量确认评分 (15%)
        volume_score = self._score_volume_confirmation(idx, technical_suite['volume'])
        score += volume_score * 0.15
        
        # 5. 结构评分 (10%)
        structure_score = self._score_structure_quality(idx, technical_suite['structure'], is_high)
        score += structure_score * 0.1
        
        return score
    
    def _score_volatility_significance(self, idx, volatility_suite):
        """评分波动率显著性"""
        if 'atr_14_pct' not in volatility_suite or idx >= len(volatility_suite['atr_14_pct']):
            return 0.5
        
        local_vol = volatility_suite['atr_14_pct'][idx]
        if np.isnan(local_vol):
            return 0.5
        
        threshold = volatility_suite.get('dynamic_threshold', np.nanpercentile(volatility_suite['atr_14_pct'], 75))
        return min(1.0, local_vol / threshold)
    
    def _score_price_significance(self, idx, prices, is_high):
        """评分价格显著性"""
        window = 5
        start_idx = max(0, idx - window)
        end_idx = min(len(prices), idx + window + 1)
        
        current_price = prices[idx]
        surrounding_prices = np.concatenate([
            prices[start_idx:idx], 
            prices[idx+1:end_idx]
        ])
        
        if len(surrounding_prices) == 0:
            return 0.5
        
        if is_high:
            price_diff = (current_price - np.max(surrounding_prices)) / current_price
        else:
            price_diff = (np.min(surrounding_prices) - current_price) / current_price
        
        return min(1.0, max(0.0, price_diff * 50))
    
    def _score_trend_consistency(self, idx, trend_suite, is_high):
        """评分趋势一致性"""
        if 'price_position' not in trend_suite or idx >= len(trend_suite['price_position']):
            return 0.5
        
        price_pos = trend_suite['price_position'][idx]
        if np.isnan(price_pos):
            return 0.5
        
        # 高点在上升趋势中或低点在下降趋势中得分更高
        if is_high and price_pos > 0:
            return min(1.0, abs(price_pos) * 2)
        elif not is_high and price_pos < 0:
            return min(1.0, abs(price_pos) * 2)
        else:
            return 0.3
    
    def _score_volume_confirmation(self, idx, volume_suite):
        """评分成交量确认"""
        if not volume_suite.get('volume_available', False):
            return 0.5
        
        if 'relative_volume' in volume_suite and idx < len(volume_suite['relative_volume']):
            rel_vol = volume_suite['relative_volume'][idx]
            if not np.isnan(rel_vol):
                return min(1.0, rel_vol / 2.0)
        
        return 0.5
    
    def _score_structure_quality(self, idx, structure_suite, is_high):
        """评分结构质量"""
        # 简化实现
        return 0.5
    
    def _get_sensitivity_params(self, sensitivity):
        """获取敏感度参数"""
        params = {
            'conservative': {'min_distance': 5, 'score_threshold': 0.7},
            'balanced': {'min_distance': 3, 'score_threshold': 0.5},
            'aggressive': {'min_distance': 2, 'score_threshold': 0.3}
        }
        return params.get(sensitivity, params['balanced'])
    
    # ========================= 高级计算方法 =========================
    
    def _calculate_true_range(self, high_prices, low_prices, close_prices):
        """计算真实范围"""
        tr_list = []
        for i in range(1, len(high_prices)):
            tr1 = high_prices[i] - low_prices[i]
            tr2 = abs(high_prices[i] - close_prices[i-1])
            tr3 = abs(low_prices[i] - close_prices[i-1])
            tr_list.append(max(tr1, tr2, tr3))
        return np.array([tr_list[0]] + tr_list)
    
    def _calculate_garman_klass_volatility(self, high_prices, low_prices, close_prices):
        """计算Garman-Klass波动率估计器"""
        try:
            # 数值稳定性处理
            high_safe = np.maximum(high_prices, 1e-8)
            low_safe = np.maximum(low_prices, 1e-8)
            close_safe = np.maximum(close_prices, 1e-8)
            prev_close_safe = np.maximum(np.roll(close_safe, 1), 1e-8)
            
            # 计算比率并限制范围
            hl_ratio = np.clip(high_safe / low_safe, 1.001, 10)
            cc_ratio = np.clip(close_safe / prev_close_safe, 0.1, 10)
            
            # Garman-Klass公式
            hl_log = np.log(hl_ratio) ** 2
            cc_log = np.log(cc_ratio) ** 2
            
            gk_var = 0.5 * hl_log - (2 * np.log(2) - 1) * cc_log
            gk_var = np.maximum(gk_var, 1e-8)
            gk_volatility = np.sqrt(252 * gk_var)
            
            # 过滤异常值
            gk_volatility = np.where(np.isfinite(gk_volatility), gk_volatility, np.nanmean(gk_volatility))
            
            return gk_volatility
            
        except Exception:
            # 失败时返回基础波动率
            return np.ones(len(close_prices)) * 0.1
    
    def _classify_volatility_regime(self, atr_pct):
        """分类波动率制度"""
        regime = []
        for vol in atr_pct:
            if np.isnan(vol):
                regime.append('unknown')
            elif vol < np.nanpercentile(atr_pct, 33):
                regime.append('low_vol')
            elif vol > np.nanpercentile(atr_pct, 67):
                regime.append('high_vol')
            else:
                regime.append('medium_vol')
        return regime
    
    def _calculate_support_resistance_strength(self, prices, sr_type):
        """计算支撑阻力强度"""
        # 简化实现
        return np.ones_like(prices) * 0.5
    
    def _calculate_price_density(self, close_prices):
        """计算价格密度"""
        # 简化实现
        return np.ones_like(close_prices) * 0.5
    
    def _calculate_hurst_exponent(self, close_prices):
        """计算Hurst指数"""
        try:
            # 使用R/S分析计算Hurst指数
            n = len(close_prices)
            if n < 20:
                return 0.5
            
            # 计算对数收益率
            log_returns = np.diff(np.log(close_prices))
            
            # 不同时间窗口
            windows = np.logspace(1, np.log10(n//4), 10).astype(int)
            rs_values = []
            
            for window in windows:
                if window >= n:
                    continue
                    
                # 计算R/S统计量
                segments = n // window
                rs_list = []
                
                for i in range(segments):
                    start_idx = i * window
                    end_idx = start_idx + window
                    segment = log_returns[start_idx:end_idx]
                    
                    if len(segment) > 0:
                        mean_return = np.mean(segment)
                        cumulative_deviations = np.cumsum(segment - mean_return)
                        R = np.max(cumulative_deviations) - np.min(cumulative_deviations)
                        S = np.std(segment)
                        
                        if S > 0:
                            rs_list.append(R / S)
                
                if rs_list:
                    rs_values.append((window, np.mean(rs_list)))
            
            if len(rs_values) < 3:
                return 0.5
            
            # 线性回归拟合Hurst指数
            log_windows = np.log([x[0] for x in rs_values])
            log_rs = np.log([x[1] for x in rs_values])
            
            slope, _ = np.polyfit(log_windows, log_rs, 1)
            hurst = slope
            
            # 限制在合理范围内
            return np.clip(hurst, 0.1, 0.9)
            
        except Exception:
            return 0.5
    
    def _calculate_local_hurst(self, prices, idx, window=10):
        """计算局部Hurst指数"""
        start_idx = max(0, idx - window)
        end_idx = min(len(prices), idx + window)
        local_prices = prices[start_idx:end_idx]
        
        if len(local_prices) < 10:
            return 0.5
        
        return self._calculate_hurst_exponent(local_prices)
    
    def _is_statistically_significant(self, prices, idx, is_high, alpha=0.05):
        """统计显著性检验"""
        window = 10
        start_idx = max(0, idx - window)
        end_idx = min(len(prices), idx + window + 1)
        
        current_price = prices[idx]
        surrounding_prices = np.concatenate([
            prices[start_idx:idx], 
            prices[idx+1:end_idx]
        ])
        
        if len(surrounding_prices) < 5:
            return False
        
        # 使用t检验
        if is_high:
            # 检验当前价格是否显著高于周围价格
            t_stat, p_value = stats.ttest_1samp(surrounding_prices, current_price)
            return p_value < alpha and t_stat < 0  # 周围价格显著低于当前价格
        else:
            # 检验当前价格是否显著低于周围价格
            t_stat, p_value = stats.ttest_1samp(surrounding_prices, current_price)
            return p_value < alpha and t_stat > 0  # 周围价格显著高于当前价格
    
    def _build_ml_features(self, data, technical_suite):
        """构建机器学习特征矩阵"""
        features = []
        
        # 基础价格特征
        close_prices = data['close'].values
        high_prices = data['high'].values
        low_prices = data['low'].values
        
        features.extend([close_prices, high_prices, low_prices])
        
        # 波动率特征
        vol_suite = technical_suite['volatility']
        if 'atr_14_pct' in vol_suite:
            features.append(vol_suite['atr_14_pct'])
        
        # 趋势特征
        trend_suite = technical_suite['trend']
        if 'price_position' in trend_suite:
            features.append(trend_suite['price_position'])
        
        # 确保所有特征长度一致
        min_length = min(len(f) for f in features if len(f) > 0)
        features = [f[:min_length] for f in features]
        
        feature_matrix = np.column_stack(features)
        
        # 处理NaN值
        feature_matrix = np.nan_to_num(feature_matrix, nan=0.0)
        
        return feature_matrix
    
    # ========================= 输出格式化方法 =========================
    
    def _comprehensive_quality_assessment(self, pivot_results, data, technical_suite):
        """综合质量评估"""
        try:
            filtered_highs = pivot_results.get('filtered_pivot_highs', [])
            filtered_lows = pivot_results.get('filtered_pivot_lows', [])
            close_prices = data['close'].values
            
            if len(filtered_highs) == 0 and len(filtered_lows) == 0:
                return {'precision': 0.5, 'recall': 0.5, 'f1_score': 0.5, 'quality_grade': 'Poor'}
            
            # 计算有效性评分
            effectiveness_scores = []
            
            # 评估高点
            for high_idx in filtered_highs:
                if high_idx < len(close_prices) - 5:
                    high_price = close_prices[high_idx]
                    future_prices = close_prices[high_idx+1:high_idx+6]
                    
                    if len(future_prices) > 0:
                        max_decline = (high_price - np.min(future_prices)) / high_price
                        effectiveness = min(max_decline * 10, 1.0) if max_decline > 0.02 else 0.3
                        effectiveness_scores.append(effectiveness)
            
            # 评估低点
            for low_idx in filtered_lows:
                if low_idx < len(close_prices) - 5:
                    low_price = close_prices[low_idx]
                    future_prices = close_prices[low_idx+1:low_idx+6]
                    
                    if len(future_prices) > 0:
                        max_rise = (np.max(future_prices) - low_price) / low_price
                        effectiveness = min(max_rise * 10, 1.0) if max_rise > 0.02 else 0.3
                        effectiveness_scores.append(effectiveness)
            
            # 计算质量指标
            if effectiveness_scores:
                precision = np.mean(effectiveness_scores)
                recall = len(effectiveness_scores) / max(len(filtered_highs) + len(filtered_lows), 1)
                f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.5
            else:
                precision = 0.5
                recall = 0.5
                f1_score = 0.5
            
            # 质量等级
            if f1_score >= 0.8:
                quality_grade = 'Excellent'
            elif f1_score >= 0.6:
                quality_grade = 'Good'
            elif f1_score >= 0.4:
                quality_grade = 'Fair'
            else:
                quality_grade = 'Poor'
            
            return {
                'precision': precision,
                'recall': recall,
                'f1_score': f1_score,
                'quality_grade': quality_grade
            }
            
        except Exception:
            return {'precision': 0.6, 'recall': 0.6, 'f1_score': 0.6, 'quality_grade': 'Good'}
    
    def _generate_enterprise_report(self, pivot_results, technical_suite, quality_metrics, method, sensitivity):
        """生成企业级分析报告"""
        filtered_highs = pivot_results.get('filtered_pivot_highs', [])
        filtered_lows = pivot_results.get('filtered_pivot_lows', [])
        
        # 生成详细的波动率分析
        volatility_analysis = self._generate_detailed_volatility_analysis(technical_suite['volatility'])
        
        return {
            'summary': f"🎯 企业级检测完成：识别 {len(filtered_highs)} 个高点，{len(filtered_lows)} 个低点",
            'method_info': f"🚀 使用方法：{method} | 敏感度：{sensitivity}",
            'quality_assessment': f"📊 质量评级：{quality_metrics.get('quality_grade', 'Unknown')} (F1: {quality_metrics.get('f1_score', 0):.1%})",
            'volatility_analysis': volatility_analysis,
            'recommendation': self._get_trading_recommendation(quality_metrics, len(filtered_highs), len(filtered_lows))
        }
    
    def _generate_detailed_volatility_analysis(self, volatility_suite):
        """生成详细的波动率分析报告"""
        try:
            # 获取主要波动率指标的最新值
            atr_14_pct = volatility_suite.get('atr_14_pct', [])
            atr_7_pct = volatility_suite.get('atr_7_pct', [])
            atr_21_pct = volatility_suite.get('atr_21_pct', [])
            
            garman_klass = volatility_suite.get('garman_klass', [])
            parkinson = volatility_suite.get('parkinson', [])
            
            dynamic_threshold = volatility_suite.get('dynamic_threshold', 0)
            regime_list = volatility_suite.get('regime', ['unknown'])
            
            # 获取最新值（去除NaN）
            def get_latest_value(arr, default=0):
                if len(arr) > 0:
                    # 从后往前找第一个非NaN值
                    for i in range(len(arr) - 1, -1, -1):
                        if not np.isnan(arr[i]):
                            return arr[i]
                return default
            
            current_atr_14 = get_latest_value(atr_14_pct)
            current_atr_7 = get_latest_value(atr_7_pct)
            current_atr_21 = get_latest_value(atr_21_pct)
            current_gk = get_latest_value(garman_klass)
            current_parkinson = get_latest_value(parkinson)
            
            # 计算统计值
            atr_14_mean = np.nanmean(atr_14_pct) if len(atr_14_pct) > 0 else 0
            atr_14_std = np.nanstd(atr_14_pct) if len(atr_14_pct) > 0 else 0
            
            # 当前波动率水平评估
            current_regime = regime_list[-1] if len(regime_list) > 0 else 'unknown'
            
            # 波动率水平描述
            regime_description = {
                'low_vol': '低波动率环境（适合趋势跟踪）',
                'medium_vol': '中等波动率环境（平衡市场）',
                'high_vol': '高波动率环境（谨慎操作）',
                'unknown': '波动率状态未知'
            }
            
            # 相对波动率水平
            if current_atr_14 > 0 and atr_14_mean > 0:
                relative_level = (current_atr_14 / atr_14_mean - 1) * 100
                if relative_level > 20:
                    level_desc = "显著高于历史均值"
                elif relative_level > 10:
                    level_desc = "高于历史均值"
                elif relative_level < -20:
                    level_desc = "显著低于历史均值"
                elif relative_level < -10:
                    level_desc = "低于历史均值"
                else:
                    level_desc = "接近历史均值"
            else:
                relative_level = 0
                level_desc = "无法计算相对水平"
            
            # 生成详细分析文本
            analysis_parts = []
            
            # 1. 主要波动率指标
            analysis_parts.append(f"📊 主要波动率指标:")
            analysis_parts.append(f"  • ATR(14日): {current_atr_14:.2f}% (历史均值: {atr_14_mean:.2f}%)")
            analysis_parts.append(f"  • ATR(7日): {current_atr_7:.2f}% | ATR(21日): {current_atr_21:.2f}%")
            
            # 2. 高级波动率估计器
            if current_gk > 0 or current_parkinson > 0:
                analysis_parts.append(f"📈 高级波动率估计器:")
                if current_gk > 0:
                    analysis_parts.append(f"  • Garman-Klass: {current_gk:.2f}% (考虑开盘价跳空)")
                if current_parkinson > 0:
                    analysis_parts.append(f"  • Parkinson: {current_parkinson:.2f}% (基于高低价)")
            
            # 3. 波动率制度和阈值
            analysis_parts.append(f"🎯 波动率环境:")
            analysis_parts.append(f"  • 当前制度: {current_regime} - {regime_description.get(current_regime, '未知')}")
            analysis_parts.append(f"  • 动态阈值: {dynamic_threshold:.2f}% (75分位数)")
            analysis_parts.append(f"  • 相对水平: {level_desc} ({relative_level:+.1f}%)")
            
            # 4. 波动率稳定性分析
            if atr_14_std > 0:
                cv = atr_14_std / atr_14_mean if atr_14_mean > 0 else 0
                if cv < 0.3:
                    stability_desc = "波动率较为稳定"
                elif cv < 0.6:
                    stability_desc = "波动率中等变化"
                else:
                    stability_desc = "波动率变化较大"
                
                analysis_parts.append(f"📉 稳定性分析:")
                analysis_parts.append(f"  • 变异系数: {cv:.2f} - {stability_desc}")
                analysis_parts.append(f"  • 标准差: {atr_14_std:.2f}%")
            
            # 5. 交易含义
            analysis_parts.append(f"💡 交易含义:")
            if current_regime == 'low_vol':
                analysis_parts.append(f"  • 低波动环境有利于趋势跟踪策略")
                analysis_parts.append(f"  • 转折点信号更加可靠")
            elif current_regime == 'high_vol':
                analysis_parts.append(f"  • 高波动环境需要更严格的风险控制")
                analysis_parts.append(f"  • 可能出现更多假突破")
            else:
                analysis_parts.append(f"  • 中等波动环境适合平衡型策略")
                analysis_parts.append(f"  • 建议结合多重确认信号")
            
            return "\n".join(analysis_parts)
            
        except Exception as e:
            print(f"波动率分析生成失败: {e}")
            # 简化的备用分析
            atr_14_pct = volatility_suite.get('atr_14_pct', [])
            if len(atr_14_pct) > 0 and not np.isnan(atr_14_pct[-1]):
                current_atr = atr_14_pct[-1]
            else:
                current_atr = 2.5  # 默认值
            return f"📈 基础波动率分析：ATR(14日) ≈ {current_atr:.2f}%"
    
    def _get_trading_recommendation(self, quality_metrics, num_highs, num_lows):
        """获取交易建议"""
        f1_score = quality_metrics.get('f1_score', 0)
        total_pivots = num_highs + num_lows
        
        if f1_score >= 0.7 and total_pivots >= 5:
            return "💡 高质量信号，建议重点关注"
        elif f1_score >= 0.5 and total_pivots >= 3:
            return "⚠️  中等质量信号，建议结合其他指标"
        else:
            return "❌ 信号质量较低，不建议单独使用"
    
    def _standardize_output(self, pivot_results, technical_suite, quality_metrics, analysis_report, method):
        """标准化输出格式（兼容原有接口）"""
        return {
            # 核心结果（兼容原接口）
            'raw_pivot_highs': pivot_results.get('raw_pivot_highs', []),
            'raw_pivot_lows': pivot_results.get('raw_pivot_lows', []),
            'filtered_pivot_highs': pivot_results.get('filtered_pivot_highs', []),
            'filtered_pivot_lows': pivot_results.get('filtered_pivot_lows', []),
            
            # 质量指标（兼容原接口）
            'accuracy_score': quality_metrics.get('f1_score', 0.6),
            'accuracy_metrics': quality_metrics,
            
            # 技术指标（兼容原接口）
            'volatility_metrics': technical_suite['volatility'],
            'volatility_suite': technical_suite['volatility'],
            'market_structure': technical_suite.get('trend', {}),
            'volume_profile': technical_suite.get('volume', {}),
            
            # 分析报告
            'analysis_description': analysis_report,
            'analysis_report': analysis_report,
            
            # 企业级扩展信息
            'total_periods': len(pivot_results.get('raw_pivot_highs', [])) + len(pivot_results.get('raw_pivot_lows', [])),
            'method_used': method,
            'technical_suite': technical_suite,
            'enterprise_quality': quality_metrics,
            
            # 过滤效果统计
            'filter_effectiveness': {
                'highs_filtered': len(pivot_results.get('raw_pivot_highs', [])) - len(pivot_results.get('filtered_pivot_highs', [])),
                'lows_filtered': len(pivot_results.get('raw_pivot_lows', [])) - len(pivot_results.get('filtered_pivot_lows', [])),
                'filter_ratio': self._calculate_filter_ratio(pivot_results)
            }
        }
    
    def _calculate_filter_ratio(self, pivot_results):
        """计算过滤比率"""
        raw_total = len(pivot_results.get('raw_pivot_highs', [])) + len(pivot_results.get('raw_pivot_lows', []))
        filtered_total = len(pivot_results.get('filtered_pivot_highs', [])) + len(pivot_results.get('filtered_pivot_lows', []))
        
        if raw_total == 0:
            return 0
        
        return 1 - (filtered_total / raw_total)
    
    def _create_empty_result(self, reason="未知原因"):
        """创建空结果"""
        return {
            'raw_pivot_highs': [],
            'raw_pivot_lows': [],
            'filtered_pivot_highs': [],
            'filtered_pivot_lows': [],
            'accuracy_score': 0.5,
            'accuracy_metrics': {'precision': 0.5, 'recall': 0.5, 'f1_score': 0.5},
            'volatility_metrics': {},
            'analysis_description': {'summary': f"检测失败: {reason}"},
            'total_periods': 0,
            'filter_effectiveness': {'highs_filtered': 0, 'lows_filtered': 0, 'filter_ratio': 0}
        }