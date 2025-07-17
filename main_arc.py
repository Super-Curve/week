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
    args = parser.parse_args()

    csv_file_path = args.csv
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'images'), exist_ok=True)

    # 处理数据
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

    # 检测圆弧底并生成图表和HTML
    arc_html_gen = ArcHTMLGenerator(output_dir=output_dir)
    arc_results = {}
    chart_paths = {}
    analyzer = PatternAnalyzer()
    for code, df in stock_data.items():
        prices = df['close'].values
        arc_result = analyzer.detect_global_arc_bottom(prices)
        if arc_result:
            arc_results[code] = {
                'arc_result': arc_result,
                'prices': prices,
                'name': df.get('name', code)
            }
            chart_paths[code] = os.path.join(output_dir, 'images', f'global_arc_{code}.png')
            # 生成图表
            ArcChartGenerator(output_dir=os.path.join(output_dir, 'images')).generate_global_arc_chart(code, prices, arc_result)
    if not arc_results:
        print('未检测到任何圆弧底形态')
        return
    arc_html_gen.generate_arc_html(arc_results, chart_paths)
    print('圆弧底分析图和HTML已生成，输出目录:', output_dir)

if __name__ == '__main__':
    main() 