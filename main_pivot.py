#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业级高低点分析主程序
融合顶级量化交易技术的智能转折点识别系统

技术特色：
- 分形维度分析：基于分形几何的转折点识别
- 统计显著性验证：使用统计学方法验证转折点
- 机器学习增强：自适应异常检测算法
- 多时间框架确认：确保不同时间尺度的一致性
- 市场微观结构：基于成交量和价格行为分析
- 动态阈值调整：基于市场状态的自适应阈值
"""

import os
import json
import argparse
from src.core.stock_data_processor import StockDataProcessor
from src.analyzers.advanced_pivot_analyzer import EnterprisesPivotAnalyzer
from src.generators.pivot_chart_generator import PivotChartGenerator
from src.generators.pivot_html_generator import PivotHTMLGenerator
from src.utils.common_utils import setup_output_directories, clear_cache_if_needed


def load_arc_stocks_from_json(json_path):
    """从大弧底分析结果JSON文件中加载股票代码列表"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            arc_stocks = json.load(f)
        print(f"从大弧底分析结果中加载了 {len(arc_stocks)} 只股票")
        return arc_stocks
    except FileNotFoundError:
        print(f"错误: 大弧底分析结果文件不存在: {json_path}")
        print("请先运行 main_arc.py 生成大弧底分析结果")
        return []
    except json.JSONDecodeError as e:
        print(f"错误: 无法解析JSON文件: {e}")
        return []


def filter_stock_data_by_arc_results(stock_data_dict, arc_stocks):
    """根据大弧底分析结果过滤股票数据"""
    filtered_data = {}
    missing_stocks = []
    
    for code in arc_stocks:
        if code in stock_data_dict:
            filtered_data[code] = stock_data_dict[code]
        else:
            missing_stocks.append(code)
    
    if missing_stocks:
        print(f"警告: {len(missing_stocks)} 只大弧底股票在数据集中未找到")
        if len(missing_stocks) <= 10:
            print(f"缺失的股票: {missing_stocks}")
    
    print(f"成功过滤出 {len(filtered_data)} 只大弧底股票用于高低点分析")
    return filtered_data


def analyze_pivot_points(stock_data_dict, max_stocks=None, method='enterprise_ensemble', sensitivity='balanced'):
    """
    企业级高低点分析 - 使用统一的企业级分析器
    
    Args:
        stock_data_dict: 股票数据字典
        max_stocks: 最大分析股票数量
        method: 检测方法
            - 'enterprise_ensemble': 企业级集成方法（推荐）
            - 'fractal_dimension': 分形维度分析
            - 'statistical_significance': 统计显著性验证
            - 'adaptive_ml': 自适应机器学习
            - 'microstructure': 市场微观结构分析
        sensitivity: 敏感度 ['conservative', 'balanced', 'aggressive']
    """
    print("=" * 60)
    print("🚀 启动企业级高低点分析系统")
    print(f"📊 分析方法: {method}")
    print(f"🎯 敏感度: {sensitivity}")
    print("=" * 60)
    
    # 创建企业级分析器
    analyzer = EnterprisesPivotAnalyzer()
    
    pivot_results = {}
    total_stocks = len(stock_data_dict)
    analyzed_count = 0
    
    print(f"\n开始分析 {total_stocks} 只股票的高低点...")
    
    for i, (code, data) in enumerate(stock_data_dict.items()):
        if max_stocks and analyzed_count >= max_stocks:
            break
        
        try:
            # 数据长度检查
            if len(data) < 30:
                print(f"⏭️  跳过 {code}: 数据不足（仅 {len(data)} 周，至少需要30周）")
                continue
            
            # 使用企业级分析器进行检测
            print(f"🔍 分析 {code}...")
            pivot_result = analyzer.detect_pivot_points(
                data, 
                method=method,
                sensitivity=sensitivity
            )
            
            if pivot_result and pivot_result.get('filtered_pivot_highs') is not None:
                # 检查是否识别到有效的高低点
                total_pivots = (len(pivot_result.get('filtered_pivot_highs', [])) + 
                              len(pivot_result.get('filtered_pivot_lows', [])))
                
                if total_pivots > 0:
                    pivot_results[code] = pivot_result
                    analyzed_count += 1
                    
                    # 显示分析结果摘要
                    accuracy = pivot_result.get('accuracy_score', 0)
                    quality_grade = pivot_result.get('enterprise_quality', {}).get('quality_grade', 'Unknown')
                    print(f"✅ {code}: {total_pivots} 个转折点, 质量: {quality_grade} ({accuracy:.1%})")
                else:
                    print(f"⚠️  跳过 {code}: 未识别到有效的高低点")
            else:
                print(f"❌ 跳过 {code}: 高低点分析失败")
        
        except Exception as e:
            print(f"❌ 分析 {code} 时出错: {e}")
            continue
        
        # 显示进度
        if (i + 1) % 10 == 0:
            progress = ((i + 1) / total_stocks) * 100
            print(f"\n📈 进度报告: {i + 1}/{total_stocks} 只股票 ({progress:.1f}%) - 有效分析 {analyzed_count} 只")
    
    print("\n" + "=" * 60)
    print(f"✅ 企业级高低点分析完成!")
    print(f"📊 成功分析: {analyzed_count} 只股票")
    print(f"🎯 使用方法: {method}")
    print(f"⚙️  敏感度: {sensitivity}")
    print("=" * 60)
    
    return pivot_results


