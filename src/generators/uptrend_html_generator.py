#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from datetime import datetime

class UptrendHTMLGenerator:
    """上升通道HTML生成器"""
    
    def __init__(self, output_dir="output/uptrend"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_uptrend_html(self, results, chart_paths):
        """生成上升通道分析HTML报告 - 修复版"""
        try:
            if not results:
                print("警告: 没有结果数据可生成HTML")
                return None
            
            # 按评分排序，使用更鲁棒的评分获取
            sorted_results = []
            for key, result in results.items():
                # 尝试获取多种可能的评分字段
                score = (result.get('enhanced_quality_score') or 
                        result.get('quality_score') or 
                        result.get('similarity_score') or 
                        0.0)
                sorted_results.append((key, result, score))
            
            # 按评分降序排序
            sorted_results.sort(key=lambda x: x[2], reverse=True)
            
            # 生成HTML内容
            html_content = self._generate_html_content_enhanced(sorted_results, chart_paths)
            
            # 保存HTML文件
            html_path = os.path.join(self.output_dir, 'uptrend_analysis.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print("上升通道分析HTML已生成:", html_path)
            return html_path
            
        except Exception as e:
            print("生成上升通道HTML失败:", str(e))
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_html_content_enhanced(self, sorted_results, chart_paths):
        """生成增强版HTML内容 - 修复数据显示问题"""
        # 计算统计信息
        total_stocks = len(sorted_results)
        avg_score = sum(result[2] for result in sorted_results) / total_stocks if total_stocks > 0 else 0
        high_quality = sum(1 for result in sorted_results if result[2] > 0.7)
        
        # 生成统计信息HTML
        stats_html = f"""
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{total_stocks}</div>
                <div class="stat-label">识别股票数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{avg_score:.3f}</div>
                <div class="stat-label">平均质量分</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{high_quality}</div>
                <div class="stat-label">高质量形态</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(chart_paths)}</div>
                <div class="stat-label">生成图表数</div>
            </div>
        </div>
        """
        
        # 生成结果卡片HTML
        results_html = ""
        for i, (key, result, score) in enumerate(sorted_results):
            stock_code = key.replace('uptrend_', '').replace('similar_', '')
            stock_name = result.get('name', stock_code)
            
            # 获取图表路径
            chart_path = chart_paths.get(key)
            if chart_path:
                # 转换为相对路径
                chart_filename = os.path.basename(chart_path)
                chart_relative_path = f"images/{chart_filename}"
            else:
                chart_relative_path = None
            
            # 获取通道信息
            channel_info = self._extract_channel_info(result)
            
            # 生成卡片HTML
            card_html = self._generate_result_card(
                i + 1, stock_code, stock_name, score, 
                chart_relative_path, channel_info
            )
            results_html += card_html
        
        # 组装完整HTML
        full_html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>上升通道分析报告</title>
    <style>
        {self._get_enhanced_css()}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 上升通道分析报告</h1>
            <p>专业股票技术分析 - 基于大弧底形态筛选</p>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        {stats_html}
        
        <div class="results-grid">
            {results_html}
        </div>
    </div>
</body>
</html>
        """
        
        return full_html
    
    def _extract_channel_info(self, result):
        """提取通道线信息"""
        channel_info = {
            'upper_slope': None,
            'lower_slope': None,
            'channel_width': None,
            'quality_score': None,
            'parallel': False
        }
        
        try:
            # 尝试从channel_result中提取信息
            channel_result = result.get('channel_result', {})
            
            if 'upper_channel' in channel_result and 'lower_channel' in channel_result:
                upper_channel = channel_result['upper_channel']
                lower_channel = channel_result['lower_channel']
                
                channel_info['upper_slope'] = upper_channel.get('slope')
                channel_info['lower_slope'] = lower_channel.get('slope')
                
                # 判断是否平行
                if (channel_info['upper_slope'] is not None and 
                    channel_info['lower_slope'] is not None):
                    slope_diff = abs(channel_info['upper_slope'] - channel_info['lower_slope'])
                    channel_info['parallel'] = slope_diff < 0.001
                
                # 计算通道宽度
                if ('intercept' in upper_channel and 'intercept' in lower_channel):
                    channel_info['channel_width'] = (
                        upper_channel['intercept'] - lower_channel['intercept']
                    )
            
            # 获取质量评分
            channel_info['quality_score'] = (
                channel_result.get('enhanced_quality_score') or
                channel_result.get('quality_score') or
                result.get('similarity_score') or
                0.0
            )
            
        except Exception as e:
            print("提取通道信息失败:", str(e))
        
        return channel_info
    
    def _generate_result_card(self, rank, code, name, score, chart_path, channel_info):
        """生成结果卡片HTML"""
        # 图表部分
        if chart_path:
            chart_html = f'<img src="{chart_path}" alt="上升通道图表" class="chart-image">'
        else:
            chart_html = '<div class="no-chart">图表生成失败</div>'
        
        # 质量标识
        if score > 0.8:
            quality_class = "excellent"
            quality_text = "优秀"
        elif score > 0.6:
            quality_class = "good"
            quality_text = "良好"
        elif score > 0.4:
            quality_class = "average"
            quality_text = "一般"
        else:
            quality_class = "poor"
            quality_text = "较差"
        
        # 通道信息
        channel_html = ""
        if channel_info['upper_slope'] is not None:
            channel_html += f"<p><strong>上轨斜率:</strong> {channel_info['upper_slope']:.6f}</p>"
        if channel_info['lower_slope'] is not None:
            channel_html += f"<p><strong>下轨斜率:</strong> {channel_info['lower_slope']:.6f}</p>"
        if channel_info['parallel']:
            channel_html += "<p><strong>通道类型:</strong> <span class='parallel'>平行通道</span></p>"
        if channel_info['channel_width'] is not None:
            channel_html += f"<p><strong>通道宽度:</strong> {channel_info['channel_width']:.2f}</p>"
        
        card_html = f"""
        <div class="result-card">
            <div class="card-header">
                <div class="rank">#{rank}</div>
                <div class="stock-info">
                    <h3>{code}</h3>
                    <p>{name}</p>
                </div>
                <div class="quality-badge {quality_class}">
                    {quality_text}
                </div>
            </div>
            
            <div class="chart-container">
                {chart_html}
            </div>
            
            <div class="card-content">
                <div class="score-section">
                    <h4>质量评分: <span class="score">{score:.3f}</span></h4>
                </div>
                
                <div class="channel-info">
                    <h4>通道信息</h4>
                    {channel_html if channel_html else "<p>暂无详细信息</p>"}
                </div>
            </div>
        </div>
        """
        
        return card_html
    
    def _get_enhanced_css(self):
        """获取增强版CSS样式"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #4facfe;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
        }
        
        .results-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            padding: 30px;
        }
        
        .result-card {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .result-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }
        
        .card-header {
            display: flex;
            align-items: center;
            padding: 20px;
            background: linear-gradient(45deg, #f8f9fa, #e9ecef);
            border-bottom: 1px solid #dee2e6;
        }
        
        .rank {
            font-size: 1.5em;
            font-weight: bold;
            color: #495057;
            margin-right: 15px;
        }
        
        .stock-info {
            flex: 1;
        }
        
        .stock-info h3 {
            font-size: 1.3em;
            color: #212529;
            margin-bottom: 5px;
        }
        
        .stock-info p {
            color: #6c757d;
            font-size: 0.9em;
        }
        
        .quality-badge {
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .quality-badge.excellent {
            background: #d4edda;
            color: #155724;
        }
        
        .quality-badge.good {
            background: #d1ecf1;
            color: #0c5460;
        }
        
        .quality-badge.average {
            background: #fff3cd;
            color: #856404;
        }
        
        .quality-badge.poor {
            background: #f8d7da;
            color: #721c24;
        }
        
        .chart-container {
            padding: 20px;
            text-align: center;
            background: #f8f9fa;
        }
        
        .chart-image {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .no-chart {
            padding: 50px;
            color: #6c757d;
            font-style: italic;
        }
        
        .card-content {
            padding: 20px;
        }
        
        .score-section {
            margin-bottom: 20px;
        }
        
        .score-section h4 {
            color: #495057;
            margin-bottom: 10px;
        }
        
        .score {
            color: #007bff;
            font-weight: bold;
        }
        
        .channel-info h4 {
            color: #495057;
            margin-bottom: 10px;
            border-bottom: 1px solid #dee2e6;
            padding-bottom: 5px;
        }
        
        .channel-info p {
            margin: 5px 0;
            color: #6c757d;
        }
        
        .parallel {
            color: #28a745;
            font-weight: bold;
        }
        """ 