# -*- coding: utf-8 -*-
"""
HTML模板系统
用于生成统一风格的HTML报告，减少重复代码
"""

import os
from typing import Dict, List, Any

class HTMLTemplate:
    """HTML模板基类"""
    
    @staticmethod
    def get_base_header(title: str, extra_css: str = "", extra_js: str = "") -> str:
        """
        获取HTML头部模板
        
        Args:
            title: 页面标题
            extra_css: 额外的CSS样式
            extra_js: 额外的JavaScript代码
        """
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="../assets/common_styles.css">
    <style>
        {extra_css}
    </style>
</head>
<body>
    <div class="container">
'''

    @staticmethod
    def get_base_footer(extra_js: str = "") -> str:
        """获取HTML尾部模板"""
        return f'''
    </div>
    <script>
        {extra_js}
    </script>
</body>
</html>'''

    @staticmethod
    def get_page_title(title: str, subtitle: str = "") -> str:
        """获取页面标题HTML"""
        subtitle_html = f'<p class="subtitle">{subtitle}</p>' if subtitle else ''
        return f'''
        <h1>{title}</h1>
        {subtitle_html}
'''

    @staticmethod
    def get_stats_cards(stats: List[Dict[str, Any]]) -> str:
        """
        生成统计卡片HTML
        
        Args:
            stats: 统计数据列表，每项包含 value 和 label
        """
        cards_html = ''
        for stat in stats:
            cards_html += f'''
            <div class="stat-card">
                <div class="stat-value">{stat['value']}</div>
                <div class="stat-label">{stat['label']}</div>
            </div>
'''
        return f'''
        <div class="stats-container">
            {cards_html}
        </div>
'''

    @staticmethod
    def get_pagination_js() -> str:
        """获取分页JavaScript代码"""
        return '''
        let currentPage = 1;
        const totalPages = document.querySelectorAll('.page').length;
        
        function showPage(pageNum) {
            // 隐藏所有页面
            document.querySelectorAll('.page').forEach(page => {
                page.style.display = 'none';
            });
            
            // 显示当前页面
            const currentPageElement = document.getElementById('page' + pageNum);
            if (currentPageElement) {
                currentPageElement.style.display = 'block';
            }
            
            // 更新分页信息
            document.getElementById('pageInfo').textContent = pageNum + ' / ' + totalPages;
            
            // 更新按钮状态
            document.getElementById('prevBtn').disabled = pageNum === 1;
            document.getElementById('nextBtn').disabled = pageNum === totalPages;
            
            currentPage = pageNum;
        }
        
        function nextPage() {
            if (currentPage < totalPages) {
                showPage(currentPage + 1);
            }
        }
        
        function prevPage() {
            if (currentPage > 1) {
                showPage(currentPage - 1);
            }
        }
        
        // 初始化显示第一页
        showPage(1);
'''

    @staticmethod
    def get_pagination_controls() -> str:
        """获取分页控件HTML"""
        return '''
        <div class="pagination">
            <button id="prevBtn" onclick="prevPage()">上一页</button>
            <span id="pageInfo" class="page-info">1 / 1</span>
            <button id="nextBtn" onclick="nextPage()">下一页</button>
        </div>
'''


class StockAnalysisTemplate(HTMLTemplate):
    """股票分析报告模板"""
    
    @staticmethod
    def get_stock_row(code: str, name: str, index: int, 
                     quality_class: str, quality_text: str,
                     images: Dict[str, str], analysis_html: str) -> str:
        """
        生成单个股票行HTML
        
        Args:
            code: 股票代码
            name: 股票名称
            index: 排名
            quality_class: 质量CSS类
            quality_text: 质量文本
            images: 图片路径字典
            analysis_html: 分析内容HTML
        """
        # 根据是否有质量文本决定是否显示徽章
        quality_badge_html = f'<div class="quality-badge {quality_class}">{quality_text}</div>' if quality_text else ''
        
        return f'''
        <div class="stock-row {quality_class}">
            <div class="stock-header">
                <div class="stock-info">
                    <div class="stock-code">{code}</div>
                    <div class="stock-name">{name}</div>
                    <div class="rank-badge">#{index}</div>
                </div>
                {quality_badge_html}
            </div>
            
            <div class="three-column-layout">
                {StockAnalysisTemplate._get_chart_columns(images)}
                
                <div class="analysis-column">
                    <div class="column-title">
                        <h3>📊 分析结果</h3>
                        <p>关键指标</p>
                    </div>
                    <div class="analysis-content">
                        {analysis_html}
                    </div>
                </div>
            </div>
        </div>