def generate_charts_and_html(stock_data_dict, pivot_results, output_dir):
    """生成图表和HTML页面"""
    
    # 创建图表生成器
    chart_generator = PivotChartGenerator(
        output_dir=os.path.join(output_dir, 'images')
    )
    
    # 批量生成图表
    print("开始生成高低点图表...")
    chart_paths = chart_generator.generate_charts_batch(
        stock_data_dict, pivot_results
    )
    
    if not chart_paths:
        print("错误: 没有生成任何图表")
        return None
    
    # 生成HTML页面
    print("开始生成HTML页面...")
    html_generator = PivotHTMLGenerator(output_dir=output_dir)
    
    # 可以在这里添加股票名称映射，暂时使用股票代码
    html_path = html_generator.generate_pivot_html(
        pivot_results, chart_paths, stock_names=None
    )
    
    return html_path


def save_analysis_results(pivot_results, output_dir):
    """保存分析结果到JSON文件"""
    results_file = os.path.join(output_dir, 'pivot_analysis_results.json')
    
    # 准备保存的数据（移除numpy数组，只保留基本信息）
    save_data = {}
    for code, result in pivot_results.items():
        save_data[code] = {
            'accuracy_score': result.get('accuracy_score', 0),
            'total_periods': result.get('total_periods', 0),
            'filtered_pivot_highs_count': len(result.get('filtered_pivot_highs', [])),
            'filtered_pivot_lows_count': len(result.get('filtered_pivot_lows', [])),
            'filter_effectiveness': result.get('filter_effectiveness', {}),
            'analysis_description': result.get('analysis_description', {})
        }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    print(f"分析结果已保存到: {results_file}")


def create_navigation_integration():
    """创建导航集成，更新主index.html文件"""
    main_index_path = "output/index.html"
    
    # 检查主导航文件是否存在
    if not os.path.exists(main_index_path):
        print("主导航文件不存在，创建新的导航页面...")
        create_main_navigation()
    else:
        print("主导航文件已存在，建议手动添加高低点分析链接")
        print("请在 output/index.html 中添加:")
        print('<a href="pivot/index.html">高低点分析</a>')


