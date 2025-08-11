#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试SQL查询
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.database_stock_data_processor import DatabaseStockDataProcessor
import pandas as pd

def test_simple_query():
    processor = DatabaseStockDataProcessor()
    
    if not processor._create_connection():
        print("数据库连接失败")
        return
    
    print("数据库连接成功")
    
    # 直接查询测试
    test_code = "000001.SZ"
    query = f"""
    SELECT 
        trade_date,
        open, high, low, close
    FROM history_week_data 
    WHERE code = '{test_code}' 
    LIMIT 5
    """
    
    print(f"测试查询: {test_code}")
    print(f"SQL: {query}")
    
    try:
        df = pd.read_sql(query, processor.engine)
        print(f"查询结果: {len(df)} 条记录")
        if len(df) > 0:
            print(df)
        else:
            print("没有数据")
    except Exception as e:
        print(f"查询失败: {e}")
    
    processor.close_connection()

if __name__ == "__main__":
    test_simple_query()