# -*- coding: utf-8 -*-
"""
数据库版本的股票数据处理器
从 MySQL 读取周/日 K 线数据，并提供统一的装载、缓存、访问接口。

- 使用 SQLAlchemy 管理连接与连接池
- 周频默认近三年数据；日频按自然日截取最近 N 天
- 所有对外数据结构保持为 {code: pandas.DataFrame}，索引为日期，列为 open/high/low/close
- 本地缓存放置于 `cache/`，周频与日频分别分桶；当传入选择集时，按选择集生成独立缓存

注意：仅负责读取与简单处理（类型/索引/缺失值），不做业务分析。
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
    - 从 MySQL 读取周/日 K 线数据，支持按选择集加载，结果支持本地缓存

    实现:
    - 连接: SQLAlchemy 引擎（预 ping、回收、超时、连接池参数）
    - 周频: 查询近三年周线，返回 DataFrame（索引为 trade_date）
    - 日频: 查询最近 N 天（日历天）内的日线
    - 缓存: `cache/weekly_data_db*.pkl` 与 `cache/daily_data_db_*.pkl`，并写入 cache_info 说明

    约定与返回:
    - `load_data()` 仅建立连接；`process_weekly_data()`/`process_daily_data_recent()` 填充内存字典
    - `get_all_data()`/`get_all_daily_data()` 返回内存缓存；键为股票代码，值为 DataFrame

    维护建议:
    - 如数据库表结构调整，优先更新 `_get_weekly_data_for_stock` 与 `_get_daily_data_for_stock` 中的 SQL 与 CAST 精度
    - 如需变更缓存策略，集中修改 `_is_cache_valid`/`_save_cache` 及对应日频方法
    - 请勿更改对外返回字典结构，避免影响上游分析/渲染
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
        """返回周频缓存文件路径。当存在选择集时，基于选择集内容生成 md5 后缀以实现独立缓存。"""
        if self.selected_codes:
            import hashlib
            join_key = ",".join(sorted(self.selected_codes))
            digest = hashlib.md5(join_key.encode("utf-8")).hexdigest()[:8]
            return os.path.join(self.cache_dir, f"weekly_data_db_{digest}.pkl")
        return os.path.join(self.cache_dir, "weekly_data_db.pkl")

    def _get_daily_cache_file(self, days: int = 90):
        """返回日频缓存文件路径（按选择集与天数分桶）。"""
        if self.selected_codes:
            import hashlib
            join_key = ",".join(sorted(self.selected_codes))
            digest = hashlib.md5(join_key.encode("utf-8")).hexdigest()[:8]
            return os.path.join(self.cache_dir, f"daily_data_db_{days}_{digest}.pkl")
        return os.path.join(self.cache_dir, f"daily_data_db_{days}.pkl")
    
    def _get_cache_info_file(self):
        """返回周频缓存说明文件路径。"""
        if self.selected_codes:
            import hashlib
            join_key = ",".join(sorted(self.selected_codes))
            digest = hashlib.md5(join_key.encode("utf-8")).hexdigest()[:8]
            return os.path.join(self.cache_dir, f"cache_info_db_{digest}.txt")
        return os.path.join(self.cache_dir, "cache_info_db.txt")

    def _get_daily_cache_info_file(self, days: int = 90):
        """返回日频缓存说明文件路径。"""
        if self.selected_codes:
            import hashlib
            join_key = ",".join(sorted(self.selected_codes))
            digest = hashlib.md5(join_key.encode("utf-8")).hexdigest()[:8]
            return os.path.join(self.cache_dir, f"cache_info_daily_db_{days}_{digest}.txt")
        return os.path.join(self.cache_dir, f"cache_info_daily_db_{days}.txt")
    
    def _is_cache_valid(self, max_age_hours=24):
        """检查周频缓存是否仍然有效（基于文件 mtime，默认 24 小时）。"""
        cache_file = self._get_cache_file()
        info_file = self._get_cache_info_file()
        if not os.path.exists(cache_file) or not os.path.exists(info_file):
            return False
        cache_mtime = os.path.getmtime(cache_file)
        current_time = datetime.now().timestamp()
        return (current_time - cache_mtime) < max_age_hours * 3600

    def _is_daily_cache_valid(self, days: int = 90, max_age_hours: int = 12):
        """检查日频缓存是否仍然有效（默认 12 小时）。"""
        cache_file = self._get_daily_cache_file(days)
        info_file = self._get_daily_cache_info_file(days)
        if not os.path.exists(cache_file) or not os.path.exists(info_file):
            return False
        cache_mtime = os.path.getmtime(cache_file)
        current_time = datetime.now().timestamp()
        return (current_time - cache_mtime) < max_age_hours * 3600
    
    def _save_cache(self):
        """持久化周频内存数据到缓存文件，并写出说明信息。"""
        cache_file = self._get_cache_file()
        info_file = self._get_cache_info_file()
        with open(cache_file, 'wb') as f:
            pickle.dump(self.weekly_data, f)
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write("生成时间: {}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            f.write("数据源: 数据库\n")
            f.write("股票数量: {}\n".format(len(self.weekly_data)))
            f.write("数据点数: {}\n".format(sum(len(data) for data in self.weekly_data.values())))
            if self.selected_codes:
                f.write("选择集: {} 只 (独立缓存)\n".format(len(self.selected_codes)))
        print("缓存已保存到: {}".format(cache_file))

    def _save_daily_cache(self, days: int = 90):
        """持久化日频内存数据到缓存文件，并写出说明信息。"""
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
        """加载周频缓存到内存。"""
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
        """加载日频缓存到内存。"""
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
        """创建数据库连接引擎并做一次轻量探活，成功后将引擎保存在实例上。"""
        try:
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
                pool_size=10,
                max_overflow=20,
                connect_args={
                    "connect_timeout": 60,
                    "read_timeout": 300,
                    "write_timeout": 300,
                    "charset": "utf8mb4"
                }
            )
            # 探活
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("数据库连接成功")
            return True
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return False
    
    def _get_stock_codes(self):
        """获取股票代码列表。若构造时提供了选择集，则直接返回该集合。"""
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
        """返回单只股票的周 K 线 DataFrame。索引为日期，列为 open/high/low/close。"""
        try:
            three_years_ago = (datetime.now() - timedelta(days=3*365)).strftime('%Y-%m-%d')
            query = """
            SELECT 
                trade_date,
                CAST(open AS DECIMAL(10,2)) as open,
                CAST(high AS DECIMAL(10,2)) as high,
                CAST(low  AS DECIMAL(10,2)) as low,
                CAST(close AS DECIMAL(10,2)) as close
            FROM history_week_data 
            WHERE code = %s AND trade_date >= %s
            ORDER BY trade_date
            """
            df = pd.read_sql(query, self.engine, params=(stock_code, three_years_ago))
            if len(df) == 0:
                return None
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df = df.set_index('trade_date')
            numeric_cols = ['open', 'high', 'low', 'close']
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
            df = df.dropna()
            return df if len(df) > 0 else None
        except Exception:
            return None

    def _get_daily_data_for_stock(self, stock_code: str, days: int = 90):
        """返回单只股票最近 N 天（日历天）内的日 K 线 DataFrame。"""
        try:
            start_date = (datetime.now() - timedelta(days=days + 30)).strftime('%Y-%m-%d')
            query = """
            SELECT 
                trade_date,
                CAST(open AS DECIMAL(10,2)) as open,
                CAST(high AS DECIMAL(10,2)) as high,
                CAST(low  AS DECIMAL(10,2)) as low,
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
            # 只保留最近 days 个自然日内的交易记录
            cutoff = pd.Timestamp(datetime.now() - timedelta(days=days))
            df = df[df.index >= cutoff]
            return df if len(df) > 0 else None
        except Exception:
            return None
    
    def load_data(self):
        """兼容接口：建立数据库连接。成功返回 True。"""
        return self._create_connection()
    
    def process_weekly_data(self):
        """加载所有（或选择集）股票的周 K 线数据到内存并缓存。"""
        # 优先尝试缓存
        if self._is_cache_valid():
            if self._load_cache():
                return True
        # 加载
        if not self._create_connection():
            print("无法连接到数据库")
            return False
        print("开始从数据库加载周K线数据...")
        try:
            stock_codes = self._get_stock_codes()
            if not stock_codes:
                print("未能获取股票代码列表")
                return False
            print(f"获取到 {len(stock_codes)} 个股票代码")
            self._load_all_stock_data(stock_codes)
            print(f"成功处理 {len(self.weekly_data)} 只股票的周K线数据")
            if self.weekly_data:
                self._save_cache()
            return True
        except Exception as e:
            print(f"加载数据失败: {e}")
            return False

    def process_daily_data_recent(self, days: int = 90):
        """加载所有（或选择集）股票最近 N 天的日 K 线数据到内存并缓存。"""
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
        """按给定列表遍历加载周 K 线数据，填充到 `self.weekly_data`。"""
        successful_count = 0
        total_count = len(stock_codes)
        print(f"开始遍历 {total_count} 只股票...")
        for i, stock_code in enumerate(stock_codes, 1):
            if i % 100 == 0:
                print(f"处理进度: {i}/{total_count} ({i/total_count*100:.1f}%)")
            weekly_data = self._get_weekly_data_for_stock(stock_code)
            if weekly_data is not None and len(weekly_data) > 0:
                self.weekly_data[stock_code] = weekly_data
                successful_count += 1
        print(f"遍历完成，成功处理 {successful_count} 只股票")
    
    def get_stock_codes(self):
        """返回已加载的股票代码列表（来自内存字典键）。"""
        return list(self.weekly_data.keys())
    
    def get_stock_data(self, code):
        """返回单只股票的周 K 线 DataFrame（若不存在则返回 None）。"""
        return self.weekly_data.get(code)
    
    def get_all_data(self):
        """返回全部周频数据字典。"""
        return self.weekly_data

    def get_all_daily_data(self):
        """返回全部日频数据字典。"""
        return self.daily_data
    
    def close_connection(self):
        """关闭数据库连接引擎（如存在）。"""
        if self.engine:
            self.engine.dispose()
            print("数据库连接已关闭")


if __name__ == "__main__":
    """简单的性能测试入口：连接→加载→统计用时"""
    import time
    start_time = time.time()
    processor = DatabaseStockDataProcessor()
    print("开始性能测试...")
    if processor.load_data():
        print("数据库连接成功")
        if processor.process_weekly_data():
            stock_codes = processor.get_stock_codes()
            print(f"✅ 成功加载 {len(stock_codes)} 只股票的数据")
            total_time = time.time() - start_time
            print(f"🚀 总耗时: {total_time:.1f} 秒")
            if len(stock_codes) > 0:
                print(f"📊 平均每只股票处理时间: {total_time/len(stock_codes)*1000:.2f} 毫秒")
        else:
            print("❌ 数据处理失败")
    else:
        print("❌ 数据库连接失败")
    processor.close_connection()