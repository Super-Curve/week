# -*- coding: utf-8 -*-
"""
策略标的池HTML生成器
复用高低点页面布局，在第三列展示策略相关指标
"""

import os
import json
import numpy as np
from datetime import datetime
from src.generators.html_templates import StockAnalysisTemplate, ReportGenerator
from src.utils.logger import get_logger

logger = get_logger(__name__)


class StrategyHTMLGenerator:
    """策略标的池HTML报告生成器"""
    
    def __init__(self, output_dir="output/strategy"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, '..', 'assets'), exist_ok=True)
        
        self.template = StockAnalysisTemplate()
        self.report_generator = ReportGenerator(self.template)
    
    def generate_strategy_html(self, strategy_results, chart_paths, strategy_type='long_term'):
        """
        生成策略标的池HTML页面
        
        Args:
            strategy_results: 策略分析结果
            chart_paths: 图表路径
            strategy_type: 策略类型 ('long_term' 或 'short_term')
        """
        if not strategy_results:
            logger.error("没有策略分析结果，无法生成HTML")
            return None
        
        logger.info(f"开始生成{self._get_strategy_name(strategy_type)}HTML，共 {len(strategy_results)} 只股票")
        
        # 按夏普比率降序排序
        sorted_codes = sorted(strategy_results.keys(), 
                            key=lambda x: strategy_results[x]['sharpe'], 
                            reverse=True)
        
        # 准备统计数据
        stats = self._calculate_stats(strategy_results, strategy_type)
        
        # 准备数据项
        items = []
        for code in sorted_codes:
            if code not in chart_paths:
                continue
            
            items.append({
                'code': code,
                'name': strategy_results[code]['name'],
                'result': strategy_results[code],
                'paths': chart_paths[code]
            })
        
        # 生成报告
        title = self._get_strategy_name(strategy_type)
        subtitle = self._get_strategy_subtitle(strategy_type)
        
        html_content = self.report_generator.generate_paginated_report(
            title=title,
            subtitle=subtitle,
            stats=stats,
            items=items,
            items_per_page=10,  # 每页显示10只股票
            item_renderer=lambda item, idx: self._render_stock_item(item, idx, strategy_type)
        )
        
        # 保存HTML文件
        html_path = os.path.join(self.output_dir, "index.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 保存分析结果JSON
        self._save_analysis_json(sorted_codes, strategy_results, strategy_type)
        
        logger.info(f"{title}HTML已生成: {html_path}")
        logger.info(f"文件大小: {os.path.getsize(html_path) / 1024 / 1024:.2f} MB")
        
        return html_path
    
    def _get_strategy_name(self, strategy_type):
        """获取策略名称"""
        return "中长期策略标的池" if strategy_type == 'long_term' else "短期波段策略标的池"
    
    def _get_strategy_subtitle(self, strategy_type):
        """获取策略副标题"""
        if strategy_type == 'long_term':
            return "周线数据：年化波动率40%-50%，夏普比率≥0.5 · " + datetime.now().strftime('%Y年%m月%d日')
        else:
            return "日线数据：半年化波动率≥50%，夏普比率>1.0 · " + datetime.now().strftime('%Y年%m月%d日')
    
    def _calculate_stats(self, strategy_results, strategy_type):
        """计算统计数据"""
        total_stocks = len(strategy_results)
        
        # 计算平均指标
        volatilities = [r['volatility'] for r in strategy_results.values()]
        sharpes = [r['sharpe'] for r in strategy_results.values()]
        
        avg_volatility = np.mean(volatilities) if volatilities else 0
        avg_sharpe = np.mean(sharpes) if sharpes else 0
        
        # 统计市值分布
        market_cap_dist = {'大盘股': 0, '中盘股': 0, '小盘股': 0}
        for result in strategy_results.values():
            category = result.get('market_cap_category', '未知')
            if category in market_cap_dist:
                market_cap_dist[category] += 1
        
        # 找出表现最好的
        if sharpes:
            best_sharpe = max(sharpes)
        else:
            best_sharpe = 0
        
        return [
            {'value': total_stocks, 'label': '符合条件股票'},
            {'value': f"{avg_volatility:.1%}", 'label': '平均波动率'},
            {'value': f"{avg_sharpe:.2f}", 'label': '平均夏普比'},
            {'value': f"{best_sharpe:.2f}", 'label': '最高夏普比'}
        ]
    
    def _render_stock_item(self, item, index, strategy_type):
        """渲染单个股票项目"""
        code = item['code']
        name = item['name']
        result = item['result']
        paths = item['paths']
        
        # 准备图片路径
        images = {
            'original': os.path.relpath(paths['original'], self.output_dir),
            'analysis': os.path.relpath(paths.get('analysis', paths.get('pivot', '')), self.output_dir)
        }
        
        # 生成分析内容（策略指标）
        analysis_html = self._generate_analysis_html(result, strategy_type)
        
        # 根据夏普比率决定质量等级
        sharpe = result.get('sharpe', 0)
        if sharpe >= 2:
            quality_class = 'quality-premium'
            quality_text = '🌟 优秀'
        elif sharpe >= 1.5:
            quality_class = 'quality-good'
            quality_text = '⭐ 良好'
        else:
            quality_class = 'quality-normal'
            quality_text = ''
        
        return self.template.get_stock_row(
            code=code,
            name=name,
            index=index,
            quality_class=quality_class,
            quality_text=quality_text,
            images=images,
            analysis_html=analysis_html
        )
    
    def _generate_analysis_html(self, result, strategy_type):
        """生成分析内容HTML"""
        html = ""
        
        # 1. 策略指标
        strategy_metrics = [
            {'label': '年化波动率', 'value': f"{result['volatility']:.1%}"},
            {'label': '夏普比率', 'value': f"{result['sharpe']:.2f}"},
            {'label': '市值分类', 'value': result.get('market_cap_category', '未知')},
            {'label': '总市值', 'value': f"{result.get('market_value', 0):.0f}亿"}
        ]
        
        html += self.template.get_metric_group('策略指标', strategy_metrics)
        
        # 2. 投资建议
        html += self._generate_investment_suggestion(result, strategy_type)
        
        return html
    
    def _generate_investment_suggestion(self, result, strategy_type):
        """生成投资建议"""
        sharpe = result.get('sharpe', 0)
        volatility = result.get('volatility', 0)
        market_cap = result.get('market_cap_category', '未知')
        
        suggestion = "<div class='metric-group'><h4>投资建议</h4><p style='line-height: 1.5; margin: 0;'>"
        
        if strategy_type == 'long_term':
            # 中长期策略建议
            if sharpe >= 0.8:
                suggestion += "📈 <strong>推荐</strong>：风险收益比优秀，适合中长期持有"
            else:
                suggestion += "📊 <strong>关注</strong>：符合波动率要求，可适当配置"
            
            if market_cap == '大盘股':
                suggestion += " | 🏦 大盘稳健"
            elif market_cap == '中盘股':
                suggestion += " | 💼 中盘均衡"
            else:
                suggestion += " | 🚀 小盘成长"
        else:
            # 短期波段策略建议
            if sharpe >= 1.5:
                suggestion += "⚡ <strong>积极</strong>：高波动高收益，适合波段操作"
            else:
                suggestion += "🎯 <strong>适度</strong>：波动充足，注意控制仓位"
            
            if volatility >= 0.7:
                suggestion += " | ⚠️ 高风险"
            else:
                suggestion += " | 📊 中高风险"
        
        suggestion += "</p></div>"
        
        return suggestion
    
    def _save_analysis_json(self, sorted_codes, strategy_results, strategy_type):
        """保存分析结果为JSON格式"""
        summary = {
            'strategy_type': strategy_type,
            'strategy_name': self._get_strategy_name(strategy_type),
            'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_stocks': len(sorted_codes),
            'stocks': []
        }
        
        for code in sorted_codes:
            if code in strategy_results:
                result = strategy_results[code]
                summary['stocks'].append({
                    'code': code,
                    'name': result['name'],
                    'volatility': result['volatility'],
                    'sharpe': result['sharpe'],
                    'market_cap_category': result.get('market_cap_category', '未知'),
                    'market_value': result.get('market_value', 0)
                })
        
        json_path = os.path.join(self.output_dir, f'{strategy_type}_strategy_summary.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"策略分析摘要已保存到: {json_path}")
