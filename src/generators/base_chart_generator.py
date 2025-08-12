#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

class BaseChartGenerator:
    """
    基础图表生成器

    用途:
    - 提供坐标标准化与统一的风格化绘制（Wind/简单风格），供业务图表复用

    实现:
    - `normalize_data` 将 OHLC 标准化为像素坐标，保留显示/全局价格信息与日期标签
    - `draw_wind_candlestick_chart`/`draw_wind_axes_and_labels` 提供统一风格输出
    - 字体、虚线、时间刻度与坐标边界等通用工具方法

    维护建议:
    - 新的绘制能力尽量沉淀在基类中，避免在子类重复实现
    - 不改变 `normalize_data` 返回结构，确保子类绘制兼容
    """
    
    def __init__(self, output_dir="images", width=600, height=400):
        self.output_dir = output_dir
        self.width = width
        self.height = height
        os.makedirs(self.output_dir, exist_ok=True)

    def normalize_data(self, data):
        """将 DataFrame(OHLC, 索引为日期) 标准化为图片坐标字典。"""
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
        
        # 添加边距以显示价格标签
        price_range = global_max - global_min
        margin = price_range * 0.05  # 5% 边距
        display_min = global_min - margin
        display_max = global_max + margin
        
        # 标准化所有价格数据
        def normalize_price(price):
            if display_max == display_min:
                return self.height // 2
            return ((display_max - price) / (display_max - display_min)) * (self.height - 80) + 40
        
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

    # ========== 统一的Wind风格K线绘制方法 ==========
    
    def get_chinese_font(self, size):
        """返回一个尽可能支持中文显示的字体对象。"""
        # macOS中文字体列表
        chinese_fonts = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Arial.ttf",
        ]
        for font_path in chinese_fonts:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        return ImageFont.load_default()
    
    def get_chart_boundaries(self, style='wind'):
        """返回图表绘制区域边界字典。"""
        if style == 'wind':
            return {
                'chart_left': 120,
                'chart_right': self.width - 80,
                'chart_top': 80,
                'chart_bottom': self.height - 120
            }
        else:
            return {
                'chart_left': 60,
                'chart_right': self.width - 10,
                'chart_top': 40,
                'chart_bottom': self.height - 30
            }
    
    def draw_wind_candlestick_chart(self, draw, normalized_data, style='wind', show_volume=False):
        """绘制统一风格的 K 线（Wind 或简单风格）。"""
        dates = normalized_data['dates']
        opens = normalized_data['open']
        highs = normalized_data['high']
        lows = normalized_data['low']
        closes = normalized_data['close']
        if len(dates) == 0:
            return
        boundaries = self.get_chart_boundaries(style)
        chart_left = boundaries['chart_left']
        chart_right = boundaries['chart_right']
        chart_top = boundaries['chart_top']
        chart_bottom = boundaries['chart_bottom']
        # 背景与网格
        if style == 'wind':
            draw.rectangle([chart_left, chart_top, chart_right, chart_bottom], 
                          fill='#f8f9fa', outline='#dee2e6', width=1)
            self._draw_wind_grid_lines(draw, chart_left, chart_right, chart_top, chart_bottom)
        # K 线宽度
        if len(dates) > 1:
            avg_spacing = (chart_right - chart_left) / len(dates)
            candle_width = max(1, int(avg_spacing * 0.7))
        else:
            candle_width = 3
        # 逐根绘制
        for i in range(len(dates)):
            x = int(dates[i])
            open_y = int(opens[i])
            high_y = int(highs[i])
            low_y = int(lows[i])
            close_y = int(closes[i])
            if not (chart_left <= x <= chart_right):
                continue
            is_up = close_y <= open_y  # 注意：y 方向向下
            if style == 'wind':
                if is_up:
                    fill_color = '#ff3333'; outline_color = '#cc0000'; shadow_color = '#cc0000'; is_hollow = False
                else:
                    fill_color = '#ffffff'; outline_color = '#008833'; shadow_color = '#008833'; is_hollow = True
            else:
                if is_up:
                    fill_color = outline_color = shadow_color = 'red'; is_hollow = False
                else:
                    fill_color = outline_color = shadow_color = 'green'; is_hollow = False
            # 影线
            shadow_width = 2 if style == 'wind' else 1
            draw.line([(x, high_y), (x, low_y)], fill=shadow_color, width=shadow_width)
            # 实体
            if abs(close_y - open_y) < 1:
                cross_width = int(candle_width)
                draw.line([(x - cross_width//2, close_y), (x + cross_width//2, close_y)], fill=outline_color, width=2)
            else:
                left = int(x - candle_width // 2)
                right = int(x + candle_width // 2)
                top = int(min(close_y, open_y))
                bottom = int(max(close_y, open_y))
                if style == 'wind' and is_hollow:
                    draw.rectangle([left, top, right, bottom], fill=fill_color, outline=outline_color, width=2)
                else:
                    draw.rectangle([left, top, right, bottom], fill=fill_color, outline=outline_color, width=1)
    
    def _draw_wind_grid_lines(self, draw, chart_left, chart_right, chart_top, chart_bottom):
        """绘制 Wind 风格网格线。"""
        grid_color = '#e1e5e9'
        grid_width = 1
        # 水平
        for i in range(1, 5):
            y = chart_top + (chart_bottom - chart_top) * i / 5
            draw.line([(chart_left, y), (chart_right, y)], fill=grid_color, width=grid_width)
        # 垂直（最多 8 条）
        if hasattr(self, '_dates_count') and self._dates_count > 0:
            grid_count = min(8, max(3, self._dates_count // 10))
            for i in range(1, grid_count):
                x = chart_left + (chart_right - chart_left) * i / grid_count
                draw.line([(x, chart_top), (x, chart_bottom)], fill=grid_color, width=grid_width)
    
    def draw_wind_axes_and_labels(self, draw, normalized_data, code="", style='wind'):
        """绘制 Wind 风格坐标轴与标签（可选简单风格）。"""
        boundaries = self.get_chart_boundaries(style)
        chart_left = boundaries['chart_left']
        chart_right = boundaries['chart_right']
        chart_top = boundaries['chart_top']
        chart_bottom = boundaries['chart_bottom']
        if style == 'wind':
            self._draw_wind_professional_axes(draw, normalized_data, code, chart_left, chart_right, chart_top, chart_bottom)
        else:
            self._draw_simple_axes(draw, normalized_data, chart_left, chart_right, chart_top, chart_bottom)
    
    def _draw_wind_professional_axes(self, draw, normalized_data, code, 
                                   chart_left, chart_right, chart_top, chart_bottom):
        """绘制 Wind 专业风格坐标轴与标签。"""
        # 坐标轴
        axis_color = '#2c3e50'
        axis_width = 2
        axis_font = self.get_chinese_font(11)
        draw.rectangle([chart_left, chart_top, chart_right, chart_bottom], outline=axis_color, width=axis_width)
        # 价格标签
        price_info = normalized_data['price_info']
        for i in range(9):
            ratio = i / 8
            price = price_info['display_min'] + (price_info['display_max'] - price_info['display_min']) * ratio
            y = chart_bottom - (chart_bottom - chart_top) * ratio
            if price >= 1000: price_text = f"{price:.0f}"
            elif price >= 100: price_text = f"{price:.1f}"
            else: price_text = f"{price:.2f}"
            text_bbox = draw.textbbox((0, 0), price_text, font=axis_font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            draw.text((chart_left - text_width - 10, y - text_height // 2), price_text, fill=axis_color, font=axis_font)
            draw.line([(chart_left - 5, y), (chart_left, y)], fill=axis_color, width=1)
        # 时间标签
        self._draw_wind_time_labels(draw, normalized_data, axis_font, axis_color, chart_left, chart_right, chart_bottom)
        # 标题
        if code:
            title_font = self.get_chinese_font(18)
            title = f"{code} 周K线图"
            draw.text((20, 20), title, fill='#2c3e50', font=title_font)
    
    def _draw_wind_time_labels(self, draw, normalized_data, font, color,
                             chart_left, chart_right, chart_bottom):
        """绘制 Wind 风格时间标签。"""
        date_info = normalized_data.get('date_info', {})
        start_date = date_info.get('start_date')
        end_date = date_info.get('end_date')
        if not start_date or not end_date:
            return
        dates_count = getattr(self, '_dates_count', len(normalized_data.get('dates', [])))
        num_labels = min(6, max(2, dates_count // 10))
        for i in range(num_labels):
            ratio = i / (num_labels - 1) if num_labels > 1 else 0
            x = chart_left + (chart_right - chart_left) * ratio
            if num_labels > 1:
                time_diff = (end_date - start_date) * ratio
                current_date = start_date + time_diff
            else:
                current_date = start_date
            time_text = current_date.strftime('%Y-%m') if dates_count > 104 else current_date.strftime('%m-%d')
            text_bbox = draw.textbbox((0, 0), time_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            draw.text((x - text_width // 2, chart_bottom + 10), time_text, fill=color, font=font)
            draw.line([(x, chart_bottom), (x, chart_bottom + 5)], fill=color, width=1)
    
    def _draw_simple_axes(self, draw, normalized_data, 
                         chart_left, chart_right, chart_top, chart_bottom):
        """绘制简单风格坐标轴与网格。"""
        draw.line([(chart_left, chart_top), (chart_left, chart_bottom)], fill='black', width=2)
        draw.line([(chart_left, chart_bottom), (chart_right, chart_bottom)], fill='black', width=2)
        price_info = normalized_data['price_info']
        price_range = price_info['display_max'] - price_info['display_min']
        num_price_labels = 5
        for i in range(num_price_labels + 1):
            price = price_info['display_min'] + (price_range * i / num_price_labels)
            y = chart_bottom - (chart_bottom - chart_top) * i / num_price_labels
            if i > 0 and i < num_price_labels:
                draw.line([(chart_left, y), (chart_right, y)], fill='lightgray', width=1)
            if chart_top <= y <= chart_bottom:
                price_text = f"{price:.2f}"
                try:
                    font = self.get_chinese_font(8)
                    text_bbox = draw.textbbox((0, 0), price_text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    draw.text((chart_left - text_width - 5, y - 5), price_text, fill='black', font=font)
                except:
                    pass
    
    def _generate_date_labels(self, date_index):
        """根据数据点数量自适配地生成不重叠的日期标签数组。"""
        if len(date_index) == 0:
            return []
        labels = []
        total_points = len(date_index)
        max_labels = (self.width - 120) // 60
        if total_points <= max_labels:
            step = 1
        else:
            step = max(1, total_points // max_labels)
        if step < 5 and total_points > 20:
            step = 5
        elif step < 10 and total_points > 40:
            step = 10
        for i in range(0, total_points, step):
            if i < len(date_index):
                date = date_index[i]
                label = date.strftime('%Y-%m') if hasattr(date, 'strftime') else str(date)[:7]
                labels.append((i, label))
        if total_points > 1 and (total_points - 1) % step != 0:
            last_date = date_index[-1]
            label = last_date.strftime('%Y-%m') if hasattr(last_date, 'strftime') else str(last_date)[:7]
            if len(labels) > 0:
                last_label_idx = labels[-1][0]
                if (total_points - 1) - last_label_idx >= 3:
                    labels.append((total_points - 1, label))
            else:
                labels.append((total_points - 1, label))
        return labels

    def get_fonts(self, font_size=14, small_font_size=10):
        """返回中文/英文字体（若不可用则回退到默认字体）。"""
        chinese_fonts = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/System/Library/Fonts/Arial Unicode MS.ttf",
            "/Library/Fonts/Arial Unicode MS.ttf",
            "/System/Library/Fonts/Arial.ttf",
        ]
        font = None
        small_font = None
        for font_path in chinese_fonts:
            try:
                if font_path.endswith('.ttc'):
                    font = ImageFont.truetype(font_path, font_size, index=0)
                    small_font = ImageFont.truetype(font_path, small_font_size, index=0)
                else:
                    font = ImageFont.truetype(font_path, font_size)
                    small_font = ImageFont.truetype(font_path, small_font_size)
                break
            except:
                continue
        if font is None:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        return font, small_font

    def normalize_price_for_display(self, price, price_info):
        """将真实价格映射为当前画布上的 y 坐标。"""
        if price_info['display_max'] == price_info['display_min']:
            return self.height // 2
        return ((price_info['display_max'] - price) / (price_info['display_max'] - price_info['display_min'])) * (self.height - 80) + 40 