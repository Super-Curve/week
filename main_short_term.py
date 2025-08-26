#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
短期波段策略标的池入口

说明：
- 筛选条件：最近6个月的年化波动率≥50%，夏普率>1（基于日线数据）
- 自动过滤ST股票、U股和上市不足一年的股票
- 复用高低点页面布局，第三列展示策略指标
- 输出目录：`output/short_term/`
"""

import os
import argparse
from src.analyzers.strategy_analyzer import StrategyAnalyzer
from src.analyzers.advanced_pivot_analyzer import EnterprisesPivotAnalyzer
from src.generators.pivot_chart_generator_optimized import PivotChartGeneratorOptimized
from src.generators.strategy_html_generator import StrategyHTMLGenerator
from src.utils.common_utils import (
    setup_output_directories, clear_cache_if_needed,
    load_and_process_data, load_recent_daily_data
)
from src.core.database_stock_data_processor import DatabaseStockDataProcessor
from src.utils.logger import get_logger, log_performance
import time

logger = get_logger(__name__)


@log_performance(logger)
def main():
    """主函数"""
    start_time = time.time()
    parser = argparse.ArgumentParser(description='短期波段策略标的池筛选')
    parser.add_argument('--output', default='output/short_term', help='输出目录')
    parser.add_argument('--max', type=int, help='最大分析股票数量（用于测试）')
    parser.add_argument('--clear-cache', action='store_true', help='清除缓存重新处理数据')
    
    args = parser.parse_args()
    
    # 设置输出目录
    output_dir = args.output
    setup_output_directories(output_dir)
    
    # 清除缓存（如果需要）
    if args.clear_cache:
        clear_cache_if_needed(args.clear_cache)
    
    logger.info("=" * 70)
    logger.info("⚡ 短期波段策略标的池筛选")
    logger.info("筛选条件：半年化波动率≥50%，夏普比率>1.0（基于日线数据）")
    logger.info("=" * 70)
    
    # 1. 加载股票日线数据（最近6个月，约120个交易日）
    logger.info("\n📈 步骤1: 加载股票日线数据（最近6个月）")
    daily_data = load_recent_daily_data(max_stocks=args.max, days=180, use_arc_top=False)  # 180天约6个月
    
    if not daily_data:
        logger.error("日线数据加载失败")
        return
    
    logger.info(f"成功加载 {len(daily_data)} 只股票的日K线数据")
    
    # 2. 获取股票基本信息（市值、上市日期等）
    logger.info("\n📊 步骤2: 获取股票基本信息")
    # 创建临时的周线数据处理器来获取股票信息
    from src.core.database_stock_data_processor import DatabaseStockDataProcessor
    data_processor = DatabaseStockDataProcessor()
    
    if not data_processor._create_connection():
        logger.error("数据库连接失败")
        return
    
    # 加载股票信息
    data_processor.load_stock_names()  # 这会加载完整的股票信息
    raw_stock_info = data_processor.get_loaded_stock_info()
    data_processor.close_connection()
    
    # 处理股票信息（转换为策略分析器所需的格式）
    logger.info("\n📊 处理股票基本信息")
    analyzer = StrategyAnalyzer()
    
    # 转换股票信息格式
    stock_info = {}
    if raw_stock_info:
        for code in daily_data.keys():
            if code in raw_stock_info:
                info = raw_stock_info[code]
                market_value = analyzer._parse_market_value(info.get('total_market_value', '0'))
                
                # 计算市值分类
                if market_value >= 500:
                    category = '大盘股'
                elif market_value >= 100:
                    category = '中盘股'
                else:
                    category = '小盘股'
                
                stock_info[code] = {
                    'name': info.get('name', code),
                    'market_value': market_value,
                    'ipo_date': info.get('ipo_date'),
                    'market_cap_category': category
                }
    else:
        # 如果没有获取到信息，才查询数据库（兼容旧版本）
        analyzer_temp = StrategyAnalyzer()
        data_processor = DatabaseStockDataProcessor()
        if not data_processor._create_connection():
            logger.error("数据库连接失败")
            return
        stock_info = analyzer_temp.get_stock_info(data_processor.engine, list(daily_data.keys()))
        data_processor.close_connection()
    
    logger.info(f"成功处理 {len(stock_info)} 只股票的基本信息")
    
    # 3. 执行策略筛选（使用日线数据）
    logger.info("\n🎯 步骤3: 执行短期波段策略筛选（基于日线数据）")
    strategy_results = analyzer.analyze_short_term_strategy(daily_data, stock_info, use_daily_data=True)
    
    if not strategy_results:
        logger.info("没有找到符合短期波段策略条件的股票")
        return
    
    logger.info(f"找到 {len(strategy_results)} 只符合条件的股票")
    
    # 4. 对筛选出的股票进行高低点分析
    logger.info("\n🎯 步骤4: 对策略标的进行高低点分析（日线数据）")
    pivot_analyzer = EnterprisesPivotAnalyzer()
    pivot_results = {}
    
    # 准备用于图表生成的数据（使用日线数据）
    chart_stock_data = {code: result['data'] for code, result in strategy_results.items()}
    
    # 对每只股票进行高低点分析
    for code, df in chart_stock_data.items():
        try:
            # 使用ZigZag+ATR方法识别高低点（日线数据）
            pivot_result = pivot_analyzer.detect_pivot_points(
                df,
                method='zigzag_atr',
                sensitivity='aggressive',
                frequency='daily'  # 指定为日频
            )
            
            if pivot_result and pivot_result.get('filtered_pivot_highs') is not None:
                pivot_results[code] = pivot_result
                logger.info(f"{code}: 识别到 {len(pivot_result.get('filtered_pivot_highs', []))} 个高点，"
                          f"{len(pivot_result.get('filtered_pivot_lows', []))} 个低点")
            else:
                # 如果没有识别到高低点，使用空的结果
                pivot_results[code] = {
                    'filtered_pivot_highs': [],
                    'filtered_pivot_lows': [],
                    'pivot_highs': [],
                    'pivot_lows': []
                }
        except Exception as e:
            logger.error(f"分析 {code} 高低点失败: {e}")
            pivot_results[code] = {
                'filtered_pivot_highs': [],
                'filtered_pivot_lows': [],
                'pivot_highs': [],
                'pivot_lows': []
            }
    
    # 5. 生成图表
    logger.info("\n📊 步骤5: 生成K线图表（带高低点标注）")
    chart_generator = PivotChartGeneratorOptimized(
        output_dir=os.path.join(output_dir, 'images'),
        frequency_label="日K线图（近6个月）"  # 标注为日K线
    )
    
    # 生成带高低点标注的K线图
    chart_paths = {}
    for code, df in chart_stock_data.items():
        try:
            # 生成原始K线图
            original_path = chart_generator.generate_original_chart(code, df)
            
            # 生成带高低点的分析图
            pivot_result = pivot_results.get(code, {
                'filtered_pivot_highs': [],
                'filtered_pivot_lows': [],
                'pivot_highs': [],
                'pivot_lows': []
            })
            analysis_path = chart_generator.generate_pivot_chart(code, df, pivot_result)
            
            if original_path and analysis_path:
                chart_paths[code] = {
                    'original': original_path,
                    'analysis': analysis_path
                }
        except Exception as e:
            logger.error(f"生成 {code} 图表失败: {e}")
    
    logger.info(f"成功生成 {len(chart_paths)} 个图表")
    
    # 6. 生成HTML报告
    logger.info("\n📄 步骤6: 生成HTML报告")
    html_generator = StrategyHTMLGenerator(output_dir=output_dir)
    html_path = html_generator.generate_strategy_html(
        strategy_results, chart_paths, strategy_type='short_term'
    )
    
    if not html_path:
        logger.error("HTML生成失败")
        return
    
    # 7. 更新主导航页面
    logger.info("\n🔗 步骤7: 更新主导航页面")
    try:
        from main_pivot import create_main_navigation
        create_main_navigation()
    except Exception as e:
        logger.error(f"更新主导航失败: {e}")
    
    # 完成总结
    logger.info("\n" + "=" * 70)
    logger.info("✅ 短期波段策略标的池筛选完成!")
    logger.info(f"⚡ 符合条件股票: {len(strategy_results)} 只")
    logger.info(f"📁 输出目录: {output_dir}")
    logger.info(f"🌐 HTML报告: {html_path}")
    logger.info(f"🏠 主导航: output/index.html")
    logger.info("=" * 70)
    
    # 显示统计信息
    volatilities = [r['volatility'] for r in strategy_results.values()]
    sharpes = [r['sharpe'] for r in strategy_results.values()]
    
    if volatilities and sharpes:
        import numpy as np
        logger.info(f"\n📊 策略统计（基于日线数据）:")
        logger.info(f"   📈 平均波动率: {np.mean(volatilities):.1%}")
        logger.info(f"   💎 平均夏普比: {np.mean(sharpes):.2f}")
        logger.info(f"   🏆 最高夏普比: {max(sharpes):.2f}")
        logger.info(f"   ⚡ 最高波动率: {max(volatilities):.1%}")
        
        # 市值分布
        market_cap_dist = {}
        for result in strategy_results.values():
            cat = result.get('market_cap_category', '未知')
            market_cap_dist[cat] = market_cap_dist.get(cat, 0) + 1
        
        logger.info(f"   📊 市值分布:")
        for cat, count in market_cap_dist.items():
            percentage = (count / len(strategy_results)) * 100
            logger.info(f"      {cat}: {count} 只 ({percentage:.1f}%)")
    
    # 记录总耗时
    total_time = time.time() - start_time
    logger.info(f"\n⏱️ 总耗时: {total_time:.2f} 秒")
    if strategy_results:
        logger.info(f"📦 平均每只股票耗时: {total_time/len(daily_data):.2f} 秒")


if __name__ == "__main__":
    main()