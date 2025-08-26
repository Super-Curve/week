#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化版高低点图表生成器 - 支持多进程并行生成
"""

import os
import time
import multiprocessing as mp
from functools import partial
from .pivot_chart_generator import PivotChartGenerator


class PivotChartGeneratorOptimized(PivotChartGenerator):
    """优化版高低点图表生成器，使用多进程加速"""
    
    def __init__(self, output_dir="output/pivot/images", frequency_label="周K线图"):
        super().__init__(output_dir, frequency_label)
        
    def _generate_single_chart_wrapper(self, args):
        """单个图表生成的包装函数，用于多进程"""
        code, stock_data, pivot_result, chart_type = args
        
        try:
            if chart_type == 'original':
                path = self.generate_original_chart(code, stock_data)
            else:  # 'pivot'
                path = self.generate_pivot_chart(code, stock_data, pivot_result)
            return (code, chart_type, path)
        except Exception as e:
            print(f"生成 {code} 的{chart_type}图表时出错: {e}")
            return (code, chart_type, None)
    
    def generate_charts_batch(self, stock_data_dict, pivot_results_dict, max_charts=None):
        """
        批量生成原始K线图和高低点图表（多进程版本）
        
        Args:
            stock_data_dict: 股票数据字典 {code: DataFrame}
            pivot_results_dict: 高低点分析结果字典 {code: pivot_result}
            max_charts: 最大生成图表数量
            
        Returns:
            dict: 生成的图表路径字典 {code: {'original': path, 'pivot': path}}
        """
        chart_paths = {}
        
        # 准备任务列表
        tasks = []
        for i, code in enumerate(pivot_results_dict):
            if max_charts and i >= max_charts:
                break
                
            if code not in stock_data_dict:
                print(f"警告: 股票 {code} 的数据不存在，跳过")
                continue
            
            # 添加原始图任务
            tasks.append((code, stock_data_dict[code], pivot_results_dict[code], 'original'))
            # 添加高低点图任务
            tasks.append((code, stock_data_dict[code], pivot_results_dict[code], 'pivot'))
        
        if not tasks:
            print("没有需要生成的图表")
            return chart_paths
        
        print(f"开始批量生成K线图表（原始图 + 高低点图）...")
        print(f"共 {len(tasks)} 个任务，预计生成 {len(tasks)//2} 只股票的图表")
        
        # 使用多进程并行生成
        num_processes = min(mp.cpu_count(), 8)  # 最多使用8个进程
        print(f"使用 {num_processes} 个进程并行生成...")
        
        start_time = time.time()
        
        with mp.Pool(processes=num_processes) as pool:
            results = pool.map(self._generate_single_chart_wrapper, tasks)
        
        # 整理结果
        generated_count = 0
        for code, chart_type, path in results:
            if path:
                if code not in chart_paths:
                    chart_paths[code] = {}
                chart_paths[code][chart_type] = path
                
                # 统计完整的股票数
                if chart_type == 'pivot' and 'original' in chart_paths.get(code, {}):
                    generated_count += 1
                    if generated_count % 10 == 0:
                        elapsed = time.time() - start_time
                        speed = generated_count / elapsed if elapsed > 0 else 0
                        print(f"已生成 {generated_count} 只股票的图表 - 速度: {speed:.1f} 只/秒")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"批量生成完成，共生成 {generated_count} 只股票的图表（{generated_count * 2} 张图）")
        print(f"总耗时: {total_time:.1f}秒，平均速度: {generated_count/total_time:.1f} 只/秒")
        
        return chart_paths
