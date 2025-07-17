# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import pickle

class StockDataProcessor:
    def __init__(self, csv_file_path, cache_dir="cache"):
        self.csv_file_path = csv_file_path
        self.cache_dir = cache_dir
        self.data = None
        self.weekly_data = {}
        
        # 创建缓存目录
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _get_cache_file(self):
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, "weekly_data.pkl")
    
    def _get_cache_info_file(self):
        """获取缓存信息文件路径"""
        return os.path.join(self.cache_dir, "cache_info.txt")
    
    def _is_cache_valid(self):
        """检查缓存是否有效"""
        cache_file = self._get_cache_file()
        info_file = self._get_cache_info_file()
        
        if not os.path.exists(cache_file) or not os.path.exists(info_file):
            return False
        
        # 检查CSV文件是否比缓存文件新
        csv_mtime = os.path.getmtime(self.csv_file_path)
        cache_mtime = os.path.getmtime(cache_file)
        
        return csv_mtime <= cache_mtime
    
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
            f.write("CSV文件: {}\n".format(self.csv_file_path))
            f.write("股票数量: {}\n".format(len(self.weekly_data)))
            f.write("数据点数: {}\n".format(sum(len(data) for data in self.weekly_data.values())))
        
        print("缓存已保存到: {}".format(cache_file))
    
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
        
    def load_data(self):
        """加载CSV数据"""
        try:
            self.data = pd.read_csv(self.csv_file_path)
            print("成功加载数据，共 {} 条记录".format(len(self.data)))
            return True
        except Exception as e:
            print("加载数据失败: {}".format(e))
            return False
    
    def process_weekly_data(self):
        """处理数据，生成周K线"""
        # 首先尝试从缓存加载
        if self._is_cache_valid():
            if self._load_cache():
                return True
        
        if self.data is None:
            print("请先加载数据")
            return False
        
        print("开始处理数据...")
        
        # 转换时间格式
        self.data['time'] = pd.to_datetime(self.data['time'])
        
        # 按股票代码分组
        grouped = self.data.groupby('code')
        
        for code, group in grouped:
            # 按周重采样
            weekly = group.set_index('time').resample('W').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last'
            }).dropna()
            
            # 只保留最近三年的数据
            three_years_ago = datetime.now() - timedelta(days=3*365)
            weekly = weekly[weekly.index >= three_years_ago]
            
            if len(weekly) > 0:
                self.weekly_data[code] = weekly
        
        print("成功处理 {} 只股票的周K线数据".format(len(self.weekly_data)))
        
        # 保存缓存
        self._save_cache()
        
        return True
    
    def get_stock_codes(self):
        """获取所有股票代码"""
        return list(self.weekly_data.keys())
    
    def get_stock_data(self, code):
        """获取指定股票的周K线数据"""
        return self.weekly_data.get(code)
    
    def get_all_data(self):
        """获取所有数据"""
        return self.weekly_data 