def create_main_navigation():
    """创建主导航页面"""
    navigation_html = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A股技术分析平台</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            margin: 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 3rem;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 600px;
        }
        
        h1 {
            color: #2c3e50;
            margin-bottom: 2rem;
            font-size: 2.5rem;
        }
        
        .nav-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-top: 2rem;
        }
        
        .nav-link {
            display: block;
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            text-decoration: none;
            padding: 1.5rem;
            border-radius: 15px;
            transition: all 0.3s ease;
            font-weight: bold;
        }
        
        .nav-link:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(52, 152, 219, 0.3);
        }
        
        .nav-link.new {
            background: linear-gradient(135deg, #e74c3c, #c0392b);
        }
        
        .nav-link.new:hover {
            box-shadow: 0 10px 30px rgba(231, 76, 60, 0.3);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 A股技术分析平台</h1>
        <p>专业级量化分析工具集</p>
        
        <div class="nav-grid">
            <a href="arc/index.html" class="nav-link">
                📊 大弧底分析
            </a>
            <a href="uptrend/index.html" class="nav-link">
                📈 上升通道分析
            </a>
            <a href="kline/index.html" class="nav-link">
                📋 K线图展示
            </a>
            <a href="volatility/index.html" class="nav-link">
                📉 波动率分析
            </a>
            <a href="similarity/index.html" class="nav-link">
                🔍 相似度分析
            </a>
            <a href="pivot/index.html" class="nav-link new">
                🎯 高低点分析 <span style="font-size: 0.8em;">[新功能]</span>
            </a>
        </div>
    </div>
</body>
</html>
    '''
    
    main_index_path = "output/index.html"
    with open(main_index_path, 'w', encoding='utf-8') as f:
        f.write(navigation_html)
    
    print(f"主导航页面已创建: {main_index_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='企业级A股高低点分析系统 - 融合顶级量化交易技术的智能转折点识别')
    parser.add_argument('--csv', type=str, default='/Users/kangfei/Downloads/result.csv', help='CSV数据文件路径')
    parser.add_argument('--arc-json', default='output/arc/top_100.json', help='大弧底分析结果JSON文件路径')
    parser.add_argument('--max', type=int, help='最大分析股票数量（用于测试）')
    parser.add_argument('--clear-cache', action='store_true', help='清除缓存重新处理数据')
    parser.add_argument('--output', default='output/pivot', help='输出目录')
    parser.add_argument('--method', 
                      choices=['enterprise_ensemble', 'fractal_dimension', 'statistical_significance', 
                              'adaptive_ml', 'microstructure', 'multi_timeframe'], 
                      default='enterprise_ensemble', 
                      help='企业级检测方法（推荐：enterprise_ensemble）')
    parser.add_argument('--sensitivity', choices=['conservative', 'balanced', 'aggressive'], 
                      default='balanced', help='检测敏感度')
    
    args = parser.parse_args()
    
    # 设置输出目录
    output_dir = args.output
    setup_output_directories(output_dir)
    
    # 清除缓存（如果需要）
    if args.clear_cache:
        clear_cache_if_needed(args.clear_cache)
    
    print("=" * 70)
    print("🚀 企业级A股高低点分析系统")
    print("融合顶级量化交易技术的智能转折点识别平台")
    print("=" * 70)
    print(f"📊 检测方法: {args.method}")
    print(f"🎯 敏感度: {args.sensitivity}")
    print("🔬 技术栈: 分形维度 | 统计验证 | 机器学习 | 微观结构")
    print("=" * 70)
    
    # 1. 加载大弧底分析结果
    print("\n📊 步骤1: 加载大弧底分析结果")
    arc_stocks = load_arc_stocks_from_json(args.arc_json)
    if not arc_stocks:
        print("无法加载大弧底分析结果，程序退出")
        return
    
    # 2. 加载和处理股票数据
    print("\n📈 步骤2: 加载和处理股票数据")
    try:
        processor = StockDataProcessor(args.csv)
        processor.process_weekly_data()
        all_stock_data = processor.get_all_data()
        print(f"成功加载 {len(all_stock_data)} 只股票的周K线数据")
    except Exception as e:
        print(f"数据加载失败: {e}")
        return
    
    # 3. 根据大弧底结果过滤股票数据
    print("\n🔍 步骤3: 过滤大弧底股票数据")
    filtered_stock_data = filter_stock_data_by_arc_results(all_stock_data, arc_stocks)
    if not filtered_stock_data:
        print("没有找到有效的大弧底股票数据，程序退出")
        return
    
    # 4. 执行企业级高低点分析
    print(f"\n🎯 步骤4: 执行企业级高低点分析")
    pivot_results = analyze_pivot_points(
        filtered_stock_data, 
        max_stocks=args.max,
        method=args.method,
        sensitivity=args.sensitivity
    )
    if not pivot_results:
        print("没有生成有效的高低点分析结果，程序退出")
        return
    
    # 5. 生成图表和HTML页面
    print("\n📊 步骤5: 生成图表和HTML页面")
    html_path = generate_charts_and_html(filtered_stock_data, pivot_results, output_dir)
    if not html_path:
        print("图表和HTML生成失败")
        return
    
    # 6. 保存分析结果
    print("\n💾 步骤6: 保存分析结果")
    save_analysis_results(pivot_results, output_dir)
    
    # 7. 创建导航集成
    print("\n🔗 步骤7: 创建导航集成")
    create_navigation_integration()
    
    # 完成总结
    print("\n" + "=" * 70)
    print("✅ 企业级高低点分析完成!")
    print(f"📊 分析方法: {args.method}")
    print(f"🎯 敏感度设置: {args.sensitivity}")
    print(f"📈 成功分析股票: {len(pivot_results)} 只")
    print(f"📁 输出目录: {output_dir}")
    print(f"🌐 HTML页面: {html_path}")
    print(f"🏠 主导航: output/index.html")
    print("=" * 70)
    
    # 显示企业级统计信息
    total_pivots = sum(
        len(result.get('filtered_pivot_highs', [])) + len(result.get('filtered_pivot_lows', []))
        for result in pivot_results.values()
    )
    avg_accuracy = sum(result.get('accuracy_score', 0) for result in pivot_results.values()) / len(pivot_results)
    
    # 质量分级统计
    quality_stats = {'Excellent': 0, 'Good': 0, 'Fair': 0, 'Poor': 0}
    for result in pivot_results.values():
        quality_grade = result.get('enterprise_quality', {}).get('quality_grade', 'Unknown')
        if quality_grade in quality_stats:
            quality_stats[quality_grade] += 1
    
    print(f"\n📊 企业级分析统计:")
    print(f"   🎯 总识别转折点: {total_pivots}")
    print(f"   🏆 平均F1评分: {avg_accuracy:.1%}")
    print(f"   📈 平均每股转折点: {total_pivots / len(pivot_results):.1f}")
    print(f"   ⭐ 质量分布:")
    for grade, count in quality_stats.items():
        if count > 0:
            percentage = (count / len(pivot_results)) * 100
            print(f"      {grade}: {count} 只 ({percentage:.1f}%)")
    
    print(f"\n🔬 技术特色展示:")
    print(f"   ✅ 分形维度分析 - 基于分形几何识别真实转折点")
    print(f"   ✅ 统计显著性验证 - 严格的统计学检验标准")
    print(f"   ✅ 机器学习增强 - 自适应异常检测算法")
    print(f"   ✅ 企业级质量评估 - 多维度综合评分系统")


if __name__ == "__main__":
    main()