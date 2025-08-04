# -*- coding: utf-8 -*-
"""
高低点HTML生成器 - 生成美观的高低点分析展示页面
提供现代化的UI设计，展示K线图和详细的分析说明
"""

import os
import json
import numpy as np
from datetime import datetime


class PivotHTMLGenerator:
    """高低点HTML生成器"""
    
    def __init__(self, output_dir="pivot_output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def generate_pivot_html(self, pivot_results, chart_paths, stock_names=None):
        """
        生成高低点分析HTML页面
        
        Args:
            pivot_results: 高低点分析结果字典 {code: pivot_result}
            chart_paths: 图表路径字典 {code: {'original': path, 'pivot': path}}
            stock_names: 股票名称字典 {code: name}，可选
            
        Returns:
            str: 生成的HTML文件路径
        """
        if not pivot_results:
            print("没有高低点分析结果，无法生成HTML")
            return None
        
        # 按照大弧底JSON文件的顺序排序
        sorted_codes = self._sort_by_arc_order(pivot_results)
        
        # 分页处理 - 每行一个股票
        stocks_per_page = 5  # 每页5只股票
        total_pages = (len(sorted_codes) + stocks_per_page - 1) // stocks_per_page
        
        # 生成HTML内容
        html_content = self._generate_html_content(
            sorted_codes, pivot_results, chart_paths, 
            stock_names, stocks_per_page, total_pages
        )
        
        # 保存HTML文件
        html_path = os.path.join(self.output_dir, "index.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"高低点分析HTML已生成: {html_path}")
        print(f"共分析 {len(sorted_codes)} 只股票，分为 {total_pages} 页展示")
        
        return html_path
    
    def _sort_by_arc_order(self, pivot_results):
        """按照大弧底JSON文件的顺序排序股票代码"""
        arc_json_path = "output/arc/top_100.json"
        
        try:
            # 读取大弧底分析结果文件
            with open(arc_json_path, 'r', encoding='utf-8') as f:
                arc_order = json.load(f)
            
            print(f"从 {arc_json_path} 加载了 {len(arc_order)} 只股票的排序")
            
            # 按照JSON文件的顺序排序
            sorted_codes = []
            
            # 首先添加按JSON顺序的股票
            for code in arc_order:
                if code in pivot_results:
                    sorted_codes.append(code)
            
            # 然后添加不在JSON中但有分析结果的股票（按准确度排序）
            remaining_codes = []
            for code in pivot_results:
                if code not in arc_order:
                    remaining_codes.append(code)
            
            if remaining_codes:
                print(f"发现 {len(remaining_codes)} 只股票不在大弧底排序中，将按准确度排序追加")
                # 对剩余股票按准确度排序
                remaining_scores = []
                for code in remaining_codes:
                    result = pivot_results[code]
                    accuracy_score = result.get('accuracy_score', 0)
                    remaining_scores.append((code, accuracy_score))
                
                remaining_scores.sort(key=lambda x: x[1], reverse=True)
                sorted_codes.extend([code for code, score in remaining_scores])
            
            print(f"最终排序: 前{len(sorted_codes) - len(remaining_codes)}只按大弧底顺序，后{len(remaining_codes)}只按准确度排序")
            return sorted_codes
            
        except FileNotFoundError:
            print(f"警告: 未找到大弧底排序文件 {arc_json_path}，将按准确度排序")
            return self._sort_by_quality_fallback(pivot_results)
        except json.JSONDecodeError as e:
            print(f"警告: 大弧底排序文件格式错误 {e}，将按准确度排序")
            return self._sort_by_quality_fallback(pivot_results)
        except Exception as e:
            print(f"警告: 读取大弧底排序文件时出错 {e}，将按准确度排序")
            return self._sort_by_quality_fallback(pivot_results)
    
    def _sort_by_quality_fallback(self, pivot_results):
        """备用的按质量评分排序方法"""
        code_scores = []
        for code, result in pivot_results.items():
            accuracy_score = result.get('accuracy_score', 0)
            pivot_count = len(result.get('filtered_pivot_highs', [])) + len(result.get('filtered_pivot_lows', []))
            
            # 综合评分: 准确度 * 0.7 + 标准化的转折点数量 * 0.3
            combined_score = accuracy_score * 0.7 + min(pivot_count / 10, 1.0) * 0.3
            code_scores.append((code, combined_score))
        
        # 按评分降序排序
        code_scores.sort(key=lambda x: x[1], reverse=True)
        return [code for code, score in code_scores]
    
    def _generate_html_content(self, sorted_codes, pivot_results, chart_paths, 
                             stock_names, stocks_per_page, total_pages):
        """生成完整的HTML内容"""
        
        html = self._get_html_header(len(sorted_codes), total_pages)
        
        # 生成每一页的内容
        for page in range(1, total_pages + 1):
            start_idx = (page - 1) * stocks_per_page
            end_idx = min(start_idx + stocks_per_page, len(sorted_codes))
            
            html += f'''
            <div id="page{page}" class="page" style="display: {"block" if page == 1 else "none"};">
                <div class="stocks-container">
            '''
            
            for i in range(start_idx, end_idx):
                code = sorted_codes[i]
                if code not in chart_paths:
                    continue
                
                html += self._generate_stock_row(
                    code, pivot_results[code], chart_paths[code], 
                    stock_names.get(code, code) if stock_names else code,
                    i + 1
                )
            
            html += '''
                </div>
            </div>
            '''
        
        html += self._get_html_footer()
        return html
    
    def _generate_stock_row(self, code, pivot_result, chart_paths, name, index):
        """生成单个股票行的HTML（三列布局）"""
        
        # 获取关键指标
        accuracy_score = pivot_result.get('accuracy_score', 0)
        analysis_desc = pivot_result.get('analysis_description', {})
        volatility_metrics = pivot_result.get('volatility_metrics', {})
        filter_effectiveness = pivot_result.get('filter_effectiveness', {})
        
        # 质量等级
        quality_class, quality_text = self._get_quality_class(accuracy_score)
        
        # 相对路径
        original_image_path = os.path.relpath(chart_paths['original'], self.output_dir)
        pivot_image_path = os.path.relpath(chart_paths['pivot'], self.output_dir)
        
        return f'''
        <div class="stock-row {quality_class}">
            <div class="stock-header">
                <div class="stock-info">
                    <div class="stock-code">{code}</div>
                    <div class="stock-name">{name}</div>
                    <div class="rank-badge">#{index}</div>
                </div>
                <div class="quality-badge {quality_class}">
                    {quality_text}
                </div>
            </div>
            
            <div class="three-column-layout">
                <!-- 第一列：原始K线图 -->
                <div class="chart-column">
                    <div class="column-title">
                        <h3>📊 原始K线图</h3>
                        <p>股票基础走势，无任何标记</p>
                    </div>
                    <div class="chart-container">
                        <img src="{original_image_path}" alt="{code} 原始K线图" class="chart-image">
                    </div>
                </div>
                
                <!-- 第二列：高低点标记图 -->
                <div class="chart-column">
                    <div class="column-title">
                        <h3>🎯 高低点识别</h3>
                        <p>波动率过滤后的关键转折点</p>
                    </div>
                    <div class="chart-container">
                        <img src="{pivot_image_path}" alt="{code} 高低点分析" class="chart-image">
                    </div>
                </div>
                
                <!-- 第三列：详细分析说明 -->
                <div class="analysis-column">
                    <div class="column-title">
                        <h3>📈 分析说明</h3>
                        <p>准确度、波动率、过滤效果</p>
                    </div>
                    <div class="analysis-content">
                        {self._generate_detailed_analysis_summary(pivot_result)}
                    </div>
                </div>
            </div>
        </div>
        '''

    def _generate_detailed_analysis_summary(self, pivot_result):
        """生成详细分析摘要"""
        
        analysis_desc = pivot_result.get('analysis_description', {})
        volatility_metrics = pivot_result.get('volatility_metrics', {})
        filter_effectiveness = pivot_result.get('filter_effectiveness', {})
        accuracy_score = pivot_result.get('accuracy_score', 0)
        
        # 高低点统计
        filtered_highs = len(pivot_result.get('filtered_pivot_highs', []))
        filtered_lows = len(pivot_result.get('filtered_pivot_lows', []))
        raw_highs = len(pivot_result.get('raw_pivot_highs', []))
        raw_lows = len(pivot_result.get('raw_pivot_lows', []))
        
        # 获取新的详细波动率分析
        volatility_analysis = analysis_desc.get('volatility_analysis', '')
        
        # 如果有新的详细分析，使用它；否则回退到旧的简单显示
        if volatility_analysis and len(volatility_analysis.strip()) > 20:
            # 有详细分析，使用新格式
            # 将波动率分析文本转换为HTML格式
            volatility_html = self._format_volatility_analysis_to_html(volatility_analysis)
        else:
            # 回退到旧的简单格式
            avg_volatility = np.nanmean(volatility_metrics.get('atr_percentage', [0])) if 'atr_percentage' in volatility_metrics else 0
            volatility_threshold = volatility_metrics.get('volatility_threshold', 0)
            volatility_html = f'''
                <div class="metric-row">
                    <span class="metric-label">平均ATR波动率:</span>
                    <span class="metric-value">{avg_volatility:.2f}%</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">过滤阈值:</span>
                    <span class="metric-value">{volatility_threshold:.2f}%</span>
                </div>
            '''
        
        return f'''
        <div class="analysis-metrics">
            <div class="metric-group">
                <h4>🎯 识别结果</h4>
                <div class="metric-row">
                    <span class="metric-label">识别准确度:</span>
                    <span class="metric-value accuracy-{self._get_quality_class(accuracy_score)[0]}">{accuracy_score:.1%}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">关键高点:</span>
                    <span class="metric-value">{filtered_highs} 个</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">关键低点:</span>
                    <span class="metric-value">{filtered_lows} 个</span>
                </div>
            </div>
            
            <div class="metric-group">
                <h4>📊 波动率分析</h4>
                {volatility_html}
            </div>
            
            <div class="metric-group">
                <h4>🔍 过滤效果</h4>
                <div class="metric-row">
                    <span class="metric-label">原始高点:</span>
                    <span class="metric-value text-muted">{raw_highs} 个</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">原始低点:</span>
                    <span class="metric-value text-muted">{raw_lows} 个</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">过滤率:</span>
                    <span class="metric-value">{filter_effectiveness.get('filter_ratio', 0):.1%}</span>
                </div>
            </div>
            
            <div class="metric-group">
                <h4>💡 质量评估</h4>
                <div class="quality-description">
                    {analysis_desc.get('quality_assessment', '分析中...')}
                </div>
                <div class="analysis-summary">
                    {analysis_desc.get('summary', '无详细信息')}
                </div>
            </div>
        </div>
        '''

    def _format_volatility_analysis_to_html(self, volatility_analysis):
        """将波动率分析文本转换为HTML格式"""
        if not volatility_analysis:
            return '<div class="metric-row"><span class="metric-label">无波动率分析</span></div>'
        
        lines = volatility_analysis.strip().split('\n')
        html_parts = []
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否是新的章节标题
            if line.startswith('📊') or line.startswith('📈') or line.startswith('🎯') or line.startswith('📉') or line.startswith('💡'):
                # 章节标题
                if line.startswith('📊 主要波动率指标:'):
                    current_section = 'main_indicators'
                    html_parts.append('<div class="volatility-section">')
                    html_parts.append(f'<div class="section-title">{line}</div>')
                elif line.startswith('📈 高级波动率估计器:'):
                    current_section = 'advanced_estimators'
                    html_parts.append('</div><div class="volatility-section">')
                    html_parts.append(f'<div class="section-title">{line}</div>')
                elif line.startswith('🎯 波动率环境:'):
                    current_section = 'environment'
                    html_parts.append('</div><div class="volatility-section">')
                    html_parts.append(f'<div class="section-title">{line}</div>')
                elif line.startswith('📉 稳定性分析:'):
                    current_section = 'stability'
                    html_parts.append('</div><div class="volatility-section">')
                    html_parts.append(f'<div class="section-title">{line}</div>')
                elif line.startswith('💡 交易含义:'):
                    current_section = 'trading_implications'
                    html_parts.append('</div><div class="volatility-section">')
                    html_parts.append(f'<div class="section-title">{line}</div>')
                else:
                    html_parts.append(f'<div class="section-title">{line}</div>')
            elif line.startswith('  • '):
                # 列表项
                content = line[4:]  # 移除 "  • "
                html_parts.append(f'<div class="metric-item">{content}</div>')
            else:
                # 普通文本
                if line:
                    html_parts.append(f'<div class="metric-text">{line}</div>')
        
        # 关闭最后一个section
        if html_parts:
            html_parts.append('</div>')
        
        # 添加CSS样式（内联方式，确保显示效果）
        formatted_html = f'''
        <div class="detailed-volatility-analysis">
            {chr(10).join(html_parts)}
        </div>
        <style>
        .detailed-volatility-analysis .volatility-section {{
            margin-bottom: 1rem;
            padding: 0.8rem;
            border-left: 3px solid #3498db;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 0 5px 5px 0;
        }}
        .detailed-volatility-analysis .section-title {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 0.5rem;
            font-size: 0.95rem;
        }}
        .detailed-volatility-analysis .metric-item {{
            margin: 0.3rem 0;
            padding-left: 1rem;
            color: #495057;
            font-size: 0.9rem;
            line-height: 1.4;
        }}
        .detailed-volatility-analysis .metric-text {{
            margin: 0.2rem 0;
            color: #6c757d;
            font-size: 0.85rem;
            font-style: italic;
        }}
        </style>
        '''
        
        return formatted_html

    def _get_quality_class(self, accuracy_score):
        """根据准确度获取质量等级"""
        if accuracy_score >= 0.8:
            return "quality-excellent", "优秀"
        elif accuracy_score >= 0.6:
            return "quality-good", "良好"
        elif accuracy_score >= 0.4:
            return "quality-fair", "一般"
        else:
            return "quality-poor", "较差"
    
    def _get_html_header(self, total_stocks, total_pages):
        """生成HTML头部"""
        return f'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A股高低点分析 - 波动率过滤识别</title>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="header-gradient"></div>
    
    <header class="main-header">
        <div class="header-content">
            <h1 class="main-title">
                <span class="title-icon">📈</span>
                A股高低点分析系统
            </h1>
            <div class="subtitle">基于波动率过滤的智能转折点识别</div>
            
            <div class="stats-bar">
                <div class="stat-item">
                    <div class="stat-number">{total_stocks}</div>
                    <div class="stat-label">分析股票</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{total_pages}</div>
                    <div class="stat-label">展示页面</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{datetime.now().strftime('%Y-%m-%d')}</div>
                    <div class="stat-label">更新日期</div>
                </div>
            </div>
        </div>
    </header>
    
    <nav class="pagination-nav">
        <div class="nav-content">
            <button onclick="prevPage()" id="prevBtn" class="nav-btn" disabled>
                ← 上一页
            </button>
            <div class="page-info">
                <span id="currentPage">1</span> / <span id="totalPages">{total_pages}</span>
            </div>
            <button onclick="nextPage()" id="nextBtn" class="nav-btn">
                下一页 →
            </button>
        </div>
    </nav>
    
    <main class="main-content">
        '''
    
    def _get_html_footer(self):
        """生成HTML尾部"""
        return '''
    </main>
    
    <footer class="main-footer">
        <div class="footer-content">
            <p>© 2024 A股量化分析平台 - 高低点识别系统</p>
            <p>采用波动率过滤算法，精确识别关键转折点</p>
        </div>
    </footer>
    
    <script>
        let currentPageNum = 1;
        const totalPagesNum = document.getElementById('totalPages').textContent;
        
        function showPage(pageNum) {
            // 隐藏所有页面
            document.querySelectorAll('.page').forEach(page => {
                page.style.display = 'none';
            });
            
            // 显示目标页面
            const targetPage = document.getElementById('page' + pageNum);
            if (targetPage) {
                targetPage.style.display = 'block';
            }
            
            // 更新页面信息
            document.getElementById('currentPage').textContent = pageNum;
            
            // 更新按钮状态
            document.getElementById('prevBtn').disabled = pageNum <= 1;
            document.getElementById('nextBtn').disabled = pageNum >= parseInt(totalPagesNum);
            
            // 滚动到顶部
            window.scrollTo(0, 0);
        }
        
        function nextPage() {
            if (currentPageNum < parseInt(totalPagesNum)) {
                currentPageNum++;
                showPage(currentPageNum);
            }
        }
        
        function prevPage() {
            if (currentPageNum > 1) {
                currentPageNum--;
                showPage(currentPageNum);
            }
        }
        
        function toggleDetails(code) {
            const details = document.getElementById('details-' + code);
            const button = event.target;
            
            if (details.style.display === 'none') {
                details.style.display = 'block';
                button.textContent = '收起详情 ▲';
            } else {
                details.style.display = 'none';
                button.textContent = '查看详情 ▼';
            }
        }
        
        // 键盘导航
        document.addEventListener('keydown', function(e) {
            if (e.key === 'ArrowLeft') {
                prevPage();
            } else if (e.key === 'ArrowRight') {
                nextPage();
            }
        });
        
        // 初始化
        showPage(1);
    </script>
</body>
</html>
        '''
    
    def _get_css_styles(self):
        """生成CSS样式"""
        return '''
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .header-gradient {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 200px;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.9) 0%, rgba(118, 75, 162, 0.9) 100%);
            z-index: -1;
        }
        
        .main-header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 2rem 0;
            margin-bottom: 2rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }
        
        .header-content {
            max-width: 1200px;
            margin: 0 auto;
            text-align: center;
            padding: 0 2rem;
        }
        
        .main-title {
            font-size: 2.5rem;
            color: #2c3e50;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
        }
        
        .title-icon {
            font-size: 3rem;
        }
        
        .subtitle {
            font-size: 1.1rem;
            color: #7f8c8d;
            margin-bottom: 2rem;
        }
        
        .stats-bar {
            display: flex;
            justify-content: center;
            gap: 3rem;
            flex-wrap: wrap;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            color: #3498db;
        }
        
        .stat-label {
            font-size: 0.9rem;
            color: #7f8c8d;
            margin-top: 0.5rem;
        }
        
        .pagination-nav {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            padding: 1rem 0;
            margin-bottom: 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        
        .nav-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 2rem;
        }
        
        .nav-btn {
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
        }
        
        .nav-btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(52, 152, 219, 0.4);
        }
        
        .nav-btn:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .page-info {
            font-size: 1.1rem;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .main-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 2rem 4rem;
        }
        
        .stocks-container {
            display: flex;
            flex-direction: column;
            gap: 3rem;
            margin-bottom: 2rem;
        }
        
        .stock-row {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            border: 3px solid transparent;
        }
        
        .stock-row:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 50px rgba(0, 0, 0, 0.15);
        }
        
        .stock-row.quality-excellent {
            border-color: #27ae60;
        }
        
        .stock-row.quality-good {
            border-color: #f39c12;
        }
        
        .stock-row.quality-fair {
            border-color: #e67e22;
        }
        
        .stock-row.quality-poor {
            border-color: #e74c3c;
        }
        
        .stock-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #ecf0f1;
        }
        
        .three-column-layout {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 2rem;
            min-height: 500px;
        }
        
        .chart-column, .analysis-column {
            display: flex;
            flex-direction: column;
        }
        
        .column-title {
            margin-bottom: 1rem;
        }
        
        .column-title h3 {
            color: #2c3e50;
            margin-bottom: 0.5rem;
            font-size: 1.1rem;
        }
        
        .column-title p {
            color: #7f8c8d;
            font-size: 0.9rem;
            margin: 0;
        }
        
        .stock-info {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .stock-code {
            font-size: 1.2rem;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .stock-name {
            font-size: 0.9rem;
            color: #7f8c8d;
        }
        
        .rank-badge {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .quality-badge {
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
            color: white;
        }
        
        .quality-badge.quality-excellent {
            background: linear-gradient(135deg, #27ae60, #2ecc71);
        }
        
        .quality-badge.quality-good {
            background: linear-gradient(135deg, #f39c12, #f1c40f);
        }
        
        .quality-badge.quality-fair {
            background: linear-gradient(135deg, #e67e22, #f39c12);
        }
        
        .quality-badge.quality-poor {
            background: linear-gradient(135deg, #e74c3c, #c0392b);
        }
        
        .chart-container {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            background: rgba(248, 249, 250, 0.8);
            border-radius: 15px;
            padding: 1rem;
        }
        
        .chart-image {
            max-width: 100%;
            max-height: 450px;
            height: auto;
            border-radius: 12px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
            transition: transform 0.3s ease;
            border: 1px solid #e9ecef;
        }
        
        .chart-image:hover {
            transform: scale(1.02);
        }
        
        .analysis-content {
            flex: 1;
            background: rgba(248, 249, 250, 0.8);
            border-radius: 15px;
            padding: 1.5rem;
            overflow-y: auto;
            max-height: 350px;
        }
        
        .analysis-metrics {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }
        
        .metric-group {
            background: white;
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }
        
        .metric-group h4 {
            color: #2c3e50;
            margin-bottom: 0.75rem;
            font-size: 0.95rem;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 0.5rem;
        }
        
        .metric-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        
        .metric-label {
            font-size: 0.85rem;
            color: #7f8c8d;
            flex: 1;
        }
        
        .metric-value {
            font-weight: bold;
            color: #2c3e50;
            font-size: 0.9rem;
        }
        
        .metric-value.accuracy-quality-excellent {
            color: #27ae60;
        }
        
        .metric-value.accuracy-quality-good {
            color: #f39c12;
        }
        
        .metric-value.accuracy-quality-fair {
            color: #e67e22;
        }
        
        .metric-value.accuracy-quality-poor {
            color: #e74c3c;
        }
        
        .text-muted {
            color: #95a5a6 !important;
        }
        
        .quality-description {
            background: rgba(52, 152, 219, 0.1);
            padding: 0.75rem;
            border-radius: 8px;
            font-size: 0.9rem;
            color: #2c3e50;
            margin-bottom: 0.5rem;
            border-left: 4px solid #3498db;
        }
        
        .analysis-summary {
            font-size: 0.85rem;
            color: #7f8c8d;
            line-height: 1.4;
        }
        
        .volatility-info {
            margin: 1rem 0;
            padding: 1rem;
            background: rgba(52, 152, 219, 0.1);
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }
        
        .info-item {
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
            line-height: 1.4;
        }
        
        .toggle-details {
            text-align: center;
            margin: 1rem 0;
        }
        
        .details-btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 0.5rem 1.5rem;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.3s ease;
        }
        
        .details-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        .detailed-analysis {
            margin-top: 1rem;
            padding: 1rem;
            background: rgba(236, 240, 241, 0.5);
            border-radius: 8px;
            border: 1px solid #ecf0f1;
        }
        
        .detail-section {
            margin-bottom: 1.5rem;
        }
        
        .detail-section h4 {
            color: #2c3e50;
            margin-bottom: 0.75rem;
            font-size: 1rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 0.5rem;
            margin-bottom: 1rem;
        }
        
        .stat-item {
            text-align: center;
            padding: 0.5rem;
            background: white;
            border-radius: 6px;
        }
        
        .stat-label {
            font-size: 0.8rem;
            color: #7f8c8d;
        }
        
        .stat-value {
            font-weight: bold;
            color: #2c3e50;
        }
        
        .volatility-details, .filter-analysis {
            background: white;
            padding: 0.75rem;
            border-radius: 6px;
        }
        
        .vol-item, .filter-item {
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
        }
        
        .analysis-text {
            background: white;
            padding: 0.75rem;
            border-radius: 6px;
            font-size: 0.9rem;
            line-height: 1.4;
        }
        
        .main-footer {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            padding: 2rem 0;
            text-align: center;
            color: #7f8c8d;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .footer-content p {
            margin-bottom: 0.5rem;
        }
        
        @media (max-width: 1200px) {
            .three-column-layout {
                grid-template-columns: 1fr 1fr;
                gap: 1.5rem;
            }
            
            .analysis-column {
                grid-column: 1 / -1;
                margin-top: 1rem;
            }
        }
        
        @media (max-width: 768px) {
            .main-title {
                font-size: 2rem;
                flex-direction: column;
                gap: 0.5rem;
            }
            
            .stats-bar {
                gap: 1.5rem;
            }
            
            .three-column-layout {
                grid-template-columns: 1fr;
                gap: 1.5rem;
            }
            
            .stock-row {
                padding: 1.5rem;
                margin: 0 1rem;
            }
            
            .stock-header {
                flex-direction: column;
                gap: 1rem;
                text-align: center;
            }
            
            .chart-image {
                max-height: 300px;
            }
            
            .analysis-content {
                max-height: none;
            }
            
            .metric-group {
                padding: 0.75rem;
            }
        }
        '''