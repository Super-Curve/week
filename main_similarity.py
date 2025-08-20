#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K线图像相似度入口（pHash）

说明：
- 使用 `output/kline_images/` 下的周K线图片，通过 pHash 计算与目标股票的相似度，输出最相似列表与简单 HTML 报告。
- 若图库图片数量不足，会自动触发生成流程（数据库周线 -> 图片）。
"""

import os
import sys
import argparse
from src.similarity.image_similarity import find_similar_stocks
from src.generators.chart_generator import FastChartGenerator
from src.utils.common_utils import load_and_process_data

def main():
    parser = argparse.ArgumentParser(description='K线图像相似度分析')
    parser.add_argument('--imgdir', type=str, default='output/kline_images', help='K线图图片目录')
    parser.add_argument('--target', type=str, required=True, help='目标股票代码')
    parser.add_argument('--top', type=int, default=10, help='返回最相似的前N只股票')
    parser.add_argument('--force-regenerate', action='store_true', help='强制重新生成所有图片')
    args = parser.parse_args()

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
        # 处理数据 - 使用数据库数据源
        stock_data = load_and_process_data()
        if not stock_data:
            return

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

    # 生成HTML报告（暂时简化）
    output_dir = 'output/similarity'
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成简单的HTML报告
    html_path = os.path.join(output_dir, 'index.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(f'''<!DOCTYPE html>
<html>
<head>
    <title>相似度分析 - {target_code}</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .stock-item {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; }}
        .similarity-score {{ color: #007bff; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>与 {target_code} 最相似的前{top_n}只股票</h1>
    <div class="target-stock">
        <h2>目标股票: {target_code}</h2>
        <img src="../kline_images/{target_code}.png" alt="{target_code}" style="max-width: 400px;">
    </div>
    <h2>相似股票列表:</h2>
''')
        
        for i, (code, score, img_path) in enumerate(result, 1):
            f.write(f'''    <div class="stock-item">
        <h3>{i}. {code} <span class="similarity-score">(相似度: {score:.4f})</span></h3>
        <img src="../kline_images/{code}.png" alt="{code}" style="max-width: 400px;">
    </div>
''')
        
        f.write('''</body>
</html>''')
    
    print(f'\n相似度分析HTML报告已生成: {html_path}')

if __name__ == '__main__':
    main() 