"""统一数据处理器入口：仅支持数据库数据源（实时）。"""

from .database_stock_data_processor import DatabaseStockDataProcessor

# 为向后兼容，提供同名别名，指向数据库数据处理器
StockDataProcessor = DatabaseStockDataProcessor


def create_stock_data_processor(cache_dir="cache"):
    """创建股票数据处理器（始终返回数据库处理器）。
    
    Args:
        cache_dir: 缓存目录路径
        
    Returns:
        DatabaseStockDataProcessor 实例
    """
    return DatabaseStockDataProcessor(cache_dir=cache_dir)