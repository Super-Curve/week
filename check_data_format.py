#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中的数据格式
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.database_stock_data_processor import DatabaseStockDataProcessor
import pandas as pd

def check_data_format():
    processor = DatabaseStockDataProcessor()
    
    # 创建连接
    if not processor._create_connection():
        print("数据库连接失败")
        return
    
    print("数据库连接成功")
    
    try:
        # 检查stock_name表的格式
        print("\n=== stock_name表 ===")
        stock_name_query = "SELECT stock_code, stock_name FROM stock_name LIMIT 5"
        stock_df = pd.read_sql(stock_name_query, processor.engine)
        print("stock_name表示例数据:")
        print(stock_df)
        
        # 检查history_week_data表的格式
        print("\n=== history_week_data表 ===")
        week_data_query = "SELECT DISTINCT code FROM history_week_data LIMIT 5"
        week_df = pd.read_sql(week_data_query, processor.engine)
        print("history_week_data表中的股票代码示例:")
        print(week_df)
        
        # 检查是否有匹配的数据
        print("\n=== 检查匹配情况 ===")
        sample_code_from_stock_name = stock_df.iloc[0]['stock_code']
        sample_code_from_week_data = week_df.iloc[0]['code']
        
        print(f"stock_name表示例代码: {sample_code_from_stock_name}")
        print(f"history_week_data表示例代码: {sample_code_from_week_data}")
        
        # 尝试查询
        if sample_code_from_stock_name == sample_code_from_week_data:
            print("✅ 代码格式匹配")
        else:
            print("❌ 代码格式不匹配")
            
            # 看看是否有数据
            test_query = f"SELECT COUNT(*) as count FROM history_week_data WHERE code = '{sample_code_from_week_data}'"
            count_df = pd.read_sql(test_query, processor.engine)
            print(f"使用 {sample_code_from_week_data} 查询到 {count_df.iloc[0]['count']} 条记录")
    
    except Exception as e:
        print(f"查询出错: {e}")
    
    processor.close_connection()

if __name__ == "__main__":
    check_data_format()