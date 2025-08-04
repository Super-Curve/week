import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
from .base_chart_generator import BaseChartGenerator

class ArcChartGenerator(BaseChartGenerator):
    def __init__(self, output_dir="arc_images"):
        # 调用父类初始化，设置默认尺寸为400x300（与FastChartGenerator一致）
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
            price_info = normalized_data['price_info']
            
            # 首先绘制最高价格线（所有类型的图表都需要）
            self._draw_highest_price_line(draw, x_coords, y_coords, normalized_data)
            
            # 检查是否为相似度分析结果
            if arc_result.get('type') in ['similarity_based', 'similarity_analysis']:
                self._draw_similarity_features(draw, arc_result, x_coords, y_coords, normalized_data)
                return
            
            # 原始的大弧底特征绘制
            self._draw_perfect_match_features(draw, arc_result, x_coords, y_coords, normalized_data)
                
        except Exception as e:
            print(f"绘制大弧底特征失败: {e}")
    
    def _draw_highest_price_line(self, draw, x_coords, y_coords, normalized_data):
        """绘制最高价格线标注"""
        try:
            price_info = normalized_data['price_info']
            max_price = price_info['global_max']
            
            # 找到最高价格对应的所有索引
            max_price_indices = []
            for i, price in enumerate(normalized_data['high']):  # 使用high价格数据
                real_price = self.denormalize_price(price, price_info)
                if abs(real_price - max_price) < max_price * 0.005:  # 0.5%的误差范围
                    max_price_indices.append(i)
            
            if max_price_indices:
                # 使用第一个最高价点
                max_idx = max_price_indices[0]
                if max_idx < len(x_coords):
                    # 绘制最高价格水平线（贯穿整个图表）
                    max_price_y = self.normalize_price_for_display(max_price, price_info)
                    chart_left = 60
                    chart_right = self.width - 10
                    
                    # 绘制红色实线
                    draw.line([(chart_left, max_price_y), (chart_right, max_price_y)], 
                             fill='red', width=2)
                    
                    # 在右侧添加价格标注
                    font, _ = self.get_fonts()
                    draw.text((chart_right - 120, max_price_y - 20), 
                             f"最高价: {max_price:.2f}", 
                             fill='red', font=font)
                    
                    # 在最高价点添加标记
                    x = x_coords[max_idx]
                    y = y_coords[max_idx]
                    draw.ellipse([(x-4, y-4), (x+4, y+4)], fill='red', outline='darkred', width=2)
                    
                    # 验证并标注低位区间范围
                    self._draw_price_validation_zones(draw, max_price, price_info, x_coords)
                    
        except Exception as e:
            print(f"绘制最高价格线失败: {e}")
    
    def _draw_price_validation_zones(self, draw, max_price, price_info, x_coords):
        """绘制价格验证区间（最高价/3的0.8-1.2倍）"""
        try:
            # 计算理论低位区间
            base_price = max_price / 3
            zone_low = base_price * 0.8
            zone_high = base_price * 1.2
            
            # 转换为图表坐标
            zone_low_y = self.normalize_price_for_display(zone_low, price_info)
            zone_high_y = self.normalize_price_for_display(zone_high, price_info)
            
            chart_left = 60
            chart_right = self.width - 10
            
            # 绘制理论低位区间（虚线）
            self._draw_dashed_line(draw, chart_left, zone_low_y, chart_right, zone_low_y, 'blue', width=2)
            self._draw_dashed_line(draw, chart_left, zone_high_y, chart_right, zone_high_y, 'blue', width=2)
            
            # 添加标注
            font, small_font = self.get_fonts()
            draw.text((chart_right - 180, zone_low_y + 5), 
                     f"理论低位下限: {zone_low:.2f}", 
                     fill='blue', font=small_font)
            draw.text((chart_right - 180, zone_high_y - 20), 
                     f"理论低位上限: {zone_high:.2f}", 
                     fill='blue', font=small_font)
            
            # 检查实际最低价是否在理论区间内
            actual_min = price_info['global_min']
            is_in_zone = zone_low <= actual_min <= zone_high
            
            # 在左上角显示验证结果
            validation_text = f"低位验证: {'✓' if is_in_zone else '✗'}"
            validation_color = 'green' if is_in_zone else 'red'
            draw.text((70, 60), validation_text, fill=validation_color, font=font)
            
            # 显示具体数值
            draw.text((70, 80), f"实际最低: {actual_min:.2f}", fill='black', font=small_font)
            draw.text((70, 95), f"理论区间: {zone_low:.2f}-{zone_high:.2f}", fill='blue', font=small_font)
            
            # 计算偏差百分比
            if is_in_zone:
                ratio_text = f"符合预期区间"
            else:
                if actual_min < zone_low:
                    deviation = ((zone_low - actual_min) / zone_low) * 100
                    ratio_text = f"低于预期 {deviation:.1f}%"
                else:
                    deviation = ((actual_min - zone_high) / zone_high) * 100
                    ratio_text = f"高于预期 {deviation:.1f}%"
            
            draw.text((70, 110), ratio_text, fill=validation_color, font=small_font)
            
        except Exception as e:
            print(f"绘制价格验证区间失败: {e}")
    
    def _draw_dashed_line(self, draw, x1, y1, x2, y2, color, width=1, dash_length=8, gap_length=4):
        """绘制虚线"""
        try:
            total_length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            if total_length == 0:
                return
            
            # 计算方向向量
            dx = (x2 - x1) / total_length
            dy = (y2 - y1) / total_length
            
            # 绘制虚线段
            current_pos = 0
            while current_pos < total_length:
                # 计算当前段的起点和终点
                start_x = x1 + dx * current_pos
                start_y = y1 + dy * current_pos
                
                end_pos = min(current_pos + dash_length, total_length)
                end_x = x1 + dx * end_pos
                end_y = y1 + dy * end_pos
                
                # 绘制线段
                draw.line([(start_x, start_y), (end_x, end_y)], fill=color, width=width)
                
                # 移动到下一段的起点
                current_pos = end_pos + gap_length
                
        except Exception as e:
            print(f"绘制虚线失败: {e}")

    def _draw_similarity_features(self, draw, arc_result, x_coords, y_coords, normalized_data):
        """绘制相似度分析的特征"""
        price_info = normalized_data['price_info']
        
        # 1. 标记最高价格点
        max_price = price_info['global_max']
        max_price_indices = [i for i, price in enumerate(normalized_data['close']) 
                           if abs(self.denormalize_price(price, price_info) - max_price) < max_price * 0.01]
        
        if max_price_indices:
            max_idx = max_price_indices[0]
            if max_idx < len(x_coords):
                x = x_coords[max_idx]
                y = y_coords[max_idx]
                # 绘制最高价点
                draw.ellipse([(x-6, y-6), (x+6, y+6)], fill='red', outline='darkred', width=2)
                draw.text((x+10, y-15), f"最高价: {max_price:.2f}", fill='red', font=self.get_fonts()[1])
        
        # 2. 绘制低位区间的两条线
        factors = arc_result.get('factors', {})
        if 'low_zone' in factors:
            low_zone_data = factors['low_zone'].get('data', {})
            if low_zone_data:
                min_price = low_zone_data.get('min_price', 0)
                low_zone_max = low_zone_data.get('low_zone_max', 0)
                
                # 转换为图表坐标
                min_price_y = self.normalize_price_for_display(min_price, price_info)
                low_zone_max_y = self.normalize_price_for_display(low_zone_max, price_info)
                
                # 绘制低位区下边界（最低价）
                draw.line([(x_coords[0], min_price_y), (x_coords[-1], min_price_y)], 
                         fill='green', width=2)
                draw.text((x_coords[-1] - 100, min_price_y - 15), 
                         f"最低价: {min_price:.2f}", fill='green', font=self.get_fonts()[1])
                
                # 绘制低位区上边界（虚线效果）
                dash_length = 10
                gap_length = 5
                x_start, x_end = x_coords[0], x_coords[-1]
                x_current = x_start
                while x_current < x_end:
                    dash_end = min(x_current + dash_length, x_end)
                    draw.line([(x_current, low_zone_max_y), (dash_end, low_zone_max_y)], 
                             fill='orange', width=2)
                    x_current = dash_end + gap_length
                draw.text((x_coords[-1] - 100, low_zone_max_y + 5), 
                         f"低位区上限: {low_zone_max:.2f}", fill='orange', font=self.get_fonts()[1])
                
                # 填充低位区间
                for i in range(0, len(x_coords)-1, 5):  # 每5个点画一条竖线，形成阴影效果
                    draw.line([(x_coords[i], min_price_y), (x_coords[i], low_zone_max_y)], 
                             fill='lightgreen', width=1)
        
        # 3. 绘制箱体区间和盘整时间（基于实际的低位区数据）
        if 'consolidation' in factors:
            consolidation_data = factors['consolidation']
            
            # 使用改进的盘整数据
            consolidation_indices = consolidation_data.get('consolidation_indices', [])
            box_high = consolidation_data.get('box_high', 0)
            box_low = consolidation_data.get('box_low', 0)
            consolidation_weeks = consolidation_data.get('consolidation_weeks', 0)
            
            if consolidation_indices and len(consolidation_indices) >= 6:
                box_start_idx = consolidation_indices[0]
                box_end_idx = consolidation_indices[-1]
                
                # 确保索引在有效范围内
                if (box_start_idx < len(x_coords) and box_end_idx < len(x_coords) and 
                    box_high > 0 and box_low > 0):
                    
                    # 转换为图表坐标
                    box_high_y = self.normalize_price_for_display(box_high, price_info)
                    box_low_y = self.normalize_price_for_display(box_low, price_info)
                    box_start_x = x_coords[box_start_idx]
                    box_end_x = x_coords[box_end_idx]
                    
                    # 绘制箱体
                    draw.rectangle([(box_start_x, box_high_y), (box_end_x, box_low_y)], 
                                  outline='blue', width=3, fill=None)
                    
                    # 添加箱体标签
                    mid_x = (box_start_x + box_end_x) / 2
                    draw.text((mid_x - 30, box_high_y - 25), 
                             f"箱体: {box_low:.2f}-{box_high:.2f}", 
                             fill='blue', font=self.get_fonts()[1])
                    
                    # 显示盘整时间
                    draw.text((mid_x - 20, box_low_y + 10), 
                             f"盘整: {consolidation_weeks}周", 
                             fill='blue', font=self.get_fonts()[1])
            else:
                # 如果没有有效的consolidation_indices，回退到原来的方法
                if 'low_zone' in factors:
                    low_zone_factor = factors['low_zone']
                    low_zone_max = low_zone_factor.get('low_zone_max', 0)
                    
                    # 找到实际在低位区内的价格点
                    actual_prices = []
                    box_indices = []
                    for i, price in enumerate(normalized_data['close']):
                        real_price = self.denormalize_price(price, price_info)
                        if real_price <= low_zone_max:
                            actual_prices.append(real_price)
                            box_indices.append(i)
                    
                    if len(box_indices) >= 10:  # 至少10个点才画箱体
                        # 找到连续的盘整区间（最后的连续低位区段）
                        box_start_idx = self._find_consolidation_start(box_indices)
                        box_end_idx = box_indices[-1]
                        
                        if box_start_idx is not None and box_start_idx < len(x_coords):
                            # 计算箱体区间的实际价格范围
                            consolidation_indices = [i for i in box_indices if i >= box_start_idx]
                            if consolidation_indices:
                                box_prices = [self.denormalize_price(normalized_data['close'][i], price_info) 
                                            for i in consolidation_indices]
                                box_high = max(box_prices)
                                box_low = min(box_prices)
                                
                                # 转换为图表坐标
                                box_high_y = self.normalize_price_for_display(box_high, price_info)
                                box_low_y = self.normalize_price_for_display(box_low, price_info)
                                box_start_x = x_coords[box_start_idx]
                                box_end_x = x_coords[min(box_end_idx, len(x_coords)-1)]
                                
                                # 绘制箱体
                                draw.rectangle([(box_start_x, box_high_y), (box_end_x, box_low_y)], 
                                              outline='blue', width=3, fill=None)
                                
                                # 添加箱体标签
                                mid_x = (box_start_x + box_end_x) / 2
                                draw.text((mid_x - 30, box_high_y - 25), 
                                         f"箱体: {box_low:.2f}-{box_high:.2f}", 
                                         fill='blue', font=self.get_fonts()[1])
                                
                                # 显示盘整时间
                                actual_weeks = len(consolidation_indices)
                                draw.text((mid_x - 20, box_low_y + 10), 
                                         f"盘整: {actual_weeks}周", 
                                         fill='blue', font=self.get_fonts()[1])
    
    def _find_consolidation_start(self, box_indices):
        """找到最后一个连续盘整区间的开始位置"""
        if not box_indices:
            return None
        
        # 从后往前找连续区间
        box_indices = sorted(box_indices)
        consolidation_start = box_indices[-1]
        
        for i in range(len(box_indices) - 2, -1, -1):
            # 如果间隔超过4周，说明不连续
            if box_indices[i+1] - box_indices[i] <= 4:
                consolidation_start = box_indices[i]
            else:
                break
        
        # 确保盘整区间至少有26周
        consolidation_length = box_indices[-1] - consolidation_start + 1
        if consolidation_length < 26:
            # 尝试向前扩展到26周
            target_start = max(0, box_indices[-1] - 25)
            if target_start in box_indices:
                consolidation_start = target_start
        
        return consolidation_start
    
    def _draw_perfect_match_features(self, draw, arc_result, x_coords, y_coords, normalized_data):
        """绘制完美匹配的大弧底特征"""
        price_info = normalized_data['price_info']
        
        # 1. 绘制最高价格点
        if 'initial_high' in arc_result or 'low_zone_analysis' in arc_result:
            max_price = 0
            max_idx = 0
            
            if 'low_zone_analysis' in arc_result:
                max_price = arc_result['low_zone_analysis']['max_price']
                # 找到最高价对应的索引
                for i, price in enumerate(normalized_data['close']):
                    if abs(self.denormalize_price(price, price_info) - max_price) < max_price * 0.01:
                        max_idx = i
                        break
            elif 'initial_high' in arc_result:
                max_idx = arc_result['initial_high']['max_idx']
                max_price = arc_result['initial_high']['max_price']
            
            if max_idx < len(x_coords):
                x = x_coords[max_idx]
                y = y_coords[max_idx]
                draw.ellipse([(x-6, y-6), (x+6, y+6)], fill='red', outline='darkred', width=2)
                draw.text((x+10, y-15), f"最高价: {max_price:.2f}", fill='red', font=self.get_fonts()[1])
        
        # 2. 绘制低位区间的两条线
        if 'low_zone_analysis' in arc_result:
            low_zone = arc_result['low_zone_analysis']
            min_price = low_zone['min_price']
            low_zone_max = low_zone['low_zone_max']
            
            # 转换为图表坐标
            min_price_y = self.normalize_price_for_display(min_price, price_info)
            low_zone_max_y = self.normalize_price_for_display(low_zone_max, price_info)
            
            # 绘制低位区下边界（最低价）
            draw.line([(x_coords[0], min_price_y), (x_coords[-1], min_price_y)], 
                     fill='green', width=2)
            draw.text((x_coords[-1] - 100, min_price_y - 15), 
                     f"最低价: {min_price:.2f}", fill='green', font=self.get_fonts()[1])
            
            # 绘制低位区上边界（虚线效果）
            dash_length = 10
            gap_length = 5
            x_start, x_end = x_coords[0], x_coords[-1]
            x_current = x_start
            while x_current < x_end:
                dash_end = min(x_current + dash_length, x_end)
                draw.line([(x_current, low_zone_max_y), (dash_end, low_zone_max_y)], 
                         fill='orange', width=2)
                x_current = dash_end + gap_length
            draw.text((x_coords[-1] - 100, low_zone_max_y + 5), 
                     f"低位区上限: {low_zone_max:.2f}", fill='orange', font=self.get_fonts()[1])
            
            # 填充低位区间
            for i in range(0, len(x_coords)-1, 5):
                draw.line([(x_coords[i], min_price_y), (x_coords[i], low_zone_max_y)], 
                         fill='lightgreen', width=1)
        
        # 3. 绘制箱体区间和盘整时间（基于实际的consolidation_indices）
        if 'box_analysis' in arc_result:
            box_analysis = arc_result['box_analysis']
            box_high = box_analysis['box_high']
            box_low = box_analysis['box_low']
            consolidation_indices = box_analysis.get('consolidation_indices', [])
            duration = box_analysis.get('duration', 0)
            
            if len(consolidation_indices) > 0:
                # 使用实际的consolidation_indices
                consolidation_indices = np.array(consolidation_indices)
                
                # 找到连续的盘整区间
                box_start_idx = consolidation_indices[0]
                box_end_idx = consolidation_indices[-1]
                
                # 确保索引在有效范围内
                if box_start_idx < len(x_coords) and box_end_idx < len(x_coords):
                    # 转换为图表坐标
                    box_high_y = self.normalize_price_for_display(box_high, price_info)
                    box_low_y = self.normalize_price_for_display(box_low, price_info)
                    box_start_x = x_coords[box_start_idx]
                    box_end_x = x_coords[box_end_idx]
                    
                    # 绘制箱体
                    draw.rectangle([(box_start_x, box_high_y), (box_end_x, box_low_y)], 
                                  outline='blue', width=3, fill=None)
                    
                    # 添加箱体标签
                    mid_x = (box_start_x + box_end_x) / 2
                    draw.text((mid_x - 30, box_high_y - 25), 
                             f"箱体: {box_low:.2f}-{box_high:.2f}", 
                             fill='blue', font=self.get_fonts()[1])
                    
                    # 显示盘整时间
                    draw.text((mid_x - 20, box_low_y + 10), 
                             f"盘整: {duration}周", 
                             fill='blue', font=self.get_fonts()[1])
        
        # 4. 绘制下跌趋势线
        if 'decline_analysis' in arc_result:
            decline = arc_result['decline_analysis']
            max_idx = decline.get('max_idx', 0)
            decline_end = decline.get('first_low_zone_entry', len(x_coords)//2)
            
            if max_idx < len(x_coords) and decline_end < len(x_coords):
                x1, y1 = x_coords[max_idx], y_coords[max_idx]
                x2, y2 = x_coords[decline_end], y_coords[decline_end]
                
                # 绘制下跌趋势线
                draw.line([(x1, y1), (x2, y2)], fill='red', width=3)
                
                # 添加下跌信息
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2
                decline_pct = decline.get('decline_amplitude', 0) * 100
                draw.text((mid_x - 30, mid_y - 20), 
                         f"下跌: {decline_pct:.1f}%", 
                         fill='red', font=self.get_fonts()[1])
    
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
        
        # 检查是否为相似度分析结果
        if arc_result.get('type') in ['similarity_based', 'similarity_analysis']:
            # 相似度分析的显示
            similarity_score = arc_result.get('similarity_score', 0)
            draw.text((10, 30), f"相似度: {similarity_score:.3f}", fill='purple', font=small_font)
            draw.text((10, 45), f"PRICE: {price_info['global_min']:.2f}-{price_info['global_max']:.2f}", fill='black', font=small_font)
            
            recommendation = arc_result.get('recommendation', '无推荐')
            draw.text((10, 60), f"评级: {recommendation[:20]}", fill='green', font=small_font)
            
            # 显示主要评分因素
            factors = arc_result.get('factors', {})
            y_pos = 75
            for factor_name, factor_data in factors.items():
                if isinstance(factor_data, dict) and 'score' in factor_data:
                    score = factor_data['score']
                    factor_display = {
                        'low_zone': '低位区',
                        'initial_high': '初期高位', 
                        'decline': '下跌趋势',
                        'consolidation': '盘整质量',
                        'uptrend': '上升趋势'
                    }.get(factor_name, factor_name)
                    
                    draw.text((10, y_pos), f"{factor_display}: {score:.3f}", fill='blue', font=small_font)
                    y_pos += 15
                    if y_pos > 150:  # 避免超出图表边界
                        break
        else:
            # 原始的大弧底分析显示
            quality_score = arc_result.get('quality_score', 0)
            r2 = arc_result.get('r2', 0)
            draw.text((10, 30), f"SCORE: {quality_score:.2f}", fill='purple', font=small_font)
            draw.text((10, 45), f"r2: {r2:.2f}", fill='blue', font=small_font)
            draw.text((10, 60), f"PRICE: {price_info['global_min']:.2f}-{price_info['global_max']:.2f}", fill='black', font=small_font)
            
            if 'initial_high' in arc_result:
                initial_high = arc_result['initial_high']
                draw.text((10, 75), f"初期高位: {initial_high['max_price']:.2f}", fill='red', font=small_font)
            
            if 'decline_analysis' in arc_result:
                decline = arc_result['decline_analysis']
                draw.text((10, 90), f"下跌幅度: {decline['decline_amplitude']:.1%}", fill='red', font=small_font)
                draw.text((10, 105), f"下跌时长: {decline['decline_duration']}周", fill='red', font=small_font)
            
            if 'box_analysis' in arc_result:
                box = arc_result['box_analysis']
                draw.text((10, 120), f"箱体震荡: {box.get('oscillation_count', 0)}次", fill='blue', font=small_font)
                draw.text((10, 135), f"箱体范围: {box['box_low']:.2f}-{box['box_high']:.2f}", fill='blue', font=small_font) 

    def denormalize_price(self, normalized_price, price_info):
        """将标准化价格转换回真实价格"""
        chart_top = 40
        chart_bottom = self.height - 30
        chart_height = chart_bottom - chart_top
        
        # 反向计算真实价格
        price_ratio = (chart_bottom - normalized_price) / chart_height
        real_price = price_info['display_min'] + price_ratio * (price_info['display_max'] - price_info['display_min'])
        return real_price 