# -*- coding: utf-8 -*-
"""
数据库版本的股票数据处理器
从MySQL数据库读取股票数据并处理为周K线数据
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import pickle
import pymysql
from sqlalchemy import create_engine, text
import sys
import warnings
import time

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import DATABASE_CONFIG

warnings.filterwarnings('ignore')


class DatabaseStockDataProcessor:
    """
    数据库股票数据处理器

    用途:
    - 从 MySQL 读取周K线数据，支持选择集 selected_codes；对结果做本地缓存（按选择集分桶）。

    实现方式:
    - SQLAlchemy 连接（连接池、超时预设）→ 逐代码查询最近三年周K线
    - 缓存: cache/weekly_data_db.pkl 或带 8 位 md5 后缀的独立缓存
    - 兼容接口: load_data/process_weekly_data/get_all_data/close_connection

    优点:
    - 实时性好；缓存减少重复 IO；选择集加速专题分析（如 ARC Top 200）

    局限:
    - 依赖数据库可用性；schema 变更需同步 SQL
    - 周期固定为三年，若需更长需暴露参数

    维护建议:
    - 更新 _get_weekly_data_for_stock 的 SQL 与 CAST 精度与索引
    - 调整 _is_cache_valid 失效策略；必要时引入增量更新
    - 严格保持键为股票代码、值为 DataFrame 的返回结构
    """
    
    def __init__(self, cache_dir="cache", selected_codes=None):
        self.cache_dir = cache_dir
        self.weekly_data = {}
        self.daily_data = {}
        self.db_config = DATABASE_CONFIG
        self.engine = None
        # 可选：仅加载指定股票代码，减少数据库与内存负担
        self.selected_codes = list(selected_codes) if selected_codes else None
        
        # 创建缓存目录
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _get_cache_file(self):
        """获取缓存文件路径（针对选择集生成独立缓存）。"""
        if self.selected_codes:
            # 基于选择集生成简单的哈希后缀，避免过长文件名
            import hashlib
            join_key = ",".join(sorted(self.selected_codes))
            digest = hashlib.md5(join_key.encode("utf-8")).hexdigest()[:8]
            return os.path.join(self.cache_dir, f"weekly_data_db_{digest}.pkl")
        return os.path.join(self.cache_dir, "weekly_data_db.pkl")

    def _get_daily_cache_file(self, days: int = 90):
        """获取日线缓存文件路径（按选择集与days分桶）。"""
        if self.selected_codes:
            import hashlib
            join_key = ",".join(sorted(self.selected_codes))
            digest = hashlib.md5(join_key.encode("utf-8")).hexdigest()[:8]
            return os.path.join(self.cache_dir, f"daily_data_db_{days}_{digest}.pkl")
        return os.path.join(self.cache_dir, f"daily_data_db_{days}.pkl")
    
    def _get_cache_info_file(self):
        """获取缓存信息文件路径（针对选择集生成独立缓存信息）。"""
        if self.selected_codes:
            import hashlib
            join_key = ",".join(sorted(self.selected_codes))
            digest = hashlib.md5(join_key.encode("utf-8")).hexdigest()[:8]
            return os.path.join(self.cache_dir, f"cache_info_db_{digest}.txt")
        return os.path.join(self.cache_dir, "cache_info_db.txt")

    def _get_daily_cache_info_file(self, days: int = 90):
        """获取日线缓存信息文件路径。"""
        if self.selected_codes:
            import hashlib
            join_key = ",".join(sorted(self.selected_codes))
            digest = hashlib.md5(join_key.encode("utf-8")).hexdigest()[:8]
            return os.path.join(self.cache_dir, f"cache_info_daily_db_{days}_{digest}.txt")
        return os.path.join(self.cache_dir, f"cache_info_daily_db_{days}.txt")
    
    def _is_cache_valid(self, max_age_hours=24):
        """
        检查缓存是否有效
        数据库数据基于时间失效，默认24小时后重新获取
        """
        cache_file = self._get_cache_file()
        info_file = self._get_cache_info_file()
        
        if not os.path.exists(cache_file) or not os.path.exists(info_file):
            return False
        
        # 检查缓存是否过期
        cache_mtime = os.path.getmtime(cache_file)
        current_time = datetime.now().timestamp()
        
        # 如果缓存超过指定小时数则认为过期
        return (current_time - cache_mtime) < max_age_hours * 3600

    def _is_daily_cache_valid(self, days: int = 90, max_age_hours: int = 12):
        """检查日线缓存是否有效（默认12小时失效）。"""
        cache_file = self._get_daily_cache_file(days)
        info_file = self._get_daily_cache_info_file(days)
        if not os.path.exists(cache_file) or not os.path.exists(info_file):
            return False
        cache_mtime = os.path.getmtime(cache_file)
        current_time = datetime.now().timestamp()
        return (current_time - cache_mtime) < max_age_hours * 3600
    
    def _save_cache(self):
        """保存缓存"""
        cache_file = self._get_cache_file()
        info_file = self._get_cache_info_file()
        
        # 保存数据
        with open(cache_file, 'wb') as f:
            pickle.dump(self.weekly_data, f)
        
        # 保存缓存信息
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write("生成时间: {}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            f.write("数据源: 数据库\n")
            f.write("股票数量: {}\n".format(len(self.weekly_data)))
            f.write("数据点数: {}\n".format(sum(len(data) for data in self.weekly_data.values())))
            if self.selected_codes:
                f.write("选择集: {} 只 (独立缓存)\n".format(len(self.selected_codes)))
        
        print("缓存已保存到: {}".format(cache_file))

    def _save_daily_cache(self, days: int = 90):
        """保存日线缓存。"""
        cache_file = self._get_daily_cache_file(days)
        info_file = self._get_daily_cache_info_file(days)
        with open(cache_file, 'wb') as f:
            pickle.dump(self.daily_data, f)
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write("生成时间: {}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            f.write("数据源: 数据库（日线）\n")
            f.write("股票数量: {}\n".format(len(self.daily_data)))
            f.write("天数: {}\n".format(days))
            if self.selected_codes:
                f.write("选择集: {} 只 (独立缓存)\n".format(len(self.selected_codes)))
        print("日线缓存已保存到: {}".format(cache_file))
    
    def _load_cache(self):
        """加载缓存"""
        cache_file = self._get_cache_file()
        
        try:
            with open(cache_file, 'rb') as f:
                self.weekly_data = pickle.load(f)
            print("从缓存加载数据: {} 只股票".format(len(self.weekly_data)))
            return True
        except Exception as e:
            print("加载缓存失败: {}".format(e))
            return False

    def _load_daily_cache(self, days: int = 90):
        """加载日线缓存。"""
        cache_file = self._get_daily_cache_file(days)
        try:
            with open(cache_file, 'rb') as f:
                self.daily_data = pickle.load(f)
            print("从日线缓存加载数据: {} 只股票".format(len(self.daily_data)))
            return True
        except Exception as e:
            print("加载日线缓存失败: {}".format(e))
            return False
    
    def _create_connection(self):
        """创建数据库连接"""
        try:
            # 创建SQLAlchemy引擎
            connection_string = (
                f"mysql+pymysql://{self.db_config['username']}:{self.db_config['password']}"
                f"@{self.db_config['host']}:{self.db_config['port']}"
                f"/{self.db_config['database']}?charset={self.db_config['charset']}"
            )
            
            self.engine = create_engine(
                connection_string,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False,
                # 性能优化参数
                pool_size=10,          # 连接池大小
                max_overflow=20,       # 最大溢出连接数
                connect_args={
                    "connect_timeout": 60,     # 连接超时
                    "read_timeout": 300,       # 读取超时
                    "write_timeout": 300,      # 写入超时
                    "charset": "utf8mb4"
                }
            )
            
            # 测试连接
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            print("数据库连接成功")
            return True
            
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return False
    
    def _get_stock_codes(self):
        """获取股票代码：若有选择集，则直接使用；否则查询全量。"""
        if self.selected_codes:
            print(f"使用选择集股票代码 {len(self.selected_codes)} 个")
            return list(self.selected_codes)
        try:
            query = "SELECT stock_code FROM stock_name ORDER BY stock_code"
            df = pd.read_sql(query, self.engine)
            stock_codes = df['stock_code'].tolist()
            print(f"获取到 {len(stock_codes)} 个股票代码")
            return stock_codes
        except Exception as e:
            print(f"获取股票代码失败: {e}")
            return []
    
    def _get_weekly_data_for_stock(self, stock_code):
        """获取指定股票的周K线数据"""
        try:
            # 计算三年前的日期
            three_years_ago = (datetime.now() - timedelta(days=3*365)).strftime('%Y-%m-%d')
            
            # 查询SQL
            query = """
            SELECT 
                trade_date,
                CAST(open AS DECIMAL(10,2)) as open,
                CAST(high AS DECIMAL(10,2)) as high,
                CAST(low AS DECIMAL(10,2)) as low,
                CAST(close AS DECIMAL(10,2)) as close
            FROM history_week_data 
            WHERE code = %s AND trade_date >= %s
            ORDER BY trade_date
            """
            # 执行查询
            df = pd.read_sql(query, self.engine, params=(stock_code, three_years_ago))

            
            if len(df) == 0:
                return None
            
            # 数据处理
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df = df.set_index('trade_date')
            
            # 数据类型转换
            numeric_cols = ['open', 'high', 'low', 'close']
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
            
            # 移除空值并返回
            df = df.dropna()
            return df if len(df) > 0 else None
            
        except Exception:
            return None

    def _get_daily_data_for_stock(self, stock_code: str, days: int = 90):
        """获取指定股票的最近N天日K线数据（默认90天，按日历天筛选）。"""
        try:
            start_date = (datetime.now() - timedelta(days=days + 30)).strftime('%Y-%m-%d')
            query = """
            SELECT 
                trade_date,
                CAST(open AS DECIMAL(10,2)) as open,
                CAST(high AS DECIMAL(10,2)) as high,
                CAST(low AS DECIMAL(10,2)) as low,
                CAST(close AS DECIMAL(10,2)) as close
            FROM history_day_data 
            WHERE code = %s AND trade_date >= %s
            ORDER BY trade_date
            """
            df = pd.read_sql(query, self.engine, params=(stock_code, start_date))
            if len(df) == 0:
                return None
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df = df.set_index('trade_date')
            numeric_cols = ['open', 'high', 'low', 'close']
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
            df = df.dropna()
            # 只保留最近days个自然日内的交易记录
            cutoff = pd.Timestamp(datetime.now() - timedelta(days=days))
            df = df[df.index >= cutoff]
            return df if len(df) > 0 else None
        except Exception:
            return None
    
    def load_data(self):
        """
        兼容性方法，保持与原StockDataProcessor接口一致
        实际上数据库版本不需要这个方法，但为了兼容性保留
        """
        return self._create_connection()
    
    def process_weekly_data(self):
        """处理数据，从数据库获取周K线数据 - 简化版本"""
        # 首先尝试从缓存加载
        if self._is_cache_valid():
            if self._load_cache():
                return True
        
        # 创建数据库连接
        if not self._create_connection():
            print("无法连接到数据库")
            return False
        
        print("开始从数据库加载周K线数据...")
        
        try:
            # 1. 获取所有股票代码
            stock_codes = self._get_stock_codes()
            if not stock_codes:
                print("未能获取股票代码列表")
                return False
            
            print(f"获取到 {len(stock_codes)} 个股票代码")
            
            # 2. 遍历每只股票获取数据
            self._load_all_stock_data(stock_codes)
            
            print(f"成功处理 {len(self.weekly_data)} 只股票的周K线数据")
            
            # 保存缓存
            if self.weekly_data:
                self._save_cache()
            
            return True
            
        except Exception as e:
            print(f"加载数据失败: {e}")
            return False

    def process_daily_data_recent(self, days: int = 90):
        """处理数据，从数据库获取最近N天（日线）数据。"""
        if self._is_daily_cache_valid(days=days):
            if self._load_daily_cache(days=days):
                return True
        if not self._create_connection():
            print("无法连接到数据库")
            return False
        print(f"开始从数据库加载最近{days}天的日K线数据...")
        try:
            stock_codes = self._get_stock_codes()
            if not stock_codes:
                print("未能获取股票代码列表")
                return False
            print(f"获取到 {len(stock_codes)} 个股票代码")
            successful_count = 0
            total_count = len(stock_codes)
            for i, stock_code in enumerate(stock_codes, 1):
                if i % 100 == 0:
                    print(f"处理进度(日): {i}/{total_count} ({i/total_count*100:.1f}%)")
                daily_df = self._get_daily_data_for_stock(stock_code, days=days)
                if daily_df is not None and len(daily_df) > 0:
                    self.daily_data[stock_code] = daily_df
                    successful_count += 1
            print(f"遍历完成（日线），成功处理 {successful_count} 只股票")
            if self.daily_data:
                self._save_daily_cache(days=days)
            return True
        except Exception as e:
            print(f"加载日线数据失败: {e}")
            return False
    
    def _load_all_stock_data(self, stock_codes):
        """遍历所有股票获取周K线数据 - 简化版本"""
        successful_count = 0
        total_count = len(stock_codes)
        
        print(f"开始遍历 {total_count} 只股票...")
        
        for i, stock_code in enumerate(stock_codes, 1):
            # 每100只股票显示一次进度
            if i % 100 == 0:
                print(f"处理进度: {i}/{total_count} ({i/total_count*100:.1f}%)")
            
            # 获取单只股票的周K线数据
            weekly_data = self._get_weekly_data_for_stock(stock_code)
            if weekly_data is not None and len(weekly_data) > 0:
                self.weekly_data[stock_code] = weekly_data
                successful_count += 1
        
        print(f"遍历完成，成功处理 {successful_count} 只股票")
    
    def get_stock_codes(self):
        """获取所有股票代码"""
        return list(self.weekly_data.keys())
    
    def get_stock_data(self, code):
        """获取指定股票的周K线数据"""
        return self.weekly_data.get(code)
    
    def get_all_data(self):
        """获取所有数据"""
        return self.weekly_data

    def get_all_daily_data(self):
        """获取所有日线数据"""
        return self.daily_data
    
    def close_connection(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            print("数据库连接已关闭")


if __name__ == "__main__":
    """性能测试"""
    import time
    start_time = time.time()
    
    processor = DatabaseStockDataProcessor()
    
    print("开始性能测试...")
    
    # 测试连接
    if processor.load_data():
        print("数据库连接成功")
        
        # 测试数据处理
        if processor.process_weekly_data():
            
            # 显示统计信息
            stock_codes = processor.get_stock_codes()
            print(f"✅ 成功加载 {len(stock_codes)} 只股票的数据")
            
            total_time = time.time() - start_time
            print(f"🚀 总耗时: {total_time:.1f} 秒")
            print(f"📊 平均每只股票处理时间: {total_time/len(stock_codes)*1000:.2f} 毫秒")
            
        else:
            print("❌ 数据处理失败")
    else:
        print("❌ 数据库连接失败")
    
    processor.close_connection()