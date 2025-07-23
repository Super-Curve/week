import os
import json
from datetime import datetime
from src.analyzers.pattern_analyzer import PatternAnalyzer
from src.generators.arc_chart_generator import ArcChartGenerator

class ArcHTMLGenerator:
    def __init__(self, output_dir="arc_output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.pattern_analyzer = PatternAnalyzer()
        self.arc_chart_generator = ArcChartGenerator(output_dir=os.path.join(self.output_dir, "images"))
        
    def analyze_and_generate(self, stock_data_dict, max_charts=None):
        """分析圆弧底形态并生成HTML"""
        print("开始分析圆弧底形态...")
        
        # 检测圆弧底形态
        arc_patterns = {}
        total_stocks = len(stock_data_dict)
        
        for i, (code, data) in enumerate(stock_data_dict.items()):
            if max_charts and len(arc_patterns) >= max_charts:
                break
                
            # 检测圆弧底
            pattern = self.pattern_analyzer.detect_arc_bottom(data)
            
            if pattern and self.pattern_analyzer.is_valid_arc_bottom(pattern['stages']):
                arc_patterns[code] = pattern
            
            # 显示进度
            if (i + 1) % 500 == 0:
                progress = ((i + 1) / total_stocks) * 100
                print(f"已分析 {i + 1}/{total_stocks} 只股票 ({progress:.1f}%) - 发现 {len(arc_patterns)} 个圆弧底")
        
        print(f"圆弧底分析完成，发现 {len(arc_patterns)} 个圆弧底形态")
        
        if len(arc_patterns) == 0:
            print("未发现有效的圆弧底形态")
            return False
        
        # 生成圆弧底分析图表
        arc_charts = self.arc_chart_generator.generate_arc_charts_batch(arc_patterns)
        
        # 生成HTML文件
        self._generate_arc_html(arc_charts, arc_patterns)
        
        return True
    
    def generate_arc_html(self, arc_results, chart_paths):
        """根据新结构生成圆弧底分析HTML"""
        charts_per_page = 100  # 一页100个图表（25行×4列）
        total = len(arc_results)
        total_pages = (total + charts_per_page - 1) // charts_per_page
        html = self._get_html_header(total, total_pages)
        codes = list(arc_results.keys())
        for page in range(1, total_pages + 1):
            start_idx = (page - 1) * charts_per_page
            end_idx = min(start_idx + charts_per_page, total)
            html += f'<div id="page{page}" class="page" style="display: {"block" if page == 1 else "none"};"><div class="charts-grid">'
            for i in range(start_idx, end_idx):
                code = codes[i]
                if code not in chart_paths:
                    print(f"警告: 股票代码 {code} 在 chart_paths 中不存在，跳过")
                    continue
                img_path = os.path.relpath(chart_paths[code], self.output_dir)
                arc_result = arc_results[code]['arc_result']
                name = arc_results[code].get('name', code)
                # 判断类型
                if arc_result.get('type') == 'global_arc_bottom':
                    min_idx = arc_result.get('min_point', 0)
                    total_points = arc_result.get('total_points', 0)
                    r2 = arc_result.get('r2', 0)
                    quality = arc_result.get('quality_score', 0)
                    
                    # 检查是否有横盘阶段
                    stages = arc_result.get('stages', {})
                    has_flat = 'flat' in stages and isinstance(stages['flat'], dict)
                    
                    if has_flat:
                        title = f"{code} {name} 严重下降→横盘→轻微上涨 R²={r2:.2f} 质量={quality:.1f}"
                    else:
                        title = f"{code} {name} 下降→上涨 R²={r2:.2f} 质量={quality:.1f}"
                elif arc_result.get('type') in ['similarity_based', 'similarity_analysis']:
                    # 相似度分析结果的标题
                    similarity_score = arc_result.get('similarity_score', 0)
                    r2 = arc_result.get('r2', 0)
                    total_points = arc_result.get('total_points', len(arc_results[code].get('prices', [])))
                    start = arc_result.get('start', 0)
                    end = arc_result.get('end', total_points - 1)
                    
                    # 确保R²值格式正确
                    r2_display = f"{r2:.3f}" if r2 > 0 else "0.000"
                    
                    title = f"{code} {name} 相似度: {similarity_score:.3f} 区间: {start}-{end} R²={r2_display}"
                elif arc_result.get('type') == 'strategic_major_arc_bottom':
                    # 战略大弧底结果
                    r2 = arc_result.get('r2', 0)
                    quality_score = arc_result.get('quality_score', 0)
                    enhanced_score = arc_result.get('enhanced_quality_score', quality_score)
                    consolidation_weeks = arc_result.get('consolidation_weeks', 0)
                    
                    if 'talib_analysis' in arc_result:
                        title = f"{code} {name} 增强评分: {enhanced_score:.3f} 盘整: {consolidation_weeks}周 R²={r2:.2f}"
                    else:
                        title = f"{code} {name} 质量评分: {quality_score:.3f} 盘整: {consolidation_weeks}周 R²={r2:.2f}"
                else:
                    # 默认格式
                    start = arc_result.get('start', 0)
                    end = arc_result.get('end', 0)
                    r2 = arc_result.get('r2', 0)
                    title = f"{code} {name} 区间: {start}-{end} R²={r2:.2f}"
                html += f'''
                <div class="chart-container">
                    <div class="chart-title">{title}</div>
                    <div class="chart-content">
                        <img src="{img_path}" alt="{code} 圆弧底分析" style="width: 100%; height: auto;">
                    </div>
                </div>
                '''
            html += '</div></div>'
        html += self._get_javascript(total_pages)
        html += self._get_html_footer()
        with open(os.path.join(self.output_dir, 'arc_analysis.html'), 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"圆弧底分析HTML已生成: {os.path.join(self.output_dir, 'arc_analysis.html')}")
    
    def _generate_arc_html(self, arc_charts, arc_patterns):
        """生成圆弧底分析的HTML文件"""
        charts_per_page = 50  # 每页50个图表
        total_pages = (len(arc_charts) + charts_per_page - 1) // charts_per_page
        
        html_content = self._get_html_header(len(arc_charts), total_pages)
        
        # 生成所有页面的图表
        for page in range(1, total_pages + 1):
            start_idx = (page - 1) * charts_per_page
            end_idx = min(start_idx + charts_per_page, len(arc_charts))
            
            page_charts = {}
            stock_codes = list(arc_charts.keys())
            for i in range(start_idx, end_idx):
                code = stock_codes[i]
                page_charts[code] = arc_charts[code]
            
            html_content += f'<div id="page{page}" class="page" style="display: {"block" if page == 1 else "none"};"><div class="charts-grid">'
            
            for code, image_path in page_charts.items():
                # 获取相对路径
                rel_path = os.path.relpath(image_path, self.output_dir)
                pattern_data = arc_patterns[code]
                score = pattern_data['score']
                stages = pattern_data['stages']
                
                # 生成详细信息
                details = self._generate_stage_details(stages)
                
                html_content += f'''
                <div class="chart-container">
                    <div class="chart-title">{code} (拟合度: {score:.2f})</div>
                    <div class="chart-content">
                        <img src="{rel_path}" alt="{code} 圆弧底分析" style="width: 100%; height: auto;">
                    </div>
                    <div class="stage-details">
                        {details}
                    </div>
                </div>
                '''
            
            html_content += '</div></div>'
        
        # 添加JavaScript
        html_content += self._get_javascript(total_pages)
        
        # 添加HTML尾部
        html_content += self._get_html_footer()
        
        # 保存文件
        with open(os.path.join(self.output_dir, 'arc_analysis.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"圆弧底分析HTML已生成: {os.path.join(self.output_dir, 'arc_analysis.html')}")
    
    def _generate_stage_details(self, stages):
        """生成阶段详细信息"""
        details = ""
        
        for stage_name, stage_data in stages.items():
            if not stage_data:
                continue
            
            stage_type = stage_data['type']
            price_change = stage_data['price_change_pct']
            duration = stage_data['duration']
            slope = stage_data['slope']
            
            color_map = {'decline': 'red', 'flat': 'orange', 'rise': 'green'}
            color = color_map.get(stage_type, 'black')
            
            details += f'<div class="stage-info" style="color: {color};">'
            details += f'<strong>{stage_type}:</strong> {price_change:+.1f}% ({duration}周)'
            details += '</div>'
        
        return details
    
    def _get_html_header(self, total_arcs, total_pages):
        """获取HTML头部"""
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A股全局圆弧底形态分析</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }}
        
        .header h1 {{
            color: #333;
            margin: 0;
            font-size: 2.5em;
        }}
        
        .control-panel {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }}
        
        .control-panel h2 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        
        .pagination-controls {{
            margin-top: 15px;
        }}
        
        .btn {{
            background-color: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
            border-radius: 5px;
            cursor: pointer;
            margin: 0 10px;
            transition: background-color 0.3s;
        }}
        
        .btn:hover {{
            background-color: #0056b3;
        }}
        
        .btn:disabled {{
            background-color: #6c757d;
            cursor: not-allowed;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-top: 20px;
        }}
        
        .chart-container {{
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        
        .chart-container:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        }}
        
        .chart-title {{
            text-align: center;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
            font-size: 12px;
            line-height: 1.2;
        }}
        
        .chart-content {{
            text-align: center;
        }}
        
        .chart-content img {{
            border-radius: 4px;
            max-width: 100%;
            height: auto;
        }}
        
        .page {{
            margin-bottom: 30px;
        }}
        
        .info {{
            background-color: #e7f3ff;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #007bff;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 A股全局圆弧底形态分析</h1>
            <p>基于全局圆弧底检测算法的形态分析</p>
        </div>
        
        <div class="info">
            <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>检测结果:</strong> 共发现 {total_arcs} 只股票存在全局圆弧底形态</p>
        </div>

        <div class="control-panel">
            <h2>A股全局圆弧底形态分析</h2>
            <p>共 <span id="totalStocks">{total_arcs}</span> 只股票，<span id="totalPages">{total_pages}</span> 页</p>
            <div class="pagination-controls">
                <button id="prevPageBtn" class="btn" onclick="prevPage()">上一页</button>
                <span id="pageInfo">第 1 页，共 {total_pages} 页</span>
                <button id="nextPageBtn" class="btn" onclick="nextPage()">下一页</button>
            </div>
        </div>
'''
    
    def _get_javascript(self, total_pages):
        """获取JavaScript代码"""
        return f'''
        <script>
            let currentPage = 1;
            const totalPages = {total_pages};
            
            function showPage(page) {{
                // 隐藏所有页面
                for (let i = 1; i <= totalPages; i++) {{
                    document.getElementById(`page${{i}}`).style.display = 'none';
                }}
                
                // 显示当前页面
                document.getElementById(`page${{page}}`).style.display = 'block';
                
                // 更新按钮状态
                document.getElementById('prevPageBtn').disabled = page <= 1;
                document.getElementById('nextPageBtn').disabled = page >= totalPages;
                
                // 更新页面信息
                document.getElementById('pageInfo').textContent = `第 ${{page}} 页，共 ${{totalPages}} 页`;
            }}
            
            function prevPage() {{
                if (currentPage > 1) {{
                    currentPage--;
                    showPage(currentPage);
                }}
            }}
            
            function nextPage() {{
                if (currentPage < totalPages) {{
                    currentPage++;
                    showPage(currentPage);
                }}
            }}
            
            // 初始化页面
            showPage(1);
        </script>
'''
    
    def _get_html_footer(self):
        """获取HTML尾部"""
        return '''
    </div>
</body>
</html>
''' 