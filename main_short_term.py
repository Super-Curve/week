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
from datetime import datetime, date
from src.integration.strategy_persistence import save_strategy_candidates, save_pivot_points_batch

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
    daily_data = load_recent_daily_data(max_stocks=args.max, days=120, use_arc_top=False)  # 120个交易日约6个月
    
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
    
    # 3. 过滤不合格的股票（ST、U股、上市不足一年）
    logger.info("\n🔍 步骤3: 过滤不合格的股票")
    stock_codes = list(daily_data.keys())
    filtered_codes = analyzer.filter_stocks(stock_codes, stock_info, min_ipo_days=365)
    
    # 只保留过滤后的股票数据
    filtered_daily_data = {code: daily_data[code] for code in filtered_codes if code in daily_data}
    
    excluded_count = len(stock_codes) - len(filtered_codes)
    if excluded_count > 0:
        logger.info(f"过滤掉 {excluded_count} 只股票（ST/U股/上市不足一年）")
    logger.info(f"剩余 {len(filtered_daily_data)} 只股票进行策略筛选")
    
    # 4. 执行策略筛选（使用日线数据）
    logger.info("\n🎯 步骤4: 执行短期波段策略筛选（基于日线数据）")
    strategy_results = analyzer.short_term_strategy(filtered_daily_data, stock_info, use_daily_data=True)
    
    if not strategy_results:
        logger.info("没有找到符合短期波段策略条件的股票")
        return
    
    logger.info(f"找到 {len(strategy_results)} 只符合条件的股票")
    
    # 5. 为策略标的加载周线数据（用于图表显示）
    logger.info("\n📊 步骤5: 加载策略标的的周线数据")
    # 加载全部周线数据，然后筛选出策略标的
    weekly_stock_codes = list(strategy_results.keys())
    weekly_result = load_and_process_data(use_arc_top=False, return_with_names=True)
    
    if isinstance(weekly_result, tuple):
        all_weekly_data, _ = weekly_result
    else:
        all_weekly_data = weekly_result
    
    # 筛选出策略标的的周线数据
    weekly_data = {}
    if all_weekly_data:
        for code in weekly_stock_codes:
            if code in all_weekly_data:
                weekly_data[code] = all_weekly_data[code]
        logger.info(f"成功加载 {len(weekly_data)} 只策略标的的周K线数据")
    else:
        logger.error("周线数据加载失败")
        # 使用日线数据作为备选
        for code in strategy_results:
            if code in daily_data:
                weekly_data[code] = daily_data[code]
    
    # 6. 对筛选出的股票进行高低点分析
    logger.info("\n🎯 步骤6: 对策略标的进行高低点分析（日线数据）")
    pivot_analyzer = EnterprisesPivotAnalyzer()
    pivot_results = {}
    pivot_results_weekly = {}  # 存储周线的高低点分析结果
    
    # 准备用于图表生成的数据（使用日线数据）
    chart_stock_data = {code: result['data'] for code, result in strategy_results.items()}
    
    # 对每只股票进行高低点分析（收集数据，最后批量保存）
    dt_today = datetime.now().date()
    pivot_data_batch = []  # 收集待保存的数据
    total_stocks = len(chart_stock_data)
    batch_save_size = 50  # 每50只股票批量保存一次
    
    for i, (code, df) in enumerate(chart_stock_data.items(), 1):
        try:
            # 使用ZigZag+ATR方法识别高低点（日线数据）
            pivot_result = pivot_analyzer.detect_pivot_points(
                df,
                method='zigzag_atr',
                sensitivity='conservative',
                frequency='daily'  # 指定为日频
            )
            
            if pivot_result and pivot_result.get('filtered_pivot_highs') is not None:
                pivot_results[code] = pivot_result
                logger.info(f"{code}: 识别到 {len(pivot_result.get('filtered_pivot_highs', []))} 个高点，"
                          f"{len(pivot_result.get('filtered_pivot_lows', []))} 个低点")
                
                # 收集高低点数据，准备批量保存
                data_idx_daily = list(df.index.date)
                prices_high_daily = df['high'].tolist() if 'high' in df.columns else None
                prices_low_daily = df['low'].tolist() if 'low' in df.columns else None
                
                pivot_data_batch.append({
                    'dt': dt_today,
                    'code': code,
                    'data_frequency': 'daily',
                    'pivot_result': pivot_result,
                    'data_index': data_idx_daily,
                    'prices_high': prices_high_daily,
                    'prices_low': prices_low_daily,
                    'is_filtered': True
                })
                
                # 计算T2和入场点（使用周线数据）
                # 注意：这里使用的是周线数据的结果，因为我们需要在周线图上标注
                if code in weekly_data:
                    t2_entry_info = analyzer.find_t2_and_entry_point(weekly_data[code], pivot_results_weekly.get(code, pivot_result))
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
            
            # 每处理batch_save_size只股票或处理完成时，批量保存一次
            if len(pivot_data_batch) >= batch_save_size or i == total_stocks:
                if pivot_data_batch:
                    try:
                        saved_count = save_pivot_points_batch(pivot_data_batch, batch_size=100)
                        logger.info(f"批量保存完成: 处理 {len(pivot_data_batch)} 只股票，保存 {saved_count} 个高低点")
                        pivot_data_batch = []  # 清空批次数据
                    except Exception as save_e:
                        logger.error(f"批量保存高低点失败: {save_e}")
                        pivot_data_batch = []  # 清空批次数据避免重复保存
            
            # 每处理50只股票报告一次进度
            if i % 50 == 0:
                logger.info(f"高低点分析进度: {i}/{total_stocks} ({i/total_stocks*100:.1f}%)")
                
        except Exception as e:
            logger.error(f"分析 {code} 高低点失败: {e}")
            pivot_results[code] = {
                'filtered_pivot_highs': [],
                'filtered_pivot_lows': [],
                'pivot_highs': [],
                'pivot_lows': []
            }
        
        # 同时分析周线数据的高低点（用于T2和入场点计算）
        if code in weekly_data:
            try:
                pivot_result_weekly = pivot_analyzer.detect_pivot_points(
                    weekly_data[code],
                    method='zigzag_atr',
                    sensitivity='aggressive',
                    frequency='weekly'
                )
                if pivot_result_weekly and pivot_result_weekly.get('filtered_pivot_highs') is not None:
                    pivot_results_weekly[code] = pivot_result_weekly
            except Exception as e:
                logger.error(f"分析 {code} 周线高低点失败: {e}")
                pivot_results_weekly[code] = {
                    'filtered_pivot_highs': [],
                    'filtered_pivot_lows': [],
                    'pivot_highs': [],
                    'pivot_lows': []
                }
    
    # 7. 生成图表（使用周线数据以便显示T2和入场点）
    logger.info("\n📊 步骤7: 生成K线图表（带高低点标注）")
    # chart_generator = PivotChartGeneratorOptimized(
    #     output_dir=os.path.join(output_dir, 'images'),
    #     frequency_label="周K线图"  # 使用周K线图
    # )
    
    # # 生成带高低点标注的K线图（使用周线数据）
    # chart_paths = {}
    # for code in strategy_results:
    #     # 使用周线数据生成图表
    #     if code not in weekly_data:
    #         logger.warning(f"{code}: 没有周线数据，跳过图表生成")
    #         continue
            
    #     df = weekly_data[code]
        
    #     try:
    #         # 生成原始K线图
    #         original_path = chart_generator.generate_original_chart(code, df)
            
    #         # 生成带高低点的分析图（使用周线的高低点结果）
    #         pivot_result = pivot_results_weekly.get(code, {
    #             'filtered_pivot_highs': [],
    #             'filtered_pivot_lows': [],
    #             'pivot_highs': [],
    #             'pivot_lows': []
    #         })
    #         analysis_path = chart_generator.generate_pivot_chart(code, df, pivot_result)
            
    #         if original_path and analysis_path:
    #             chart_paths[code] = {
    #                 'original': original_path,
    #                 'analysis': analysis_path
    #             }
    #     except Exception as e:
    #         logger.error(f"生成 {code} 图表失败: {e}")
    
    # logger.info(f"成功生成 {len(chart_paths)} 个图表")

    # 7. 落库：将本次短期策略结果存入 strategy_candidates（按 dt 幂等）
    try:
        dt_today: date = datetime.now().date()
        written = save_strategy_candidates(
            dt=dt_today,
            strategy_type="short_term",
            results=strategy_results,
            stock_info=stock_info,
            data_frequency="daily",
            data_window_days=120,
        )
        logger.info(f"已落库短期策略标的 {written} 条（dt={dt_today}）")
    except Exception as e:
        logger.error(f"落库短期策略标的失败: {e}")

    # 8. 高低点分析和批量保存已完成
    logger.info("短期策略标的高低点分析和批量保存完成")

    # 9. 处理其他所有股票的高低点分析（strategy_type='day'）
    logger.info("\n🔍 步骤9: 处理其他股票的高低点分析（strategy_type='day'）")
    
    # 找出不在短期策略中的其他股票
    strategy_codes = set(strategy_results.keys())
    all_codes = set(filtered_daily_data.keys())
    other_codes = all_codes - strategy_codes
    
    logger.info(f"短期策略股票: {len(strategy_codes)} 只")
    logger.info(f"其他股票: {len(other_codes)} 只")
    logger.info(f"总计处理: {len(all_codes)} 只股票")
    
    if other_codes:
        # 为其他股票创建虚拟的strategy结果（用于保存到stock_targets）
        other_strategy_results = {}
        other_pivot_data_batch = []
        batch_save_size = 100  # 每100只股票保存一次
        
        logger.info(f"开始处理 {len(other_codes)} 只其他股票...")
        
        for i, code in enumerate(other_codes, 1):
            try:
                df = filtered_daily_data[code]
                
                # 计算基本的波动率和夏普比
                returns = df['close'].pct_change().dropna()
                if len(returns) > 0:
                    volatility = returns.std() * (252 ** 0.5)  # 年化波动率
                    mean_return = returns.mean() * 252  # 年化收益率
                    sharpe = mean_return / volatility if volatility > 0 else 0
                else:
                    volatility = 0
                    sharpe = 0
                
                # 创建其他股票的策略结果
                other_strategy_results[code] = {
                    'volatility': volatility,
                    'sharpe': sharpe,
                    'name': stock_info.get(code, {}).get('name', code),
                    'market_cap_category': stock_info.get(code, {}).get('market_cap_category', '未知'),
                    'market_value': stock_info.get(code, {}).get('market_value', 0),
                    'data': df
                }
                
                # 进行高低点分析
                pivot_result = pivot_analyzer.detect_pivot_points(
                    df,
                    method='zigzag_atr',
                    sensitivity='conservative',
                    frequency='daily'
                )
                
                if pivot_result and pivot_result.get('filtered_pivot_highs') is not None:
                    # 收集高低点数据
                    data_idx_daily = list(df.index.date)
                    prices_high_daily = df['high'].tolist() if 'high' in df.columns else None
                    prices_low_daily = df['low'].tolist() if 'low' in df.columns else None
                    
                    other_pivot_data_batch.append({
                        'dt': dt_today,
                        'code': code,
                        'data_frequency': 'daily',
                        'pivot_result': pivot_result,
                        'data_index': data_idx_daily,
                        'prices_high': prices_high_daily,
                        'prices_low': prices_low_daily,
                        'is_filtered': True
                    })
                
                # 分批保存高低点数据，避免内存积累过多
                if len(other_pivot_data_batch) >= batch_save_size or i == len(other_codes):
                    if other_pivot_data_batch:
                        try:
                            saved_count = save_pivot_points_batch(other_pivot_data_batch, batch_size=100)
                            logger.info(f"批量保存其他股票高低点: 处理 {len(other_pivot_data_batch)} 只股票，保存 {saved_count} 条记录")
                            other_pivot_data_batch = []  # 清空批次数据
                        except Exception as save_e:
                            logger.error(f"批量保存其他股票高低点失败: {save_e}")
                            other_pivot_data_batch = []
                
                # 显示进度
                if i % 200 == 0:
                    logger.info(f"其他股票分析进度: {i}/{len(other_codes)} ({i/len(other_codes)*100:.1f}%)")
                
            except Exception as e:
                logger.error(f"分析其他股票 {code} 失败: {e}")
                continue
        
        # 保存其他股票到stock_targets（strategy_type='day'）
        if other_strategy_results:
            try:
                written = save_strategy_candidates(
                    dt=dt_today,
                    strategy_type='day',  # 使用'day'作为strategy_type
                    results=other_strategy_results,
                    stock_info=stock_info,
                    data_frequency='daily',
                    data_window_days=120
                )
                logger.info(f"已落库其他股票标的 {written} 条（strategy_type='day'，dt={dt_today}）")
            except Exception as e:
                logger.error(f"落库其他股票标的失败: {e}")
        
        logger.info(f"其他股票处理完成: 共处理 {len(other_strategy_results)} 只股票")

    # 10. 生成HTML报告
    logger.info("\n📄 步骤10: 生成HTML报告")
    # html_generator = StrategyHTMLGenerator(output_dir=output_dir)
    # html_path = html_generator.generate_strategy_html(
    #     strategy_results, chart_paths, strategy_type='short_term'
    # )
    
    # if not html_path:
    #     logger.error("HTML生成失败")
    #     return
    
    # # 9. 更新主导航页面
    # logger.info("\n🔗 步骤9: 更新主导航页面")
    # try:
    #     from main_pivot import create_main_navigation
    #     create_main_navigation()
    # except Exception as e:
    #     logger.error(f"更新主导航失败: {e}")
    
    # 完成总结
    logger.info("\n" + "=" * 70)
    logger.info("✅ 短期波段策略标的池筛选完成!")
    logger.info(f"⚡ 符合条件股票: {len(strategy_results)} 只")
    logger.info(f"📁 输出目录: {output_dir}")
    #logger.info(f"🌐 HTML报告: {html_path}")
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