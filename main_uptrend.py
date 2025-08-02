#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
import shutil
import re
from src.core.stock_data_processor import StockDataProcessor
from src.analyzers.uptrend_channel_analyzer import UptrendChannelAnalyzer
from src.generators.uptrend_chart_generator import UptrendChartGenerator
from src.generators.uptrend_html_generator import UptrendHTMLGenerator
import numpy as np
from scipy import stats

def setup_output_directories(output_dir):
    """创建输出目录"""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'images'), exist_ok=True)

def clear_cache_if_needed(clear_cache):
    """清除缓存"""
    if clear_cache:
        cache_dir = "cache"
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            print("缓存已清除")

def load_and_process_data(csv_file_path, max_stocks=None):
    """加载和处理股票数据"""
    data_processor = StockDataProcessor(csv_file_path)
    
    if not data_processor.load_data():
        print('数据加载失败:', csv_file_path)
        return None
        
    if not data_processor.process_weekly_data():
        print('数据处理失败')
        return None
        
    stock_data = data_processor.get_all_data()
    
    # 限制处理的股票数量
    if max_stocks:
        stock_data = dict(list(stock_data.items())[:max_stocks])
    
    return stock_data

def extract_arc_stocks_from_html(arc_html_path):
    """从大弧底分析HTML中提取股票代码"""
    arc_stocks = []
    
    try:
        with open(arc_html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 使用正则表达式提取股票代码
        # 匹配模式：similar_XXXXXX.XX 或 major_XXXXXX.XX
        pattern = r'(?:similar_|major_)([A-Z0-9]{6}\.[A-Z]{2})'
        matches = re.findall(pattern, html_content)
        
        # 去重并返回
        arc_stocks = list(set(matches))
        print("从大弧底分析中提取到 {} 只股票: {}".format(len(arc_stocks), arc_stocks))
        
    except Exception as e:
        print(f"读取大弧底分析HTML失败: {e}")
    
    return arc_stocks

def filter_stock_data_by_arc(stock_data, arc_stocks):
    """根据大弧底股票列表过滤股票数据"""
    if not arc_stocks:
        print("没有大弧底股票数据，返回原始数据")
        return stock_data
    
    filtered_data = {}
    found_count = 0
    
    for code in arc_stocks:
        if code in stock_data:
            filtered_data[code] = stock_data[code]
            found_count += 1
        else:
            print(f"警告: 股票 {code} 在大弧底分析中找到，但在数据中不存在")
    
    print(f"成功过滤出 {found_count}/{len(arc_stocks)} 只大弧底股票")
    return filtered_data

def detect_and_generate_charts(stock_data, output_dir):
    """检测上升通道并生成图表，针对大弧底股票进行优化分析"""
    analyzer = UptrendChannelAnalyzer()
    chart_generator = UptrendChartGenerator(output_dir=os.path.join(output_dir, 'images'))
    
    perfect_matches = {}
    similarity_results = {}
    chart_paths = {}
    
    print(f"开始分析 {len(stock_data)} 只大弧底股票的上升通道形态...")
    print(f"TA-Lib可用: {analyzer.talib_available}")
    
    for i, (code, df) in enumerate(stock_data.items()):
        prices = df['close'].values
        
        # 准备TA-Lib增强检测所需的数据
        high_prices = df['high'].values if 'high' in df.columns else None
        low_prices = df['low'].values if 'low' in df.columns else None
        
        # 检测上升通道（针对大弧底股票优化 - 专注最近半年）
        channel_result = analyzer.detect_uptrend_channel(
            prices, high_prices, low_prices,
            min_points=20,           # 20个数据点，约5个月
            min_channel_width=0.02,  # 2%，适应大弧底后的反弹
            min_duration_weeks=8,    # 8周，确保趋势稳定
            r2_threshold=0.6,        # 0.6，确保质量
            recent_focus=True        # 专注最近趋势（最近半年数据）
        )
        
        # 如果传统检测失败，尝试入场信号检测
        if not channel_result:
            entry_signal = analyzer.detect_entry_signal(
                prices, high_prices, low_prices,
                recent_weeks=26,     # 分析最近26周，约半年
                min_slope=0.008      # 最小斜率0.8%，适应反弹
            )
            
            if entry_signal:
                # 基于K线高低点创建真实的通道线 - 最近3个月
                recent_weeks = 13  # 约3个月
                start_idx = max(0, len(prices) - recent_weeks)
                end_idx = len(prices) - 1
                
                # 获取最近半年的高低点数据
                recent_highs = high_prices[-recent_weeks:] if high_prices is not None else prices[-recent_weeks:]
                recent_lows = low_prices[-recent_weeks:] if low_prices is not None else prices[-recent_weeks:]
                
                # 基于K线图特征识别真正的高低点，使用波动率过滤 - 最近3个月
                # 计算价格波动率作为过滤阈值
                price_volatility = np.std(recent_highs) * 0.15  # 使用标准差的15%作为最小波动阈值（3个月数据更敏感）
                min_swing = max(price_volatility, np.mean(recent_highs) * 0.015)  # 至少1.5%的价格波动（3个月数据）
                
                # 识别真正的高点（基于波动率过滤）
                high_points = []
                for i in range(2, len(recent_highs)-2):  # 跳过首尾2个点
                    current_high = recent_highs[i]
                    # 检查是否是显著的高点：比前后各2个点都高，且波动足够大
                    left_avg = np.mean(recent_highs[max(0, i-2):i])
                    right_avg = np.mean(recent_highs[i+1:min(len(recent_highs), i+3)])
                    
                    # 当前高点必须比左右平均值都高，且波动超过阈值
                    if (current_high > left_avg + min_swing and 
                        current_high > right_avg + min_swing):
                        high_points.append((i, current_high))
                
                # 如果首尾点也是显著高点，也加入
                if len(recent_highs) > 2:
                    if recent_highs[0] > np.mean(recent_highs[1:3]) + min_swing:
                        high_points.insert(0, (0, recent_highs[0]))
                    if recent_highs[-1] > np.mean(recent_highs[-3:-1]) + min_swing:
                        high_points.append((len(recent_highs)-1, recent_highs[-1]))
                
                # 识别真正的低点（基于波动率过滤）
                low_points = []
                for i in range(2, len(recent_lows)-2):  # 跳过首尾2个点
                    current_low = recent_lows[i]
                    # 检查是否是显著的低点：比前后各2个点都低，且波动足够大
                    left_avg = np.mean(recent_lows[max(0, i-2):i])
                    right_avg = np.mean(recent_lows[i+1:min(len(recent_lows), i+3)])
                    
                    # 当前低点必须比左右平均值都低，且波动超过阈值
                    if (current_low < left_avg - min_swing and 
                        current_low < right_avg - min_swing):
                        low_points.append((i, current_low))
                
                # 如果首尾点也是显著低点，也加入
                if len(recent_lows) > 2:
                    if recent_lows[0] < np.mean(recent_lows[1:3]) - min_swing:
                        low_points.insert(0, (0, recent_lows[0]))
                    if recent_lows[-1] < np.mean(recent_lows[-3:-1]) - min_swing:
                        low_points.append((len(recent_lows)-1, recent_lows[-1]))
                
                # 如果高低点太少，使用更智能的方法：选择最显著的高低点
                if len(high_points) < 2:
                    # 计算每个点的显著性得分
                    high_scores = []
                    for i in range(len(recent_highs)):
                        if i == 0:
                            score = recent_highs[i] - recent_highs[i+1] if len(recent_highs) > 1 else 0
                        elif i == len(recent_highs) - 1:
                            score = recent_highs[i] - recent_highs[i-1]
                        else:
                            score = recent_highs[i] - (recent_highs[i-1] + recent_highs[i+1]) / 2
                        high_scores.append((i, score))
                    
                    # 选择得分最高的3个点
                    high_scores.sort(key=lambda x: x[1], reverse=True)
                    high_points = [(i, recent_highs[i]) for i, _ in high_scores[:3]]
                
                if len(low_points) < 2:
                    # 计算每个点的显著性得分
                    low_scores = []
                    for i in range(len(recent_lows)):
                        if i == 0:
                            score = recent_lows[i+1] - recent_lows[i] if len(recent_lows) > 1 else 0
                        elif i == len(recent_lows) - 1:
                            score = recent_lows[i-1] - recent_lows[i]
                        else:
                            score = (recent_lows[i-1] + recent_lows[i+1]) / 2 - recent_lows[i]
                        low_scores.append((i, score))
                    
                    # 选择得分最高的3个点
                    low_scores.sort(key=lambda x: x[1], reverse=True)
                    low_points = [(i, recent_lows[i]) for i, _ in low_scores[:3]]
                
                # 使用高低点拟合通道线，确保始终有结果
                # 上轨线：基于高点
                if len(high_points) >= 2:
                    high_x = [p[0] for p in high_points]
                    high_y = [p[1] for p in high_points]
                    try:
                        high_slope, high_intercept, _, _, _ = stats.linregress(high_x, high_y)
                    except:
                        # 如果拟合失败，使用简单的线性插值
                        high_slope = (high_points[-1][1] - high_points[0][1]) / (high_points[-1][0] - high_points[0][0])
                        high_intercept = high_points[0][1] - high_slope * high_points[0][0]
                else:
                    # 如果找不到足够的高点，使用整体趋势
                    x_high = np.arange(len(recent_highs))
                    try:
                        high_slope, high_intercept, _, _, _ = stats.linregress(x_high, recent_highs)
                    except:
                        high_slope = 0.01
                        high_intercept = np.mean(recent_highs)
                
                # 下轨线：基于低点
                if len(low_points) >= 2:
                    low_x = [p[0] for p in low_points]
                    low_y = [p[1] for p in low_points]
                    try:
                        low_slope, low_intercept, _, _, _ = stats.linregress(low_x, low_y)
                    except:
                        # 如果拟合失败，使用简单的线性插值
                        low_slope = (low_points[-1][1] - low_points[0][1]) / (low_points[-1][0] - low_points[0][0])
                        low_intercept = low_points[0][1] - low_slope * low_points[0][0]
                else:
                    # 如果找不到足够的低点，使用整体趋势
                    x_low = np.arange(len(recent_lows))
                    try:
                        low_slope, low_intercept, _, _, _ = stats.linregress(x_low, recent_lows)
                    except:
                        low_slope = 0.01
                        low_intercept = np.mean(recent_lows)
                
                # 确保斜率合理，避免极端值
                if abs(high_slope) > 1.0:
                    high_slope = 0.01
                    high_intercept = np.mean(recent_highs)
                if abs(low_slope) > 1.0:
                    low_slope = 0.01
                    low_intercept = np.mean(recent_lows)
                
                # 调整截距到原始数据坐标系，确保通道线在合理范围内
                adjusted_high_intercept = high_intercept - high_slope * start_idx
                adjusted_low_intercept = low_intercept - low_slope * start_idx
                
                # 确保截距在合理范围内，但保持基于高低点的拟合
                min_price = min(recent_highs)
                max_price = max(recent_highs)
                
                # 如果截距不合理，重新计算基于真正的高低点
                if adjusted_high_intercept < min_price or adjusted_low_intercept > max_price:
                    # 找到最近3个月的最高点和最低点
                    if len(high_points) >= 2:
                        # 找到最近3个月的最高点和最低点作为起点和终点
                        sorted_highs = sorted(high_points, key=lambda x: x[0])  # 按时间排序
                        start_high = sorted_highs[0]  # 最早的高点
                        end_high = sorted_highs[-1]   # 最晚的高点
                        
                        # 计算上轨线：连接最早高点和最晚高点
                        high_slope = (end_high[1] - start_high[1]) / (end_high[0] - start_high[0])
                        high_intercept = start_high[1] - high_slope * start_high[0]
                        adjusted_high_intercept = high_intercept - high_slope * start_idx
                    else:
                        # 如果只有一个高点，使用水平线
                        adjusted_high_intercept = max_price
                        high_slope = 0.0
                    
                    if len(low_points) >= 2:
                        # 找到最近3个月的最低点和最高点作为起点和终点
                        sorted_lows = sorted(low_points, key=lambda x: x[0])  # 按时间排序
                        start_low = sorted_lows[0]  # 最早的低点
                        end_low = sorted_lows[-1]   # 最晚的低点
                        
                        # 计算下轨线：连接最早低点和最晚低点
                        low_slope = (end_low[1] - start_low[1]) / (end_low[0] - start_low[0])
                        low_intercept = start_low[1] - low_slope * start_low[0]
                        adjusted_low_intercept = low_intercept - low_slope * start_idx
                        
                        # 确保下轨线截距合理
                        if adjusted_low_intercept < min_price - (max_price - min_price) * 0.3:
                            # 如果截距太低，使用最低点作为起点
                            adjusted_low_intercept = min_price
                            low_slope = 0.0
                    else:
                        # 如果只有一个低点，使用水平线
                        adjusted_low_intercept = min_price
                        low_slope = 0.0
                
                # 验证截距是否合理，但保持基于高低点的拟合
                min_price = min(recent_highs)
                max_price = max(recent_highs)
                price_range = max_price - min_price
                
                # 计算通道线在数据范围内的价格值
                high_price_at_start = adjusted_high_intercept
                high_price_at_end = adjusted_high_intercept + high_slope * (len(recent_highs) - 1)
                low_price_at_start = adjusted_low_intercept
                low_price_at_end = adjusted_low_intercept + low_slope * (len(recent_lows) - 1)
                
                # 只在极端情况下微调截距，保持基于高低点的拟合
                if high_price_at_start < min_price - price_range * 0.5:
                    # 轻微调整上轨截距，但保持斜率
                    adjusted_high_intercept = min_price + price_range * 0.1
                if low_price_at_start > max_price + price_range * 0.5:
                    # 轻微调整下轨截距，但保持斜率
                    adjusted_low_intercept = max_price - price_range * 0.1
                

                

                

                

                

                

                
                virtual_upper_channel = {
                    'slope': high_slope,
                    'intercept': adjusted_high_intercept,
                    'start_idx': start_idx,
                    'end_idx': end_idx,
                    'r2': entry_signal['recent_trend']['r2'],
                    'score': entry_signal['entry_strength'],
                    'fit_quality': entry_signal['entry_strength']
                }
                
                virtual_lower_channel = {
                    'slope': low_slope,
                    'intercept': adjusted_low_intercept,
                    'start_idx': start_idx,
                    'end_idx': end_idx,
                    'r2': entry_signal['recent_trend']['r2'],
                    'score': entry_signal['entry_strength'],
                    'fit_quality': entry_signal['entry_strength']
                }
                
                # 将入场信号转换为通道结果格式
                channel_result = {
                    'type': 'entry_signal',
                    'entry_strength': entry_signal['entry_strength'],
                    'recommendation': entry_signal['recommendation'],
                    'quality_score': entry_signal['entry_strength'],
                    'enhanced_quality_score': entry_signal['entry_strength'],
                    'recent_trend': entry_signal['recent_trend'],
                    'channel_analysis': entry_signal['channel_analysis'],
                    'is_entry_signal': True,
                    'upper_channel': virtual_upper_channel,
                    'lower_channel': virtual_lower_channel,
                    'channel_quality': {
                        'duration': recent_weeks,
                        'channel_width_pct': (np.mean(recent_highs) - np.mean(recent_lows)) / np.mean(prices[-recent_weeks:]) * 100,
                        'start_idx': start_idx,
                        'end_idx': end_idx,
                        'slope_diff': abs(high_slope - low_slope),
                        'price_distribution': {
                            'inside_ratio': 0.7,
                            'outside_ratio': 0.3,
                            'inside_count': int(recent_weeks * 0.7),
                            'total_count': recent_weeks
                        }
                    },
                    'channel_features': {
                        'channel_strength': entry_signal['entry_strength'],
                        'breakout_attempts': 0,
                        'price_position': entry_signal['channel_analysis']['price_position']
                    }
                }
        
        if channel_result:

            
            # 使用统一的键格式
            key = f'uptrend_{code}'
            
            # 获取质量评分（优先使用增强评分）
            quality_score = channel_result.get('enhanced_quality_score', 
                                             channel_result.get('quality_score', 0.5))
            
            perfect_matches[key] = {
                'channel_result': channel_result,
                'prices': prices,
                'name': df.get('name', code) if hasattr(df, 'get') else code,
                'similarity_score': quality_score,
                'enhanced_analysis': 'talib_analysis' in channel_result,
                'is_arc_stock': True  # 标记为大弧底股票
            }
            
            # 生成图表（只显示最近半年数据）
            chart_path = generate_uptrend_chart_for_arc(chart_generator, code, df, channel_result)
            if chart_path:
                chart_paths[key] = chart_path
        else:
            # 如果严格检测失败，计算相似度
            similarity_result = analyzer.calculate_channel_similarity(prices, high_prices, low_prices)
            if similarity_result['similarity_score'] > 0.1:  # 只保留有一定相似度的
                similarity_results[code] = {
                    'similarity_result': similarity_result,
                    'prices': prices,
                    'name': df.get('name', code) if hasattr(df, 'get') else code,
                    'similarity_score': similarity_result['similarity_score'],
                    'is_arc_stock': True  # 标记为大弧底股票
                }
        
        # 显示进度
        if (i + 1) % 10 == 0 or (i + 1) == len(stock_data):
            enhanced_count = sum(1 for m in perfect_matches.values() if m.get('enhanced_analysis', False))
            print(f"已分析 {i + 1}/{len(stock_data)} 只股票 - "
                  f"完美匹配: {len(perfect_matches)} (TA-Lib增强: {enhanced_count}), "
                  f"相似匹配: {len(similarity_results)}")
    
    # 如果有完美匹配，按质量评分降序排序后返回
    if perfect_matches:
        # 按质量评分降序排序
        sorted_matches = sorted(perfect_matches.items(), 
                               key=lambda x: x[1]['similarity_score'], 
                               reverse=True)
        perfect_matches = dict(sorted_matches)
        
        enhanced_count = sum(1 for m in perfect_matches.values() if m.get('enhanced_analysis', False))
        print(f"检测到 {len(perfect_matches)} 个完美的上升通道形态 (其中 {enhanced_count} 个经过TA-Lib增强分析)")
        print(f"质量评分范围: {min([m['similarity_score'] for m in perfect_matches.values()]):.3f} - {max([m['similarity_score'] for m in perfect_matches.values()]):.3f}")
        return perfect_matches, chart_paths
    
    # 如果没有完美匹配，返回TOP100相似度最高的
    if similarity_results:
        print(f"未发现完美匹配，从 {len(similarity_results)} 个候选中选择TOP100相似度最高的")
        
        # 按相似度排序，取TOP100
        sorted_results = sorted(similarity_results.items(), 
                               key=lambda x: x[1]['similarity_score'], 
                               reverse=True)
        top_100 = dict(sorted_results[:100])
        
        # 为TOP100生成图表
        top_100_with_charts = {}
        top_100_chart_paths = {}
        
        for i, (code, result) in enumerate(top_100.items()):
            key = f'similar_{code}'
            
            # 创建兼容的channel_result结构用于图表生成
            mock_channel_result = {
                'type': 'similarity_based',
                'similarity_score': result['similarity_score'],
                'recommendation': result['similarity_result']['recommendation'],
                'factors': result['similarity_result']['factors']
            }
            
            top_100_with_charts[key] = {
                'channel_result': mock_channel_result,
                'prices': result['prices'],
                'name': result['name'],
                'similarity_score': result['similarity_score'],
                'is_similarity_match': True,
                'is_arc_stock': True  # 标记为大弧底股票
            }
            
            # 生成相似度图表
            chart_path = generate_similarity_chart(chart_generator, code, 
                                                  stock_data[code], 
                                                  result['similarity_result'])
            if chart_path:
                top_100_chart_paths[key] = chart_path
            
            # 显示进度
            if (i + 1) % 20 == 0:
                print(f"已生成 {i + 1}/100 个相似度图表")
        
        print(f"相似度分析完成，TOP100平均分: {np.mean([r['similarity_score'] for r in top_100.values()]):.3f}")
        return top_100_with_charts, top_100_chart_paths
    
    # 都没有
    print("未发现任何符合条件或具有相似性的上升通道形态")
    return {}, {}

def generate_uptrend_chart_for_arc(chart_generator, code, df, channel_result):
    """为大弧底股票生成上升通道图表（显示完整一年K线图，标注最近上升通道）"""
    try:
        # 使用完整的一年数据（最多52周）
        full_year_weeks = 52
        if len(df) > full_year_weeks:
            df_full_year = df.tail(full_year_weeks).copy()
        else:
            df_full_year = df.copy()
        
        # 调整通道线参数，使其在完整数据中正确显示
        if 'upper_channel' in channel_result and 'lower_channel' in channel_result:
            # 获取原始通道线数据
            original_upper = channel_result['upper_channel']
            original_lower = channel_result['lower_channel']
            
            # 计算通道在完整数据中的位置
            # 假设通道是在最近3个月（约13周）形成的
            channel_duration = original_upper.get('end_idx', 0) - original_upper.get('start_idx', 0)
            if channel_duration == 0:
                channel_duration = 13  # 默认13周
            
            # 在完整数据中，通道应该在最后部分
            full_data_length = len(df_full_year)
            new_channel_start = max(0, full_data_length - channel_duration - 1)
            new_channel_end = full_data_length - 1
            
            # 重新计算截距，使通道线在正确位置显示
            # 计算原始通道线在完整数据开始点的价格值
            original_start_idx_for_full = len(df) - full_data_length  # 完整数据在原始数据中的起始位置
            
            # 使用原始斜率和截距，计算在完整数据起点的价格
            upper_price_at_full_start = (original_upper['slope'] * original_start_idx_for_full + 
                                       original_upper['intercept'])
            lower_price_at_full_start = (original_lower['slope'] * original_start_idx_for_full + 
                                       original_lower['intercept'])
            
            # 重新计算截距，使得在新的索引0点上价格值正确
            new_upper_intercept = upper_price_at_full_start
            new_lower_intercept = lower_price_at_full_start
            
            # 更新通道线参数
            new_upper_channel = {
                'slope': original_upper['slope'],
                'intercept': new_upper_intercept,
                'start_idx': new_channel_start,
                'end_idx': new_channel_end,
                'r2': original_upper.get('r2', 0.8),
                'score': original_upper.get('score', 0.5),
                'fit_quality': original_upper.get('fit_quality', 0.5)
            }
            
            new_lower_channel = {
                'slope': original_lower['slope'],
                'intercept': new_lower_intercept,
                'start_idx': new_channel_start,
                'end_idx': new_channel_end,
                'r2': original_lower.get('r2', 0.8),
                'score': original_lower.get('score', 0.5),
                'fit_quality': original_lower.get('fit_quality', 0.5)
            }
            
            # 更新通道结果
            channel_result['upper_channel'] = new_upper_channel
            channel_result['lower_channel'] = new_lower_channel
            
            # 更新通道质量信息
            if 'channel_quality' in channel_result:
                channel_result['channel_quality']['start_idx'] = new_channel_start
                channel_result['channel_quality']['end_idx'] = new_channel_end
                channel_result['channel_quality']['duration'] = channel_duration
        
        # 生成图表（使用完整一年数据）
        image_path = chart_generator.generate_uptrend_chart(code, df_full_year, channel_result)
        return image_path
        
    except Exception as e:
        print("生成大弧底上升通道图表失败 {}: {}".format(code, str(e)))
        return None

def generate_similarity_chart(chart_generator, code, df, similarity_result):
    """为相似度分析生成图表"""
    try:
        # 创建一个简化的channel_result用于图表生成
        prices = df['close'].values
        
        # 计算基本统计信息
        start_idx = 0
        end_idx = len(prices) - 1
        
        # 计算R²拟合度
        x = np.arange(len(prices))
        try:
            # 确保prices是numpy数组且为float类型
            prices_array = np.array(prices, dtype=np.float64)
            
            # 尝试线性拟合（上升通道通常是线性的）
            coeffs = np.polyfit(x, prices_array, 1)
            y_fit = np.polyval(coeffs, x)
            
            # 计算R²
            ss_res = np.sum((prices_array - y_fit) ** 2)
            ss_tot = np.sum((prices_array - np.mean(prices_array)) ** 2)
            
            if ss_tot > 0:
                r2 = 1 - (ss_res / ss_tot)
                r2 = float(max(0, min(1, r2)))  # 确保R²在合理范围内且为float类型
            else:
                r2 = 0.0
                
        except Exception as e:
            print(f"拟合计算失败 {code}: {e}")
            coeffs = [0, np.mean(prices)]
            r2 = 0.0
        
        # 使用相似度分析的结果创建图表数据
        mock_channel_result = {
            'type': 'similarity_analysis',
            'similarity_score': similarity_result['similarity_score'],
            'recommendation': similarity_result['recommendation'],
            'coeffs': coeffs,
            'r2': r2,
            'start': start_idx,
            'end': end_idx,
            'total_points': len(prices),
            'quality_score': similarity_result['similarity_score'],
            'enhanced_quality_score': similarity_result['similarity_score'],
            'factors': similarity_result['factors'],
            'details': similarity_result['details'],
            # 添加基本的价格信息
            'price_range': {
                'start': prices[0],
                'end': prices[-1],
                'min': np.min(prices),
                'max': np.max(prices)
            },
            # 添加虚拟的通道线数据，避免图表生成错误
            'upper_channel': {
                'slope': coeffs[0],
                'intercept': coeffs[1] + np.std(prices) * 0.5,
                'start_idx': start_idx,
                'end_idx': end_idx
            },
            'lower_channel': {
                'slope': coeffs[0],
                'intercept': coeffs[1] - np.std(prices) * 0.5,
                'start_idx': start_idx,
                'end_idx': end_idx
            },
            # 添加虚拟的通道质量数据
            'channel_quality': {
                'duration': len(prices),
                'channel_width_pct': np.std(prices) / np.mean(prices) * 100 if np.mean(prices) > 0 else 0
            },
            # 添加虚拟的通道特征数据
            'channel_features': {
                'channel_strength': r2,
                'breakout_attempts': 0
            }
        }
        
        # 生成图表
        image_path = chart_generator.generate_uptrend_chart(code, df, mock_channel_result)
        return image_path
        
    except Exception as e:
        print(f"生成相似度图表失败 {code}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='针对大弧底股票进行上升通道分析')
    parser.add_argument('--csv', type=str, default='/Users/kangfei/Downloads/result.csv', help='CSV数据文件路径')
    parser.add_argument('--output', type=str, default='output/uptrend', help='输出目录')
    parser.add_argument('--arc-html', type=str, default='output/arc/arc_analysis.html', help='大弧底分析HTML文件路径')
    parser.add_argument('--max', type=int, default=None, help='最多处理多少只股票（调试用）')
    parser.add_argument('--clear-cache', action='store_true', help='清除缓存，重新处理数据')
    args = parser.parse_args()

    # 设置输出目录
    setup_output_directories(args.output)
    
    # 清除缓存
    clear_cache_if_needed(args.clear_cache)
    
    # 加载和处理数据
    stock_data = load_and_process_data(args.csv, args.max)
    if not stock_data:
        return
    
    # 从大弧底分析中提取股票代码
    arc_stocks = extract_arc_stocks_from_html(args.arc_html)
    
    # 根据大弧底股票过滤数据
    filtered_stock_data = filter_stock_data_by_arc(stock_data, arc_stocks)
    
    if not filtered_stock_data:
        print("没有找到大弧底股票数据，使用原始数据进行上升通道分析")
        filtered_stock_data = stock_data
    
    # 检测形态并生成图表
    results, chart_paths = detect_and_generate_charts(filtered_stock_data, args.output)
    
    if not results:
        print('未检测到任何上升通道形态')
        return
    
    print(f"检测到 {len(results)} 个上升通道形态")
    
    # 生成HTML报告
    html_generator = UptrendHTMLGenerator(output_dir=args.output)
    html_generator.generate_uptrend_html(results, chart_paths)
    
    print('大弧底股票上升通道分析图和HTML已生成，输出目录:', args.output)

if __name__ == '__main__':
    main() 