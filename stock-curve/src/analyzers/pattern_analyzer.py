# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
import os

class PatternAnalyzer:
    def __init__(self):
        pass
    
    def detect_global_arc_bottom(self, prices, min_points=20, r2_threshold=0.7):
        """
        分析整个价格序列是否构成圆弧底形态
        
        Args:
            prices: 价格序列
            min_points: 最小数据点数
            r2_threshold: R²拟合度阈值
            
        Returns:
            dict: 圆弧底分析结果，如果不满足则返回None
        """
        if len(prices) < min_points:
            return None
        
        # 1. 整体二次拟合
        x = np.arange(len(prices))
        coeffs = np.polyfit(x, prices, 2)
        
        # 检查是否为向上开口的抛物线
        if coeffs[0] <= 0:
            return None
        
        # 计算拟合度
        y_fit = np.polyval(coeffs, x)
        r2 = 1 - np.sum((prices - y_fit) ** 2) / np.sum((prices - np.mean(prices)) ** 2)
        
        if r2 < r2_threshold:
            return None
        
        # 2. 验证圆弧底的基本特征
        min_idx = np.argmin(prices)
        min_price = prices[min_idx]
        
        # 检查最低点是否在合理位置（不在两端）
        if min_idx < len(prices) * 0.2 or min_idx > len(prices) * 0.8:
            return None
        
        # 检查两端价格是否高于最低点
        if prices[0] <= min_price or prices[-1] <= min_price:
            return None
        
        # 3. 分析三阶段特征
        stages = self._analyze_global_stages(prices, min_idx)
        
        if not self._validate_global_arc_bottom(stages):
            return None
        
        # 4. 计算圆弧底质量评分
        quality_score = self._calculate_arc_quality(prices, coeffs, r2, stages)
        
        return {
            'type': 'global_arc_bottom',
            'r2': r2,
            'quality_score': quality_score,
            'coeffs': coeffs,
            'min_point': min_idx,
            'min_price': min_price,
            'stages': stages,
            'total_points': len(prices),
            'price_range': {
                'start': prices[0],
                'end': prices[-1],
                'min': min_price,
                'max': np.max(prices)
            }
        }
    
    def _analyze_global_stages(self, prices, min_idx):
        """分析全局三阶段特征：严重下降、横盘、轻微上涨"""
        n = len(prices)
        
        # 寻找横盘阶段（更宽松的定义）
        flat_stage = self._find_flat_stage_improved(prices, min_idx)
        
        if flat_stage:
            # 三阶段：严重下降、横盘、轻微上涨
            decline_prices = prices[:flat_stage['start']]
            decline_dates = np.arange(flat_stage['start'])
            
            flat_prices = prices[flat_stage['start']:flat_stage['end']+1]
            flat_dates = np.arange(flat_stage['start'], flat_stage['end']+1)
            
            rise_prices = prices[flat_stage['end']+1:]
            rise_dates = np.arange(flat_stage['end']+1, n)
            
            decline_stage = self._analyze_stage(decline_prices, decline_dates, 'decline')
            flat_stage_data = self._analyze_stage(flat_prices, flat_dates, 'flat')
            rise_stage = self._analyze_stage(rise_prices, rise_dates, 'rise')
            
            return {
                'decline': decline_stage,
                'flat': flat_stage_data,
                'rise': rise_stage,
                'min_point': min_idx,
                'min_price': prices[min_idx]
            }
        else:
            # 两阶段：下降、上涨
            decline_prices = prices[:min_idx+1]
            decline_dates = np.arange(min_idx+1)
            
            rise_prices = prices[min_idx:]
            rise_dates = np.arange(min_idx, n)
            
            decline_stage = self._analyze_stage(decline_prices, decline_dates, 'decline')
            rise_stage = self._analyze_stage(rise_prices, rise_dates, 'rise')
            
            return {
                'decline': decline_stage,
                'rise': rise_stage,
                'min_point': min_idx,
                'min_price': prices[min_idx]
            }
    
    def _find_flat_stage_improved(self, prices, min_idx):
        """寻找横盘阶段（改进版）"""
        n = len(prices)
        min_price = prices[min_idx]
        
        # 更宽松的横盘定义：最低点附近±10%
        price_tolerance = min_price * 0.10
        
        # 从最低点向前寻找横盘开始
        flat_start = min_idx
        for i in range(min_idx, -1, -1):
            if abs(prices[i] - min_price) <= price_tolerance:
                flat_start = i
            else:
                break
        
        # 从最低点向后寻找横盘结束
        flat_end = min_idx
        for i in range(min_idx, n):
            if abs(prices[i] - min_price) <= price_tolerance:
                flat_end = i
            else:
                break
        
        # 确保横盘阶段有足够长度（至少3个数据点）
        if flat_end - flat_start >= 2:
            return {
                'start': flat_start,
                'end': flat_end,
                'duration': flat_end - flat_start + 1
            }
        
        return None
    
    def _validate_global_arc_bottom(self, stages):
        """验证全局圆弧底形态的有效性"""
        if not stages or not stages['decline'] or not stages['rise']:
            return False
        
        decline = stages['decline']
        rise = stages['rise']
        
        # 下降阶段验证 - 要求更严重的下降
        if decline['duration'] < 3:  # 至少3个数据点
            return False
        
        if decline['slope'] > -0.001:  # 应该有下降趋势
            return False
        
        if decline['price_change_pct'] > -10:  # 下降幅度至少10%
            return False
        
        # 上涨阶段验证 - 要求轻微上涨
        if rise['duration'] < 2:  # 至少2个数据点
            return False
        
        if rise['slope'] < 0.0001:  # 应该有轻微的上涨趋势
            return False
        
        if rise['price_change_pct'] < 3:  # 上涨幅度至少3%
            return False
        
        # 横盘阶段验证（如果存在）
        if 'flat' in stages and stages['flat']:
            flat = stages['flat']
            if flat['duration'] < 2:  # 横盘至少2个数据点
                return False
            
            # 横盘时间应该比上涨时间长（放宽条件）
            if flat['duration'] < rise['duration'] * 0.5:  # 横盘至少是上涨时间的一半
                return False
            
            # 横盘阶段价格变化应该较小
            if abs(flat['price_change_pct']) > 12:  # 横盘阶段价格变化不超过12%
                return False
        
        # 验证形态的合理性
        total_duration = decline['duration'] + rise['duration']
        if 'flat' in stages and stages['flat']:
            total_duration += stages['flat']['duration']
        
        decline_ratio = decline['duration'] / total_duration
        if decline_ratio < 0.15 or decline_ratio > 0.6:  # 下降阶段占比15%-60%
            return False
        
        return True
    
    def _calculate_arc_quality(self, prices, coeffs, r2, stages):
        """计算圆弧底质量评分"""
        quality_factors = []
        
        # 1. 拟合度评分 (0-20分)
        quality_factors.append(r2 * 20)
        
        # 2. 下降严重程度评分 (0-25分)
        decline_severity = abs(stages['decline']['price_change_pct'])
        decline_score = min(decline_severity / 2, 25)  # 每2%得1分，最高25分
        quality_factors.append(decline_score)
        
        # 3. 横盘质量评分 (0-25分)
        if 'flat' in stages and stages['flat']:
            flat = stages['flat']
            # 横盘时间越长得分越高
            flat_duration_score = min(flat['duration'] / 2, 15)  # 每2个数据点得1分，最高15分
            # 横盘价格稳定性
            flat_stability_score = max(0, 10 - abs(flat['price_change_pct']))  # 价格变化越小得分越高
            quality_factors.append(flat_duration_score + flat_stability_score)
        else:
            quality_factors.append(0)
        
        # 4. 上涨轻微程度评分 (0-15分)
        rise_change = abs(stages['rise']['price_change_pct'])
        # 上涨幅度在5%-15%之间得分最高
        if 5 <= rise_change <= 15:
            rise_score = 15
        elif rise_change < 5:
            rise_score = rise_change * 3  # 线性得分
        else:
            rise_score = max(0, 15 - (rise_change - 15))  # 超过15%开始扣分
        quality_factors.append(rise_score)
        
        # 5. 形态合理性评分 (0-10分)
        total_duration = stages['decline']['duration'] + stages['rise']['duration']
        if 'flat' in stages and stages['flat']:
            total_duration += stages['flat']['duration']
        
        decline_ratio = stages['decline']['duration'] / total_duration
        # 下降占比30%左右得分最高
        symmetry_score = 10 * (1 - abs(decline_ratio - 0.3) * 2)
        quality_factors.append(max(0, symmetry_score))
        
        # 6. 数据点数量评分 (0-5分)
        point_score = min(len(prices) / 10, 5)  # 每10个数据点得1分，最高5分
        quality_factors.append(point_score)
        
        return sum(quality_factors)
    
    def detect_arc_bottom(self, data, min_points=20):
        """检测圆弧底形态"""
        if len(data) < min_points:
            return None
        
        # 获取收盘价数据
        prices = data['close'].values
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
        ma_short = pd.Series(prices).rolling(window=3).mean().values
        ma_long = pd.Series(prices).rolling(window=7).mean().values
        
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

    def detect_arc_bottom_simple(self, prices, min_len=20, max_len=40, r2_thresh=0.8):
        """滑动窗口二次拟合识别圆弧底，返回区间和拟合参数"""
        n = len(prices)
        for win_len in range(min_len, max_len+1):
            for start in range(n - win_len + 1):
                end = start + win_len
                x = np.arange(win_len)
                y = prices[start:end]
                coeffs = np.polyfit(x, y, 2)
                if coeffs[0] <= 0:
                    continue  # 不是开口向上
                y_fit = np.polyval(coeffs, x)
                r2 = 1 - np.sum((y - y_fit) ** 2) / np.sum((y - np.mean(y)) ** 2)
                if r2 < r2_thresh:
                    continue
                min_idx = np.argmin(y)
                if min_idx < win_len//3 or min_idx > win_len*2//3:
                    continue  # 最低点不在中间
                if y[0] <= y[min_idx] or y[-1] <= y[min_idx]:
                    continue  # 两端必须高于中间
                # 满足条件，返回区间
                return {
                    'start': start,
                    'end': end,
                    'coeffs': coeffs,
                    'r2': r2,
                    'min_idx': min_idx,
                    'window_prices': y,
                }
        return None 