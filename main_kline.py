#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
from src.core.stock_data_processor import StockDataProcessor
from src.generators.chart_generator import FastChartGenerator
from src.generators.html_generator import StaticHTMLGenerator

def main():
    parser = argparse.ArgumentParser(description='批量生成所有股票的周K线图和index.html')
    parser.add_argument('--csv', type=str, default='/Users/kangfei/Downloads/result.csv', help='CSV数据文件路径')
    parser.add_argument('--output', type=str, default='output', help='输出目录')
    parser.add_argument('--max', type=int, default=None, help='最多处理多少只股票（调试用）')
    args = parser.parse_args()

    csv_file_path = args.csv
    output_dir = args.output
    kline_output_dir = os.path.join(output_dir, 'kline')  # K线页面输出到 output/kline
    kline_img_dir = os.path.join(output_dir, 'kline_images')
    os.makedirs(kline_output_dir, exist_ok=True)
    os.makedirs(kline_img_dir, exist_ok=True)

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

    # 批量生成K线图
    chart_gen = FastChartGenerator(output_dir=kline_img_dir)
    chart_gen.generate_charts_batch(stock_data)

    # 生成静态HTML（只生成HTML，不重复生成图片）
    html_gen = StaticHTMLGenerator(csv_file_path, output_dir=kline_output_dir)
    html_gen.generate_html_only(stock_data, args.max)
    print('全部周K线图和index.html已生成，输出目录:', kline_output_dir)

if __name__ == '__main__':
    main() 