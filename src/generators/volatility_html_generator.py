#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from datetime import datetime
from typing import Dict, List
import pandas as pd
from src.analyzers.volatility_analyzer import VolatilityAnalyzer

class VolatilityHTMLGenerator:
    """
    波动率 HTML 生成器

    用途:
    - 批量计算/展示波动率与波幅指标，生成可分页浏览的 HTML 报告。

    实现方式:
    - 依赖 VolatilityAnalyzer 产出各类波动率序列与统计；渲染网格化图表与统计卡片

    优点:
    - 覆盖多种常见波动率估计器；报告结构化

    局限:
    - 页面较长；样式内嵌，跨项目复用度有限

    维护建议:
    - 保持 analysis_results/chart_paths 的约定键；新指标统一在 _generate_main_html 中扩展
    """
    
    def __init__(self, output_dir="output/volatility"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "images"), exist_ok=True)
        self.volatility_analyzer = VolatilityAnalyzer()
    
    def generate_volatility_html(self, stock_data_dict: Dict[str, pd.DataFrame], 
                               selected_stocks: List[str] = None,
                               start_date: str = None,
                               end_date: str = None) -> str:
        """
        生成波动率分析HTML页面
        
        Args:
            stock_data_dict: 股票数据字典
            selected_stocks: 选中的股票列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            HTML文件路径
        """
        if selected_stocks is None:
            selected_stocks = list(stock_data_dict.keys())[:50]  # 默认显示前50只股票
        
        # 生成所有股票的波动率分析
        analysis_results = {}
        chart_paths = {}
        
        for code in selected_stocks:
            if code in stock_data_dict:
                stock_data = stock_data_dict[code]
                
                # 分析波动率
                result = self.volatility_analyzer.analyze_stock_volatility(
                    stock_data, start_date, end_date
                )
                
                if "error" not in result:
                    analysis_results[code] = result
                    
                    # 生成图表
                    chart_path = os.path.join(self.output_dir, "images", f"volatility_{code}.png")
                    if self.volatility_analyzer.generate_volatility_chart(result, chart_path):
                        chart_paths[code] = chart_path
        
        # 生成HTML文件
        html_content = self._generate_main_html(analysis_results, chart_paths, start_date, end_date)
        
        # 保存HTML文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = f"volatility_analysis_{timestamp}.html"
        html_path = os.path.join(self.output_dir, html_filename)
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_path
    
    def _generate_main_html(self, analysis_results: Dict, chart_paths: Dict, 
                          start_date: str, end_date: str) -> str:
        """生成主HTML内容"""
        
        # 生成股票选择器
        stock_selector = self._generate_stock_selector(list(analysis_results.keys()))
        
        # 生成时间选择器
        time_selector = self._generate_time_selector(start_date, end_date)
        
        # 生成统计摘要
        summary_stats = self._generate_summary_stats(analysis_results)
        
        # 生成图表网格
        charts_grid = self._generate_charts_grid(analysis_results, chart_paths)
        
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>股票波动率和波幅分析</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .container {{
            max-width: 1600px;
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
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        
        .control-row {{
            display: flex;
            gap: 20px;
            margin-bottom: 15px;
            align-items: center;
        }}
        
        .control-group {{
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}
        
        .control-group label {{
            font-weight: bold;
            color: #333;
        }}
        
        .control-group select, .control-group input {{
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}
        
        .btn {{
            background-color: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s;
        }}
        
        .btn:hover {{
            background-color: #0056b3;
        }}
        
        .btn-secondary {{
            background-color: #6c757d;
            margin: 2px;
            padding: 5px 10px;
            font-size: 12px;
        }}
        
        .btn-secondary:hover {{
            background-color: #545b62;
        }}
        
        .btn:disabled {{
            background-color: #6c757d;
            cursor: not-allowed;
        }}
        
        /* 自定义下拉多选样式 */
        .custom-select {{
            position: relative;
            display: inline-block;
            width: 100%;
            max-width: 300px;
        }}
        
        .select-selected {{
            background-color: #fff;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 8px 12px;
            cursor: pointer;
            user-select: none;
            position: relative;
            min-height: 20px;
        }}
        
        .select-selected:after {{
            position: absolute;
            content: "";
            top: 14px;
            right: 10px;
            width: 0;
            height: 0;
            border: 6px solid transparent;
            border-color: #666 transparent transparent transparent;
        }}
        
        .select-selected.select-arrow-active:after {{
            border-color: transparent transparent #666 transparent;
            top: 7px;
        }}
        
        .select-items {{
            position: absolute;
            background-color: #fff;
            top: 100%;
            left: 0;
            right: 0;
            z-index: 99;
            border: 1px solid #ddd;
            border-top: none;
            border-radius: 0 0 4px 4px;
            max-height: 200px;
            overflow-y: auto;
            display: none;
        }}
        
        .select-items.show {{
            display: block;
        }}
        
        .select-items div {{
            color: #333;
            padding: 8px 12px;
            text-decoration: none;
            display: block;
            cursor: pointer;
            border-bottom: 1px solid #f0f0f0;
        }}
        
        .select-items div:hover {{
            background-color: #f8f9fa;
        }}
        
        .select-items div.selected {{
            background-color: #007bff;
            color: white;
        }}
        
        .select-items div.selected:hover {{
            background-color: #0056b3;
        }}
        
        .selected-items {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-top: 5px;
        }}
        
        .selected-item {{
            background-color: #007bff;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .selected-item .remove {{
            cursor: pointer;
            font-weight: bold;
        }}
        
        .summary-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background-color: #e7f3ff;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }}
        
        .stat-card h3 {{
            margin: 0 0 10px 0;
            color: #333;
            font-size: 16px;
        }}
        
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }}
        
        .chart-container {{
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        .chart-title {{
            text-align: center;
            font-weight: bold;
            margin-bottom: 15px;
            color: #333;
            font-size: 16px;
        }}
        
        .chart-content {{
            text-align: center;
        }}
        
        .chart-content img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }}
        
        .risk-indicator {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }}
        
        .risk-low {{
            background-color: #d4edda;
            color: #155724;
        }}
        
        .risk-medium {{
            background-color: #fff3cd;
            color: #856404;
        }}
        
        .risk-high {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        
        .info-section {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border: 1px solid #e9ecef;
        }}
        
        .info-section h2 {{
            color: #495057;
            margin-bottom: 20px;
            text-align: center;
        }}
        
        .formula-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .formula-card {{
            background-color: white;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #dee2e6;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .formula-card h3 {{
            color: #495057;
            margin-bottom: 10px;
            font-size: 14px;
        }}
        
        .formula {{
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: #495057;
            margin: 10px 0;
            border-left: 3px solid #007bff;
        }}
        
        .formula-card p {{
            color: #6c757d;
            font-size: 12px;
            line-height: 1.4;
            margin: 0;
        }}
        
        .legend {{
            background-color: #e7f3ff;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            font-size: 12px;
            color: #495057;
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
            <h1>📊 股票波动率和波幅分析</h1>
            <p>基于周K线数据的波动率和波幅分析工具</p>
        </div>
        
        <div class="info-section">
            <h2>📈 波动率计算方式说明</h2>
            <div class="formula-grid">
                <div class="formula-card">
                    <h3>1. 历史波动率 (Historical Volatility)</h3>
                    <div class="formula">σ = std(ln(Pt/Pt-1)) × √52</div>
                    <p>基于收盘价对数收益率的标准差，年化处理。反映价格变化的离散程度。</p>
                </div>
                <div class="formula-card">
                    <h3>2. 已实现波动率 (Realized Volatility)</h3>
                    <div class="formula">σ = √(Σ(rt²)/n) × √52</div>
                    <p>基于收益率平方和的平方根，更直接地反映实际波动情况。</p>
                </div>
                <div class="formula-card">
                    <h3>3. Parkinson波动率</h3>
                    <div class="formula">σ = √(Σ(ln(Ht/Lt)²)/(4×ln(2)×n)) × √52</div>
                    <p>利用日内最高价和最低价信息，比收盘价波动率更精确。</p>
                </div>
                <div class="formula-card">
                    <h3>4. Garman-Klass波动率</h3>
                    <div class="formula">σ = √(Σ(0.5×ln(Ht/Lt)²-(2×ln(2)-1)×ln(Ct/Ot)²)/n) × √52</div>
                    <p>综合开盘、收盘、最高、最低价信息，提供最全面的波动率估计。</p>
                </div>
            </div>
            <div class="legend">
                <p><strong>符号说明:</strong> Pt=价格, rt=收益率, Ht=最高价, Lt=最低价, Ct=收盘价, Ot=开盘价, n=样本数</p>
            </div>
        </div>
        
        <div class="info">
            <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>分析范围:</strong> {start_date or '全部'} 至 {end_date or '全部'}</p>
            <p><strong>分析股票:</strong> {len(analysis_results)} 只</p>
        </div>
        
        <div class="control-panel">
            <h2>分析控制面板</h2>
            {stock_selector}
            {time_selector}
            <div class="control-row">
                <button class="btn" onclick="refreshAnalysis()">重新分析</button>
                <button class="btn" onclick="exportData()">导出数据</button>
            </div>
        </div>
        
        <div class="summary-stats">
            {summary_stats}
        </div>
        
        <div class="charts-grid">
            {charts_grid}
        </div>
    </div>
    
    <script>
        // 全局变量存储选中的股票
        let selectedStocks = [];
        
        // 存储所有股票的数据
        const allStockData = {json.dumps(analysis_results, ensure_ascii=False, default=str)};
        
        function refreshAnalysis() {{
            // 获取选中的股票和时间范围
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            
            // 构建URL参数
            const params = new URLSearchParams({{
                stocks: selectedStocks.join(','),
                start_date: startDate,
                end_date: endDate
            }});
            
            // 重新加载页面
            window.location.href = window.location.pathname + '?' + params.toString();
        }}
        
        function updateDisplay() {{
            // 过滤选中的股票数据
            const filteredData = {{}};
            selectedStocks.forEach(stock => {{
                if (allStockData[stock]) {{
                    filteredData[stock] = allStockData[stock];
                }}
            }});
            
            // 更新统计摘要
            updateSummaryStats(filteredData);
            
            // 更新图表显示
            updateChartsGrid(filteredData);
            
            // 更新信息面板
            updateInfoPanel(filteredData);
        }}
        
        function updateSummaryStats(data) {{
            const summaryContainer = document.querySelector('.summary-stats');
            if (Object.keys(data).length === 0) {{
                summaryContainer.innerHTML = '<div class="stat-card"><h3>无数据</h3><div class="stat-value">0</div></div>';
                return;
            }}
            
            // 计算汇总统计
            const volatilities = Object.values(data).map(result => result.statistics.current_volatility);
            const amplitudes = Object.values(data).map(result => result.statistics.current_amplitude);
            const riskLevels = Object.values(data).map(result => result.risk_level);
            
            const avgVol = volatilities.reduce((a, b) => a + b, 0) / volatilities.length;
            const avgAmp = amplitudes.reduce((a, b) => a + b, 0) / amplitudes.length;
            const highRiskCount = riskLevels.filter(level => level === '高风险').length;
            const lowRiskCount = riskLevels.filter(level => level === '低风险').length;
            
            summaryContainer.innerHTML = `
                <div class="stat-card">
                    <h3>平均波动率</h3>
                    <div class="stat-value">${{avgVol.toFixed(4)}}</div>
                </div>
                <div class="stat-card">
                    <h3>平均波幅</h3>
                    <div class="stat-value">${{avgAmp.toFixed(2)}}%</div>
                </div>
                <div class="stat-card">
                    <h3>高风险股票</h3>
                    <div class="stat-value">${{highRiskCount}}</div>
                </div>
                <div class="stat-card">
                    <h3>低风险股票</h3>
                    <div class="stat-value">${{lowRiskCount}}</div>
                </div>
            `;
        }}
        
        function updateChartsGrid(data) {{
            const chartsContainer = document.querySelector('.charts-grid');
            if (Object.keys(data).length === 0) {{
                chartsContainer.innerHTML = '<div class="chart-container"><div class="chart-title">无数据</div></div>';
                return;
            }}
            
            let chartsHtml = '';
            Object.entries(data).forEach(([code, result]) => {{
                const stats = result.statistics;
                const riskLevel = result.risk_level;
                
                const riskClass = {{
                    '低风险': 'risk-low',
                    '中等风险': 'risk-medium',
                    '中高风险': 'risk-high',
                    '高风险': 'risk-high'
                }}[riskLevel] || 'risk-medium';
                
                chartsHtml += `
                    <div class="chart-container">
                        <div class="chart-title">
                            ${{code}}
                            <span class="risk-indicator ${{riskClass}}">${{riskLevel}}</span>
                        </div>
                        <div class="chart-content">
                            <img src="images/volatility_${{code}}.png" alt="${{code}} 波动率分析" style="width: 100%; height: auto;">
                        </div>
                        <div style="margin-top: 10px; font-size: 12px; color: #666;">
                            波动率: ${{stats.current_volatility.toFixed(4)}} | 波幅: ${{stats.current_amplitude.toFixed(2)}}%
                        </div>
                    </div>
                `;
            }});
            
            chartsContainer.innerHTML = chartsHtml;
        }}
        
        function updateInfoPanel(data) {{
            const infoContainer = document.querySelector('.info');
            const stockCount = Object.keys(data).length;
            infoContainer.innerHTML = `
                <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>分析范围:</strong> {start_date or '全部'} 至 {end_date or '全部'}</p>
                <p><strong>分析股票:</strong> ${{stockCount}} 只</p>
            `;
        }}
        
                    function exportData() {{
                // 导出分析数据（简化版本）
                const data = {{
                    generation_time: '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                    total_stocks: {len(analysis_results)}
                }};
                
                const blob = new Blob([JSON.stringify(data, null, 2)], {{type: 'application/json'}});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'volatility_analysis_summary.json';
                a.click();
                URL.revokeObjectURL(url);
            }}
        
        // 自定义下拉多选相关函数
        function toggleSelect() {{
            const selectItems = document.getElementById('stockOptions');
            const selectSelected = document.querySelector('.select-selected');
            selectItems.classList.toggle('show');
            selectSelected.classList.toggle('select-arrow-active');
        }}
        
        function selectStock(stockCode) {{
            const item = document.querySelector(`[data-value="${{stockCode}}"]`);
            if (selectedStocks.includes(stockCode)) {{
                // 取消选择
                selectedStocks = selectedStocks.filter(s => s !== stockCode);
                item.classList.remove('selected');
            }} else {{
                // 选择
                selectedStocks.push(stockCode);
                item.classList.add('selected');
            }}
            updateSelectedDisplay();
            updateDisplay(); // 更新数据显示
        }}
        
        function updateSelectedDisplay() {{
            const selectedItemsContainer = document.getElementById('selectedItems');
            const selectedCount = document.getElementById('selectedCount');
            
            // 更新选中数量
            selectedCount.textContent = selectedStocks.length;
            
            // 更新选中项目显示
            selectedItemsContainer.innerHTML = '';
            selectedStocks.forEach(stock => {{
                const item = document.createElement('div');
                item.className = 'selected-item';
                item.innerHTML = `${{stock}} <span class="remove" onclick="removeStock('${{stock}}')">&times;</span>`;
                selectedItemsContainer.appendChild(item);
            }});
            
            // 更新下拉框显示文本
            const selectSelected = document.querySelector('.select-selected');
            if (selectedStocks.length === 0) {{
                selectSelected.textContent = '点击选择股票';
            }} else if (selectedStocks.length <= 3) {{
                selectSelected.textContent = selectedStocks.join(', ');
            }} else {{
                selectSelected.textContent = `已选择 ${{selectedStocks.length}} 只股票`;
            }}
        }}
        
        function removeStock(stockCode) {{
            selectedStocks = selectedStocks.filter(s => s !== stockCode);
            const item = document.querySelector(`[data-value="${{stockCode}}"]`);
            item.classList.remove('selected');
            updateSelectedDisplay();
            updateDisplay(); // 更新数据显示
        }}
        
        // 股票选择相关函数
        function selectAll() {{
            const stockItems = document.querySelectorAll('.select-item');
            selectedStocks = [];
            stockItems.forEach((item, index) => {{
                const stockCode = item.getAttribute('data-value');
                selectedStocks.push(stockCode);
                item.classList.add('selected');
            }});
            updateSelectedDisplay();
            updateDisplay(); // 更新数据显示
        }}
        
        function clearSelection() {{
            const stockItems = document.querySelectorAll('.select-item');
            selectedStocks = [];
            stockItems.forEach(item => {{
                item.classList.remove('selected');
            }});
            updateSelectedDisplay();
            updateDisplay(); // 更新数据显示
        }}
        
        function selectTop10() {{
            const stockItems = document.querySelectorAll('.select-item');
            selectedStocks = [];
            stockItems.forEach((item, index) => {{
                const stockCode = item.getAttribute('data-value');
                if (index < 10) {{
                    selectedStocks.push(stockCode);
                    item.classList.add('selected');
                }} else {{
                    item.classList.remove('selected');
                }}
            }});
            updateSelectedDisplay();
            updateDisplay(); // 更新数据显示
        }}
        
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', function() {{
            // 从URL参数中恢复选择状态
            const urlParams = new URLSearchParams(window.location.search);
            const stocks = urlParams.get('stocks');
            const startDate = urlParams.get('start_date');
            const endDate = urlParams.get('end_date');
            
            // 初始化默认选择前10只股票
            const stockItems = document.querySelectorAll('.select-item');
            stockItems.forEach((item, index) => {{
                const stockCode = item.getAttribute('data-value');
                if (index < 10) {{
                    selectedStocks.push(stockCode);
                    item.classList.add('selected');
                }}
                
                // 添加点击事件
                item.addEventListener('click', function() {{
                    selectStock(stockCode);
                }});
            }});
            
            // 如果有URL参数，覆盖默认选择
            if (stocks) {{
                const stockArray = stocks.split(',');
                selectedStocks = stockArray;
                stockItems.forEach(item => {{
                    const stockCode = item.getAttribute('data-value');
                    if (stockArray.includes(stockCode)) {{
                        item.classList.add('selected');
                    }} else {{
                        item.classList.remove('selected');
                    }}
                }});
            }}
            
            if (startDate) {{
                document.getElementById('startDate').value = startDate;
            }}
            
            if (endDate) {{
                document.getElementById('endDate').value = endDate;
            }}
            
            // 更新显示
            updateSelectedDisplay();
            updateDisplay(); // 初始化数据显示
            
            // 点击外部关闭下拉框
            document.addEventListener('click', function(e) {{
                if (!e.target.closest('.custom-select')) {{
                    const selectItems = document.getElementById('stockOptions');
                    const selectSelected = document.querySelector('.select-selected');
                    selectItems.classList.remove('show');
                    selectSelected.classList.remove('select-arrow-active');
                }}
            }});
        }});
    </script>
