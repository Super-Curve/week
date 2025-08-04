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
        """
        绘制K线图 - 已重构为使用统一的Wind风格方法
        保留此方法为向后兼容
        """
        # 使用统一的方法，但保持简单风格
        self.draw_wind_candlestick_chart(draw, normalized_data, style='simple')

    def _draw_axes_and_grid(self, draw, normalized_data):
        """
        绘制坐标轴和网格 - 已重构为使用统一的Wind风格方法
        保留此方法为向后兼容
        """
        # 使用统一的方法，但保持简单风格
        self.draw_wind_axes_and_labels(draw, normalized_data, style='simple')

    def generate_uptrend_chart(self, code, data, channel_result):
        """生成上升通道图表 - 显示完整一年K线图，标注最近上升通道"""
        try:
            # 确保使用完整的一年数据
            full_data = self._prepare_full_year_data(data)
            
            # 标准化完整数据
            normalized_data = self.normalize_data(full_data)
            
            if len(normalized_data['dates']) < 2:
                return None
            
            img = Image.new('RGB', (self.width, self.height), color='white')
            draw = ImageDraw.Draw(img)
            
            # 绘制坐标轴和网格
            self._draw_axes_and_grid(draw, normalized_data)
            
            # 绘制完整K线图
            self._draw_candlestick_chart(draw, normalized_data)
            
            # 绘制上升通道（只在最近部分显示）
            self._draw_uptrend_channel_on_full_data(draw, channel_result, normalized_data, full_data)
            
            # 添加时间范围标注
            self._draw_time_range_annotation(draw, normalized_data)
            
            image_path = os.path.join(self.output_dir, f"uptrend_{code}.png")
            img.save(image_path, 'PNG', optimize=True)
            
            return image_path
            
        except Exception as e:
            print("生成上升通道图表失败 {}: {}".format(code, str(e)))
            return None
    
    def _prepare_full_year_data(self, data):
        """准备完整的一年数据"""
        # 如果数据少于52周（一年），使用所有可用数据
        if len(data) <= 52:
            return data
        
        # 如果数据超过52周，使用最近52周的数据
        return data.tail(52).copy()
    
    def _draw_uptrend_channel_on_full_data(self, draw, channel_result, normalized_data, full_data):
        """在完整数据上绘制上升通道（只在最近部分显示）"""
        try:
            price_info = normalized_data['price_info']
            dates = normalized_data['dates']
            
            # 检查是否有通道数据
            if 'upper_channel' not in channel_result or 'lower_channel' not in channel_result:
                return
            
            # 获取通道数据
            upper_channel = channel_result['upper_channel']
            lower_channel = channel_result['lower_channel']
            
            # 计算通道在完整数据中的位置
            channel_start_idx = upper_channel.get('start_idx', 0)
            channel_end_idx = upper_channel.get('end_idx', len(dates) - 1)
            
            # 确保通道范围在有效数据范围内
            if channel_start_idx >= len(dates) or channel_end_idx >= len(dates):
                # 如果通道范围超出当前数据，调整到最近的部分
                channel_duration = channel_end_idx - channel_start_idx
                channel_start_idx = max(0, len(dates) - channel_duration - 1)
                channel_end_idx = len(dates) - 1
            
            # 绘制通道区域背景（半透明）
            self._draw_channel_background(draw, channel_start_idx, channel_end_idx, 
                                        dates, price_info, upper_channel, lower_channel)
            
            # 绘制通道线（只在通道范围内）
            self._draw_channel_lines_limited(draw, upper_channel, lower_channel, 
                                           dates, price_info, channel_start_idx, channel_end_idx)
            
            # 标记关键点（只在通道范围内）
            self._mark_key_points_limited(draw, channel_result, normalized_data, 
                                        channel_start_idx, channel_end_idx)
            
            # 添加通道标注
            self._draw_channel_annotation(draw, channel_start_idx, channel_end_idx, 
                                        dates, price_info, channel_result)
            
        except Exception as e:
            print("绘制上升通道失败:", str(e))
    
    def _draw_channel_background(self, draw, start_idx, end_idx, dates, price_info, upper_channel, lower_channel):
        """绘制通道区域背景"""
        try:
            # 计算通道区域的坐标
            x1 = dates[start_idx]
            x2 = dates[end_idx]
            
            # 计算上轨和下轨在通道区域的价格
            upper_y1 = self.normalize_price_for_display(
                upper_channel['slope'] * start_idx + upper_channel['intercept'], price_info)
            upper_y2 = self.normalize_price_for_display(
                upper_channel['slope'] * end_idx + upper_channel['intercept'], price_info)
            
            lower_y1 = self.normalize_price_for_display(
                lower_channel['slope'] * start_idx + lower_channel['intercept'], price_info)
            lower_y2 = self.normalize_price_for_display(
                lower_channel['slope'] * end_idx + lower_channel['intercept'], price_info)
            
            # 创建通道区域的点
            points = [
                (x1, upper_y1),
                (x2, upper_y2),
                (x2, lower_y2),
                (x1, lower_y1)
            ]
            
            # 绘制半透明背景 - 使用简单的矩形区域
            # 计算通道区域的边界
            min_x = min(x1, x2)
            max_x = max(x1, x2)
            min_y = min(upper_y1, upper_y2, lower_y1, lower_y2)
            max_y = max(upper_y1, upper_y2, lower_y1, lower_y2)
            
            # 扩展区域以包含整个通道
            padding = 10
            min_x = max(0, min_x - padding)
            max_x = min(self.width, max_x + padding)
            min_y = max(0, min_y - padding)
            max_y = min(self.height, max_y + padding)
            
            # 绘制半透明矩形背景
            overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle([min_x, min_y, max_x, max_y], 
                                 fill=(255, 255, 0, 30))  # 淡黄色半透明
            
            # 将覆盖层合并到主图像
            img = draw._image
            img.paste(overlay, (0, 0), overlay)
            
        except Exception as e:
            print("绘制通道背景失败:", str(e))
            # 如果失败，跳过背景绘制
            pass
    
    def _draw_channel_lines_limited(self, draw, upper_channel, lower_channel, dates, price_info, start_idx, end_idx):
        """绘制限制在通道范围内的通道线"""
        try:
            # 绘制上轨线
            self._draw_single_channel_line(draw, upper_channel, dates, price_info, 
                                         start_idx, end_idx, '#FF0000', '上轨线')
            
            # 绘制下轨线
            self._draw_single_channel_line(draw, lower_channel, dates, price_info, 
                                         start_idx, end_idx, '#0000FF', '下轨线')
            
        except Exception as e:
            print("绘制通道线失败:", str(e))
    
    def _draw_single_channel_line(self, draw, channel_data, dates, price_info, start_idx, end_idx, color, label):
        """绘制单条通道线"""
        try:
            slope = channel_data['slope']
            intercept = channel_data['intercept']
            
            # 计算线的坐标
            x1 = dates[start_idx]
            x2 = dates[end_idx]
            
            y1 = self.normalize_price_for_display(slope * start_idx + intercept, price_info)
            y2 = self.normalize_price_for_display(slope * end_idx + intercept, price_info)
            
            # 绘制线
            line_width = 3
            shadow_color = '#800000' if color == '#FF0000' else '#000080'
            
            # 阴影效果
            draw.line([(x1+1, y1+1), (x2+1, y2+1)], fill=shadow_color, width=line_width)
            # 主线条
            draw.line([(x1, y1), (x2, y2)], fill=color, width=line_width)
            
            # 添加标签
            font, _ = self.get_fonts()
            draw.text((x2 + 5, y2 - 10), label, fill=color, font=font)
            
        except Exception as e:
            print("绘制单条通道线失败:", str(e))
    
    def _mark_key_points_limited(self, draw, channel_result, normalized_data, start_idx, end_idx):
        """在限制范围内标记关键点"""
        try:
            # 这里可以添加关键点标记逻辑
            # 暂时跳过，避免过度复杂
            pass
        except Exception as e:
            print("标记关键点失败:", str(e))
    
    def _draw_channel_annotation(self, draw, start_idx, end_idx, dates, price_info, channel_result):
        """添加通道标注"""
        try:
            # 计算通道信息
            channel_duration = end_idx - start_idx
            channel_width_pct = channel_result.get('channel_quality', {}).get('channel_width_pct', 0)
            quality_score = channel_result.get('quality_score', 0)
            
            # 在通道区域添加标注
            x = dates[start_idx] + (dates[end_idx] - dates[start_idx]) / 2
            y = price_info['display_min'] + (price_info['display_max'] - price_info['display_min']) * 0.1
            
            # 创建标注文本
            annotation_text = "上升通道\n{}周 | {:.1f}% | 评分:{:.2f}".format(
                channel_duration, channel_width_pct, quality_score)
            
            # 绘制标注框
            font, _ = self.get_fonts(10, 10)
            text_bbox = draw.textbbox((0, 0), annotation_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # 背景框
            padding = 5
            box_x1 = x - text_width/2 - padding
            box_y1 = y - text_height/2 - padding
            box_x2 = x + text_width/2 + padding
            box_y2 = y + text_height/2 + padding
            
            # 绘制背景
            draw.rectangle([box_x1, box_y1, box_x2, box_y2], 
                         fill='white', outline='#FF0000', width=2)
            
            # 绘制文本
            draw.text((x - text_width/2, y - text_height/2), annotation_text, 
                     fill='#FF0000', font=font)
            
        except Exception as e:
            print("绘制通道标注失败:", str(e))
    
    def _draw_time_range_annotation(self, draw, normalized_data):
        """添加时间范围标注"""
        try:
            # 在图表顶部添加时间范围信息
            dates = normalized_data['dates']
            if len(dates) > 0:
                start_date = dates[0]
                end_date = dates[-1]
                
                # 计算显示位置
                x = self.width * 0.5
                y = 20
                
                # 创建时间范围文本
                time_text = "数据范围: {} - {} ({}周)".format(
                    start_date, end_date, len(dates))
                
                # 绘制文本
                font, _ = self.get_fonts(12, 12)
                text_bbox = draw.textbbox((0, 0), time_text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                
                # 绘制背景
                padding = 5
                box_x1 = x - text_width/2 - padding
                box_y1 = y - padding
                box_x2 = x + text_width/2 + padding
                box_y2 = y + text_bbox[3] - text_bbox[1] + padding
                
                draw.rectangle([box_x1, box_y1, box_x2, box_y2], 
                             fill='white', outline='#333333', width=1)
                
                # 绘制文本
                draw.text((x - text_width/2, y), time_text, fill='#333333', font=font)
                
        except Exception as e:
            print("绘制时间范围标注失败:", str(e))

    def _draw_uptrend_channel(self, draw, channel_result, normalized_data):
        """绘制上升通道"""
        try:
            price_info = normalized_data['price_info']
            dates = normalized_data['dates']
            
            # 检查是否有通道数据
            if 'upper_channel' not in channel_result or 'lower_channel' not in channel_result:
                return
            
            # 获取通道数据
            upper_channel = channel_result['upper_channel']
            lower_channel = channel_result['lower_channel']
            

            
            # 先标记关键点
            self._mark_key_points(draw, channel_result, normalized_data)
            
            # 最后绘制通道线，确保在最顶层
            self._draw_channel_line(draw, upper_channel, dates, price_info, 'upper', '#FF0000')
            self._draw_channel_line(draw, lower_channel, dates, price_info, 'lower', '#0000FF')
            
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
            if start_idx >= len(dates) or end_idx >= len(dates) or start_idx < 0 or end_idx < 0:
                return
            
            # 计算线的坐标
            x1 = dates[start_idx]
            x2 = dates[end_idx]
            
            y1 = self.normalize_price_for_display(slope * start_idx + intercept, price_info)
            y2 = self.normalize_price_for_display(slope * end_idx + intercept, price_info)
            
            # 绘制线 - 使用适中的线条宽度，不遮挡K线
            line_width = 3  # 适中的线条宽度，确保可见但不遮挡
            
            # 使用传入的颜色或默认颜色
            if not color:
                color = '#FF0000' if line_type == 'upper' else '#0000FF'
            
            # 绘制通道线（带轻微阴影效果确保可见）
            shadow_color = '#800000' if line_type == 'upper' else '#000080'  # 深色阴影
            draw.line([(x1+1, y1+1), (x2+1, y2+1)], fill=shadow_color, width=line_width)  # 阴影
            draw.line([(x1, y1), (x2, y2)], fill=color, width=line_width)  # 主线条
            
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
        """绘制通道信息（简化版 - 只显示基本信息）"""
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
                
            else:
                # 传统通道信息
                quality_score = channel_result.get('quality_score', 0)
                enhanced_score = channel_result.get('enhanced_quality_score', quality_score)
                draw.text((10, 30), f"评分: {enhanced_score:.3f}", fill='purple', font=small_font)
            
        except Exception as e:
            print(f"绘制通道信息失败: {e}")

    def normalize_price_for_display(self, price, price_info):
        """标准化价格用于显示"""
        if price_info['display_max'] == price_info['display_min']:
            return self.height // 2
        return ((price_info['display_max'] - price) / (price_info['display_max'] - price_info['display_min'])) * (self.height - 80) + 40 