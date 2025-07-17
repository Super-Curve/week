#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

class BaseChartGenerator:
    """基础图表生成器，包含公共的周K数据处理方法"""
    
    def __init__(self, output_dir="images", width=600, height=400):
        self.output_dir = output_dir
        self.width = width
        self.height = height
        os.makedirs(self.output_dir, exist_ok=True)

    def normalize_data(self, data):
        """标准化数据到图片坐标 - 周K线标准版本"""
        if len(data) == 0:
            return {
                'dates': [],
                'open': [],
                'high': [],
                'low': [],
                'close': [],
                'price_info': {
                    'display_min': 0,
                    'display_max': 0,
                    'global_min': 0,
                    'global_max': 0
                },
                'date_info': {
                    'start_date': None,
                    'end_date': None,
                    'date_labels': []
                }
            }
        
        # 提取OHLC数据和日期
        open_prices = data['open'].values
        high_prices = data['high'].values
        low_prices = data['low'].values
        close_prices = data['close'].values
        
        # 获取日期信息
        date_index = data.index
        start_date = date_index[0] if len(date_index) > 0 else None
        end_date = date_index[-1] if len(date_index) > 0 else None
        
        # 生成日期标签（显示关键时间点）
        date_labels = self._generate_date_labels(date_index)
        
        dates = np.arange(len(close_prices))
        
        # 计算整体价格范围，保持真实比例
        global_min = np.min(low_prices)
        global_max = np.max(high_prices)
        
        # 添加一些边距以显示价格标签
        price_range = global_max - global_min
        margin = price_range * 0.05  # 5%的边距
        display_min = global_min - margin
        display_max = global_max + margin
        
        # 标准化所有价格数据
        def normalize_price(price):
            if display_max == display_min:
                return self.height // 2
            return ((display_max - price) / (display_max - display_min)) * (self.height - 80) + 40
        
        # 标准化OHLC数据
        normalized_open = np.array([normalize_price(p) for p in open_prices])
        normalized_high = np.array([normalize_price(p) for p in high_prices])
        normalized_low = np.array([normalize_price(p) for p in low_prices])
        normalized_close = np.array([normalize_price(p) for p in close_prices])
        
        # 标准化日期到图片宽度，留出空间给坐标轴标签
        normalized_dates = (dates / (len(dates) - 1)) * (self.width - 120) + 60
        
        return {
            'dates': normalized_dates,
            'open': normalized_open,
            'high': normalized_high,
            'low': normalized_low,
            'close': normalized_close,
            'price_info': {
                'display_min': display_min,
                'display_max': display_max,
                'global_min': global_min,
                'global_max': global_max
            },
            'date_info': {
                'start_date': start_date,
                'end_date': end_date,
                'date_labels': date_labels
            }
        }
    
    def _generate_date_labels(self, date_index):
        """生成日期标签 - 优化版本，避免重叠"""
        if len(date_index) == 0:
            return []
        
        labels = []
        total_points = len(date_index)
        
        # 根据数据点数量和图片宽度计算合适的标签数量
        # 假设每个标签需要约60像素宽度（包括间距）
        max_labels = (self.width - 120) // 60  # 120是左右边距
        
        if total_points <= max_labels:
            # 如果数据点少于最大标签数，全部显示
            step = 1
        else:
            # 否则根据最大标签数计算步长
            step = max(1, total_points // max_labels)
        
        # 确保步长不会太小
        if step < 5 and total_points > 20:
            step = 5
        elif step < 10 and total_points > 40:
            step = 10
        
        # 生成标签
        for i in range(0, total_points, step):
            if i < len(date_index):
                date = date_index[i]
                # 格式化日期为 YYYY-MM 格式
                if hasattr(date, 'strftime'):
                    label = date.strftime('%Y-%m')
                else:
                    label = str(date)[:7]  # 取前7个字符
                labels.append((i, label))
        
        # 确保最后一个点也被标记（如果还没有的话）
        if total_points > 1 and (total_points - 1) % step != 0:
            last_date = date_index[-1]
            if hasattr(last_date, 'strftime'):
                label = last_date.strftime('%Y-%m')
            else:
                label = str(last_date)[:7]
            
            # 检查最后一个标签是否与倒数第二个标签太近
            if len(labels) > 0:
                last_label_idx = labels[-1][0]
                if (total_points - 1) - last_label_idx >= 3:  # 至少间隔3个点
                    labels.append((total_points - 1, label))
            else:
                labels.append((total_points - 1, label))
        
        return labels

    def get_fonts(self, font_size=14, small_font_size=10):
        """获取字体 - 支持中文显示"""
        # 尝试多个支持中文的字体路径
        chinese_fonts = [
            "/System/Library/Fonts/PingFang.ttc",  # macOS 系统字体
            "/System/Library/Fonts/STHeiti Light.ttc",  # macOS 系统字体
            "/System/Library/Fonts/STHeiti Medium.ttc",  # macOS 系统字体
            "/System/Library/Fonts/Hiragino Sans GB.ttc",  # macOS 系统字体
            "/System/Library/Fonts/Arial Unicode MS.ttf",  # macOS 系统字体
            "/Library/Fonts/Arial Unicode MS.ttf",  # macOS 系统字体
            "/System/Library/Fonts/Arial.ttf",  # 备用字体
        ]
        
        font = None
        small_font = None
        
        for font_path in chinese_fonts:
            try:
                if font_path.endswith('.ttc'):
                    # 对于.ttc字体文件，需要指定索引
                    font = ImageFont.truetype(font_path, font_size, index=0)
                    small_font = ImageFont.truetype(font_path, small_font_size, index=0)
                else:
                    font = ImageFont.truetype(font_path, font_size)
                    small_font = ImageFont.truetype(font_path, small_font_size)
                break
            except:
                continue
        
        # 如果所有字体都失败，使用默认字体
        if font is None:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        return font, small_font

    def normalize_price_for_display(self, price, price_info):
        """标准化价格用于显示 - 公共方法"""
        if price_info['display_max'] == price_info['display_min']:
            return self.height // 2
        return ((price_info['display_max'] - price) / (price_info['display_max'] - price_info['display_min'])) * (self.height - 80) + 40 