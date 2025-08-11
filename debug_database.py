#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试数据库查询问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.database_stock_data_processor import DatabaseStockDataProcessor

def debug_database():
    processor = DatabaseStockDataProcessor()
    
    # 创建连接
    if not processor._create_connection():
        print("数据库连接失败")
        return
    
    print("数据库连接成功")
    
    # 获取股票代码
    stock_codes = processor._get_stock_codes()
    print(f"获取到 {len(stock_codes)} 个股票代码")
    
    if stock_codes:
        # 测试前3个股票
        test_codes = stock_codes[:3]
        print(f"测试股票代码: {test_codes}")
        
        for code in test_codes:
            print(f"\n测试股票: {code}")
            data = processor._get_weekly_data_for_stock(code)
            if data is not None:
                print(f"  获取到 {len(data)} 条记录")
                print(f"  时间范围: {data.index.min()} 到 {data.index.max()}")
                print("  前3条数据:")
                print(data.head(3))
            else:
                print("  未获取到数据")
    
    processor.close_connection()

if __name__ == "__main__":
    debug_database()