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
    """
    快速批量图表生成器

    用途:
    - 以多进程方式批量生成基础周K线图，供静态图库或其他模块复用。

    实现方式:
    - multiprocessing.Pool map 并行调用 generate_single_chart；复用 BaseChartGenerator 简单风格

    优点:
    - 吞吐高、实现简单

    局限:
    - 多进程在某些环境（如交互式/Windows）需注意入口保护；CPU/I/O 受限时收益有限

    维护建议:
    - 控制并发数；异常需打印但不要中断批处理
    """
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
            
            # 设置数据点数量（供网格线使用）
            self._dates_count = len(data)
            
            # 使用统一的Wind风格K线绘制方法
            self.draw_wind_candlestick_chart(draw, normalized_data, style='simple')
            
            # 使用统一的坐标轴和标签绘制方法
            self.draw_wind_axes_and_labels(draw, normalized_data, code, style='simple')
            
            # 添加股票代码和价格信息（保持原有样式）
            self.add_chart_labels(draw, code, normalized_data['price_info'])
            
            # 保存图片
            image_path = os.path.join(self.output_dir, f"{code}.png")
            img.save(image_path, 'PNG', optimize=True)
            
            return code, image_path
            
        except Exception as e:
            print(f"生成图表失败 {code}: {e}")
            return code, None
    
    def draw_candlestick_chart(self, draw, normalized_data):
        """
        绘制K线图 - 已重构为使用统一的Wind风格方法
        保留此方法为向后兼容
        """
        # 使用统一的方法，但保持简单风格
        self.draw_wind_candlestick_chart(draw, normalized_data, style='simple')
    
    def draw_axes_and_grid(self, draw, normalized_data):
        """
        绘制坐标轴和网格 - 已重构为使用统一的Wind风格方法  
        保留此方法为向后兼容
        """
        # 使用统一的方法，但保持简单风格
        self.draw_wind_axes_and_labels(draw, normalized_data, style='simple')
    
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