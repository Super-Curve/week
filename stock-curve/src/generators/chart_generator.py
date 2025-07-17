import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import time
from datetime import datetime
import multiprocessing as mp

class FastChartGenerator:
    def __init__(self, output_dir="images"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 图片尺寸
        self.width = 400
        self.height = 300
        
    def normalize_data(self, data):
        """标准化数据到图片坐标"""
        if len(data) == 0:
            return [], []
        
        prices = data['close'].values
        dates = np.arange(len(prices))
        
        # 标准化价格到图片高度（翻转Y坐标，使高价在顶部）
        min_price = np.min(prices)
        max_price = np.max(prices)
        if max_price == min_price:
            normalized_prices = np.full_like(prices, self.height // 2)
        else:
            # 翻转Y坐标：高价对应小的Y值（顶部），低价对应大的Y值（底部）
            normalized_prices = ((max_price - prices) / (max_price - min_price)) * (self.height - 40) + 20
        
        # 标准化日期到图片宽度
        normalized_dates = (dates / (len(dates) - 1)) * (self.width - 40) + 20
        
        return normalized_dates, normalized_prices
    
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
            x_coords, y_coords = self.normalize_data(data)
            
            if len(x_coords) < 2:
                return code, None
            
            # 绘制价格线
            points = list(zip(x_coords, y_coords))
            for i in range(len(points) - 1):
                draw.line([points[i], points[i + 1]], fill='blue', width=1)
            
            # 添加股票代码
            try:
                # 尝试使用系统字体
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 12)
            except:
                font = ImageFont.load_default()
            
            draw.text((10, 10), code, fill='black', font=font)
            
            # 保存图片
            image_path = os.path.join(self.output_dir, f"{code}.png")
            img.save(image_path, 'PNG', optimize=True)
            
            return code, image_path
            
        except Exception as e:
            print(f"生成图表失败 {code}: {e}")
            return code, None
    
    def generate_charts_batch(self, stock_data_dict, max_charts=None):
        """批量生成图表（多进程版本）"""
        charts = {}
        
        # 准备数据
        items = list(stock_data_dict.items())
        if max_charts:
            items = items[:max_charts]
        
        total_stocks = len(items)
        print(f"开始生成图表，共 {total_stocks} 只股票...")
        
        # 使用多进程
        num_processes = min(mp.cpu_count(), 8)
        print(f"使用 {num_processes} 个进程并行生成...")
        
        start_time = time.time()
        
        with mp.Pool(processes=num_processes) as pool:
            # 分批处理
            batch_size = 200  # 更大的批次
            for i in range(0, total_stocks, batch_size):
                batch = items[i:i+batch_size]
                
                # 并行处理当前批次
                results = pool.map(self.generate_single_chart, batch)
                
                # 收集结果
                for code, image_path in results:
                    if image_path:
                        charts[code] = image_path
                
                # 显示进度
                processed = min(i + batch_size, total_stocks)
                progress = (processed / total_stocks) * 100
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                eta = (total_stocks - processed) / rate if rate > 0 else 0
                
                print(f"已生成 {processed}/{total_stocks} 个图表 ({progress:.1f}%) - "
                      f"速度: {rate:.1f} 图表/秒 - 预计剩余时间: {eta:.0f}秒")
        
        total_time = time.time() - start_time
        print(f"图表生成完成，共 {len(charts)} 个，总耗时: {total_time:.1f}秒")
        return charts 