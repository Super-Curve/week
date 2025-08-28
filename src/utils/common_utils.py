#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import json
import numpy as np
import re
from src.utils.logger import get_logger, log_performance

# 设置日志器
logger = get_logger(__name__)


def setup_output_directories(output_dir):
    """创建输出目录结构"""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'images'), exist_ok=True)
    logger.info(f"输出目录已准备: {output_dir}")


def clear_cache_if_needed(clear_cache, cache_dir="cache"):
    """清除缓存目录"""
    if clear_cache and os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        logger.info("缓存已清除")


def save_json_with_numpy_support(data, file_path):
    """保存数据为JSON，支持numpy类型转换"""
    with open(file_path, 'w') as f:
        json.dump(data, f, default=lambda x: x.tolist() if hasattr(x, 'tolist') else x)


def generate_similarity_chart(chart_generator, code, df, similarity_result):
    """通用的相似度图表生成函数"""
    try:
        prices = df['close'].values
        
        # 计算基本拟合
        x = np.arange(len(prices))
        prices_array = np.array(prices, dtype=np.float64)
        
        try:
            # 线性拟合
            coeffs = np.polyfit(x, prices_array, 1)
            y_fit = np.polyval(coeffs, x)
            
            # 计算R²
            ss_res = np.sum((prices_array - y_fit) ** 2)
            ss_tot = np.sum((prices_array - np.mean(prices_array)) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
            r2 = float(max(0, min(1, r2)))
        except Exception as e:
            logger.error(f"拟合计算失败 {code}: {e}")
            coeffs = [0, np.mean(prices)]
            r2 = 0.0
        
        # 创建模拟的分析结果
        mock_result = {
            'type': 'similarity_analysis',
            'similarity_score': similarity_result['similarity_score'],
            'recommendation': similarity_result['recommendation'],
            'coeffs': coeffs,
            'r2': r2,
            'start': 0,
            'end': len(prices) - 1,
            'total_points': len(prices),
            'quality_score': similarity_result['similarity_score'],
            'factors': similarity_result['factors'],
            'details': similarity_result['details'],
            'price_range': {
                'start': prices[0],
                'end': prices[-1],
                'min': np.min(prices),
                'max': np.max(prices)
            }
        }
        
        # 生成图表 - 根据图表生成器类型调用相应方法
        if hasattr(chart_generator, 'generate_major_arc_chart'):
            return chart_generator.generate_major_arc_chart(code, df, mock_result)
        elif hasattr(chart_generator, 'generate_uptrend_chart'):
            # 为上升通道添加必要的通道数据
            mock_result.update({
                'upper_channel': {
                    'slope': coeffs[0],
                    'intercept': coeffs[1] + np.std(prices) * 0.5,
                    'start_idx': 0,
                    'end_idx': len(prices) - 1
                },
                'lower_channel': {
                    'slope': coeffs[0],
                    'intercept': coeffs[1] - np.std(prices) * 0.5,
                    'start_idx': 0,
                    'end_idx': len(prices) - 1
                },
                'channel_quality': {
                    'duration': len(prices),
                    'channel_width_pct': np.std(prices) / np.mean(prices) * 100 if np.mean(prices) > 0 else 0
                },
                'channel_features': {
                    'channel_strength': r2,
                    'breakout_attempts': 0
                }
            })
            return chart_generator.generate_uptrend_chart(code, df, mock_result)
        else:
            return None
            
    except Exception as e:
        logger.error(f"生成相似度图表失败 {code}: {e}")
        return None


@log_performance(logger)
def load_and_process_data(max_stocks=None, use_arc_top=True, arc_json_path="output/arc/top_100.json", return_with_names=False, return_with_info=False):
    """通用的数据加载和处理函数 - 数据库数据源（唯一支持）。

    优化：若 use_arc_top=True，优先仅加载大弧底TOP列表（最多200只），使用独立缓存，避免污染全量缓存。
    
    Args:
        max_stocks: 最大股票数量
        use_arc_top: 是否使用ARC TOP列表
        arc_json_path: ARC列表路径
        return_with_names: 是否返回股票名称
        return_with_info: 是否返回完整股票信息（包括市值、上市日期等）
    """
    from src.core.stock_data_processor import create_stock_data_processor, StockDataProcessor
    
    logger.info("使用数据库作为数据源加载股票数据...")

    selected_codes = None
    if use_arc_top:
        codes = load_arc_stock_codes(arc_json_path=arc_json_path)
        if codes:
            # 仅取前200只
            selected_codes = codes[:200]
            logger.info(f"按ARC列表限制加载 {len(selected_codes)} 只股票（独立缓存）")

    # 如果底层支持选择集，则传递
    if selected_codes and hasattr(StockDataProcessor, '__init__'):
        try:
            data_processor = StockDataProcessor(cache_dir="cache", selected_codes=selected_codes)  # DatabaseStockDataProcessor 接口
        except TypeError:
            data_processor = create_stock_data_processor()
    else:
        data_processor = create_stock_data_processor()
    
    if not data_processor.load_data():
        logger.error('数据库连接失败')
        return None
        
    if not data_processor.process_weekly_data():
        logger.error('数据处理失败')
        # 关闭数据库连接
        if hasattr(data_processor, 'close_connection'):
            data_processor.close_connection()
        return None
        
    stock_data = data_processor.get_all_data()
    
    # 获取股票名称
    stock_names = None
    if hasattr(data_processor, 'get_loaded_stock_names'):
        stock_names = data_processor.get_loaded_stock_names()
        if stock_names:
            logger.info(f"同时加载了 {len(stock_names)} 个股票名称")
    
    # 获取完整股票信息
    stock_info = None
    if hasattr(data_processor, 'get_loaded_stock_info'):
        stock_info = data_processor.get_loaded_stock_info()
        if stock_info:
            logger.info(f"同时加载了 {len(stock_info)} 个股票的完整信息")
    
    # 关闭数据库连接
    if hasattr(data_processor, 'close_connection'):
        data_processor.close_connection()
    
    if max_stocks and stock_data:
        stock_data = dict(list(stock_data.items())[:max_stocks])
    
    logger.info(f"成功加载 {len(stock_data)} 只股票的数据")
    
    # 返回股票数据和股票名称/信息
    if return_with_info and stock_info is not None:
        return stock_data, stock_info
    elif return_with_names:
        return stock_data, stock_names
    return stock_data


def create_mock_arc_result(similarity_result, prices):
    """创建模拟的大弧底结果结构"""
    start_idx = 0
    end_idx = len(prices) - 1
    
    # 计算二次拟合
    x = np.arange(len(prices))
    try:
        prices_array = np.array(prices, dtype=np.float64)
        coeffs = np.polyfit(x, prices_array, 2)
        y_fit = np.polyval(coeffs, x)
        
        ss_res = np.sum((prices_array - y_fit) ** 2)
        ss_tot = np.sum((prices_array - np.mean(prices_array)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        r2 = float(max(0, min(1, r2)))
    except:
        coeffs = [0, 0, np.mean(prices)]
        r2 = 0.0
    
    return {
        'type': 'similarity_based',
        'similarity_score': similarity_result['similarity_score'],
        'recommendation': similarity_result['recommendation'],
        'factors': similarity_result['factors'],
        'coeffs': coeffs,
        'r2': r2,
        'start': start_idx,
        'end': end_idx,
        'total_points': len(prices),
        'quality_score': similarity_result['similarity_score'],
        'details': similarity_result['details'],
        'price_range': {
            'start': prices[0],
            'end': prices[-1],
            'min': np.min(prices),
            'max': np.max(prices)
        }
    }


def load_recent_daily_data(max_stocks=None, days: int = 90, use_arc_top: bool = True, arc_json_path: str = "output/arc/top_100.json"):
    """加载最近N个交易日的日线数据，默认仅加载 ARC TOP（≤200）的小集合并使用独立缓存。

    Args:
        max_stocks: 最大股票数量限制
        days: 需要的交易日数量（注意：不是日历天数）
        use_arc_top: 是否只加载大弧底TOP股票
        arc_json_path: 大弧底JSON文件路径
        
    返回: {code: DataFrame(OHLC, 日频, 最近N个交易日)}
    """
    from src.core.stock_data_processor import StockDataProcessor

    logger.info(f"使用数据库作为数据源加载最近{days}个交易日的日线数据...")

    selected_codes = None
    if use_arc_top:
        codes = load_arc_stock_codes(arc_json_path=arc_json_path)
        if codes:
            selected_codes = codes[:200]
            logger.info(f"按ARC列表限制加载 {len(selected_codes)} 只股票（日线，独立缓存）")

    # 如果底层支持选择集，则传递
    try:
        data_processor = StockDataProcessor(cache_dir="cache", selected_codes=selected_codes)
    except TypeError:
        # 兼容创建方式
        from src.core.stock_data_processor import create_stock_data_processor
        data_processor = create_stock_data_processor()

    if not data_processor.load_data():
        logger.error('数据库连接失败')
        return None

    if not hasattr(data_processor, 'process_daily_data_recent'):
        logger.error('底层数据处理器未实现日线加载方法')
        return None

    if not data_processor.process_daily_data_recent(days=days):
        logger.error('日线数据处理失败')
        if hasattr(data_processor, 'close_connection'):
            data_processor.close_connection()
        return None

    if hasattr(data_processor, 'get_all_daily_data'):
        daily_data = data_processor.get_all_daily_data()
    else:
        logger.error('底层数据处理器未实现 get_all_daily_data')
        daily_data = None

    if hasattr(data_processor, 'close_connection'):
        data_processor.close_connection()

    if not daily_data:
        return None

    if max_stocks:
        daily_data = dict(list(daily_data.items())[:max_stocks])

    logger.info(f"成功加载 {len(daily_data)} 只股票的最近{days}天日线数据")
    return daily_data


def load_arc_stock_codes(arc_json_path="output/arc/top_100.json",
                         fallback_html_path="output/arc/index.html"):
    """优先从JSON加载大弧底股票列表，失败时从HTML回退解析。

    返回: List[str] 纯股票代码（如 000001.SZ）
    """
    # 1) 尝试JSON
    try:
        if os.path.exists(arc_json_path):
            with open(arc_json_path, 'r', encoding='utf-8') as f:
                codes = json.load(f)
            if isinstance(codes, list) and all(isinstance(c, str) for c in codes):
                return codes
    except Exception as e:
        logger.error(f"读取 {arc_json_path} 失败: {e}")

    # 2) 回退从HTML解析
    try:
        if os.path.exists(fallback_html_path):
            with open(fallback_html_path, 'r', encoding='utf-8') as f:
                html = f.read()
            pattern = r'(?:similar_|major_)([A-Z0-9]{6}\.[A-Z]{2})'
            matches = re.findall(pattern, html)
            return list(sorted(set(matches)))
    except Exception as e:
        logger.error(f"解析 {fallback_html_path} 失败: {e}")

    return []


def filter_stock_data_by_codes(stock_data_dict, codes):
    """根据给定股票代码列表过滤数据。

    返回: (filtered_dict, missing_codes)
    """
    filtered = {}
    missing = []
    code_set = set(codes or [])
    if not code_set:
        return stock_data_dict, []
    for code in code_set:
        if code in stock_data_dict:
            filtered[code] = stock_data_dict[code]
        else:
            missing.append(code)
    if missing:
        logger.warning(f"{len(missing)} 只大弧底股票在数据集中未找到")
        if len(missing) <= 10:
            logger.warning(f"缺失的股票: {missing}")
    logger.info(f"成功过滤出 {len(filtered)} 只大弧底股票用于后续分析")
    return filtered, missing