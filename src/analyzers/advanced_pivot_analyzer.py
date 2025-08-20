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
    企业级高低点分析器

    用途:
    - 提供统一的高低点识别接口，当前仅保留 zigzag_atr 信号方法，产出交易员可用的入场/出场级别的转折点。

    实现方式:
    - 预处理: 数据清洗/IQR 去噪、OHLC 合规校正、缺失填补
    - 技术套件: 计算波动率/趋势/动量/成交量/分形等指标，供检测与质量评估复用
    - 识别: 使用 ZigZag + ATR 自适应阈值，时间顺序构建交替高低点，支持“同向更极端替换”和最小K线间隔约束
    - 评估: 统一生成质量指标/分析报告/过滤统计，并标准化输出结构；HTML 可读取 pivot_meta 解释每个点入选原因

    优点:
    - 低延迟、可解释（prominence、阈值、ATR%、swing_pct），贴近实际交易使用
    - 阈值随 ATR 自适应，不同波动环境下具有稳健性
    - 输出格式向后兼容，易于与图表/HTML 复用

    局限:
    - 仍属启发式方法，对噪声/跳空和极端行情需要谨慎；敏感度参数需结合标的微调
    - 未引入监督学习标签校准；不同市场/周期应单独回测

    维护建议:
    - 仅在 _get_sensitivity_params 中调整风格参数，保持接口稳定
    - 如需扩展指标/元信息，优先在 pivot_meta 中追加键，避免破坏下游
    - 对外暴露 detect_pivot_points 的返回键名请保持不变

    关键接口:
    - detect_pivot_points(data, method='zigzag_atr', sensitivity) -> dict
    - 重要返回键: raw_pivot_highs/lows, filtered_pivot_highs/lows, pivot_meta, accuracy_score, volatility_metrics

    依赖:
    - 可选 TA-Lib/Sklearn；缺失时自动降级
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
        
    def detect_pivot_points(self, data, method='zigzag_atr', sensitivity='balanced', frequency: str = 'weekly', **kwargs):
        """
        统一的高低点检测接口 - 企业级检测系统
        
        Args:
            data: pandas DataFrame，包含OHLCV数据
            method: str, 检测方法（仅支持 'zigzag_atr'）
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
            
            # 3. 统一使用 ZigZag+ATR 方法（其余方法已移除）
            if method != 'zigzag_atr':
                print(f"提示: 方法 {method} 已废弃，已自动切换为 zigzag_atr")
            pivot_results = self._zigzag_atr_detection(processed_data, technical_suite, sensitivity, frequency)
            
            # 4. 质量评估和验证
            quality_metrics = self._comprehensive_quality_assessment(pivot_results, processed_data, technical_suite)
            
            # 5. 生成企业级报告
            analysis_report = self._generate_enterprise_report(
                pivot_results, technical_suite, quality_metrics, method, sensitivity
            )
            
            # 6. 计算“优质”评估（基于最低枢轴低点以来的年化波动率与夏普）
            premium_metrics = self._compute_premium_metrics(data, pivot_results, frequency=frequency)

            # 7. 标准化输出格式（兼容原有接口）
            return self._standardize_output(
                pivot_results, technical_suite, quality_metrics, analysis_report, method, premium_metrics
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
    
    # 已移除其他方法实现，统一使用 _zigzag_atr_detection
    
    # 已移除其他方法实现，统一使用 _zigzag_atr_detection
    
    def _statistical_significance_detection(self, data, technical_suite, sensitivity, frequency: str = 'weekly'):
        """基于统计显著性的检测（增强版）
        目标：更贴近交易员的“显著高低点”认知，突出：
        - 突出度（prominence）足够高（ATR/波动率自适应）
        - 与两侧窗口相比显著（t-test/均值差异）
        - 有最小振幅（百分比/ATR）
        - 有后验确认（价格在数根K线内向反方向运行足够幅度）
        - 枢轴之间保持时间分离，避免簇拥
        """
        print("📈 执行统计显著性检验（增强版）...")

        close_prices = data['close'].values
        high_prices = data['high'].values
        low_prices = data['low'].values
        params = self._get_sensitivity_params(sensitivity, frequency)
        
        # 计算ATR价格尺度（用于 prominence & 确认）
        atr_price = self._compute_atr_price_scale(close_prices, technical_suite.get('volatility', {}))
        # 全局最小 prominence（价格单位）
        min_prom_price = np.nanmedian(atr_price) * params.get('min_prominence_atr', 1.0)
        min_swing_pct = params.get('min_swing_pct', 0.02)  # 2%

        # 1) 通过 prominence 初筛候选
        raw_highs, high_prom_map = self._find_peaks_with_prominence(
            high_prices, distance=params['min_distance'], min_prominence=min_prom_price
        )
        raw_lows, low_prom_map_neg = self._find_peaks_with_prominence(
            -low_prices, distance=params['min_distance'], min_prominence=min_prom_price
        )
        # 低点的 prominence 以价格正数表达
        low_prom_map = {k: float(v) for k, v in low_prom_map_neg.items()}
        # 将低点索引还原
        raw_lows = raw_lows

        # 2) 严格的统计显著性检验（双侧窗口）+ 最小振幅（百分比）
        filtered_highs = []
        filtered_lows = []
        left_win = right_win = max(5, params['min_distance'])

        pivot_meta_highs = {}
        pivot_meta_lows = {}
        
        for idx in raw_highs:
            passed, z_l, z_r = self._is_statistically_significant_bilateral(high_prices, idx, is_high=True,
                                                                            left=left_win, right=right_win)
            if passed:
                # 最小振幅：相对两侧均值增幅
                left_mean = np.mean(high_prices[max(0, idx - left_win):idx]) if idx > 0 else high_prices[idx]
                right_mean = np.mean(high_prices[idx+1:idx+1+right_win]) if idx < len(high_prices)-1 else high_prices[idx]
                ref_mean = max(left_mean, right_mean)
                swing_ok = ref_mean > 0 and (high_prices[idx] - ref_mean) / ref_mean >= min_swing_pct
                conf_pass, move_val = self._confirm_pivot_move(close_prices, idx, is_high=True,
                                                               confirm_bars=params.get('confirm_bars', 2),
                                                               min_move=np.nanmedian(atr_price) * params.get('confirm_atr', 0.8))
                if swing_ok and conf_pass:
                    filtered_highs.append(idx)
                    pivot_meta_highs[idx] = {
                        'prominence': float(high_prom_map.get(idx, 0.0)),
                        'confirm_move': float(move_val),
                        'z_left': float(z_l),
                        'z_right': float(z_r)
                    }
        
        for idx in raw_lows:
            passed, z_l, z_r = self._is_statistically_significant_bilateral(low_prices, idx, is_high=False,
                                                                            left=left_win, right=right_win)
            if passed:
                left_mean = np.mean(low_prices[max(0, idx - left_win):idx]) if idx > 0 else low_prices[idx]
                right_mean = np.mean(low_prices[idx+1:idx+1+right_win]) if idx < len(low_prices)-1 else low_prices[idx]
                ref_mean = min(left_mean, right_mean)
                swing_ok = ref_mean > 0 and (ref_mean - low_prices[idx]) / ref_mean >= min_swing_pct
                conf_pass, move_val = self._confirm_pivot_move(close_prices, idx, is_high=False,
                                                               confirm_bars=params.get('confirm_bars', 2),
                                                               min_move=np.nanmedian(atr_price) * params.get('confirm_atr', 0.8))
                if swing_ok and conf_pass:
                    filtered_lows.append(idx)
                    pivot_meta_lows[idx] = {
                        'prominence': float(low_prom_map.get(idx, 0.0)),
                        'confirm_move': float(move_val),
                        'z_left': float(z_l),
                        'z_right': float(z_r)
                    }

        # 3) 枢轴之间保持最小间隔（避免过密）
        filtered_highs = self._enforce_min_separation(filtered_highs, params.get('separation_bars', 3))
        filtered_lows = self._enforce_min_separation(filtered_lows, params.get('separation_bars', 3))

        # 元信息：用于HTML展示
        meta = {
            'pivot_meta_highs': {int(k): v for k, v in pivot_meta_highs.items() if k in filtered_highs},
            'pivot_meta_lows': {int(k): v for k, v in pivot_meta_lows.items() if k in filtered_lows}
        }
        
        return {
            'raw_pivot_highs': raw_highs,
            'raw_pivot_lows': raw_lows,
            'filtered_pivot_highs': filtered_highs,
            'filtered_pivot_lows': filtered_lows,
            'pivot_meta': meta
        }

    # ======== 辅助：统计强化与交易员认知贴合 ========
    def _compute_atr_price_scale(self, close_prices: np.ndarray, vol_suite: dict) -> np.ndarray:
        """将 ATR% 转换为价格尺度（若存在）；否则用收益率波动率近似。"""
        atr_pct = vol_suite.get('atr_14_pct')
        if isinstance(atr_pct, np.ndarray) and len(atr_pct) == len(close_prices):
            return (atr_pct / 100.0) * np.maximum(close_prices, 1e-8)
        # 退化方案：用过去20期的对数收益率标准差近似
        returns = np.diff(np.log(np.maximum(close_prices, 1e-8))) if len(close_prices) > 1 else np.array([0.0])
        vol = np.zeros_like(close_prices)
        if len(returns) > 5:
            for i in range(1, len(close_prices)):
                win = returns[max(1, i-20):i]
                vol[i] = np.std(win) * close_prices[i]
        return vol

    def _find_peaks_with_prominence(self, series: np.ndarray, distance: int, min_prominence: float):
        """基于 prominence 的峰值初筛（高点传原序列，低点传负序列）。

        返回:
            peaks(list[int]), prom_map(dict[idx->prominence_price])
        """
        try:
            peaks, props = find_peaks(series, distance=max(1, distance), prominence=max(1e-8, float(min_prominence)))
            prominences = props.get('prominences', np.array([]))
            prom_map = {}
            for i, p in enumerate(peaks):
                prom_map[int(p)] = float(prominences[i]) if i < len(prominences) else 0.0
            return peaks.tolist(), prom_map
        except Exception:
            # 回退到相对极值（无 prominence 信息）
            pts = argrelextrema(series, np.greater, order=max(1, distance))[0].tolist()
            return pts, {}

    def _is_statistically_significant_bilateral(self, prices: np.ndarray, idx: int, is_high: bool,
                                                left: int, right: int, alpha: float = 0.05):
        """双侧窗口显著性：当前价需显著高于（低于）两侧窗口均值。
        返回: (passed: bool, z_left: float, z_right: float)
        """
        start_l = max(0, idx - left)
        left_arr = prices[start_l:idx]
        right_arr = prices[idx+1:idx+1+right]
        if len(left_arr) < 3 or len(right_arr) < 3:
            return False, 0.0, 0.0
        cur = prices[idx]
        # 简化：当前价与两侧均值/标准差对比（稳定可靠且高效）
        def z_side(side_arr, higher: bool):
            mean = np.mean(side_arr)
            std = np.std(side_arr) + 1e-8
            z = (cur - mean) / std
            return z
        z_l = z_side(left_arr, higher=is_high)
        z_r = z_side(right_arr, higher=is_high)
        passed = (z_l > 1.64 and z_r > 1.64) if is_high else (z_l < -1.64 and z_r < -1.64)
        return passed, float(z_l), float(z_r)

    def _confirm_pivot_move(self, close_prices: np.ndarray, idx: int, is_high: bool,
                             confirm_bars: int, min_move: float):
        """后验确认：在 confirm_bars 内，价格**反向**移动至少 min_move。
        返回: (passed: bool, move_value: float)
        """
        end = min(len(close_prices), idx + 1 + max(1, confirm_bars))
        if end <= idx + 1:
            return False, 0.0
        window = close_prices[idx+1:end]
        if len(window) == 0:
            return False, 0.0
        if is_high:
            # 高点：后续有足够下行
            drop = close_prices[idx] - np.min(window)
            return drop >= max(1e-8, float(min_move)), float(drop)
        else:
            # 低点：后续有足够上行
            rise = np.max(window) - close_prices[idx]
            return rise >= max(1e-8, float(min_move)), float(rise)

    def _enforce_min_separation(self, indices: list, min_sep: int) -> list:
        if not indices:
            return []
        indices = sorted(indices)
        kept = [indices[0]]
        for i in indices[1:]:
            if i - kept[-1] >= max(1, min_sep):
                kept.append(i)
        return kept
    
    # 已移除其他方法实现，统一使用 _zigzag_atr_detection
    
    # 已移除其他方法实现，统一使用 _zigzag_atr_detection
    
    # 已移除其他方法实现，统一使用 _zigzag_atr_detection
    
    # 已移除其他方法实现，统一使用 _zigzag_atr_detection
    
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
    
    def _get_sensitivity_params(self, sensitivity: str, frequency: str = 'weekly'):
        """获取敏感度参数，按频率（日/周）提供差异化默认值。"""
        # 周频默认参数（周K）
        weekly = {
            'conservative': {
                'min_distance': 5,
                'score_threshold': 0.7,
                'min_prominence_atr': 1.2,
                'min_swing_pct': 0.025,
                'confirm_bars': 3,
                'confirm_atr': 1.0,
                'separation_bars': 4,
                'zigzag_min_distance': 5,
                'zigzag_base_swing_pct': 0.035,   # 3.5%
                'zigzag_atr_mult': 0.80,
                'zigzag_min_bars_between': 2,
                'zigzag_prom_atr_mult': 0.80
            },
            'balanced': {
                'min_distance': 3,
                'score_threshold': 0.5,
                'min_prominence_atr': 1.0,
                'min_swing_pct': 0.020,
                'confirm_bars': 2,
                'confirm_atr': 0.8,
                'separation_bars': 3,
                'zigzag_min_distance': 3,
                'zigzag_base_swing_pct': 0.025,   # 2.5%
                'zigzag_atr_mult': 0.60,
                'zigzag_min_bars_between': 2,
                'zigzag_prom_atr_mult': 0.60
            },
            'aggressive': {
                'min_distance': 2,
                'score_threshold': 0.3,
                'min_prominence_atr': 0.8,
                'min_swing_pct': 0.015,
                'confirm_bars': 1,
                'confirm_atr': 0.6,
                'separation_bars': 2,
                'zigzag_min_distance': 2,
                'zigzag_base_swing_pct': 0.018,   # 1.8%
                'zigzag_atr_mult': 0.50,
                'zigzag_min_bars_between': 1,
                'zigzag_prom_atr_mult': 0.50
            }
        }

        # 日频覆盖（近3个月）
        daily_overrides = {
            'conservative': {
                'zigzag_min_distance': 3,
                'zigzag_base_swing_pct': 0.018,  # 1.8%
                'zigzag_atr_mult': 0.80,
                'zigzag_min_bars_between': 3,
                'zigzag_prom_atr_mult': 1.00,
                'min_distance': 3
            },
            'balanced': {
                'zigzag_min_distance': 2,
                'zigzag_base_swing_pct': 0.012,  # 1.2%
                'zigzag_atr_mult': 0.60,
                'zigzag_min_bars_between': 2,
                'zigzag_prom_atr_mult': 0.80,
                'min_distance': 2
            },
            'aggressive': {
                'zigzag_min_distance': 2,
                'zigzag_base_swing_pct': 0.008,  # 0.8%
                'zigzag_atr_mult': 0.50,
                'zigzag_min_bars_between': 1,
                'zigzag_prom_atr_mult': 0.60,
                'min_distance': 2
            }
        }

        base = weekly.get(sensitivity, weekly['balanced']).copy()
        if str(frequency).lower() == 'daily':
            override = daily_overrides.get(sensitivity, {})
            base.update(override)
        return base

    def _zigzag_atr_detection(self, data, technical_suite, sensitivity, frequency: str = 'weekly'):
        """ZigZag + ATR 自适应阈值的信号模式（更贴近交易员进出场）。

        特征：
        - 更宽松的摆动阈值：threshold_pct = max(base_swing_pct, ATR_pct * atr_mult)
        - 使用 prominence 初筛候选，随后按时间顺序交替构建 pivots
        - 保留最极端点（同向候选只保留更高/更低者）
        - 限制相邻 pivot 的最小K线间隔，减少抖动
        """

        close_prices = data['close'].values
        high_prices = data['high'].values
        low_prices = data['low'].values
        params = self._get_sensitivity_params(sensitivity, frequency)

        # 价格尺度与阈值
        vol_suite = technical_suite.get('volatility', {})
        atr_pct_arr = vol_suite.get('atr_14_pct')
        if not isinstance(atr_pct_arr, np.ndarray) or len(atr_pct_arr) != len(close_prices):
            atr_pct_arr = np.zeros_like(close_prices) + 2.0  # 退化：假设2%

        base_swing = float(params.get('zigzag_base_swing_pct', 0.015))  # 小幅摆动
        atr_mult = float(params.get('zigzag_atr_mult', 0.6))
        min_bars_between = int(params.get('zigzag_min_bars_between', 2))
        prom_atr_mult = float(params.get('zigzag_prom_atr_mult', 0.6))
        min_distance = int(params.get('zigzag_min_distance', 2))

        # prominence 初筛
        atr_price = self._compute_atr_price_scale(close_prices, vol_suite)
        min_prom_price = np.nanmedian(atr_price) * prom_atr_mult
        high_candidates, high_prom_map = self._find_peaks_with_prominence(high_prices, distance=min_distance,
                                                                          min_prominence=min_prom_price)
        low_candidates, low_prom_map_neg = self._find_peaks_with_prominence(-low_prices, distance=min_distance,
                                                                            min_prominence=min_prom_price)
        low_prom_map = {k: float(v) for k, v in low_prom_map_neg.items()}

        # 合并候选并按时间排序，标注类型与价格
        events = []
        for idx in high_candidates:
            if 0 <= idx < len(high_prices):
                events.append((idx, 'high', float(high_prices[idx])))
        for idx in low_candidates:
            if 0 <= idx < len(low_prices):
                events.append((idx, 'low', float(low_prices[idx])))
        events.sort(key=lambda x: x[0])

        filtered_highs = []
        filtered_lows = []
        pivot_meta_highs = {}
        pivot_meta_lows = {}

        last_type = None
        last_idx = None
        last_price = None

        def dynamic_threshold_pct(i):
            return max(base_swing, (atr_pct_arr[i] / 100.0) * atr_mult)

        for idx, typ, price in events:
            # 最小柱间隔约束
            if last_idx is not None and (idx - last_idx) < min_bars_between:
                # 同向保留更极端者
                if last_type == typ:
                    if (typ == 'high' and price > last_price) or (typ == 'low' and price < last_price):
                        # 替换最后一个pivot
                        if typ == 'high' and filtered_highs:
                            filtered_highs[-1] = idx
                            last_idx, last_price = idx, price
                        elif typ == 'low' and filtered_lows:
                            filtered_lows[-1] = idx
                            last_idx, last_price = idx, price
                    # 否则忽略
                # 异向但太近则忽略
                continue

            if last_type is None:
                # 第一个候选直接接受为起始pivot
                if typ == 'high':
                    filtered_highs.append(idx)
                    last_type, last_idx, last_price = 'high', idx, price
                    pivot_meta_highs[idx] = {
                        'prominence': float(high_prom_map.get(idx, 0.0)),
                        'threshold_pct': float(dynamic_threshold_pct(idx)),
                        'atr_pct': float(atr_pct_arr[idx])
                    }
                else:
                    filtered_lows.append(idx)
                    last_type, last_idx, last_price = 'low', idx, price
                    pivot_meta_lows[idx] = {
                        'prominence': float(low_prom_map.get(idx, 0.0)),
                        'threshold_pct': float(dynamic_threshold_pct(idx)),
                        'atr_pct': float(atr_pct_arr[idx])
                    }
                continue

            if typ == last_type:
                # 同向：仅在更极端时替换
                if (typ == 'high' and price > last_price) or (typ == 'low' and price < last_price):
                    if typ == 'high' and filtered_highs:
                        filtered_highs[-1] = idx
                        last_idx, last_price = idx, price
                        pivot_meta_highs[idx] = {
                            'prominence': float(high_prom_map.get(idx, 0.0)),
                            'threshold_pct': float(dynamic_threshold_pct(idx)),
                            'atr_pct': float(atr_pct_arr[idx])
                        }
                    elif typ == 'low' and filtered_lows:
                        filtered_lows[-1] = idx
                        last_idx, last_price = idx, price
                        pivot_meta_lows[idx] = {
                            'prominence': float(low_prom_map.get(idx, 0.0)),
                            'threshold_pct': float(dynamic_threshold_pct(idx)),
                            'atr_pct': float(atr_pct_arr[idx])
                        }
                continue

            # 异向：检查摆动幅度是否达到阈值
            thr = dynamic_threshold_pct(idx)
            swing_pct = (abs(price - last_price) / max(1e-8, last_price))
            if swing_pct >= thr:
                if typ == 'high':
                    filtered_highs.append(idx)
                    pivot_meta_highs[idx] = {
                        'prominence': float(high_prom_map.get(idx, 0.0)),
                        'threshold_pct': float(thr),
                        'atr_pct': float(atr_pct_arr[idx]),
                        'swing_pct': float(swing_pct)
                    }
                else:
                    filtered_lows.append(idx)
                    pivot_meta_lows[idx] = {
                        'prominence': float(low_prom_map.get(idx, 0.0)),
                        'threshold_pct': float(thr),
                        'atr_pct': float(atr_pct_arr[idx]),
                        'swing_pct': float(swing_pct)
                    }
                last_type, last_idx, last_price = typ, idx, price
            # 未达到阈值则忽略（继续等待更远的摆动）

        # 输出格式
        filtered_highs = self._enforce_min_separation(filtered_highs, max(1, min_bars_between))
        filtered_lows = self._enforce_min_separation(filtered_lows, max(1, min_bars_between))

        meta = {
            'pivot_meta_highs': {int(k): v for k, v in pivot_meta_highs.items() if k in filtered_highs},
            'pivot_meta_lows': {int(k): v for k, v in pivot_meta_lows.items() if k in filtered_lows}
        }

        return {
            'raw_pivot_highs': filtered_highs,
            'raw_pivot_lows': filtered_lows,
            'filtered_pivot_highs': filtered_highs,
            'filtered_pivot_lows': filtered_lows,
            'pivot_meta': meta
        }
    
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
    
    def _standardize_output(self, pivot_results, technical_suite, quality_metrics, analysis_report, method, premium_metrics=None):
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
            
            # 优质评估（新增）
            'premium_metrics': premium_metrics or {},
            
            # 过滤效果统计
            'filter_effectiveness': {
                'highs_filtered': len(pivot_results.get('raw_pivot_highs', [])) - len(pivot_results.get('filtered_pivot_highs', [])),
                'lows_filtered': len(pivot_results.get('raw_pivot_lows', [])) - len(pivot_results.get('filtered_pivot_lows', [])),
                'filter_ratio': self._calculate_filter_ratio(pivot_results)
            }
        }

    def _compute_premium_metrics(self, data, pivot_results, frequency: str = 'weekly'):
        """从识别的低点中找最低点，计算自该时点至今的年化波动率与夏普比率，并给出“优质”标注。

        返回:
            dict: {
                't1': str | None,                  # 最低低点时间（ISO字符串）
                'p1': float | None,                # 最低低点价格
                'annualized_volatility_pct': float,# 年化波动率（百分比值，如 45.2 表示45.2%）
                'sharpe_ratio': float,             # 夏普比率（Rf=0 假设）
                'is_premium': bool,                # 是否优质
                'reason': str                      # 说明（含R1/R2）
            }
        """
        try:
            import numpy as np
            import pandas as pd

            filtered_lows = pivot_results.get('filtered_pivot_lows', []) or []
            if len(filtered_lows) == 0 or len(data) < 2:
                return {
                    't1': None,
                    'p1': None,
                    'annualized_volatility_pct': 0.0,
                    'sharpe_ratio': 0.0,
                    'is_premium': False,
                    'reason': '无有效低点或样本过短'
                }

            low_prices = data['low'].values
            valid_idxs = [idx for idx in filtered_lows if 0 <= idx < len(low_prices)]
            if not valid_idxs:
                return {
                    't1': None,
                    'p1': None,
                    'annualized_volatility_pct': 0.0,
                    'sharpe_ratio': 0.0,
                    'is_premium': False,
                    'reason': '低点索引无效'
                }

            # 找到识别低点中的最低点
            lowest_idx = min(valid_idxs, key=lambda i: low_prices[i])
            t1_ts = data.index[lowest_idx]
            try:
                t1_str = t1_ts.strftime('%Y-%m-%d') if hasattr(t1_ts, 'strftime') else str(t1_ts)
            except Exception:
                t1_str = str(t1_ts)
            p1_val = float(low_prices[lowest_idx])

            # 自T1至最新的周收益率序列
            close_series = data['close'].iloc[lowest_idx:]
            if len(close_series) < 2:
                ann_vol_pct = 0.0
                sharpe = 0.0
            else:
                log_returns = np.diff(np.log(np.maximum(close_series.values, 1e-12)))
                if len(log_returns) == 0:
                    ann_vol_pct = 0.0
                    sharpe = 0.0
                else:
                    periods_per_year = 52 if str(frequency).lower() == 'weekly' else (252 if str(frequency).lower() == 'daily' else 52)
                    mu = float(np.mean(log_returns))
                    # 使用无偏估计（样本标准差）
                    sigma = float(np.std(log_returns, ddof=1)) if len(log_returns) > 1 else float(np.std(log_returns))
                    ann_vol = sigma * np.sqrt(periods_per_year)
                    ann_vol_pct = float(ann_vol * 100.0)
                    sharpe = float((mu / sigma) * np.sqrt(periods_per_year)) if sigma > 1e-12 else 0.0

            # 优质判定阈值（年化波动率≥40%，夏普≥0.8）
            is_premium = (ann_vol_pct >= 40.0 and sharpe >= 0.8)
            reason = f"年化波动率R1={ann_vol_pct:.1f}%，夏普比率R2={sharpe:.2f}"

            return {
                't1': t1_str,
                'p1': p1_val,
                'annualized_volatility_pct': ann_vol_pct,
                'sharpe_ratio': sharpe,
                'is_premium': bool(is_premium),
                'reason': reason
            }
        except Exception as e:
            return {
                't1': None,
                'p1': None,
                'annualized_volatility_pct': 0.0,
                'sharpe_ratio': 0.0,
                'is_premium': False,
                'reason': f'计算失败: {e}'
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