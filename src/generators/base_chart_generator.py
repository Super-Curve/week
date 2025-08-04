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

    # ========== 统一的Wind风格K线绘制方法 ==========
    
    def get_chinese_font(self, size):
        """获取支持中文的字体"""
        # macOS中文字体列表
        chinese_fonts = [
            "/System/Library/Fonts/PingFang.ttc",  # macOS系统字体
            "/System/Library/Fonts/STHeiti Light.ttc",  # macOS黑体
            "/System/Library/Fonts/Helvetica.ttc",  # 英文字体
            "/System/Library/Fonts/Arial.ttf",  # Arial
        ]
        
        for font_path in chinese_fonts:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        
        # 如果都没找到，使用默认字体
        return ImageFont.load_default()
    
    def get_chart_boundaries(self, style='wind'):
        """获取图表区域边界"""
        if style == 'wind':
            # Wind专业风格
            return {
                'chart_left': 120,
                'chart_right': self.width - 80,
                'chart_top': 80,
                'chart_bottom': self.height - 120
            }
        else:
            # 传统风格（向后兼容）
            return {
                'chart_left': 60,
                'chart_right': self.width - 10,
                'chart_top': 40,
                'chart_bottom': self.height - 30
            }
    
    def draw_wind_candlestick_chart(self, draw, normalized_data, style='wind', show_volume=False):
        """
        统一的Wind风格K线绘制方法
        
        Args:
            draw: PIL ImageDraw对象
            normalized_data: 标准化后的数据
            style: 'wind' 专业风格 | 'simple' 简单风格
            show_volume: 是否显示成交量
        """
        dates = normalized_data['dates']
        opens = normalized_data['open']
        highs = normalized_data['high']
        lows = normalized_data['low']
        closes = normalized_data['close']
        
        if len(dates) == 0:
            return
        
        # 获取图表边界
        boundaries = self.get_chart_boundaries(style)
        chart_left = boundaries['chart_left']
        chart_right = boundaries['chart_right']
        chart_top = boundaries['chart_top']
        chart_bottom = boundaries['chart_bottom']
        
        # 绘制图表背景和网格（Wind风格）
        if style == 'wind':
            # 填充图表区域背景
            draw.rectangle([chart_left, chart_top, chart_right, chart_bottom], 
                          fill='#f8f9fa', outline='#dee2e6', width=1)
            
            # 绘制网格线
            self._draw_wind_grid_lines(draw, chart_left, chart_right, chart_top, chart_bottom)
        
        # 计算K线宽度
        if len(dates) > 1:
            avg_spacing = (chart_right - chart_left) / len(dates)
            candle_width = max(1, int(avg_spacing * 0.7))  # 70%的间距作为K线宽度
        else:
            candle_width = 3
        
        # 绘制每根K线
        for i in range(len(dates)):
            x = int(dates[i])
            open_y = int(opens[i])
            high_y = int(highs[i])
            low_y = int(lows[i])
            close_y = int(closes[i])
            
            # 确保坐标在图表区域内
            if not (chart_left <= x <= chart_right):
                continue
            
            # 判断涨跌
            is_up = close_y <= open_y  # 注意：y坐标是反向的
            
            # 设置颜色
            if style == 'wind':
                if is_up:
                    # 阳线：红色实心
                    fill_color = '#ff3333'
                    outline_color = '#cc0000'
                    shadow_color = '#cc0000'
                    is_hollow = False
                else:
                    # 阴线：绿色空心
                    fill_color = '#ffffff'  # 白色填充
                    outline_color = '#008833'
                    shadow_color = '#008833'
                    is_hollow = True
            else:
                # 简单风格（向后兼容）
                if is_up:
                    fill_color = outline_color = shadow_color = 'red'
                    is_hollow = False
                else:
                    fill_color = outline_color = shadow_color = 'green'
                    is_hollow = False
            
            # 绘制影线（上下影线）
            shadow_width = 2 if style == 'wind' else 1
            draw.line([(x, high_y), (x, low_y)], fill=shadow_color, width=shadow_width)
            
            # 计算实体位置
            if is_up:
                body_top = close_y
                body_bottom = open_y
            else:
                body_top = open_y
                body_bottom = close_y
            
            # 绘制K线实体
            if abs(body_top - body_bottom) < 1:
                # 十字星：绘制水平线
                cross_width = int(candle_width)
                draw.line([(x - cross_width//2, body_top), (x + cross_width//2, body_top)], 
                         fill=outline_color, width=2)
            else:
                # 绘制实体矩形
                left = int(x - candle_width // 2)
                right = int(x + candle_width // 2)
                top = int(min(body_top, body_bottom))
                bottom = int(max(body_top, body_bottom))
                
                if style == 'wind' and is_hollow:
                    # Wind风格阴线：空心矩形
                    draw.rectangle([left, top, right, bottom], 
                                  fill=fill_color, outline=outline_color, width=2)
                else:
                    # 实心矩形
                    line_width = 1 if style == 'wind' else 1
                    draw.rectangle([left, top, right, bottom], 
                                  fill=fill_color, outline=outline_color, width=line_width)
    
    def _draw_wind_grid_lines(self, draw, chart_left, chart_right, chart_top, chart_bottom):
        """绘制Wind风格的网格线"""
        grid_color = '#e1e5e9'
        grid_width = 1
        
        # 水平网格线 (5条)
        for i in range(1, 5):
            y = chart_top + (chart_bottom - chart_top) * i / 5
            draw.line([(chart_left, y), (chart_right, y)], 
                     fill=grid_color, width=grid_width)
        
        # 垂直网格线 (最多8条，根据数据点数量动态调整)
        if hasattr(self, '_dates_count') and self._dates_count > 0:
            grid_count = min(8, max(3, self._dates_count // 10))
            for i in range(1, grid_count):
                x = chart_left + (chart_right - chart_left) * i / grid_count
                draw.line([(x, chart_top), (x, chart_bottom)], 
                         fill=grid_color, width=grid_width)
    
    def draw_wind_axes_and_labels(self, draw, normalized_data, code="", style='wind'):
        """
        统一的Wind风格坐标轴和标签绘制
        
        Args:
            draw: PIL ImageDraw对象
            normalized_data: 标准化后的数据
            code: 股票代码
            style: 'wind' 专业风格 | 'simple' 简单风格
        """
        boundaries = self.get_chart_boundaries(style)
        chart_left = boundaries['chart_left']
        chart_right = boundaries['chart_right']
        chart_top = boundaries['chart_top']
        chart_bottom = boundaries['chart_bottom']
        
        if style == 'wind':
            # Wind专业风格的坐标轴
            self._draw_wind_professional_axes(draw, normalized_data, code, 
                                            chart_left, chart_right, chart_top, chart_bottom)
        else:
            # 简单风格的坐标轴（向后兼容）
            self._draw_simple_axes(draw, normalized_data, 
                                 chart_left, chart_right, chart_top, chart_bottom)
    
    def _draw_wind_professional_axes(self, draw, normalized_data, code, 
                                   chart_left, chart_right, chart_top, chart_bottom):
        """绘制Wind专业风格的坐标轴"""
        # 坐标轴颜色和字体
        axis_color = '#2c3e50'
        axis_width = 2
        axis_font = self.get_chinese_font(11)
        
        # 绘制坐标轴边框
        draw.rectangle([chart_left, chart_top, chart_right, chart_bottom], 
                      outline=axis_color, width=axis_width)
        
        # 绘制价格标签（Y轴）
        price_info = normalized_data['price_info']
        for i in range(9):  # 9个价格点
            ratio = i / 8
            price = price_info['display_min'] + (price_info['display_max'] - price_info['display_min']) * ratio
            y = chart_bottom - (chart_bottom - chart_top) * ratio
            
            # 格式化价格
            if price >= 1000:
                price_text = f"{price:.0f}"
            elif price >= 100:
                price_text = f"{price:.1f}"
            else:
                price_text = f"{price:.2f}"
            
            # 绘制价格标签
            text_bbox = draw.textbbox((0, 0), price_text, font=axis_font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            draw.text((chart_left - text_width - 10, y - text_height // 2), 
                     price_text, fill=axis_color, font=axis_font)
            
            # 绘制价格刻度线
            draw.line([(chart_left - 5, y), (chart_left, y)], 
                     fill=axis_color, width=1)
        
        # 绘制时间标签（X轴）
        self._draw_wind_time_labels(draw, normalized_data, axis_font, axis_color,
                                  chart_left, chart_right, chart_bottom)
        
        # 绘制标题
        if code:
            title_font = self.get_chinese_font(18)
            title = f"{code} 周K线图"
            draw.text((20, 20), title, fill='#2c3e50', font=title_font)
    
    def _draw_wind_time_labels(self, draw, normalized_data, font, color,
                             chart_left, chart_right, chart_bottom):
        """绘制Wind风格的时间标签"""
        date_info = normalized_data.get('date_info', {})
        start_date = date_info.get('start_date')
        end_date = date_info.get('end_date')
        
        if not start_date or not end_date:
            return
        
        # 根据数据长度决定显示的时间点数量
        dates_count = getattr(self, '_dates_count', len(normalized_data.get('dates', [])))
        num_labels = min(6, max(2, dates_count // 10))
        
        for i in range(num_labels):
            ratio = i / (num_labels - 1) if num_labels > 1 else 0
            x = chart_left + (chart_right - chart_left) * ratio
            
            # 计算对应的日期
            if num_labels > 1:
                time_diff = (end_date - start_date) * ratio
                current_date = start_date + time_diff
            else:
                current_date = start_date
            
            # 格式化时间标签
            if dates_count > 104:  # 超过2年数据，显示年-月
                time_text = current_date.strftime('%Y-%m')
            else:  # 显示月-日
                time_text = current_date.strftime('%m-%d')
            
            # 绘制时间标签
            text_bbox = draw.textbbox((0, 0), time_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            
            draw.text((x - text_width // 2, chart_bottom + 10), 
                     time_text, fill=color, font=font)
            
            # 绘制时间刻度线
            draw.line([(x, chart_bottom), (x, chart_bottom + 5)], 
                     fill=color, width=1)
    
    def _draw_simple_axes(self, draw, normalized_data, 
                         chart_left, chart_right, chart_top, chart_bottom):
        """绘制简单风格的坐标轴（向后兼容）"""
        # 绘制坐标轴
        draw.line([(chart_left, chart_top), (chart_left, chart_bottom)], fill='black', width=2)  # Y轴
        draw.line([(chart_left, chart_bottom), (chart_right, chart_bottom)], fill='black', width=2)  # X轴
        
        # 简单的价格标签
        price_info = normalized_data['price_info']
        price_range = price_info['display_max'] - price_info['display_min']
        
        num_price_labels = 5
        for i in range(num_price_labels + 1):
            price = price_info['display_min'] + (price_range * i / num_price_labels)
            # 这里需要一个简单的价格转换方法
            y = chart_bottom - (chart_bottom - chart_top) * i / num_price_labels
            
            # 绘制水平网格线
            if i > 0 and i < num_price_labels:
                draw.line([(chart_left, y), (chart_right, y)], fill='lightgray', width=1)
            
            # 绘制价格标签
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