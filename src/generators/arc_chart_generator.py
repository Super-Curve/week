import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import time
from datetime import datetime
import multiprocessing as mp

class ArcChartGenerator:
    def __init__(self, output_dir="arc_images"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 图片尺寸
        self.width = 600
        self.height = 400
        
    def generate_arc_analysis_chart(self, args):
        """生成圆弧底分析图表"""
        code, pattern_data = args
        if not pattern_data:
            return code, None
        
        try:
            # 创建空白图片
            img = Image.new('RGB', (self.width, self.height), color='white')
            draw = ImageDraw.Draw(img)
            
            # 获取数据
            data = pattern_data['data']
            stages = pattern_data['stages']
            score = pattern_data['score']
            
            prices = data['close'].values
            dates = np.arange(len(prices))
            
            # 标准化坐标
            x_coords, y_coords = self._normalize_coordinates(prices, dates)
            
            # 绘制价格线
            points = list(zip(x_coords, y_coords))
            for i in range(len(points) - 1):
                draw.line([points[i], points[i + 1]], fill='black', width=2)
            
            # 绘制三阶段
            self._draw_stages(draw, stages, x_coords, y_coords)
            
            # 绘制圆弧拟合线
            self._draw_arc_fit(draw, prices, dates, x_coords, y_coords)
            
            # 添加标题和信息
            self._draw_info(draw, code, score, stages)
            
            # 保存图片
            image_path = os.path.join(self.output_dir, f"arc_{code}.png")
            img.save(image_path, 'PNG', optimize=True)
            
            return code, image_path
            
        except Exception as e:
            print(f"生成圆弧底图表失败 {code}: {e}")
            return code, None
    
    def _normalize_coordinates(self, prices, dates):
        """标准化坐标到图片尺寸"""
        if len(prices) == 0:
            return [], []
        
        # 标准化价格到图片高度（翻转Y坐标，使高价在顶部）
        min_price = np.min(prices)
        max_price = np.max(prices)
        if max_price == min_price:
            normalized_prices = np.full_like(prices, self.height // 2)
        else:
            # 翻转Y坐标：高价对应小的Y值（顶部），低价对应大的Y值（底部）
            normalized_prices = ((max_price - prices) / (max_price - min_price)) * (self.height - 80) + 40
        
        # 标准化日期到图片宽度
        normalized_dates = (dates / (len(dates) - 1)) * (self.width - 40) + 20
        
        return normalized_dates, normalized_prices
    
    def _draw_stages(self, draw, stages, x_coords, y_coords):
        """绘制三阶段"""
        import numpy as np
        
        # 确保 x_coords/y_coords 是列表
        x_coords = list(x_coords)
        y_coords = list(y_coords)
        
        colors = {
            'decline': 'red',
            'flat': 'orange', 
            'rise': 'green'
        }
        
        for stage_name, stage_data in stages.items():
            if not stage_data:
                continue
            
            stage_type = stage_data['type']
            stage_dates = stage_data['dates']
            stage_prices = stage_data['prices']
            
            # 找到对应的坐标，过滤掉越界索引
            stage_x = []
            stage_y = []
            
            for i, date in enumerate(stage_dates):
                # 确保 date 是整数且在有效范围内
                try:
                    date_idx = int(date)
                    if 0 <= date_idx < len(x_coords) and 0 <= date_idx < len(y_coords):
                        # 直接转换为 Python 标量
                        x_val = float(x_coords[date_idx])
                        y_val = float(y_coords[date_idx])
                        stage_x.append(x_val)
                        stage_y.append(y_val)
                except (ValueError, TypeError, IndexError):
                    continue
            
            # 绘制阶段线
            if len(stage_x) > 1:
                color = colors.get(stage_type, 'blue')
                # 使用简单的点对点连接
                for i in range(len(stage_x) - 1):
                    try:
                        draw.line([(stage_x[i], stage_y[i]), (stage_x[i+1], stage_y[i+1])], 
                                 fill=color, width=2)
                    except Exception as e:
                        print(f"[WARN] 绘制线段失败: {e}")
                        continue
    
    def _draw_arc_fit(self, draw, prices, dates, x_coords, y_coords):
        """绘制圆弧拟合线"""
        try:
            # 拟合二次函数
            coeffs = np.polyfit(dates, prices, 2)
            fitted_prices = np.polyval(coeffs, dates)
            
            # 标准化拟合价格（翻转Y坐标）
            min_price = np.min(prices)
            max_price = np.max(prices)
            if max_price != min_price:
                fitted_normalized = ((max_price - fitted_prices) / (max_price - min_price)) * (self.height - 80) + 40
            else:
                fitted_normalized = np.full_like(fitted_prices, self.height // 2)
            
            # 绘制拟合线
            fitted_points = list(zip(x_coords, fitted_normalized))
            for i in range(len(fitted_points) - 1):
                draw.line([fitted_points[i], fitted_points[i + 1]], 
                         fill='blue', width=2)
                
        except:
            pass
    
    def _draw_info(self, draw, code, score, stages):
        """绘制信息文本"""
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
            small_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 10)
        except:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # 标题
        draw.text((10, 10), f"圆弧底分析: {code}", fill='black', font=font)
        draw.text((10, 30), f"拟合度: {score:.2f}", fill='blue', font=small_font)
        
        # 阶段信息
        y_pos = 50
        for stage_name, stage_data in stages.items():
            if not stage_data:
                continue
            
            stage_type = stage_data['type']
            price_change = stage_data['price_change_pct']
            duration = stage_data['duration']
            
            color_map = {'decline': 'red', 'flat': 'orange', 'rise': 'green'}
            color = color_map.get(stage_type, 'black')
            
            text = f"{stage_type}: {price_change:+.1f}% ({duration}周)"
            draw.text((10, y_pos), text, fill=color, font=small_font)
            y_pos += 15
    
    def generate_arc_charts_batch(self, arc_patterns, max_charts=None):
        """批量生成圆弧底分析图表"""
        charts = {}
        
        # 准备数据
        items = list(arc_patterns.items())
        if max_charts:
            items = items[:max_charts]
        
        total_stocks = len(items)
        print(f"开始生成圆弧底分析图表，共 {total_stocks} 只股票...")
        
        # 使用多进程
        num_processes = min(mp.cpu_count(), 8)
        print(f"使用 {num_processes} 个进程并行生成...")
        
        start_time = time.time()
        
        with mp.Pool(processes=num_processes) as pool:
            # 分批处理
            batch_size = 100
            for i in range(0, total_stocks, batch_size):
                batch = items[i:i+batch_size]
                
                # 并行处理当前批次
                results = pool.map(self.generate_arc_analysis_chart, batch)
                
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
                
                print(f"已生成 {processed}/{total_stocks} 个圆弧底图表 ({progress:.1f}%) - "
                      f"速度: {rate:.1f} 图表/秒 - 预计剩余时间: {eta:.0f}秒")
        
        total_time = time.time() - start_time
        print(f"圆弧底图表生成完成，共 {len(charts)} 个，总耗时: {total_time:.1f}秒")
        return charts 

    def generate_arc_chart_simple(self, code, prices, arc_result):
        """只画原始价格线和拟合曲线，arc_result为detect_arc_bottom_simple的返回"""
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
        width, height = self.width, self.height
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)

        # 标准化全局价格到图片高度（翻转Y坐标）
        min_price = np.min(prices)
        max_price = np.max(prices)
        norm_prices = ((max_price - prices) / (max_price - min_price + 1e-8)) * (height - 80) + 40
        n = len(prices)
        x_coords = np.linspace(20, width-20, n)
        # 画全局价格线
        points = list(zip(x_coords, norm_prices))
        for i in range(n-1):
            draw.line([points[i], points[i+1]], fill='black', width=2)

        # 画圆弧底拟合区间
        start = arc_result['start']
        end = arc_result['end']
        win_len = end - start
        win_x = np.arange(win_len)
        win_prices = prices[start:end]
        win_norm = ((max_price - win_prices) / (max_price - min_price + 1e-8)) * (height - 80) + 40
        win_x_coords = x_coords[start:end]
        # 拟合曲线
        coeffs = arc_result['coeffs']
        fit_y = np.polyval(coeffs, win_x)
        fit_norm = ((max_price - fit_y) / (max_price - min_price + 1e-8)) * (height - 80) + 40
        fit_points = list(zip(win_x_coords, fit_norm))
        for i in range(win_len-1):
            draw.line([fit_points[i], fit_points[i+1]], fill='blue', width=2)

        # 标注
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
        except:
            font = ImageFont.load_default()
        draw.text((10, 10), f"圆弧底: {code}", fill='black', font=font)
        draw.text((10, 30), f"区间: {start}-{end}  R²={arc_result['r2']:.2f}", fill='blue', font=font)

        # 保存
        image_path = os.path.join(self.output_dir, f"arc_{code}.png")
        img.save(image_path, 'PNG', optimize=True)
        return code, image_path 

    def generate_global_arc_chart(self, code, prices, arc_result):
        """生成全局圆弧底分析图表，arc_result为detect_global_arc_bottom的返回"""
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
        width, height = self.width, self.height
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)

        # 标准化全局价格到图片高度（翻转Y坐标）
        min_price = np.min(prices)
        max_price = np.max(prices)
        norm_prices = ((max_price - prices) / (max_price - min_price + 1e-8)) * (height - 80) + 40
        n = len(prices)
        x_coords = np.linspace(20, width-20, n)
        
        # 画全局价格线
        points = list(zip(x_coords, norm_prices))
        for i in range(n-1):
            draw.line([points[i], points[i+1]], fill='black', width=2)

        # 画全局圆弧拟合曲线
        coeffs = arc_result['coeffs']
        x_fit = np.arange(n)
        fit_y = np.polyval(coeffs, x_fit)
        fit_norm = ((max_price - fit_y) / (max_price - min_price + 1e-8)) * (height - 80) + 40
        fit_points = list(zip(x_coords, fit_norm))
        for i in range(n-1):
            draw.line([fit_points[i], fit_points[i+1]], fill='blue', width=2)

        # 标注最低点
        min_idx = arc_result['min_point']
        min_x = float(x_coords[min_idx])
        min_y = float(norm_prices[min_idx])
        draw.ellipse([min_x-5, min_y-5, min_x+5, min_y+5], fill='red', outline='red')

        # 绘制阶段信息
        stages = arc_result['stages']
        self._draw_global_stages(draw, stages, x_coords, norm_prices)

        # 标注信息
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
            small_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 10)
        except:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        draw.text((10, 10), f"全局圆弧底: {code}", fill='black', font=font)
        draw.text((10, 30), f"R²={arc_result['r2']:.3f} 质量评分={arc_result['quality_score']:.1f}", fill='blue', font=small_font)
        
        # 阶段信息
        y_pos = 50
        for stage_name in ['decline', 'flat', 'rise']:
            stage_data = stages.get(stage_name)
            if not isinstance(stage_data, dict):
                continue
            stage_type = stage_data['type']
            price_change = stage_data['price_change_pct']
            duration = stage_data['duration']
            
            # 根据阶段类型设置不同的颜色和描述
            if stage_type == 'decline':
                color = 'red'
                desc = '严重下降'
            elif stage_type == 'flat':
                color = 'orange'
                desc = '横盘筑底'
            elif stage_type == 'rise':
                color = 'green'
                desc = '轻微上涨'
            else:
                color = 'black'
                desc = stage_type
            
            text = f"{desc}: {price_change:+.1f}% ({duration}周)"
            draw.text((10, y_pos), text, fill=color, font=small_font)
            y_pos += 15

        # 保存
        image_path = os.path.join(self.output_dir, f"global_arc_{code}.png")
        img.save(image_path, 'PNG', optimize=True)
        return code, image_path

    def _draw_global_stages(self, draw, stages, x_coords, norm_prices):
        """绘制全局弧底的阶段"""
        colors = {
            'decline': 'red',
            'flat': 'orange',
            'rise': 'green'
        }
        
        for stage_name in ['decline', 'flat', 'rise']:
            stage_data = stages.get(stage_name)
            if not isinstance(stage_data, dict):
                continue
            
            stage_type = stage_data['type']
            stage_dates = stage_data['dates']
            
            # 找到对应的坐标
            stage_x = []
            stage_y = []
            
            for date_idx in stage_dates:
                if 0 <= date_idx < len(x_coords) and 0 <= date_idx < len(norm_prices):
                    stage_x.append(float(x_coords[date_idx]))
                    stage_y.append(float(norm_prices[date_idx]))
            
            # 绘制阶段线
            if len(stage_x) > 1:
                color = colors.get(stage_type, 'blue')
                width = 3 if stage_type == 'flat' else 2  # 横盘阶段用粗线
                for i in range(len(stage_x) - 1):
                    try:
                        draw.line([(stage_x[i], stage_y[i]), (stage_x[i+1], stage_y[i+1])], 
                                 fill=color, width=width)
                    except Exception as e:
                        continue 