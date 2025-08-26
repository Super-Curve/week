# -*- coding: utf-8 -*-
"""
高低点图表生成器 - 生成高亮显示关键高低点的K线图表
继承自基础图表生成器，专门用于展示波动率过滤后的高低点
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
from .base_chart_generator import BaseChartGenerator


class PivotChartGenerator(BaseChartGenerator):
    """
    高低点图表生成器

    用途:
    - 绘制原始周K图和带高低点标注图，区分 raw 与 filtered 枢轴，并绘制图例。

    实现方式:
    - 复用 BaseChartGenerator 的 Wind 风格绘制；根据 pivot_result 中的索引标注三角形
    - _draw_raw_pivots 使用浅色；_draw_filtered_pivots 使用醒目颜色；内置图例

    优点:
    - 与 HTML 输出配套，快速定位枢轴位置；视觉清晰

    局限:
    - 当前未直接在图上标注 meta（prominence/阈值/ATR%），如需可后续叠加文本
    - 大量点时可能遮挡，需控制点大小或抽样

    维护建议:
    - 保持 pivot_result 约定键名；如扩展标注，优先新增可选绘制开关
    """
    
    def __init__(self, output_dir="pivot_images", frequency_label: str = "周K线图"):
        # 使用Wind标准的K线图尺寸，更好地展示专业图表
        super().__init__(output_dir=output_dir, width=800, height=600)
        self.frequency_label = frequency_label
        
    def generate_original_chart(self, code, data, save_path=None):
        """
        生成Wind风格的原始K线图（无高低点标记）
        
        Args:
            code: 股票代码
            data: pandas DataFrame，包含OHLCV数据
            save_path: 保存路径，如果为None则自动生成
            
        Returns:
            str: 生成的图片路径
        """
        if save_path is None:
            save_path = os.path.join(self.output_dir, f"{code}_original.png")
        
        # 保存数据点数量用于网格线绘制
        self._dates_count = len(data) if len(data) > 0 else 0
        
        # 使用Wind风格的数据标准化
        normalized_data = self._normalize_data_wind_style(data)
        
        # 创建高分辨率图像 - Wind风格白色背景
        img = Image.new('RGB', (self.width, self.height), '#ffffff')
        draw = ImageDraw.Draw(img)
        
        # 绘制Wind风格标题
        self._draw_wind_chart_title(draw, code, data)
        
        # 绘制K线图
        self._draw_candlestick_chart(draw, normalized_data)
        
        # 绘制Wind风格坐标轴
        self._draw_wind_axes(draw, normalized_data, data)
        
        # 保存图片
        img.save(save_path, quality=95, optimize=True)
        return save_path

    def generate_pivot_chart(self, code, data, pivot_result, save_path=None):
        """
        生成Wind风格的带高低点标记的K线图
        
        Args:
            code: 股票代码
            data: pandas DataFrame，包含OHLCV数据
            pivot_result: 高低点分析结果
            save_path: 保存路径，如果为None则自动生成
            
        Returns:
            str: 生成的图片路径
        """
        if save_path is None:
            save_path = os.path.join(self.output_dir, f"{code}_pivot.png")
        
        # 保存数据点数量用于网格线绘制
        self._dates_count = len(data) if len(data) > 0 else 0
        
        # 使用Wind风格的数据标准化
        normalized_data = self._normalize_data_wind_style(data)
        
        # 创建高分辨率图像 - Wind风格白色背景
        img = Image.new('RGB', (self.width, self.height), '#ffffff')
        draw = ImageDraw.Draw(img)
        
        # 绘制Wind风格标题（高低点版本）
        self._draw_wind_pivot_title(draw, code, data, pivot_result)
        
        # 绘制K线图
        self._draw_candlestick_chart(draw, normalized_data)
        
        # 绘制Wind风格坐标轴
        self._draw_wind_axes(draw, normalized_data, data)
        
        # 高亮显示高低点
        self._draw_pivot_points(draw, normalized_data, pivot_result)

        # 标注T1（最低的已识别低点）
        self._draw_t1_annotation(draw, normalized_data, data, pivot_result)
        
        # 保存图片
        img.save(save_path, quality=95, optimize=True)
        return save_path
    
    def _normalize_data_wind_style(self, data):
        """Wind风格的数据标准化，适配新的图表区域"""
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
        
        dates = np.arange(len(close_prices))
        
        # 计算整体价格范围，保持真实比例
        global_min = np.min(low_prices)
        global_max = np.max(high_prices)
        
        # Wind风格：添加更大的边距以确保所有点都在图表区域内
        price_range = global_max - global_min
        margin = max(price_range * 0.1, price_range * 0.05 + 1)  # 至少10%边距
        # 优化：Y轴最小不低于0，避免出现负数刻度
        display_min = max(0, global_min - margin)
        display_max = global_max + margin
        
        # Wind风格的图表区域
        chart_top = 80
        chart_bottom = self.height - 120
        chart_left = 120
        chart_right = self.width - 80
        
        # 标准化价格数据到Wind图表区域
        def normalize_price(price):
            if display_max == display_min:
                return (chart_top + chart_bottom) // 2
            return chart_top + ((display_max - price) / (display_max - display_min)) * (chart_bottom - chart_top)
        
        # 标准化OHLC数据
        normalized_open = np.array([normalize_price(p) for p in open_prices])
        normalized_high = np.array([normalize_price(p) for p in high_prices])
        normalized_low = np.array([normalize_price(p) for p in low_prices])
        normalized_close = np.array([normalize_price(p) for p in close_prices])
        
        # 标准化日期到Wind图表区域
        if len(dates) > 1:
            normalized_dates = chart_left + (dates / (len(dates) - 1)) * (chart_right - chart_left)
        else:
            normalized_dates = np.array([(chart_left + chart_right) / 2])
        
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
                'date_labels': []
            }
        }
    
    def _draw_candlestick_chart(self, draw, normalized_data):
        """绘制Wind风格的专业K线图"""
        dates = normalized_data['dates']
        opens = normalized_data['open']
        highs = normalized_data['high']
        lows = normalized_data['low']
        closes = normalized_data['close']
        
        # 定义图表区域 - Wind风格的边距
        chart_left = 120
        chart_right = self.width - 80
        chart_top = 80
        chart_bottom = self.height - 120
        
        # 绘制图表背景
        draw.rectangle([chart_left, chart_top, chart_right, chart_bottom], 
                      fill='#f8f9fa', outline='#dee2e6', width=1)
        
        # 绘制网格线 - Wind风格
        self._draw_grid_lines(draw, chart_left, chart_right, chart_top, chart_bottom)
        
        # 计算K线宽度 - Wind标准
        total_width = chart_right - chart_left
        if len(dates) > 0:
            candle_spacing = total_width / len(dates)
            candle_width = max(3, min(12, candle_spacing * 0.7))  # 70%用于K线，30%用于间距
        else:
            candle_width = 6
        
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
            
            # Wind标准颜色
            if is_up:
                # 阳线：红色实心
                fill_color = '#ff3333'
                outline_color = '#cc0000'
                shadow_color = '#cc0000'
                is_hollow = False
            else:
                # 阴线：绿色空心（Wind标准）
                fill_color = '#ffffff'  # 白色填充
                outline_color = '#008833'
                shadow_color = '#008833'
                is_hollow = True
            
            # 绘制影线（上下影线）
            shadow_width = 2
            draw.line([(x, high_y), (x, low_y)], fill=shadow_color, width=shadow_width)
            
            # 计算实体位置
            if is_up:
                body_top = close_y
                body_bottom = open_y
            else:
                body_top = open_y
                body_bottom = close_y
            
            # 确保实体有最小高度
            if abs(body_top - body_bottom) < 1:
                # 十字星：绘制水平线
                cross_width = int(candle_width)
                draw.line([(x - cross_width//2, body_top), (x + cross_width//2, body_top)], 
                         fill=outline_color, width=2)
            else:
                # 绘制K线实体
                left = int(x - candle_width // 2)
                right = int(x + candle_width // 2)
                top = int(min(body_top, body_bottom))
                bottom = int(max(body_top, body_bottom))
                
                if is_hollow:
                    # 阴线：空心矩形（只有边框）
                    draw.rectangle([left, top, right, bottom], 
                                  fill=fill_color, outline=outline_color, width=2)
                else:
                    # 阳线：实心矩形
                    draw.rectangle([left, top, right, bottom], 
                                  fill=fill_color, outline=outline_color, width=1)
    
    def _draw_grid_lines(self, draw, chart_left, chart_right, chart_top, chart_bottom):
        """绘制Wind风格的网格线"""
        grid_color = '#e1e5e9'
        grid_width = 1
        
        # 水平网格线（5条）
        for i in range(1, 5):
            y = chart_top + (chart_bottom - chart_top) * i / 5
            draw.line([(chart_left, y), (chart_right, y)], 
                     fill=grid_color, width=grid_width)
        
        # 垂直网格线（根据数据点数量动态调整）
        if hasattr(self, '_dates_count') and self._dates_count > 0:
            grid_count = min(8, self._dates_count)  # 最多8条垂直线
            for i in range(1, grid_count):
                x = chart_left + (chart_right - chart_left) * i / grid_count
                draw.line([(x, chart_top), (x, chart_bottom)], 
                         fill=grid_color, width=grid_width)
    
    def _draw_pivot_points(self, draw, normalized_data, pivot_result):
        """绘制高低点标记"""
        if not pivot_result:
            return
        
        dates = normalized_data['dates']
        highs = normalized_data['high']
        lows = normalized_data['low']
        
        # 绘制原始高低点（浅色）
        self._draw_raw_pivots(draw, dates, highs, lows, pivot_result)
        
        # 绘制过滤后的关键高低点（醒目颜色）
        self._draw_filtered_pivots(draw, dates, highs, lows, pivot_result)
        
        # 绘制图例
        self._draw_pivot_legend(draw)
    
    def _draw_raw_pivots(self, draw, dates, highs, lows, pivot_result):
        """绘制原始高低点（被过滤掉的点用浅色显示）"""
        raw_highs = pivot_result.get('raw_pivot_highs', [])
        raw_lows = pivot_result.get('raw_pivot_lows', [])
        filtered_highs = set(pivot_result.get('filtered_pivot_highs', []))
        filtered_lows = set(pivot_result.get('filtered_pivot_lows', []))
        
        # 绘制被过滤掉的高点
        for idx in raw_highs:
            if idx not in filtered_highs and idx < len(dates):
                x = int(dates[idx])
                y = int(highs[idx])
                self._draw_pivot_marker(draw, x, y, 'high', '#ffcccc', 3)
        
        # 绘制被过滤掉的低点
        for idx in raw_lows:
            if idx not in filtered_lows and idx < len(dates):
                x = int(dates[idx])
                y = int(lows[idx])
                self._draw_pivot_marker(draw, x, y, 'low', '#ccffcc', 3)
    
    def _draw_filtered_pivots(self, draw, dates, highs, lows, pivot_result):
        """绘制过滤后的关键高低点"""
        filtered_highs = pivot_result.get('filtered_pivot_highs', [])
        filtered_lows = pivot_result.get('filtered_pivot_lows', [])
        
        # 绘制关键高点
        for idx in filtered_highs:
            if idx < len(dates):
                x = int(dates[idx])
                y = int(highs[idx])
                self._draw_pivot_marker(draw, x, y, 'high', '#ff0000', 6)
        
        # 绘制关键低点
        for idx in filtered_lows:
            if idx < len(dates):
                x = int(dates[idx])
                y = int(lows[idx])
                self._draw_pivot_marker(draw, x, y, 'low', '#0000ff', 6)
    
    def _draw_pivot_marker(self, draw, x, y, pivot_type, color, size):
        """绘制高低点标记"""
        if pivot_type == 'high':
            # 高点用向下的三角形
            points = [
                (x, y - size),
                (x - size, y + size),
                (x + size, y + size)
            ]
        else:
            # 低点用向上的三角形
            points = [
                (x, y + size),
                (x - size, y - size),
                (x + size, y - size)
            ]
        
        draw.polygon(points, fill=color, outline='black')
    
    def _draw_pivot_legend(self, draw):
        """绘制图例"""
        legend_x = self.width - 150
        legend_y = 70
        
        font = self._get_chinese_font(10)
        
        # 关键高点图例
        self._draw_pivot_marker(draw, legend_x, legend_y, 'high', '#ff0000', 4)
        draw.text((legend_x + 10, legend_y - 5), "关键高点", fill='black', font=font)
        
        # 关键低点图例
        self._draw_pivot_marker(draw, legend_x, legend_y + 20, 'low', '#0000ff', 4)
        draw.text((legend_x + 10, legend_y + 15), "关键低点", fill='black', font=font)
        
        # 被过滤点图例
        self._draw_pivot_marker(draw, legend_x, legend_y + 40, 'high', '#ffcccc', 3)
        draw.text((legend_x + 10, legend_y + 35), "过滤点", fill='gray', font=font)
    
    def _get_chinese_font(self, size):
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
    
    def _draw_wind_chart_title(self, draw, code, data):
        """绘制Wind风格的图表标题和信息"""
        title_font = self._get_chinese_font(18)
        info_font = self._get_chinese_font(12)
        
        # 主标题
        title = f"{code} {self.frequency_label}"
        draw.text((20, 20), title, fill='#2c3e50', font=title_font)
        
        # 添加时间范围和统计信息
        if len(data) > 0:
            start_date = data.index[0].strftime('%Y-%m-%d') if hasattr(data.index[0], 'strftime') else str(data.index[0])
            end_date = data.index[-1].strftime('%Y-%m-%d') if hasattr(data.index[-1], 'strftime') else str(data.index[-1])
            date_range = f"时间范围: {start_date} 至 {end_date}"
            draw.text((20, 50), date_range, fill='#7f8c8d', font=info_font)
            
            # 添加价格统计信息
            current_price = data['close'].iloc[-1]
            period_high = data['high'].max()
            period_low = data['low'].min()
            
            stats_text = f"当前价格: {current_price:.2f}  区间高点: {period_high:.2f}  区间低点: {period_low:.2f}"
            draw.text((self.width - 400, 50), stats_text, fill='#7f8c8d', font=info_font)

    def _draw_wind_axes(self, draw, normalized_data, original_data):
        """绘制Wind风格的坐标轴"""
        chart_left = 120
        chart_right = self.width - 80
        chart_top = 80
        chart_bottom = self.height - 120
        
        axis_font = self._get_chinese_font(11)
        
        # 绘制坐标轴边框
        axis_color = '#2c3e50'
        axis_width = 2
        
        # 左边框（Y轴）
        draw.line([(chart_left, chart_top), (chart_left, chart_bottom)], 
                 fill=axis_color, width=axis_width)
        # 底边框（X轴）
        draw.line([(chart_left, chart_bottom), (chart_right, chart_bottom)], 
                 fill=axis_color, width=axis_width)
        # 右边框
        draw.line([(chart_right, chart_top), (chart_right, chart_bottom)], 
                 fill=axis_color, width=1)
        # 顶边框
        draw.line([(chart_left, chart_top), (chart_right, chart_top)], 
                 fill=axis_color, width=1)
        
        # 绘制Y轴价格标签
        self._draw_wind_price_labels(draw, chart_left, chart_right, chart_top, chart_bottom, 
                                   normalized_data, original_data, axis_font)
        
        # 绘制X轴时间标签
        self._draw_wind_time_labels(draw, chart_left, chart_right, chart_bottom, 
                                  normalized_data, original_data, axis_font)
    
    def _draw_wind_price_labels(self, draw, chart_left, chart_right, chart_top, chart_bottom, 
                               normalized_data, original_data, font):
        """绘制Wind风格的价格标签"""
        price_info = normalized_data['price_info']
        min_price = price_info['display_min']
        max_price = price_info['display_max']
        
        # 绘制8个价格标签（Wind标准）
        for i in range(9):
            ratio = i / 8
            price = min_price + (max_price - min_price) * (1 - ratio)  # 从上到下
            y = chart_top + (chart_bottom - chart_top) * ratio
            
            # 格式化价格显示
            if price >= 100:
                price_text = f"{price:.1f}"
            elif price >= 10:
                price_text = f"{price:.2f}"
            else:
                price_text = f"{price:.3f}"
            
            # 绘制价格标签（左侧）
            text_bbox = draw.textbbox((0, 0), price_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            draw.text((chart_left - text_width - 10, y - 6), price_text, 
                     fill='#2c3e50', font=font)
            
            # 绘制刻度线
            draw.line([(chart_left - 5, y), (chart_left, y)], 
                     fill='#2c3e50', width=1)
            
            # 右侧也绘制刻度线
            draw.line([(chart_right, y), (chart_right + 5, y)], 
                     fill='#2c3e50', width=1)
    
    def _draw_wind_time_labels(self, draw, chart_left, chart_right, chart_bottom, 
                              normalized_data, original_data, font):
        """绘制Wind风格的时间标签"""
        if len(original_data) == 0:
            return
        
        # 选择关键时间点显示（不超过6个）
        dates = original_data.index
        total_periods = len(dates)
        
        if total_periods <= 6:
            # 少于6个周期，全部显示
            display_indices = list(range(total_periods))
        else:
            # 多于6个周期，选择关键点
            display_indices = [0]  # 起始点
            step = max(1, (total_periods - 1) // 4)
            for i in range(1, 5):
                idx = i * step
                # 避免与结束点重叠
                if idx < total_periods - 1:
                    display_indices.append(idx)
            # 确保结束点仅添加一次
            if (total_periods - 1) not in display_indices:
                display_indices.append(total_periods - 1)
            display_indices = sorted(set(display_indices))
        
        # 绘制时间标签
        chart_width = chart_right - chart_left
        for i, data_idx in enumerate(display_indices):
            if data_idx >= len(dates):
                continue
                
            date = dates[data_idx]
            x_ratio = data_idx / (total_periods - 1) if total_periods > 1 else 0
            x = chart_left + chart_width * x_ratio
            
            # 格式化日期
            if hasattr(date, 'strftime'):
                if total_periods > 52:  # 超过一年的数据，只显示年月
                    date_text = date.strftime('%Y-%m')
                else:  # 一年内的数据，显示月日
                    date_text = date.strftime('%m-%d')
            else:
                date_text = str(date)[:10]
            
            # 计算文本宽度并居中显示
            text_bbox = draw.textbbox((0, 0), date_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            
            draw.text((x - text_width//2, chart_bottom + 10), date_text, 
                     fill='#2c3e50', font=font)
            
            # 绘制刻度线
            draw.line([(x, chart_bottom), (x, chart_bottom + 5)], 
                     fill='#2c3e50', width=1)

    def _draw_wind_pivot_title(self, draw, code, data, pivot_result):
        """绘制Wind风格的高低点分析标题"""
        title_font = self._get_chinese_font(18)
        info_font = self._get_chinese_font(12)
        
        # 主标题
        title = f"{code} 高低点分析图（{self.frequency_label}）"
        draw.text((20, 20), title, fill='#2c3e50', font=title_font)
        
        # 分析结果摘要
        if pivot_result:
            high_count = len(pivot_result.get('filtered_pivot_highs', []))
            low_count = len(pivot_result.get('filtered_pivot_lows', []))
            accuracy = pivot_result.get('accuracy_score', 0)
            
            summary = f"识别结果: {high_count}个关键高点, {low_count}个关键低点  准确度: {accuracy:.1%}"
            draw.text((20, 50), summary, fill='#e74c3c', font=info_font)

            # 新增：优质评估（基于最低低点以来 R1/R2）
            premium = pivot_result.get('premium_metrics', {}) or {}
            is_premium = premium.get('is_premium', False)
            r1 = premium.get('annualized_volatility_pct', 0.0)
            r2 = premium.get('sharpe_ratio', 0.0)
            t1 = premium.get('t1')
            p1 = premium.get('p1')
            p1_text = f"{p1:.2f}" if p1 is not None else "-"
            if is_premium:
                premium_text = f"优质：是（R1={r1:.1f}%  R2={r2:.2f}；T1={t1 or '-'} P1={p1_text}）"
                fill_color = '#27ae60'
            else:
                premium_text = f"优质：否（R1={r1:.1f}%  R2={r2:.2f}；T1={t1 or '-'} P1={p1_text}）"
                fill_color = '#7f8c8d'
            draw.text((20, 68), premium_text, fill=fill_color, font=info_font)
        
        # 图例说明
        legend_text = "🔺红色-关键高点  🔻蓝色-关键低点  ○浅色-过滤点"
        draw.text((self.width - 350, 20), legend_text, fill='#7f8c8d', font=info_font)

    def _draw_chart_info(self, draw, code, pivot_result):
        """绘制图表标题和关键信息"""
        title_font = self._get_chinese_font(14)
        info_font = self._get_chinese_font(10)
        
        # 绘制标题
        title = f"{code} - 高低点分析"
        draw.text((10, 10), title, fill='black', font=title_font)
        
        # 绘制统计信息
        if pivot_result:
            stats_text = self._format_stats_text(pivot_result)
            y_offset = 30
            for line in stats_text:
                draw.text((10, y_offset), line, fill='black', font=info_font)
                y_offset += 12
    
    def _format_stats_text(self, pivot_result):
        """格式化统计信息文本"""
        lines = []
        
        # 基本统计
        filtered_highs = len(pivot_result.get('filtered_pivot_highs', []))
        filtered_lows = len(pivot_result.get('filtered_pivot_lows', []))
        lines.append(f"关键点: {filtered_highs}高 + {filtered_lows}低")
        
        # 准确度
        accuracy = pivot_result.get('accuracy_score', 0)
        lines.append(f"准确度: {accuracy:.1%}")
        
        # 波动率信息
        volatility_metrics = pivot_result.get('volatility_metrics', {})
        if 'atr_percentage' in volatility_metrics:
            avg_vol = np.nanmean(volatility_metrics['atr_percentage'])
            lines.append(f"平均波动率: {avg_vol:.2f}%")
        
        # 过滤效果
        filter_effectiveness = pivot_result.get('filter_effectiveness', {})
        if 'filter_ratio' in filter_effectiveness:
            filter_ratio = filter_effectiveness['filter_ratio']
            lines.append(f"过滤比例: {filter_ratio:.1%}")
        
        return lines
    
    def _draw_axes(self, draw, normalized_data):
        """绘制坐标轴和标签"""
        # 绘制坐标轴线
        chart_left = 80
        chart_right = self.width - 60
        chart_top = 60
        chart_bottom = self.height - 80
        
        # Y轴
        draw.line([(chart_left, chart_top), (chart_left, chart_bottom)], fill='black', width=1)
        # X轴
        draw.line([(chart_left, chart_bottom), (chart_right, chart_bottom)], fill='black', width=1)
        
        try:
            font = ImageFont.truetype("arial.ttf", 9)
        except:
            font = ImageFont.load_default()
        
        # Y轴价格标签
        price_info = normalized_data['price_info']
        min_price = price_info['display_min']
        max_price = price_info['display_max']
        
        # 绘制5个价格标签
        for i in range(5):
            ratio = i / 4
            price = min_price + (max_price - min_price) * ratio
            y = chart_bottom - (chart_bottom - chart_top) * ratio
            
            # 价格标签
            price_text = f"{price:.2f}"
            draw.text((chart_left - 35, y - 6), price_text, fill='black', font=font)
            
            # 网格线
            draw.line([(chart_left, y), (chart_right, y)], fill='lightgray', width=1)
        
        # X轴时间标签（显示起始和结束时间）
        date_info = normalized_data['date_info']
        if date_info['start_date'] and date_info['end_date']:
            start_text = date_info['start_date'].strftime("%Y-%m")
            end_text = date_info['end_date'].strftime("%Y-%m")
            
            # 计算结束文本的宽度，避免重叠
            end_bbox = draw.textbbox((0, 0), end_text, font=font)
            end_width = end_bbox[2] - end_bbox[0]
            
            draw.text((chart_left, chart_bottom + 5), start_text, fill='black', font=font)
            draw.text((chart_right - end_width - 10, chart_bottom + 5), end_text, fill='black', font=font)

    def _draw_t1_annotation(self, draw, normalized_data, original_data, pivot_result):
        """在图上标注T1（识别低点中的最低点）。"""
        try:
            filtered_lows = pivot_result.get('filtered_pivot_lows', []) or []
            if not filtered_lows:
                return
            lows = original_data['low'].values
            valid = [idx for idx in filtered_lows if 0 <= idx < len(lows)]
            if not valid:
                return
            t1_idx = min(valid, key=lambda i: lows[i])
            dates = normalized_data['dates']
            low_y = normalized_data['low']
            if t1_idx >= len(dates) or t1_idx >= len(low_y):
                return
            x = int(dates[t1_idx])
            y = int(low_y[t1_idx])
            # 画一个高亮圆圈和“T1”标签
            radius = 8
            draw.ellipse([(x - radius, y - radius), (x + radius, y + radius)], outline='#f39c12', width=3)
            font = self._get_chinese_font(12)
            label = "T1"
            # 标签稍微偏右上，避免遮挡K线
            draw.text((x + radius + 3, y - radius - 2), label, fill='#f39c12', font=font)
        except Exception:
            return
    
    def generate_charts_batch(self, stock_data_dict, pivot_results_dict, max_charts=None):
        """
        批量生成原始K线图和高低点图表
        
        Args:
            stock_data_dict: 股票数据字典 {code: DataFrame}
            pivot_results_dict: 高低点分析结果字典 {code: pivot_result}
            max_charts: 最大生成图表数量
            
        Returns:
            dict: 生成的图表路径字典 {code: {'original': path, 'pivot': path}}
        """
        chart_paths = {}
        generated_count = 0
        
        print(f"开始批量生成K线图表（原始图 + 高低点图）...")
        
        for code in pivot_results_dict:
            if max_charts and generated_count >= max_charts:
                break
                
            if code not in stock_data_dict:
                print(f"警告: 股票 {code} 的数据不存在，跳过")
                continue
            
            try:
                # 生成原始K线图
                original_path = self.generate_original_chart(
                    code, 
                    stock_data_dict[code]
                )
                
                # 生成高低点标记图
                pivot_path = self.generate_pivot_chart(
                    code, 
                    stock_data_dict[code], 
                    pivot_results_dict[code]
                )
                
                chart_paths[code] = {
                    'original': original_path,
                    'pivot': pivot_path
                }
                generated_count += 1
                
                if generated_count % 10 == 0:
                    print(f"已生成 {generated_count} 个股票的图表（共 {generated_count * 2} 张图）...")
                    
            except Exception as e:
                print(f"生成 {code} 的图表时出错: {e}")
                continue
        
        print(f"批量生成完成，共生成 {generated_count} 个股票的图表（{generated_count * 2} 张图）")
        return chart_paths