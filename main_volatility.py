#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
from datetime import datetime, timedelta
from src.core.stock_data_processor import StockDataProcessor
from src.generators.volatility_html_generator import VolatilityHTMLGenerator
from config.settings import DEFAULT_CSV_PATH

def main():
    parser = argparse.ArgumentParser(description='股票波动率和波幅分析')
    parser.add_argument('--csv', type=str, default=DEFAULT_CSV_PATH, help='CSV数据文件路径')
    parser.add_argument('--output', type=str, default='output/volatility', help='输出目录')
    parser.add_argument('--stocks', type=str, help='要分析的股票代码，用逗号分隔')
    parser.add_argument('--start-date', type=str, help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--max', type=int, default=10000, help='最多分析多少只股票')
    args = parser.parse_args()

    csv_file_path = args.csv
    output_dir = args.output
    
    # 检查数据文件是否存在
    if not os.path.exists(csv_file_path):
        print(f'数据文件不存在: {csv_file_path}')
        return

    print(f'开始加载数据: {csv_file_path}')
    
    # 处理数据
    data_processor = StockDataProcessor(csv_file_path)
    if not data_processor.load_data():
        print('数据加载失败:', csv_file_path)
        return
    if not data_processor.process_weekly_data():
        print('数据处理失败')
        return
    
    stock_data = data_processor.get_all_data()
    print(f'成功加载 {len(stock_data)} 只股票的数据')

    # 确定要分析的股票
    selected_stocks = []
    if args.stocks:
        # 用户指定了股票代码
        selected_stocks = [code.strip() for code in args.stocks.split(',')]
        # 过滤掉不存在的股票
        selected_stocks = [code for code in selected_stocks if code in stock_data]
        print(f'用户指定了 {len(selected_stocks)} 只股票')
    else:
        # 使用前N只股票
        selected_stocks = list(stock_data.keys())[:args.max]
        print(f'使用前 {len(selected_stocks)} 只股票进行分析')

    if not selected_stocks:
        print('没有可分析的股票')
        return

    # 设置默认时间范围
    start_date = args.start_date
    end_date = args.end_date
    
    if not start_date:
        # 默认使用最近2年的数据
        end_date_obj = datetime.now()
        start_date_obj = end_date_obj - timedelta(days=730)
        start_date = start_date_obj.strftime('%Y-%m-%d')
        print(f'使用默认开始日期: {start_date}')
    
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
        print(f'使用默认结束日期: {end_date}')

    print(f'分析时间范围: {start_date} 至 {end_date}')
    print(f'开始分析 {len(selected_stocks)} 只股票的波动率和波幅...')

    # 创建HTML生成器
    html_generator = VolatilityHTMLGenerator(output_dir=output_dir)
    
    # 生成波动率分析HTML
    html_path = html_generator.generate_volatility_html(
        stock_data_dict=stock_data,
        selected_stocks=selected_stocks,
        start_date=start_date,
        end_date=end_date
    )
    
    print(f'波动率分析完成！')
    print(f'HTML报告已生成: {html_path}')
    print(f'输出目录: {output_dir}')

if __name__ == '__main__':
    main() 