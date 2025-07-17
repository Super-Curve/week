#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import time
from datetime import datetime
import multiprocessing as mp
from .base_chart_generator import BaseChartGenerator

class FastChartGenerator(BaseChartGenerator):
    def __init__(self, output_dir="images"):
        # 调用父类初始化，设置默认尺寸为400x300
        super().__init__(output_dir=output_dir, width=400, height=300)
        
    def generate_single_chart(self, args):
        """生成单个图表（用于多进程）"""
        code, data = args
        if data is None or len(data) == 0:
            return code, None
        
        try:
            # 创建空白图片
            img = Image.new('RGB', (self.width, self.height), color='white')
            draw = ImageDraw.Draw(img)
            
            # 标准化数据
            normalized_data = self.normalize_data(data)
            
            if len(normalized_data['dates']) < 2:
                return code, None
            
            # 绘制坐标轴和网格
            self.draw_axes_and_grid(draw, normalized_data)
            
            # 绘制周K线图
            self.draw_candlestick_chart(draw, normalized_data)
            
            # 添加股票代码和价格信息
            self.add_chart_labels(draw, code, normalized_data['price_info'])
            
            # 保存图片
            image_path = os.path.join(self.output_dir, f"{code}.png")
            img.save(image_path, 'PNG', optimize=True)
            
            return code, image_path
            
        except Exception as e:
            print(f"生成图表失败 {code}: {e}")
            return code, None
    
    def draw_candlestick_chart(self, draw, normalized_data):
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
    
    def draw_axes_and_grid(self, draw, normalized_data):
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
    
    def add_chart_labels(self, draw, code, price_info):
        """添加股票代码和价格信息"""
        font, small_font = self.get_fonts()
        
        # 添加股票代码
        draw.text((10, 10), f"STOCK: {code}", fill='black', font=font)
        
        # 添加价格信息
        price_text = f"PRICE: {price_info['global_min']:.2f} - {price_info['global_max']:.2f}"
        draw.text((10, 30), price_text, fill='blue', font=small_font)
    
    def generate_charts_batch(self, stock_data_dict, max_charts=None):
        """批量生成图表"""
        if not stock_data_dict:
            print("没有数据需要生成图表")
            return
        
        # 限制处理的图表数量
        if max_charts:
            items = list(stock_data_dict.items())[:max_charts]
        else:
            items = list(stock_data_dict.items())
        
        total_charts = len(items)
        print(f"开始生成图表，共 {total_charts} 只股票...")
        
        # 使用多进程生成图表
        num_processes = min(8, total_charts)  # 最多8个进程
        print(f"使用 {num_processes} 个进程并行生成...")
        
        start_time = time.time()
        
        with mp.Pool(processes=num_processes) as pool:
            results = pool.map(self.generate_single_chart, items)
        
        # 统计结果
        successful = sum(1 for _, path in results if path is not None)
        failed = total_charts - successful
        
        end_time = time.time()
        total_time = end_time - start_time
        
        if total_time > 0:
            speed = successful / total_time
            print(f"已生成 {successful}/{total_charts} 个图表 ({successful/total_charts*100:.1f}%) - 速度: {speed:.1f} 图表/秒 - 预计剩余时间: {0}秒")
        
        print(f"图表生成完成，共 {successful} 个，总耗时: {total_time:.1f}秒")
        
        if failed > 0:
            print(f"失败: {failed} 个图表")
        
        return results 