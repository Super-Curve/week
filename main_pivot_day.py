#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
最近三个月（日频）高低点识别入口

复用企业级高低点分析器（ZigZag+ATR），从数据库的 `history_day_data` 加载最近N天日线，
默认仅处理 ARC TOP≤200（独立小集合缓存），输出到 `output/pivot_day/` 并生成 HTML 报告。
"""

import os
import argparse
from src.analyzers.advanced_pivot_analyzer import EnterprisesPivotAnalyzer
from src.generators.pivot_chart_generator import PivotChartGenerator
from src.generators.pivot_html_generator import PivotHTMLGenerator
from src.utils.common_utils import (
    setup_output_directories, clear_cache_if_needed,
    load_recent_daily_data
)


def analyze_pivots_day(stock_data_dict, max_stocks=None, sensitivity='balanced'):
    analyzer = EnterprisesPivotAnalyzer()
    pivot_results = {}
    count = 0
    for code, df in stock_data_dict.items():
        if max_stocks and count >= max_stocks:
            break
        if len(df) < 30:
            continue
        try:
            res = analyzer.detect_pivot_points(df, method='zigzag_atr', sensitivity=sensitivity, frequency='daily')
            if res and (len(res.get('filtered_pivot_highs', [])) + len(res.get('filtered_pivot_lows', [])) > 0):
                pivot_results[code] = res
                count += 1
        except Exception as e:
            print(f"分析 {code} 失败: {e}")
    return pivot_results


def generate_charts_and_html_day(stock_data_dict, pivot_results, output_dir):
    chart_gen = PivotChartGenerator(output_dir=os.path.join(output_dir, 'images'), frequency_label='日K线图（近3个月）')
    print("开始生成图表（日频）...")
    chart_paths = chart_gen.generate_charts_batch(stock_data_dict, pivot_results)
    if not chart_paths:
        return None
    html_gen = PivotHTMLGenerator(output_dir=output_dir)
    # 标题后缀标注“日频”在页面头部，简单做法：在目录名上区分
    html_path = html_gen.generate_pivot_html(pivot_results, chart_paths, stock_names=None)
    return html_path


def main():
    parser = argparse.ArgumentParser(description='最近三个月（日频）高低点识别')
    parser.add_argument('--output', type=str, default='output/pivot_day', help='输出目录')
    parser.add_argument('--max', type=int, default=None, help='最多处理多少只股票（调试用）')
    parser.add_argument('--days', type=int, default=90, help='最近N天')
    parser.add_argument('--sensitivity', choices=['conservative', 'balanced', 'aggressive'], default='balanced')
    parser.add_argument('--clear-cache', action='store_true', help='清除缓存，重新处理数据')
    args = parser.parse_args()

    setup_output_directories(args.output)
    clear_cache_if_needed(args.clear_cache)

    # 加载最近 N 天日线（默认 ARC TOP 小集合缓存）
    daily_data = load_recent_daily_data(max_stocks=args.max, days=args.days, use_arc_top=True)
    if not daily_data:
        print('未加载到日线数据')
        return

    # 识别高低点
    pivots = analyze_pivots_day(daily_data, max_stocks=args.max, sensitivity=args.sensitivity)
    if not pivots:
        print('未识别到有效的高低点')
        return

    # 生成图表与 HTML
    html_path = generate_charts_and_html_day(daily_data, pivots, args.output)
    if not html_path:
        print('HTML 生成失败')
        return

    print(f'日频高低点分析完成，HTML: {html_path}')

    # 生成/更新首页
    try:
        from main_pivot import create_main_navigation
        create_main_navigation()
    except Exception as e:
        print(f"主页更新失败: {e}")


if __name__ == '__main__':
    main()


