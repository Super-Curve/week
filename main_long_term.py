#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中长期策略标的池入口

说明：
- 筛选条件：最近一年的年化波动率40%-50%，年化夏普率≥0.5
- 自动过滤ST股票、U股和上市不足一年的股票
- 复用高低点页面布局，第三列展示策略指标
- 输出目录：`output/long_term/`
"""

import os
import argparse
from src.analyzers.strategy_analyzer import StrategyAnalyzer
from src.analyzers.advanced_pivot_analyzer import EnterprisesPivotAnalyzer
from src.generators.pivot_chart_generator_optimized import PivotChartGeneratorOptimized
from src.generators.strategy_html_generator import StrategyHTMLGenerator
from src.utils.common_utils import (
    setup_output_directories, clear_cache_if_needed,
    load_and_process_data
)
from src.core.database_stock_data_processor import DatabaseStockDataProcessor
from src.utils.logger import get_logger, log_performance
import time
from datetime import datetime, date
from src.integration.strategy_persistence import save_strategy_candidates, save_pivot_points

logger = get_logger(__name__)


@log_performance(logger)
def main():
    """主函数"""
    start_time = time.time()
    parser = argparse.ArgumentParser(description='中长期策略标的池筛选')
    parser.add_argument('--output', default='output/long_term', help='输出目录')
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
    logger.info("📊 中长期策略标的池筛选")
    logger.info("筛选条件：年化波动率40%-50%，夏普比率≥0.5")
    logger.info("=" * 70)
    
    # 1. 加载股票数据和信息（使用全量数据，一次性获取所有信息）
    logger.info("\n📈 步骤1: 加载股票数据和基本信息")
    result = load_and_process_data(use_arc_top=False, max_stocks=args.max, return_with_info=True)
    if isinstance(result, tuple) and len(result) == 2:
        stock_data, raw_stock_info = result
    else:
        stock_data = result
        raw_stock_info = None
    
    if not stock_data:
        logger.error("数据加载失败")
        return
    
    logger.info(f"成功加载 {len(stock_data)} 只股票的周K线数据")
    
    # 2. 处理股票信息（转换为策略分析器所需的格式）
    logger.info("\n📊 步骤2: 处理股票基本信息")
    analyzer = StrategyAnalyzer()
    
    # 转换股票信息格式
    stock_info = {}
    if raw_stock_info:
        for code in stock_data.keys():
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
        data_processor = DatabaseStockDataProcessor()
        if not data_processor._create_connection():
            logger.error("数据库连接失败")
            return
        stock_info = analyzer.get_stock_info(data_processor.engine, list(stock_data.keys()))
        data_processor.close_connection()
    
    logger.info(f"成功处理 {len(stock_info)} 只股票的基本信息")
    
    # 3. 过滤不合格的股票（ST、U股、上市不足一年）
    logger.info("\n🔍 步骤3: 过滤不合格的股票")
    stock_codes = list(stock_data.keys())
    filtered_codes = analyzer.filter_stocks(stock_codes, stock_info, min_ipo_days=365)
    
    # 只保留过滤后的股票数据
    filtered_stock_data = {code: stock_data[code] for code in filtered_codes if code in stock_data}
    
    excluded_count = len(stock_codes) - len(filtered_codes)
    if excluded_count > 0:
        logger.info(f"过滤掉 {excluded_count} 只股票（ST/U股/上市不足一年）")
    logger.info(f"剩余 {len(filtered_stock_data)} 只股票进行策略筛选")
    
    # 4. 执行策略筛选
    logger.info("\n🎯 步骤4: 执行中长期策略筛选")
    strategy_results = analyzer.long_term_strategy(filtered_stock_data, stock_info)
    
    if not strategy_results:
        logger.info("没有找到符合中长期策略条件的股票")
        return
    
    logger.info(f"找到 {len(strategy_results)} 只符合条件的股票")
    
    # 5. 对筛选出的股票进行高低点分析
    logger.info("\n🎯 步骤5: 对策略标的进行高低点分析")
    pivot_analyzer = EnterprisesPivotAnalyzer()
    pivot_results = {}
    
    # 准备用于图表生成的数据
    chart_stock_data = {code: result['data'] for code, result in strategy_results.items()}
    
    # 对每只股票进行高低点分析
    for code, df in chart_stock_data.items():
        try:
            # 使用ZigZag+ATR方法识别高低点
            pivot_result = pivot_analyzer.detect_pivot_points(
                df,
                method='zigzag_atr',
                sensitivity='balanced',
                frequency='weekly'
            )
            
            if pivot_result and pivot_result.get('filtered_pivot_highs') is not None:
                pivot_results[code] = pivot_result
                logger.info(f"{code}: 识别到 {len(pivot_result.get('filtered_pivot_highs', []))} 个高点，"
                          f"{len(pivot_result.get('filtered_pivot_lows', []))} 个低点")
                
                # 计算T2和入场点
                t2_entry_info = analyzer.find_t2_and_entry_point(df, pivot_result)
                if t2_entry_info:
                    strategy_results[code]['t2_entry_info'] = t2_entry_info
                    if 'entry_date' in t2_entry_info:
                        logger.info(f"{code}: 入场时间 {t2_entry_info['entry_date']}, 入场价格 {t2_entry_info['entry_price']:.2f}")
                    else:
                        logger.info(f"{code}: T2已识别，等待入场信号")
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
    
    # 6. 生成图表
    logger.info("\n📊 步骤6: 生成K线图表（带高低点标注）")
    chart_generator = PivotChartGeneratorOptimized(
        output_dir=os.path.join(output_dir, 'images')
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
    
    # 7. 落库：将本次策略结果存入 strategy_candidates（按 dt 幂等）
    try:
        dt_today: date = datetime.now().date()
        written = save_strategy_candidates(
            dt=dt_today,
            strategy_type="long_term",
            results=strategy_results,
            stock_info=stock_info,
            data_frequency="weekly",
            data_window_days=52,
        )
        logger.info(f"已落库中长期策略标的 {written} 条（dt={dt_today}）")
    except Exception as e:
        logger.error(f"落库中长期策略标的失败: {e}")

    # 8. 保存高低点至数据库（周频，过滤后）
    try:
        dt_today: date = datetime.now().date()
        saved_total = 0
        for code, df in chart_stock_data.items():
            piv = pivot_results.get(code)
            if not piv:
                continue
            data_idx = list(df.index.date)
            prices_high = df['high'].tolist() if 'high' in df.columns else None
            prices_low = df['low'].tolist() if 'low' in df.columns else None
            saved = save_pivot_points(
                dt=dt_today,
                code=code,
                data_frequency='weekly',
                pivot_result=piv,
                data_index=data_idx,
                prices_high=prices_high,
                prices_low=prices_low,
                is_filtered=True,
            )
            saved_total += saved
        logger.info(f"已落库周频高低点 {saved_total} 条（dt={dt_today}）")
    except Exception as e:
        logger.error(f"落库周频高低点失败: {e}")

    # 9. 生成HTML报告
    logger.info("\n📄 步骤7: 生成HTML报告")
    html_generator = StrategyHTMLGenerator(output_dir=output_dir)
    html_path = html_generator.generate_strategy_html(
        strategy_results, chart_paths, strategy_type='long_term'
    )
    
    if not html_path:
        logger.error("HTML生成失败")
        return
    
    # 9. 更新主导航页面
    logger.info("\n🔗 步骤8: 更新主导航页面")
    try:
        from main_pivot import create_main_navigation
        create_main_navigation()
    except Exception as e:
        logger.error(f"更新主导航失败: {e}")
    
    # 完成总结
    logger.info("\n" + "=" * 70)
    logger.info("✅ 中长期策略标的池筛选完成!")
    logger.info(f"📊 符合条件股票: {len(strategy_results)} 只")
    logger.info(f"📁 输出目录: {output_dir}")
    logger.info(f"🌐 HTML报告: {html_path}")
    logger.info(f"🏠 主导航: output/index.html")
    logger.info("=" * 70)
    
    # 显示统计信息
    volatilities = [r['volatility'] for r in strategy_results.values()]
    sharpes = [r['sharpe'] for r in strategy_results.values()]
    
    if volatilities and sharpes:
        import numpy as np
        logger.info(f"\n📊 策略统计:")
        logger.info(f"   📈 平均波动率: {np.mean(volatilities):.1%}")
        logger.info(f"   💎 平均夏普比: {np.mean(sharpes):.2f}")
        logger.info(f"   🏆 最高夏普比: {max(sharpes):.2f}")
        
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
        logger.info(f"📦 平均每只股票耗时: {total_time/len(stock_data):.2f} 秒")


if __name__ == "__main__":
    main()