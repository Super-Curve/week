#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
from src.core.stock_data_processor import StockDataProcessor
from src.similarity.image_similarity import find_similar_stocks
from src.generators.chart_generator import FastChartGenerator
from src.utils.html_generator import SimilarityHTMLGenerator

def main():
    parser = argparse.ArgumentParser(description='K线图像相似度分析')
    parser.add_argument('--csv', type=str, default='/Users/kangfei/Downloads/result.csv', help='CSV数据文件路径')
    parser.add_argument('--imgdir', type=str, default='output/kline_images', help='K线图图片目录')
    parser.add_argument('--target', type=str, required=True, help='目标股票代码')
    parser.add_argument('--top', type=int, default=10, help='返回最相似的前N只股票')
    parser.add_argument('--force-regenerate', action='store_true', help='强制重新生成所有图片')
    args = parser.parse_args()

    csv_file_path = args.csv
    kline_img_dir = args.imgdir
    target_code = args.target
    top_n = args.top
    force_regenerate = args.force_regenerate
    os.makedirs(kline_img_dir, exist_ok=True)

    # 检查目标图片是否存在
    target_img_path = os.path.join(kline_img_dir, f'{target_code}.png')
    if not os.path.exists(target_img_path):
        print(f'目标股票图片不存在: {target_img_path}')
        print('需要先生成K线图，请运行: python main_kline.py')
        return

    # 检查是否需要生成图片
    existing_images = [f for f in os.listdir(kline_img_dir) if f.endswith('.png')]
    if force_regenerate or len(existing_images) < 100:  # 如果图片数量太少，重新生成
        print('检测到图片数量不足，开始生成K线图...')
        # 处理数据
        data_processor = StockDataProcessor(csv_file_path)
        if not data_processor.load_data():
            print('数据加载失败:', csv_file_path)
            return
        if not data_processor.process_weekly_data():
            print('数据处理失败')
            return
        stock_data = data_processor.get_all_data()

        # 生成所有K线图
        chart_gen = FastChartGenerator(output_dir=kline_img_dir)
        chart_gen.generate_charts_batch(stock_data)
    else:
        print(f'使用现有图片目录: {kline_img_dir} (共{len(existing_images)}张图片)')

    # 调用相似度分析
    result = find_similar_stocks(target_code, kline_img_dir, top_n=top_n)
    
    if not result:
        print(f'未找到与 {target_code} 相似的股票')
        return
    
    print(f'与 {target_code} 最相似的前{top_n}只股票:')
    for code, score, img_path in result:
        print(f'{code}\t相似度: {score:.4f}\t图片: {img_path}')

    # 生成HTML报告
    output_dir = 'output/similarity'
    os.makedirs(output_dir, exist_ok=True)
    
    html_generator = SimilarityHTMLGenerator(output_dir)
    html_path = html_generator.generate_similarity_report(
        target_code=target_code,
        similar_stocks=result,
        target_img_path=target_img_path
    )
    
    print(f'\n相似度分析HTML报告已生成: {html_path}')

if __name__ == '__main__':
    main() 