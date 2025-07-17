import os
import json
from src.core.stock_data_processor import StockDataProcessor
from src.generators.chart_generator import FastChartGenerator
from datetime import datetime

class StaticHTMLGenerator:
    def __init__(self, csv_file_path, output_dir="output"):
        self.csv_file_path = csv_file_path
        self.output_dir = output_dir
        self.stock_processor = None
        self.chart_generator = None
        
    def process_data(self):
        """处理数据并生成图表"""
        print("开始处理数据...")
        
        # 初始化数据处理器
        self.stock_processor = StockDataProcessor(self.csv_file_path)
        
        # 加载和处理数据
        if not self.stock_processor.load_data():
            print("数据加载失败")
            return False
        
        if not self.stock_processor.process_weekly_data():
            print("数据处理失败")
            return False
        
        # 初始化图表生成器
        self.chart_generator = FastChartGenerator(output_dir=os.path.join(self.output_dir, "images"))
        
        print("数据处理完成")
        return True
    
    def generate_static_html(self, max_charts=None):
        """生成静态HTML文件"""
        if not self.process_data():
            return False
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 获取所有股票数据
        all_data = self.stock_processor.get_all_data()
        stock_codes = list(all_data.keys())
        
        if max_charts:
            stock_codes = stock_codes[:max_charts]
            print(f"开始生成 {len(stock_codes)} 只股票的图片（限制数量）...")
        else:
            print(f"开始生成 {len(stock_codes)} 只股票的图片...")
        
        # 生成所有图片
        all_images = self.chart_generator.generate_charts_batch(all_data, max_charts)
        
        # 生成HTML文件
        self._generate_main_html(all_images, stock_codes)
        
        print(f"静态HTML文件已生成到 {self.output_dir} 目录")
        return True
    
    def generate_html_only(self, stock_data, max_charts=None):
        """只生成HTML文件，不生成图片（假设图片已存在）"""
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 获取股票代码列表
        stock_codes = list(stock_data.keys())
        
        if max_charts:
            stock_codes = stock_codes[:max_charts]
        
        # 构建图片路径字典（假设图片已存在）
        all_images = {}
        for code in stock_codes:
            img_path = os.path.join(self.output_dir, "images", f"{code}.png")
            if os.path.exists(img_path):
                all_images[code] = img_path
        
        # 生成HTML文件
        self._generate_main_html(all_images, stock_codes)
        
        print(f"静态HTML文件已生成到 {self.output_dir} 目录")
        return True
    
    def _generate_main_html(self, all_images, stock_codes):
        """生成主页面HTML"""
        charts_per_page = 100  # 每页100个图表（25行×4列）
        total_pages = (len(stock_codes) + charts_per_page - 1) // charts_per_page
        
        html_content = self._get_html_header()
        
        # 添加控制面板
        html_content += '''
        <div class="control-panel">
            <h2>A股周K线图展示</h2>
            <p>共 <span id="totalStocks">''' + str(len(stock_codes)) + '''</span> 只股票，<span id="totalPages">''' + str(total_pages) + '''</span> 页</p>
            <div class="pagination-controls">
                <button id="prevPageBtn" class="btn" onclick="prevPage()">上一页</button>
                <span id="pageInfo">第 1 页，共 ''' + str(total_pages) + ''' 页</span>
                <button id="nextPageBtn" class="btn" onclick="nextPage()">下一页</button>
            </div>
        </div>
        '''
        
        # 生成所有页面的图片
        for page in range(1, total_pages + 1):
            start_idx = (page - 1) * charts_per_page
            end_idx = min(start_idx + charts_per_page, len(stock_codes))
            
            page_images = {}
            for i in range(start_idx, end_idx):
                code = stock_codes[i]
                if code in all_images:
                    page_images[code] = all_images[code]
            
            html_content += f'<div id="page{page}" class="page" style="display: {"block" if page == 1 else "none"};"><div class="charts-grid">'
            
            for code, image_path in page_images.items():
                # 获取相对路径
                rel_path = os.path.relpath(image_path, self.output_dir)
                html_content += f'''
                <div class="chart-container">
                    <div class="chart-title">{code}</div>
                    <div class="chart-content">
                        <img src="{rel_path}" alt="{code} 周K线图" style="width: 100%; height: auto;">
                    </div>
                </div>
                '''
            
            html_content += '</div></div>'
        
        # 添加JavaScript
        html_content += self._get_javascript(total_pages)
        
        # 添加HTML尾部
        html_content += self._get_html_footer()
        
        # 保存文件
        with open(os.path.join(self.output_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _get_html_header(self):
        """获取HTML头部"""
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A股周K线图展示</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }
        
        .header h1 {
            color: #333;
            margin: 0;
            font-size: 2.5em;
        }
        
        .control-panel {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }
        
        .control-panel h2 {
            margin: 0 0 10px 0;
            color: #333;
        }
        
        .pagination-controls {
            margin-top: 15px;
        }
        
        .btn {
            background-color: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
            border-radius: 5px;
            cursor: pointer;
            margin: 0 10px;
            transition: background-color 0.3s;
        }
        
        .btn:hover {
            background-color: #0056b3;
        }
        
        .btn:disabled {
            background-color: #6c757d;
            cursor: not-allowed;
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-top: 20px;
        }
        
        .chart-container {
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        
        .chart-container:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        }
        
        .chart-title {
            text-align: center;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
            font-size: 14px;
        }
        
        .chart-content {
            text-align: center;
        }
        
        .chart-content img {
            border-radius: 4px;
            max-width: 100%;
            height: auto;
        }
        
        .page {
            margin-bottom: 30px;
        }
        
        .info {
            background-color: #e7f3ff;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #007bff;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 A股周K线图展示</h1>
            <p>基于最近三年数据的周K线图分析</p>
        </div>
        
        <div class="info">
            <p><strong>生成时间:</strong> ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''</p>
            <p><strong>数据来源:</strong> ''' + self.csv_file_path + '''</p>
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