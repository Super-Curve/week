#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
import shutil
from src.core.stock_data_processor import StockDataProcessor
from src.analyzers.pattern_analyzer import PatternAnalyzer
from src.generators.arc_chart_generator import ArcChartGenerator
from src.generators.arc_html_generator import ArcHTMLGenerator
import numpy as np

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

def detect_and_generate_charts(stock_data, output_dir):
    """Detect major arc bottom patterns and generate charts, return TOP100 if no perfect matches"""
    analyzer = PatternAnalyzer()
    chart_generator = ArcChartGenerator(output_dir=os.path.join(output_dir, 'images'))
    
    perfect_matches = {}
    similarity_results = {}
    chart_paths = {}
    
    print(f"Starting analysis of {len(stock_data)} stocks for major arc bottom patterns...")
    print(f"TA-Lib available: {analyzer.talib_available}")
    
    for i, (code, df) in enumerate(stock_data.items()):
        prices = df['close'].values
        
        # 准备TA-Lib增强检测所需的数据
        high_prices = df['high'].values if 'high' in df.columns else None
        low_prices = df['low'].values if 'low' in df.columns else None
        volume = df['volume'].values if 'volume' in df.columns else None
        
        # 首先尝试TA-Lib增强的大弧底检测
        if analyzer.talib_available and high_prices is not None and low_prices is not None:
            arc_result = analyzer.detect_major_arc_bottom_enhanced(
                prices, high_prices, low_prices, volume
            )
        else:
            # 回退到基础检测
            arc_result = analyzer.detect_major_arc_bottom(prices)
        
        if arc_result:
            # 使用统一的键格式
            key = f'major_{code}'
            
            # 获取质量评分（优先使用增强评分）
            quality_score = arc_result.get('enhanced_quality_score', arc_result.get('quality_score', 0.5))
            
            perfect_matches[key] = {
                'arc_result': arc_result,
                'prices': prices,
                'name': df.get('name', code) if hasattr(df, 'get') else code,
                'similarity_score': quality_score,
                'enhanced_analysis': 'talib_analysis' in arc_result
            }
            
            # 生成图表
            chart_path = chart_generator.generate_major_arc_chart(code, df, arc_result)
            if chart_path:
                chart_paths[key] = chart_path
        else:
            # 如果严格检测失败，计算相似度
            similarity_result = analyzer.calculate_arc_similarity(prices)
            if similarity_result['similarity_score'] > 0.1:  # 只保留有一定相似度的
                similarity_results[code] = {
                    'similarity_result': similarity_result,
                    'prices': prices,
                    'name': df.get('name', code) if hasattr(df, 'get') else code,
                    'similarity_score': similarity_result['similarity_score']
                }
        
        # 显示进度
        if (i + 1) % 500 == 0 or (i + 1) == len(stock_data):
            enhanced_count = sum(1 for m in perfect_matches.values() if m.get('enhanced_analysis', False))
            print(f"已分析 {i + 1}/{len(stock_data)} 只股票 - "
                  f"完美匹配: {len(perfect_matches)} (TA-Lib增强: {enhanced_count}), "
                  f"相似匹配: {len(similarity_results)}")
    
    # 如果有完美匹配，优先返回
    if perfect_matches:
        enhanced_count = sum(1 for m in perfect_matches.values() if m.get('enhanced_analysis', False))
        print(f"检测到 {len(perfect_matches)} 个完美的大弧底形态 (其中 {enhanced_count} 个经过TA-Lib增强分析)")
        return perfect_matches, chart_paths
    
    # 如果没有完美匹配，返回TOP100相似度最高的
    if similarity_results:
        print(f"未发现完美匹配，从 {len(similarity_results)} 个候选中选择TOP100相似度最高的")
        
        # 按相似度排序，取TOP100
        sorted_results = sorted(similarity_results.items(), 
                               key=lambda x: x[1]['similarity_score'], 
                               reverse=True)
        top_100 = dict(sorted_results[:200])
        
        # 为TOP100生成图表
        top_100_with_charts = {}
        top_100_chart_paths = {}
        
        for i, (code, result) in enumerate(top_100.items()):
            key = f'similar_{code}'
            
            # 创建兼容的arc_result结构用于图表生成
            mock_arc_result = {
                'type': 'similarity_based',
                'similarity_score': result['similarity_score'],
                'recommendation': result['similarity_result']['recommendation'],
                'factors': result['similarity_result']['factors']
            }
            
            top_100_with_charts[key] = {
                'arc_result': mock_arc_result,
                'prices': result['prices'],
                'name': result['name'],
                'similarity_score': result['similarity_score'],
                'is_similarity_match': True
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
    print("未发现任何符合条件或具有相似性的大弧底形态")
    return {}, {}

def generate_similarity_chart(chart_generator, code, df, similarity_result):
    """为相似度分析生成图表"""
    try:
        # 创建一个简化的arc_result用于图表生成
        prices = df['close'].values
        
        # 计算基本统计信息
        start_idx = 0
        end_idx = len(prices) - 1
        
        # 计算R²拟合度
        x = np.arange(len(prices))
        try:
            # 确保prices是numpy数组且为float类型
            prices_array = np.array(prices, dtype=np.float64)
            
            # 尝试二次拟合
            coeffs = np.polyfit(x, prices_array, 2)
            y_fit = np.polyval(coeffs, x)
            
            # 计算R²
            ss_res = np.sum((prices_array - y_fit) ** 2)
            ss_tot = np.sum((prices_array - np.mean(prices_array)) ** 2)
            
            if ss_tot > 0:
                r2 = 1 - (ss_res / ss_tot)
                r2 = float(max(0, min(1, r2)))  # 确保R²在合理范围内且为float类型
            else:
                r2 = 0.0
                
            # 如果二次拟合效果不好，尝试线性拟合
            if r2 < 0.1:
                coeffs_linear = np.polyfit(x, prices_array, 1)
                y_fit_linear = np.polyval(coeffs_linear, x)
                ss_res_linear = np.sum((prices_array - y_fit_linear) ** 2)
                
                if ss_tot > 0:
                    r2_linear = 1 - (ss_res_linear / ss_tot)
                    if r2_linear > r2:
                        r2 = float(max(0, min(1, r2_linear)))
                        coeffs = np.append(coeffs_linear, 0)  # 转换为二次形式
                        
        except Exception as e:
            print(f"拟合计算失败 {code}: {e}")
            coeffs = [0, 0, np.mean(prices)]
            r2 = 0.0
        
        # 使用相似度分析的结果创建图表数据
        mock_arc_result = {
            'type': 'similarity_analysis',
            'similarity_score': similarity_result['similarity_score'],
            'recommendation': similarity_result['recommendation'],
            'coeffs': coeffs,
            'r2': r2,
            'start': start_idx,
            'end': end_idx,
            'total_points': len(prices),
            'quality_score': similarity_result['similarity_score'],
            'factors': similarity_result['factors'],
            'details': similarity_result['details'],
            # 添加基本的价格信息
            'price_range': {
                'start': prices[0],
                'end': prices[-1],
                'min': np.min(prices),
                'max': np.max(prices)
            }
        }
        
        # 生成图表
        image_path = chart_generator.generate_major_arc_chart(code, df, mock_arc_result)
        return image_path
        
    except Exception as e:
        print(f"生成相似度图表失败 {code}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='批量检测圆弧底并生成分析图和HTML报告')
    parser.add_argument('--csv', type=str, default='/Users/kangfei/Downloads/result.csv', help='CSV数据文件路径')
    parser.add_argument('--output', type=str, default='output/arc', help='输出目录')
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
    
    # 检测形态并生成图表
    results, chart_paths = detect_and_generate_charts(stock_data, args.output)
    
    if not results:
        print('未检测到任何大弧底形态')
        return
    
    print(f"检测到 {len(results)} 个大弧底形态")
    
    # 生成HTML报告
    html_generator = ArcHTMLGenerator(output_dir=args.output)
    html_generator.generate_arc_html(results, chart_paths)
    
    print('大弧底分析图和HTML已生成，输出目录:', args.output)

if __name__ == '__main__':
    main() 