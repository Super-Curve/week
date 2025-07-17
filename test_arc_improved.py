#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
from src.analyzers.pattern_analyzer import PatternAnalyzer
from src.core.stock_data_processor import StockDataProcessor

def test_improved_arc_detection():
    """测试改进后的圆弧底检测算法"""
    
    # 1. 加载数据
    csv_file_path = '/Users/kangfei/Downloads/result.csv'
    data_processor = StockDataProcessor(csv_file_path)
    if not data_processor.load_data():
        print("数据加载失败")
        return
    if not data_processor.process_weekly_data():
        print("数据处理失败")
        return
    stock_data = data_processor.get_all_data()

    # 2. 初始化分析器
    analyzer = PatternAnalyzer()

    # 3. 测试检测
    arc_results = {}
    total_tested = 0
    debug_count = 0
    
    for code, df in stock_data.items():
        total_tested += 1
        if total_tested > 500:  # 测试前500只股票
            break
            
        prices = df['close'].values
        
        # 添加一些调试信息
        if debug_count < 5:
            print(f"\n调试 {code}: 数据点数={len(prices)}, 价格范围={prices.min():.2f}-{prices.max():.2f}")
            debug_count += 1
        
        arc_result = analyzer.detect_global_arc_bottom(prices)
        
        if arc_result:
            arc_results[code] = {
                'arc_result': arc_result,
                'prices': prices,
                'name': df.get('name', code)
            }
            
            # 打印详细信息
            stages = arc_result['stages']
            print(f"\n=== {code} {df.get('name', code)} ===")
            print(f"R²: {arc_result['r2']:.3f}")
            print(f"质量评分: {arc_result['quality_score']:.1f}")
            print(f"最低点: {arc_result['min_point']}")
            
            for stage_name in ['decline', 'flat', 'rise']:
                if stage_name in stages and stages[stage_name]:
                    stage = stages[stage_name]
                    if stage_name == 'decline':
                        desc = '严重下降'
                    elif stage_name == 'flat':
                        desc = '横盘筑底'
                    elif stage_name == 'rise':
                        desc = '轻微上涨'
                    else:
                        desc = stage_name
                    
                    print(f"{desc}: {stage['price_change_pct']:+.1f}% ({stage['duration']}周)")

    print(f"\n=== 检测结果 ===")
    print(f"测试股票数: {total_tested}")
    print(f"检测到圆弧底: {len(arc_results)}")
    print(f"检测率: {len(arc_results)/total_tested*100:.1f}%")
    
    # 如果检测率太低，尝试放宽一些参数
    if len(arc_results) < 5:
        print("\n=== 尝试放宽参数 ===")
        test_with_relaxed_params(stock_data, analyzer)

def test_with_relaxed_params(stock_data, analyzer):
    """使用放宽的参数测试"""
    arc_results = {}
    total_tested = 0
    
    for code, df in stock_data.items():
        total_tested += 1
        if total_tested > 200:
            break
            
        prices = df['close'].values
        # 使用更宽松的参数
        arc_result = analyzer.detect_global_arc_bottom(prices, min_points=15, r2_threshold=0.6)
        
        if arc_result:
            arc_results[code] = {
                'arc_result': arc_result,
                'prices': prices,
                'name': df.get('name', code)
            }
            
            stages = arc_result['stages']
            print(f"\n=== {code} {df.get('name', code)} (放宽参数) ===")
            print(f"R²: {arc_result['r2']:.3f}")
            print(f"质量评分: {arc_result['quality_score']:.1f}")
            
            for stage_name in ['decline', 'flat', 'rise']:
                if stage_name in stages and stages[stage_name]:
                    stage = stages[stage_name]
                    if stage_name == 'decline':
                        desc = '严重下降'
                    elif stage_name == 'flat':
                        desc = '横盘筑底'
                    elif stage_name == 'rise':
                        desc = '轻微上涨'
                    else:
                        desc = stage_name
                    
                    print(f"{desc}: {stage['price_change_pct']:+.1f}% ({stage['duration']}周)")

    print(f"\n=== 放宽参数后的检测结果 ===")
    print(f"测试股票数: {total_tested}")
    print(f"检测到圆弧底: {len(arc_results)}")
    print(f"检测率: {len(arc_results)/total_tested*100:.1f}%")

if __name__ == "__main__":
    test_improved_arc_detection() 