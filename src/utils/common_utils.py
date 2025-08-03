#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import json
import numpy as np
from scipy import stats


def setup_output_directories(output_dir):
    """创建输出目录结构"""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'images'), exist_ok=True)


def clear_cache_if_needed(clear_cache, cache_dir="cache"):
    """清除缓存目录"""
    if clear_cache and os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        print("缓存已清除")


def save_json_with_numpy_support(data, file_path):
    """保存数据为JSON，支持numpy类型转换"""
    with open(file_path, 'w') as f:
        json.dump(data, f, default=lambda x: x.tolist() if hasattr(x, 'tolist') else x)


def generate_similarity_chart(chart_generator, code, df, similarity_result):
    """通用的相似度图表生成函数"""
    try:
        prices = df['close'].values
        
        # 计算基本拟合
        x = np.arange(len(prices))
        prices_array = np.array(prices, dtype=np.float64)
        
        try:
            # 线性拟合
            coeffs = np.polyfit(x, prices_array, 1)
            y_fit = np.polyval(coeffs, x)
            
            # 计算R²
            ss_res = np.sum((prices_array - y_fit) ** 2)
            ss_tot = np.sum((prices_array - np.mean(prices_array)) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
            r2 = float(max(0, min(1, r2)))
        except Exception as e:
            print(f"拟合计算失败 {code}: {e}")
            coeffs = [0, np.mean(prices)]
            r2 = 0.0
        
        # 创建模拟的分析结果
        mock_result = {
            'type': 'similarity_analysis',
            'similarity_score': similarity_result['similarity_score'],
            'recommendation': similarity_result['recommendation'],
            'coeffs': coeffs,
            'r2': r2,
            'start': 0,
            'end': len(prices) - 1,
            'total_points': len(prices),
            'quality_score': similarity_result['similarity_score'],
            'factors': similarity_result['factors'],
            'details': similarity_result['details'],
            'price_range': {
                'start': prices[0],
                'end': prices[-1],
                'min': np.min(prices),
                'max': np.max(prices)
            }
        }
        
        # 生成图表 - 根据图表生成器类型调用相应方法
        if hasattr(chart_generator, 'generate_major_arc_chart'):
            return chart_generator.generate_major_arc_chart(code, df, mock_result)
        elif hasattr(chart_generator, 'generate_uptrend_chart'):
            # 为上升通道添加必要的通道数据
            mock_result.update({
                'upper_channel': {
                    'slope': coeffs[0],
                    'intercept': coeffs[1] + np.std(prices) * 0.5,
                    'start_idx': 0,
                    'end_idx': len(prices) - 1
                },
                'lower_channel': {
                    'slope': coeffs[0],
                    'intercept': coeffs[1] - np.std(prices) * 0.5,
                    'start_idx': 0,
                    'end_idx': len(prices) - 1
                },
                'channel_quality': {
                    'duration': len(prices),
                    'channel_width_pct': np.std(prices) / np.mean(prices) * 100 if np.mean(prices) > 0 else 0
                },
                'channel_features': {
                    'channel_strength': r2,
                    'breakout_attempts': 0
                }
            })
            return chart_generator.generate_uptrend_chart(code, df, mock_result)
        else:
            return None
            
    except Exception as e:
        print(f"生成相似度图表失败 {code}: {e}")
        return None


def load_and_process_data(csv_file_path, max_stocks=None):
    """通用的数据加载和处理函数"""
    from src.core.stock_data_processor import StockDataProcessor
    
    data_processor = StockDataProcessor(csv_file_path)
    
    if not data_processor.load_data():
        print('数据加载失败:', csv_file_path)
        return None
        
    if not data_processor.process_weekly_data():
        print('数据处理失败')
        return None
        
    stock_data = data_processor.get_all_data()
    
    if max_stocks:
        stock_data = dict(list(stock_data.items())[:max_stocks])
    
    return stock_data


def create_mock_arc_result(similarity_result, prices):
    """创建模拟的大弧底结果结构"""
    start_idx = 0
    end_idx = len(prices) - 1
    
    # 计算二次拟合
    x = np.arange(len(prices))
    try:
        prices_array = np.array(prices, dtype=np.float64)
        coeffs = np.polyfit(x, prices_array, 2)
        y_fit = np.polyval(coeffs, x)
        
        ss_res = np.sum((prices_array - y_fit) ** 2)
        ss_tot = np.sum((prices_array - np.mean(prices_array)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        r2 = float(max(0, min(1, r2)))
    except:
        coeffs = [0, 0, np.mean(prices)]
        r2 = 0.0
    
    return {
        'type': 'similarity_based',
        'similarity_score': similarity_result['similarity_score'],
        'recommendation': similarity_result['recommendation'],
        'factors': similarity_result['factors'],
        'coeffs': coeffs,
        'r2': r2,
        'start': start_idx,
        'end': end_idx,
        'total_points': len(prices),
        'quality_score': similarity_result['similarity_score'],
        'details': similarity_result['details'],
        'price_range': {
            'start': prices[0],
            'end': prices[-1],
            'min': np.min(prices),
            'max': np.max(prices)
        }
    }