'''

    @staticmethod
    def _get_chart_columns(images: Dict[str, str]) -> str:
        """生成图表列HTML"""
        columns = []
        
        # 原始K线图列
        if 'original' in images:
            columns.append(f'''
                <div class="chart-column">
                    <div class="column-title">
                        <h3>📈 原始K线图</h3>
                        <p>股票基础走势</p>
                    </div>
                    <div class="chart-container">
                        <img src="{images['original']}" alt="原始K线图" class="chart-image" loading="lazy">
                    </div>
                </div>
''')
        
        # 分析图列
        if 'analysis' in images or 'pivot' in images:
            img_path = images.get('analysis', images.get('pivot', ''))
            columns.append(f'''
                <div class="chart-column">
                    <div class="column-title">
                        <h3>🎯 技术分析</h3>
                        <p>关键点位标注</p>
                    </div>
                    <div class="chart-container">
                        <img src="{img_path}" alt="技术分析图" class="chart-image" loading="lazy">
                    </div>
                </div>
''')
        
        return '\n'.join(columns)

    @staticmethod
    def get_metric_group(title: str, metrics: List[Dict[str, Any]]) -> str:
        """
        生成指标组HTML
        
        Args:
            title: 组标题
            metrics: 指标列表，每项包含 label 和 value
        """
        items_html = ''
        for metric in metrics:
            items_html += f'''
                <div class="metric-item">
                    <span class="metric-label">{metric['label']}</span>
                    <span class="metric-value">{metric['value']}</span>
                </div>
'''
        
        return f'''
            <div class="metric-group">
                <h4>{title}</h4>
                {items_html}
            </div>
'''


class ReportGenerator:
    """报告生成器 - 使用模板生成完整报告"""
    
    def __init__(self, template: HTMLTemplate = None):
        self.template = template or HTMLTemplate()
    
    def generate_paginated_report(self, 
                                title: str,
                                subtitle: str,
                                stats: List[Dict[str, Any]],
                                items: List[Any],
                                items_per_page: int,
                                item_renderer) -> str:
        """
        生成分页报告
        
        Args:
            title: 报告标题
            subtitle: 副标题
            stats: 统计数据
            items: 数据项列表
            items_per_page: 每页项目数
            item_renderer: 项目渲染函数
        """
        # 计算总页数
        total_pages = (len(items) + items_per_page - 1) // items_per_page
        
        # 生成HTML
        html = self.template.get_base_header(title)
        html += self.template.get_page_title(title, subtitle)
        html += self.template.get_stats_cards(stats)
        
        # 生成分页内容
        for page in range(1, total_pages + 1):
            start_idx = (page - 1) * items_per_page
            end_idx = min(start_idx + items_per_page, len(items))
            
            html += f'''
            <div id="page{page}" class="page" style="display: {"block" if page == 1 else "none"};">
                <div class="stocks-container">
'''
            
            for i in range(start_idx, end_idx):
                html += item_renderer(items[i], i + 1)
            
            html += '''
                </div>
            </div>
'''
        
        # 添加分页控件
        html += self.template.get_pagination_controls()
        
        # 添加尾部和JavaScript
        html += self.template.get_base_footer(self.template.get_pagination_js())
        
        return html