</body>
</html>
        """
        
        return html_content
    
    def _generate_stock_selector(self, stock_codes: List[str]) -> str:
        """生成股票选择器"""
        options = ""
        for i, code in enumerate(stock_codes):
            # 默认选择前10个股票
            selected = "selected" if i < 10 else ""
            options += f'<div class="select-item" data-value="{code}" {selected}>{code}</div>'
        
        return f"""
        <div class="control-row">
            <div class="control-group">
                <label for="stockSelector">选择股票:</label>
                <div class="custom-select">
                    <div class="select-selected" onclick="toggleSelect()">
                        点击选择股票
                    </div>
                    <div class="select-items" id="stockOptions">
                        {options}
                    </div>
                </div>
                <div class="selected-items" id="selectedItems"></div>
                <div style="margin-top: 5px; font-size: 12px; color: #666;">
                    已选择 <span id="selectedCount">10</span> 只股票
                </div>
            </div>
            <div class="control-group">
                <button type="button" class="btn btn-secondary" onclick="selectAll()">全选</button>
                <button type="button" class="btn btn-secondary" onclick="clearSelection()">清空</button>
                <button type="button" class="btn btn-secondary" onclick="selectTop10()">选择前10</button>
            </div>
        </div>
        """
    
    def _generate_time_selector(self, start_date: str, end_date: str) -> str:
        """生成时间选择器"""
        return f"""
        <div class="control-row">
            <div class="control-group">
                <label for="startDate">开始日期:</label>
                <input type="date" id="startDate" value="{start_date or ''}">
            </div>
            <div class="control-group">
                <label for="endDate">结束日期:</label>
                <input type="date" id="endDate" value="{end_date or ''}">
            </div>
        </div>
        """
    
    def _generate_summary_stats(self, analysis_results: Dict) -> str:
        """生成统计摘要"""
        if not analysis_results:
            return '<div class="stat-card"><h3>无数据</h3><div class="stat-value">0</div></div>'
        
        # 计算汇总统计
        volatilities = [result['statistics']['current_volatility'] for result in analysis_results.values()]
        amplitudes = [result['statistics']['current_amplitude'] for result in analysis_results.values()]
        risk_levels = [result['risk_level'] for result in analysis_results.values()]
        
        avg_vol = sum(volatilities) / len(volatilities)
        avg_amp = sum(amplitudes) / len(amplitudes)
        high_risk_count = risk_levels.count('高风险')
        low_risk_count = risk_levels.count('低风险')
        
        return f"""
        <div class="stat-card">
            <h3>平均波动率</h3>
            <div class="stat-value">{avg_vol:.4f}</div>
        </div>
        <div class="stat-card">
            <h3>平均波幅</h3>
            <div class="stat-value">{avg_amp:.2f}%</div>
        </div>
        <div class="stat-card">
            <h3>高风险股票</h3>
            <div class="stat-value">{high_risk_count}</div>
        </div>
        <div class="stat-card">
            <h3>低风险股票</h3>
            <div class="stat-value">{low_risk_count}</div>
        </div>
        """
    
    def _generate_charts_grid(self, analysis_results: Dict, chart_paths: Dict) -> str:
        """生成图表网格"""
        if not analysis_results:
            return '<div class="chart-container"><div class="chart-title">无数据</div></div>'
        
        charts_html = ""
        for code, result in analysis_results.items():
            if code in chart_paths:
                chart_path = os.path.relpath(chart_paths[code], self.output_dir)
                stats = result['statistics']
                risk_level = result['risk_level']
                
                risk_class = {
                    '低风险': 'risk-low',
                    '中等风险': 'risk-medium',
                    '中高风险': 'risk-high',
                    '高风险': 'risk-high'
                }.get(risk_level, 'risk-medium')
                
                charts_html += f"""
                <div class="chart-container">
                    <div class="chart-title">
                        {code}
                        <span class="risk-indicator {risk_class}">{risk_level}</span>
                    </div>
                    <div class="chart-content">
                        <img src="{chart_path}" alt="{code} 波动率分析" style="width: 100%; height: auto;">
                    </div>
                    <div style="margin-top: 10px; font-size: 12px; color: #666;">
                        波动率: {stats['current_volatility']:.4f} | 波幅: {stats['current_amplitude']:.2f}%
                    </div>
                </div>
                """
        
        return charts_html 