#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
from .base_chart_generator import BaseChartGenerator

class UptrendChartGenerator(BaseChartGenerator):
    def __init__(self, output_dir="uptrend_images"):
        # 调用父类初始化，设置默认尺寸为400x300
        super().__init__(output_dir=output_dir, width=400, height=300)

    def _draw_candlestick_chart(self, draw, normalized_data):
        """绘制K线图"""
        dates = normalized_data['dates']
        opens = normalized_data['open']
        highs = normalized_data['high']
        lows = normalized_data['low']
        closes = normalized_data['close']
        
        # 定义图表区域边界
        chart_left = 60
        chart_right = self.width - 10
        chart_top = 40
        chart_bottom = self.height - 30
        
        # K线宽度
        candle_width = 3
        
        for i in range(len(dates)):
            x = dates[i]
            open_y = opens[i]
            high_y = highs[i]
            low_y = lows[i]
            close_y = closes[i]
            
            # 确保坐标在图表区域内
            if not (chart_left <= x <= chart_right):
                continue
            
            # 绘制影线（最高价到最低价）
            draw.line([(x, high_y), (x, low_y)], fill='black', width=1)
            
            # 绘制实体（开盘价到收盘价）
            if close_y >= open_y:
                # 阳线（收盘价高于开盘价）
                color = 'red'
                body_top = open_y
                body_bottom = close_y
            else:
                # 阴线（收盘价低于开盘价）
                color = 'green'
                body_top = close_y
                body_bottom = open_y
            
            # 绘制K线实体
            if abs(body_bottom - body_top) > 1:  # 只有当实体有高度时才绘制
                draw.rectangle([
                    (x - candle_width//2, body_top),
                    (x + candle_width//2, body_bottom)
                ], fill=color, outline=color)
            else:
                # 十字星（开盘价等于收盘价）
                draw.line([(x - candle_width//2, body_top), (x + candle_width//2, body_top)], fill='black', width=1)

    def _draw_axes_and_grid(self, draw, normalized_data):
        """绘制坐标轴和网格"""
        # 定义图表区域边界
        chart_left = 60
        chart_right = self.width - 10
        chart_top = 40
        chart_bottom = self.height - 30
        
        # 绘制坐标轴
        draw.line([(chart_left, chart_top), (chart_left, chart_bottom)], fill='black', width=2)  # Y轴
        draw.line([(chart_left, chart_bottom), (chart_right, chart_bottom)], fill='black', width=2)  # X轴
        
        # 绘制价格标签
        price_info = normalized_data['price_info']
        price_range = price_info['display_max'] - price_info['display_min']
        
        # 计算价格标签位置
        num_price_labels = 5
        for i in range(num_price_labels + 1):
            price = price_info['display_min'] + (price_range * i / num_price_labels)
            y = self.normalize_price_for_display(price, price_info)
            
            # 绘制水平网格线
            if i > 0 and i < num_price_labels:
                draw.line([(chart_left, y), (chart_right, y)], fill='lightgray', width=1)
            
            # 绘制价格标签
            if chart_top <= y <= chart_bottom:
                price_text = f"{price:.2f}"
                font, _ = self.get_fonts(8, 8)
                text_bbox = draw.textbbox((0, 0), price_text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                draw.text((chart_left - text_width - 5, y - 5), price_text, fill='black', font=font)
        
        # 绘制日期标签
        date_info = normalized_data['date_info']
        for idx, label in date_info['date_labels']:
            if 0 <= idx < len(normalized_data['dates']):
                x = normalized_data['dates'][idx]
                if chart_left <= x <= chart_right:
                    font, _ = self.get_fonts(8, 8)
                    text_bbox = draw.textbbox((0, 0), label, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    draw.text((x - text_width//2, chart_bottom + 5), label, fill='black', font=font)

    def generate_uptrend_chart(self, code, data, channel_result):
        """生成上升通道图表"""
        try:
            # 标准化数据
            normalized_data = self.normalize_data(data)
            
            if len(normalized_data['dates']) < 2:
                return None
            
            img = Image.new('RGB', (self.width, self.height), color='white')
            draw = ImageDraw.Draw(img)
            
            # 绘制坐标轴和网格
            self._draw_axes_and_grid(draw, normalized_data)
            
            # 绘制K线图
            self._draw_candlestick_chart(draw, normalized_data)
            
            # 绘制上升通道
            self._draw_uptrend_channel(draw, channel_result, normalized_data)
            
            # 绘制通道信息
            self._draw_channel_info(draw, code, channel_result, normalized_data['price_info'])
            
            image_path = os.path.join(self.output_dir, f"uptrend_{code}.png")
            img.save(image_path, 'PNG', optimize=True)
            return image_path
            
        except Exception as e:
            print(f"生成上升通道图表失败 {code}: {e}")
            return None

    def _draw_uptrend_channel(self, draw, channel_result, normalized_data):
        """绘制上升通道"""
        try:
            price_info = normalized_data['price_info']
            dates = normalized_data['dates']
            
            # 获取通道数据
            upper_channel = channel_result['upper_channel']
            lower_channel = channel_result['lower_channel']
            channel_quality = channel_result['channel_quality']
            
            # 绘制上轨线
            self._draw_channel_line(draw, upper_channel, dates, price_info, 'upper', 'blue')
            
            # 绘制下轨线
            self._draw_channel_line(draw, lower_channel, dates, price_info, 'lower', 'green')
            
            # 填充通道区域
            self._fill_channel_area(draw, upper_channel, lower_channel, dates, price_info)
            
            # 标记关键点
            self._mark_key_points(draw, channel_result, normalized_data)
            
        except Exception as e:
            print(f"绘制上升通道失败: {e}")

    def _draw_channel_line(self, draw, channel_data, dates, price_info, line_type, color):
        """绘制通道线"""
        try:
            slope = channel_data['slope']
            intercept = channel_data['intercept']
            
            # 计算线的起点和终点
            start_idx = channel_data['start_idx']
            end_idx = channel_data['end_idx']
            
            # 确保索引在有效范围内
            if start_idx >= len(dates) or end_idx >= len(dates):
                return
            
            # 计算线的坐标
            x1 = dates[start_idx]
            x2 = dates[end_idx]
            
            y1 = self.normalize_price_for_display(slope * start_idx + intercept, price_info)
            y2 = self.normalize_price_for_display(slope * end_idx + intercept, price_info)
            
            # 绘制线
            line_width = 3 if line_type == 'upper' else 2
            draw.line([(x1, y1), (x2, y2)], fill=color, width=line_width)
            
            # 添加标签
            font, _ = self.get_fonts()
            label = "上轨线" if line_type == 'upper' else "下轨线"
            draw.text((x2 + 5, y2 - 10), label, fill=color, font=font)
            
        except Exception as e:
            print(f"绘制{line_type}通道线失败: {e}")

    def _fill_channel_area(self, draw, upper_channel, lower_channel, dates, price_info):
        """填充通道区域（优化版 - 完全不遮挡K线）"""
        try:
            # 获取通道范围
            start_idx = min(upper_channel['start_idx'], lower_channel['start_idx'])
            end_idx = max(upper_channel['end_idx'], lower_channel['end_idx'])
            
            # 确保索引在有效范围内
            if start_idx >= len(dates) or end_idx >= len(dates):
                return
            
            # 创建通道区域的点
            points = []
            
            # 上轨线点
            for i in range(start_idx, end_idx + 1):
                if i < len(dates):
                    x = dates[i]
                    upper_price = upper_channel['slope'] * i + upper_channel['intercept']
                    y = self.normalize_price_for_display(upper_price, price_info)
                    points.append((x, y))
            
            # 下轨线点（反向）
            for i in range(end_idx, start_idx - 1, -1):
                if i < len(dates):
                    x = dates[i]
                    lower_price = lower_channel['slope'] * i + lower_channel['intercept']
                    y = self.normalize_price_for_display(lower_price, price_info)
                    points.append((x, y))
            
            # 完全不填充，只绘制虚线边框来标识通道区域
            if len(points) > 2:
                # 移除填充，只保留边框
                self._draw_channel_border(draw, points, start_idx, end_idx)
                
        except Exception as e:
            print(f"绘制通道边框失败: {e}")
    
    def _draw_channel_border(self, draw, points, start_idx, end_idx):
        """绘制通道边框（虚线，不遮挡K线）"""
        try:
            # 分离上轨线和下轨线点
            mid_point = len(points) // 2
            upper_points = points[:mid_point]
            lower_points = points[mid_point:]
            
            # 绘制上轨线虚线边框（更细的线，更淡的颜色）
            if len(upper_points) > 1:
                for i in range(len(upper_points) - 1):
                    if i % 4 == 0:  # 每4个点绘制一段，减少密度
                        draw.line([upper_points[i], upper_points[i+1]], 
                                fill=(100, 149, 237, 60), width=1)  # 更淡的蓝色虚线
            
            # 绘制下轨线虚线边框（更细的线，更淡的颜色）
            if len(lower_points) > 1:
                for i in range(len(lower_points) - 1):
                    if i % 4 == 0:  # 每4个点绘制一段，减少密度
                        draw.line([lower_points[i], lower_points[i+1]], 
                                fill=(34, 139, 34, 60), width=1)  # 更淡的绿色虚线
                                
        except Exception as e:
            print(f"绘制通道边框失败: {e}")

    def _mark_key_points(self, draw, channel_result, normalized_data):
        """标记关键点"""
        try:
            price_info = normalized_data['price_info']
            dates = normalized_data['dates']
            highs = normalized_data['high']
            lows = normalized_data['low']
            
            upper_channel = channel_result['upper_channel']
            lower_channel = channel_result['lower_channel']
            
            # 标记上轨线的关键点
            start_idx = upper_channel['start_idx']
            end_idx = upper_channel['end_idx']
            
            for idx in [start_idx, end_idx]:
                if idx < len(dates):
                    x = dates[idx]
                    upper_price = upper_channel['slope'] * idx + upper_channel['intercept']
                    y = self.normalize_price_for_display(upper_price, price_info)
                    
                    # 绘制蓝色圆点
                    draw.ellipse([(x-4, y-4), (x+4, y+4)], fill='blue', outline='darkblue', width=2)
            
            # 标记下轨线的关键点
            start_idx = lower_channel['start_idx']
            end_idx = lower_channel['end_idx']
            
            for idx in [start_idx, end_idx]:
                if idx < len(dates):
                    x = dates[idx]
                    lower_price = lower_channel['slope'] * idx + lower_channel['intercept']
                    y = self.normalize_price_for_display(lower_price, price_info)
                    
                    # 绘制绿色圆点
                    draw.ellipse([(x-4, y-4), (x+4, y+4)], fill='green', outline='darkgreen', width=2)
                    
        except Exception as e:
            print(f"标记关键点失败: {e}")

    def _draw_channel_info(self, draw, code, channel_result, price_info):
        """绘制通道信息（优化版 - 支持入场信号）"""
        try:
            font, small_font = self.get_fonts()
            
            # 基本信息
            draw.text((10, 10), f"STOCK: {code}", fill='black', font=font)
            
            # 检查是否为入场信号
            is_entry_signal = channel_result.get('is_entry_signal', False)
            
            if is_entry_signal:
                # 入场信号信息
                entry_strength = channel_result.get('entry_strength', 0)
                recommendation = channel_result.get('recommendation', '')
                
                # 入场信号评分（红色突出显示）
                draw.text((10, 30), f"入场信号: {entry_strength:.3f}", fill='red', font=font)
                draw.text((10, 50), f"建议: {recommendation}", fill='red', font=small_font)
                
                # 最近趋势信息
                if 'recent_trend' in channel_result:
                    trend = channel_result['recent_trend']
                    draw.text((10, 70), f"趋势斜率: {trend['slope']:.4f}", fill='blue', font=small_font)
                    draw.text((10, 85), f"趋势强度: {trend['r2']:.2f}", fill='blue', font=small_font)
                    draw.text((10, 100), f"价格变化: {trend['price_change']:.1%}", fill='green', font=small_font)
                
                # 通道分析信息
                if 'channel_analysis' in channel_result:
                    analysis = channel_result['channel_analysis']
                    draw.text((10, 115), f"通道宽度: {analysis['channel_width']:.1%}", fill='purple', font=small_font)
                    draw.text((10, 130), f"价格位置: {analysis['price_position']:.1%}", fill='purple', font=small_font)
                
            else:
                # 传统通道信息
                quality_score = channel_result.get('quality_score', 0)
                enhanced_score = channel_result.get('enhanced_quality_score', quality_score)
                draw.text((10, 30), f"评分: {enhanced_score:.3f}", fill='purple', font=small_font)
            
            # 通道特征
            if 'channel_quality' in channel_result:
                quality = channel_result['channel_quality']
                draw.text((10, 45), f"持续时间: {quality['duration']}周", fill='blue', font=small_font)
                draw.text((10, 60), f"通道宽度: {quality['channel_width_pct']:.1%}", fill='blue', font=small_font)
            
            if 'channel_features' in channel_result:
                features = channel_result['channel_features']
                draw.text((10, 75), f"通道强度: {features['channel_strength']:.2f}", fill='green', font=small_font)
                draw.text((10, 90), f"突破次数: {features['breakout_attempts']}", fill='orange', font=small_font)
            
            # 价格信息
            draw.text((10, 105), f"价格范围: {price_info['global_min']:.2f}-{price_info['global_max']:.2f}", 
                     fill='black', font=small_font)
            
            # 技术指标摘要
            if 'talib_analysis' in channel_result:
                talib_data = channel_result['talib_analysis']
                y_pos = 120
                
                if 'trend_strength' in talib_data:
                    trend = talib_data['trend_strength']
                    if trend.get('trend_strength') == 'strong':
                        draw.text((10, y_pos), "✓ 趋势强度高", fill='green', font=small_font)
                        y_pos += 15
                    if trend.get('trend_direction') == 'bullish':
                        draw.text((10, y_pos), "✓ 趋势向上", fill='green', font=small_font)
                        y_pos += 15
                
                if 'momentum' in talib_data:
                    momentum = talib_data['momentum']
                    if momentum.get('macd_bullish'):
                        draw.text((10, y_pos), "✓ MACD多头", fill='green', font=small_font)
                        y_pos += 15
                    
                    rsi = momentum.get('rsi', 50)
                    if 30 <= rsi <= 70:
                        draw.text((10, y_pos), f"RSI: {rsi:.0f} (正常)", fill='blue', font=small_font)
                    elif rsi > 70:
                        draw.text((10, y_pos), f"RSI: {rsi:.0f} (超买)", fill='red', font=small_font)
                    else:
                        draw.text((10, y_pos), f"RSI: {rsi:.0f} (超卖)", fill='orange', font=small_font)
            
        except Exception as e:
            print(f"绘制通道信息失败: {e}")

    def normalize_price_for_display(self, price, price_info):
        """标准化价格用于显示"""
        if price_info['display_max'] == price_info['display_min']:
            return self.height // 2
        return ((price_info['display_max'] - price) / (price_info['display_max'] - price_info['display_min'])) * (self.height - 80) + 40 