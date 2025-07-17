#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
from src.core.stock_data_processor import StockDataProcessor
from src.analyzers.pattern_analyzer import PatternAnalyzer
from src.generators.arc_chart_generator import ArcChartGenerator
from src.generators.arc_html_generator import ArcHTMLGenerator

def main():
    parser = argparse.ArgumentParser(description='批量检测圆弧底并生成分析图和HTML报告')
    parser.add_argument('--csv', type=str, default='/Users/kangfei/Downloads/result.csv', help='CSV数据文件路径')
    parser.add_argument('--output', type=str, default='output/arc', help='输出目录')
    parser.add_argument('--max', type=int, default=None, help='最多处理多少只股票（调试用）')
    parser.add_argument('--clear-cache', action='store_true', help='清除缓存，重新处理数据')
    args = parser.parse_args()

    csv_file_path = args.csv
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'images'), exist_ok=True)

    # 如果需要清除缓存
    if args.clear_cache:
        import shutil
        cache_dir = "cache"
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            print("缓存已清除")

    # 处理数据 - 与main_kline.py完全一致的方式
    data_processor = StockDataProcessor(csv_file_path)
    if not data_processor.load_data():
        print('数据加载失败:', csv_file_path)
        return
    if not data_processor.process_weekly_data():
        print('数据处理失败')
        return
    stock_data = data_processor.get_all_data()
    if args.max:
        stock_data = dict(list(stock_data.items())[:args.max])

    print(f"开始分析 {len(stock_data)} 只股票的圆弧底形态...")

    # 检测圆弧底和大弧底并生成图表和HTML
    arc_html_gen = ArcHTMLGenerator(output_dir=output_dir)
    arc_results = {}
    major_arc_results = {}
    chart_paths = {}
    analyzer = PatternAnalyzer()
    
    # print("开始检测传统圆弧底形态...")
    # for code, df in stock_data.items():
    #     prices = df['close'].values
    #     # 检测传统圆弧底
    #     arc_result = analyzer.detect_global_arc_bottom(prices)
    #     if arc_result:
    #         arc_results[code] = {
    #             'arc_result': arc_result,
    #             'prices': prices,
    #             'name': df.get('name', code) if hasattr(df, 'get') else code
    #         }
    #         chart_paths[code] = os.path.join(output_dir, 'images', 'global_arc_{}.png'.format(code))
    #         # 生成图表 - 传入完整的DataFrame
    #         ArcChartGenerator(output_dir=os.path.join(output_dir, 'images')).generate_global_arc_chart(code, df, arc_result)
    
    print("开始检测大弧底形态...")
    for code, df in stock_data.items():
        prices = df['close'].values
        # 检测大弧底（初期高位，长期下跌，箱体震荡）
        major_arc_result = analyzer.detect_major_arc_bottom(prices)
        if major_arc_result:
            major_arc_results[code] = {
                'arc_result': major_arc_result,
                'prices': prices,
                'name': df.get('name', code) if hasattr(df, 'get') else code
            }
            major_key = 'major_{}'.format(code)
            chart_paths[major_key] = os.path.join(output_dir, 'images', 'major_arc_{}.png'.format(code))
            # 生成大弧底图表 - 传入完整的DataFrame
            ArcChartGenerator(output_dir=os.path.join(output_dir, 'images')).generate_major_arc_chart(code, df, major_arc_result)
    
    # 合并结果，确保chart_paths键匹配
    all_results = {}
    all_chart_paths = {}
    
    # 添加传统圆弧底结果
    for code, result in arc_results.items():
        all_results[code] = result
        if code in chart_paths:
            all_chart_paths[code] = chart_paths[code]
    
    # 添加大弧底结果，使用不同的键前缀避免冲突
    for code, result in major_arc_results.items():
        major_code = 'major_{}'.format(code)
        all_results[major_code] = result
        if major_code in chart_paths:
            all_chart_paths[major_code] = chart_paths[major_code]
    
    if not all_results:
        print('未检测到任何圆弧底或大弧底形态')
        return
    
    print("检测到 {} 个传统圆弧底，{} 个大弧底".format(len(arc_results), len(major_arc_results)))
    print("总共 {} 个形态，{} 个图表文件".format(len(all_results), len(all_chart_paths)))
    
    arc_html_gen.generate_arc_html(all_results, all_chart_paths)
    print('圆弧底和大弧底分析图和HTML已生成，输出目录:', output_dir)

if __name__ == '__main__':
    main() 