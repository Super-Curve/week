import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
from .base_chart_generator import BaseChartGenerator

class ArcChartGenerator(BaseChartGenerator):
    def __init__(self, output_dir="arc_images"):
        # 调用父类初始化，设置默认尺寸为400x300（与FastChartGenerator一致）
        super().__init__(output_dir=output_dir, width=400, height=300)

    def _draw_candlestick_chart(self, draw, normalized_data):
        """绘制K线图（与FastChartGenerator相同的方式）"""
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
        """绘制坐标轴和网格（与FastChartGenerator相同的方式）"""
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

    def generate_global_arc_chart(self, code, data, arc_result):
        """生成传统圆弧底图表 - 使用OHLC数据"""
        try:
            # 标准化数据
            normalized_data = self.normalize_data(data)
            
            if len(normalized_data['dates']) < 2:
                return code, None
            
            img = Image.new('RGB', (self.width, self.height), color='white')
            draw = ImageDraw.Draw(img)
            
            # 绘制坐标轴和网格
            self._draw_axes_and_grid(draw, normalized_data)
            
            # 绘制K线图（与main_kline相同的方式）
            self._draw_candlestick_chart(draw, normalized_data)
            
            # 绘制拟合曲线
            coeffs = arc_result['coeffs']
            n = len(normalized_data['close'])
            x_fit = np.arange(n)
            fit_y = np.polyval(coeffs, x_fit)
            
            # 标准化拟合数据
            price_info = normalized_data['price_info']
            fit_norm = np.array([self.normalize_price_for_display(p, price_info) for p in fit_y])
            fit_points = list(zip(normalized_data['dates'], fit_norm))
            
            for i in range(len(fit_points) - 1):
                draw.line([fit_points[i], fit_points[i+1]], fill='blue', width=2)
            
            # 标记最低点
            min_idx = arc_result['min_point']
            if 0 <= min_idx < len(normalized_data['dates']):
                min_x = float(normalized_data['dates'][min_idx])
                min_y = float(normalized_data['close'][min_idx])
                draw.ellipse([min_x-5, min_y-5, min_x+5, min_y+5], fill='red', outline='red')
            
            # 绘制阶段
            stages = arc_result['stages']
            self._draw_global_stages(draw, stages, normalized_data['dates'], normalized_data['close'])
            
            # 添加信息
            self._draw_global_arc_info(draw, code, arc_result, normalized_data['price_info'])
            
            image_path = os.path.join(self.output_dir, f"global_arc_{code}.png")
            img.save(image_path, 'PNG', optimize=True)
            return code, image_path
            
        except Exception as e:
            print(f"生成传统圆弧底图表失败 {code}: {e}")
            return code, None

    def _draw_global_arc_info(self, draw, code, arc_result, price_info):
        """绘制传统圆弧底信息"""
        font, small_font = self.get_fonts()
        
        draw.text((10, 10), f"STOCK: {code}", fill='black', font=font)
        draw.text((10, 30), f"R²={arc_result['r2']:.3f} 质量评分={arc_result['quality_score']:.1f}", fill='blue', font=small_font)
        draw.text((10, 45), f"PRICE: {price_info['global_min']:.2f}-{price_info['global_max']:.2f}", fill='black', font=small_font)
        
        y_pos = 65
        stages = arc_result['stages']
        for stage_name in ['decline', 'flat', 'rise']:
            stage_data = stages.get(stage_name)
            if not isinstance(stage_data, dict):
                continue
            stage_type = stage_data['type']
            price_change = stage_data['price_change_pct']
            duration = stage_data['duration']
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

    def _draw_global_stages(self, draw, stages, x_coords, norm_prices):
        colors = {'decline': 'red', 'flat': 'orange', 'rise': 'green'}
        for stage_name in ['decline', 'flat', 'rise']:
            stage_data = stages.get(stage_name)
            if not isinstance(stage_data, dict):
                continue
            stage_type = stage_data['type']
            stage_dates = stage_data['dates']
            stage_x = []
            stage_y = []
            for date_idx in stage_dates:
                if 0 <= date_idx < len(x_coords) and 0 <= date_idx < len(norm_prices):
                    stage_x.append(float(x_coords[date_idx]))
                    stage_y.append(float(norm_prices[date_idx]))
            if len(stage_x) > 1:
                color = colors.get(stage_type, 'blue')
                width = 3 if stage_type == 'flat' else 2
                for i in range(len(stage_x) - 1):
                    try:
                        draw.line([(stage_x[i], stage_y[i]), (stage_x[i+1], stage_y[i+1])], fill=color, width=width)
                    except Exception:
                        continue

    def generate_major_arc_chart(self, code, data, arc_result):
        """生成大弧底图表 - 使用OHLC数据"""
        try:
            # 标准化数据
            normalized_data = self.normalize_data(data)
            
            if len(normalized_data['dates']) < 2:
                return None
            
            img = Image.new('RGB', (self.width, self.height), color='white')
            draw = ImageDraw.Draw(img)
            
            # 绘制坐标轴和网格
            self._draw_axes_and_grid(draw, normalized_data)
            
            # 绘制K线图（与main_kline相同的方式）
            self._draw_candlestick_chart(draw, normalized_data)
            
            # 绘制大弧底特征
            self._draw_major_arc_features(draw, arc_result, normalized_data['dates'], normalized_data['close'], normalized_data)
            
            # 绘制拟合线
            self._draw_major_arc_fit(draw, normalized_data, arc_result)
            
            # 绘制信息
            self._draw_major_arc_info(draw, code, arc_result, normalized_data['price_info'])
            
            image_path = os.path.join(self.output_dir, f"major_arc_{code}.png")
            img.save(image_path, 'PNG', optimize=True)
            return image_path
            
        except Exception as e:
            print(f"生成大弧底图表失败 {code}: {e}")
            return None

    def _draw_major_arc_features(self, draw, arc_result, x_coords, y_coords, normalized_data):
        """绘制大弧底特征"""
        try:
            initial_high = arc_result['initial_high']
            max_idx = initial_high['max_idx']
            if 0 <= max_idx < len(x_coords):
                x = x_coords[max_idx]
                y = y_coords[max_idx]
                draw.ellipse([(x-5, y-5), (x+5, y+5)], fill='red', outline='red')
                draw.text((x+10, y-10), f"最高点: {initial_high['max_price']:.2f}", fill='red', font=ImageFont.load_default())
            
            decline = arc_result['decline_analysis']
            decline_start = decline['max_idx']
            decline_end = decline['bottom_start']
            if decline_start < len(x_coords) and decline_end < len(x_coords):
                x1, y1 = x_coords[decline_start], y_coords[decline_start]
                x2, y2 = x_coords[decline_end], y_coords[decline_end]
                draw.line([(x1, y1), (x2, y2)], fill='red', width=3)
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2
                draw.text((mid_x, mid_y-20), f"下跌: {decline['decline_amplitude']:.1%}", fill='red', font=ImageFont.load_default())
            
            box = arc_result['box_analysis']
            box_start = box['start_idx']
            box_end = len(x_coords) - 1
            if box_start < len(x_coords):
                box_x_start = x_coords[box_start]
                box_x_end = x_coords[box_end]
                
                # 使用标准化数据计算箱体位置
                price_info = normalized_data['price_info']
                box_high_y = self.normalize_price_for_display(box['box_high'], price_info)
                box_low_y = self.normalize_price_for_display(box['box_low'], price_info)
                
                draw.rectangle([(box_x_start, box_high_y), (box_x_end, box_low_y)], outline='blue', width=2, fill=None)
                draw.text((box_x_start, box_high_y-20), f"箱体震荡: {box['oscillation_count']}次", fill='blue', font=ImageFont.load_default())
                
        except Exception as e:
            print(f"绘制大弧底特征失败: {e}")

    def _draw_major_arc_fit(self, draw, normalized_data, arc_result):
        """绘制大弧底拟合线"""
        try:
            coeffs = arc_result['coeffs']
            dates = normalized_data['dates']
            close_prices = normalized_data['close']
            
            fitted_prices = np.polyval(coeffs, np.arange(len(close_prices)))
            
            # 使用标准化数据计算拟合线位置
            price_info = normalized_data['price_info']
            fitted_normalized = np.array([self.normalize_price_for_display(p, price_info) for p in fitted_prices])
            fitted_points = list(zip(dates, fitted_normalized))
            
            for i in range(len(fitted_points) - 1):
                draw.line([fitted_points[i], fitted_points[i + 1]], fill='purple', width=2)
                
        except Exception as e:
            print(f"绘制拟合线失败: {e}")

    def _draw_major_arc_info(self, draw, code, arc_result, price_info):
        """绘制大弧底信息"""
        font, small_font = self.get_fonts()
        
        draw.text((10, 10), f"STOCK: {code}", fill='black', font=font)
        draw.text((10, 30), f"SCORE: {arc_result['quality_score']:.2f}", fill='purple', font=small_font)
        draw.text((10, 45), f"r2: {arc_result['r2']:.2f}", fill='blue', font=small_font)
        draw.text((10, 60), f"PRICE: {price_info['global_min']:.2f}-{price_info['global_max']:.2f}", fill='black', font=small_font)
        
        initial_high = arc_result['initial_high']
        draw.text((10, 75), f"初期高位: {initial_high['max_price']:.2f}", fill='red', font=small_font)
        
        decline = arc_result['decline_analysis']
        draw.text((10, 90), f"下跌幅度: {decline['decline_amplitude']:.1%}", fill='red', font=small_font)
        draw.text((10, 105), f"下跌时长: {decline['decline_duration']}周", fill='red', font=small_font)
        
        box = arc_result['box_analysis']
        draw.text((10, 120), f"箱体震荡: {box['oscillation_count']}次", fill='blue', font=small_font)
        draw.text((10, 135), f"箱体范围: {box['box_low']:.2f}-{box['box_high']:.2f}", fill='blue', font=small_font) 