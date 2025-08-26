# -*- coding: utf-8 -*-
"""
优化版高低点HTML生成器 - 使用模板系统生成报告
大幅减少文件大小，提高可维护性
"""

import os
import json
import numpy as np
from datetime import datetime
from src.generators.html_templates import StockAnalysisTemplate, ReportGenerator
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PivotHTMLGeneratorOptimized:
    """优化版高低点HTML报告生成器"""
    
    def __init__(self, output_dir="output/pivot"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, '..', 'assets'), exist_ok=True)
        
        self.template = StockAnalysisTemplate()
        self.report_generator = ReportGenerator(self.template)
        
    def generate_pivot_html(self, pivot_results, chart_paths, stock_names=None):
        """生成高低点分析HTML页面"""
        if not pivot_results:
            logger.error("没有高低点分析结果，无法生成HTML")
            return None
        
        logger.info(f"开始生成高低点分析HTML，共 {len(pivot_results)} 只股票")
        
        # 按照大弧底JSON文件的顺序排序
        sorted_codes = self._sort_by_arc_order(pivot_results)
        
        # 准备统计数据
        stats = self._calculate_stats(pivot_results)
        
        # 准备数据项
        items = []
        for code in sorted_codes:
            if code not in chart_paths:
                continue
                
            items.append({
                'code': code,
                'name': stock_names.get(code, code) if stock_names else code,
                'result': pivot_results[code],
                'paths': chart_paths[code]
            })
        
        # 生成报告
        html_content = self.report_generator.generate_paginated_report(
            title="高低点分析报告",
            subtitle=f"基于ZigZag+ATR算法的关键转折点识别 · {datetime.now().strftime('%Y年%m月%d日')}",
            stats=stats,
            items=items,
            items_per_page=5,
            item_renderer=self._render_stock_item
        )
        
        # 保存HTML文件
        html_path = os.path.join(self.output_dir, "index.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 保存分析结果JSON
        self._save_analysis_json(sorted_codes, pivot_results)
        
        logger.info(f"高低点分析HTML已生成: {html_path}")
        logger.info(f"文件大小: {os.path.getsize(html_path) / 1024 / 1024:.2f} MB")
        
        return html_path
    
    def _sort_by_arc_order(self, pivot_results):
        """按照优质股票优先，然后按大弧底JSON文件的顺序排序"""
        arc_json_path = "output/arc/top_100.json"
        
        try:
            with open(arc_json_path, 'r', encoding='utf-8') as f:
                arc_order = json.load(f)
            
            logger.info(f"从 {arc_json_path} 加载了 {len(arc_order)} 只股票的排序")
            
            # 分离优质和普通股票
            premium_codes = []
            normal_codes = []
            
            # 首先按照JSON顺序处理在arc_order中的股票
            for code in arc_order:
                if code in pivot_results:
                    premium_metrics = pivot_results[code].get('premium_metrics', {})
                    is_premium = premium_metrics.get('is_premium', False)
                    if is_premium:
                        premium_codes.append(code)
                    else:
                        normal_codes.append(code)
            
            # 处理不在arc_order中的股票
            remaining_premium = []
            remaining_normal = []
            for code in pivot_results:
                if code not in arc_order:
                    premium_metrics = pivot_results[code].get('premium_metrics', {})
                    is_premium = premium_metrics.get('is_premium', False)
                    if is_premium:
                        remaining_premium.append(code)
                    else:
                        remaining_normal.append(code)
            
            # 按准确度排序剩余股票
            remaining_premium.sort(
                key=lambda x: pivot_results[x].get('accuracy_score', 0), 
                reverse=True
            )
            remaining_normal.sort(
                key=lambda x: pivot_results[x].get('accuracy_score', 0), 
                reverse=True
            )
            
            # 合并结果：优质股票在前，普通股票在后
            sorted_codes = premium_codes + remaining_premium + normal_codes + remaining_normal
            
            # 记录优质股票数量
            total_premium = len(premium_codes) + len(remaining_premium)
            logger.info(f"共找到 {total_premium} 只优质股票，已排在前面")
            
            return sorted_codes
            
        except Exception as e:
            logger.warning(f"无法加载大弧底排序文件: {e}")
            # 如果无法加载，则按准确度和综合评分排序
            return self._sort_by_score(pivot_results)
    
    def _sort_by_score(self, pivot_results):
        """按优质股票优先，然后按评分排序股票代码"""
        premium_scores = []
        normal_scores = []
        
        for code, result in pivot_results.items():
            accuracy_score = result.get('accuracy_score', 0)
            volatility = result.get('volatility_metrics', {}).get('weekly_volatility', 0)
            premium_metrics = result.get('premium_metrics', {})
            is_premium = premium_metrics.get('is_premium', False)
            
            # 综合评分（准确度和波动率的平衡）
            combined_score = accuracy_score * 0.7 + min(volatility * 2, 1.0) * 0.3
            
            if is_premium:
                premium_scores.append((code, combined_score))
            else:
                normal_scores.append((code, combined_score))
        
        # 分别按评分降序排序
        premium_scores.sort(key=lambda x: x[1], reverse=True)
        normal_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 优质股票在前，普通股票在后
        sorted_codes = [code for code, score in premium_scores] + [code for code, score in normal_scores]
        
        logger.info(f"按评分排序：{len(premium_scores)} 只优质股票排在前面")
        
        return sorted_codes
    
    def _calculate_stats(self, pivot_results):
        """计算统计数据"""
        total_stocks = len(pivot_results)
        
        # 计算平均准确度
        accuracy_scores = [
            result.get('accuracy_score', 0) 
            for result in pivot_results.values()
        ]
        avg_accuracy = np.mean(accuracy_scores) if accuracy_scores else 0
        
        # 计算高质量股票数量
        high_quality = sum(1 for score in accuracy_scores if score >= 0.8)
        
        # 计算平均枢轴点数量
        pivot_counts = []
        for result in pivot_results.values():
            filtered_highs = result.get('filtered_pivot_highs', [])
            filtered_lows = result.get('filtered_pivot_lows', [])
            pivot_counts.append(len(filtered_highs) + len(filtered_lows))
        avg_pivots = np.mean(pivot_counts) if pivot_counts else 0
        
        return [
            {'value': total_stocks, 'label': '分析股票总数'},
            {'value': f"{avg_accuracy:.1%}", 'label': '平均准确度'},
            {'value': high_quality, 'label': '高质量信号'},
            {'value': f"{avg_pivots:.1f}", 'label': '平均枢轴点数'}
        ]
    
    def _render_stock_item(self, item, index):
        """渲染单个股票项目"""
        code = item['code']
        name = item['name']
        result = item['result']
        paths = item['paths']
        
        # 获取是否优质
        premium_metrics = result.get('premium_metrics', {})
        is_premium = premium_metrics.get('is_premium', False)
        
        # 准备图片路径
        images = {
            'original': os.path.relpath(paths['original'], self.output_dir),
            'pivot': os.path.relpath(paths['pivot'], self.output_dir)
        }
        
        # 生成分析内容
        analysis_html = self._generate_analysis_html(result)
        
        return self.template.get_stock_row(
            code=code,
            name=name,
            index=index,
            quality_class='quality-premium' if is_premium else 'quality-normal',
            quality_text='🌟 优质' if is_premium else '',
            images=images,
            analysis_html=analysis_html
        )
    
    # 删除 _get_quality_class 方法，不再需要
    
    def _generate_analysis_html(self, result):
        """生成分析内容HTML"""
        # 提取关键指标
        accuracy_score = result.get('accuracy_score', 0)
        volatility_metrics = result.get('volatility_metrics', {})
        pivot_meta = result.get('pivot_meta', {})
        premium_metrics = result.get('premium_metrics', {})
        
        html = ""
        
        # 1. 投资质量评估（重点展示）
        quality_metrics = []
        
        # 添加最低点信息
        if premium_metrics.get('t1'):
            quality_metrics.extend([
                {'label': '最低点时间', 'value': premium_metrics.get('t1', '-')},
                {'label': '最低点价格', 'value': f"{premium_metrics.get('p1', 0):.2f}" if premium_metrics.get('p1') else '-'}
            ])
        
        quality_metrics.extend([
            {'label': '年化波动率', 'value': f"{premium_metrics.get('annualized_volatility_pct', 0):.1f}%"},
            {'label': '夏普比率', 'value': f"{premium_metrics.get('sharpe_ratio', 0):.2f}"},
            {'label': '是否优质', 'value': '✅ 优质' if premium_metrics.get('is_premium', False) else '❌ 普通'}
        ])
        
        html += self.template.get_metric_group('投资质量', quality_metrics)
        
        # 2. 交易建议
        html += self._generate_trading_suggestion(result)
        
        return html
    
    def _generate_trading_suggestion(self, result):
        """生成交易建议"""
        accuracy_score = result.get('accuracy_score', 0)
        premium_metrics = result.get('premium_metrics', {})
        is_premium = premium_metrics.get('is_premium', False)
        volatility = premium_metrics.get('annualized_volatility_pct', 0)
        
        suggestion = "<div class='metric-group'><h4>交易建议</h4><p style='line-height: 1.5; margin: 0;'>"
        
        # 简化建议
        if is_premium:
            suggestion += "🌟 <strong>优质</strong>：风险收益比优秀"
        elif volatility >= 40:
            suggestion += "📊 <strong>高波动</strong>：需谨慎评估风险"
        else:
            suggestion += "📈 <strong>稳健</strong>：适合稳健投资"
        
        if accuracy_score >= 0.8:
            suggestion += " | ✅ 信号可靠"
        
        suggestion += "</p></div>"
        
        return suggestion
    
    def _save_analysis_json(self, sorted_codes, pivot_results):
        """保存分析结果为JSON格式"""
        summary = {
            'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_stocks': len(sorted_codes),
            'stocks': []
        }
        
        for code in sorted_codes:
            if code in pivot_results:
                result = pivot_results[code]
                summary['stocks'].append({
                    'code': code,
                    'accuracy_score': result.get('accuracy_score', 0),
                    'pivot_count': len(result.get('filtered_pivot_highs', [])) + 
                                  len(result.get('filtered_pivot_lows', [])),
                    'volatility': result.get('volatility_metrics', {}).get('weekly_volatility', 0)
                })
        
        json_path = os.path.join(self.output_dir, 'pivot_analysis_summary.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"分析摘要已保存到: {json_path}")
