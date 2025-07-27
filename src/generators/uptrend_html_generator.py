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
        """生成上升通道分析HTML报告"""
        try:
            # 按评分排序
            sorted_results = sorted(results.items(), 
                                  key=lambda x: x[1].get('enhanced_quality_score', x[1].get('quality_score', 0)), 
                                  reverse=True)
            
            # 生成HTML内容
            html_content = self._generate_html_content(sorted_results, chart_paths)
            
            # 保存HTML文件
            html_path = os.path.join(self.output_dir, 'uptrend_analysis.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"上升通道分析HTML已生成: {html_path}")
            return html_path
            
        except Exception as e:
            print(f"生成上升通道HTML失败: {e}")
            return None
    
    def _generate_html_content(self, sorted_results, chart_paths):
        """生成HTML内容"""
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>上升通道分析报告</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #4facfe;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 0.9em;
        }}
        
        .results-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            padding: 30px;
        }}
        
        .result-card {{
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .result-card:hover {{
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }}
        
        .chart-container {{
            position: relative;
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
        }}
        
        .chart-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        .info-container {{
            padding: 25px;
        }}
        
        .stock-code {{
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .score-badge {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .info-item {{
            background: #f8f9fa;
            padding: 12px;
            border-radius: 8px;
            border-left: 4px solid #4facfe;
        }}
        
        .info-label {{
            font-size: 0.8em;
            color: #666;
            margin-bottom: 5px;
        }}
        
        .info-value {{
            font-weight: bold;
            color: #333;
        }}
        
        .analysis-summary {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #2196f3;
        }}
        
        .summary-title {{
            font-weight: bold;
            color: #1976d2;
            margin-bottom: 10px;
        }}
        
        .summary-list {{
            list-style: none;
            padding: 0;
        }}
        
        .summary-list li {{
            padding: 5px 0;
            color: #333;
            font-size: 0.9em;
        }}
        
        .summary-list li:before {{
            content: "✓";
            color: #4caf50;
            font-weight: bold;
            margin-right: 8px;
        }}
        
        .no-results {{
            text-align: center;
            padding: 60px;
            color: #666;
        }}
        
        .no-results h2 {{
            font-size: 2em;
            margin-bottom: 20px;
            color: #999;
        }}
        
        .back-button {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 25px;
            font-weight: bold;
            transition: transform 0.3s ease;
            margin-top: 20px;
        }}
        
        .back-button:hover {{
            transform: translateY(-2px);
        }}
        
        @media (max-width: 768px) {{
            .results-grid {{
                grid-template-columns: 1fr;
            }}
            
            .info-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 上升通道分析报告</h1>
            <p>基于周K线数据的上升通道形态识别与分析</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{len(sorted_results)}</div>
                <div class="stat-label">识别到的上升通道</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{self._calculate_avg_score(sorted_results):.3f}</div>
                <div class="stat-label">平均质量评分</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{self._count_high_quality(sorted_results)}</div>
                <div class="stat-label">高质量通道 (评分>0.7)</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{datetime.now().strftime('%Y-%m-%d')}</div>
                <div class="stat-label">分析日期</div>
            </div>
        </div>
        
        <div class="results-grid">
"""
        
        if sorted_results:
            for key, result in sorted_results:
                html += self._generate_result_card(key, result, chart_paths)
        else:
            html += """
            <div class="no-results">
                <h2>🔍 未发现符合条件的上升通道</h2>
                <p>当前数据中未识别到满足条件的上升通道形态</p>
                <a href="../index.html" class="back-button">返回主页</a>
            </div>
            """
        
        html += """
        </div>
    </div>
    
    <script>
        // 添加一些交互效果
        document.addEventListener('DOMContentLoaded', function() {
            // 为图表添加点击放大效果
            const images = document.querySelectorAll('.chart-container img');
            images.forEach(img => {
                img.addEventListener('click', function() {
                    if (this.style.transform === 'scale(1.5)') {
                        this.style.transform = 'scale(1)';
                        this.style.cursor = 'zoom-in';
                    } else {
                        this.style.transform = 'scale(1.5)';
                        this.style.cursor = 'zoom-out';
                    }
                });
                img.style.cursor = 'zoom-in';
                img.style.transition = 'transform 0.3s ease';
            });
            
            // 添加滚动动画
            const observerOptions = {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            };
            
            const observer = new IntersectionObserver(function(entries) {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }
                });
            }, observerOptions);
            
            const cards = document.querySelectorAll('.result-card');
            cards.forEach(card => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(30px)';
                card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                observer.observe(card);
            });
        });
    </script>
</body>
</html>
"""
        
        return html
    
    def _generate_result_card(self, key, result, chart_paths):
        """生成单个结果卡片"""
        code = key.replace('uptrend_', '')
        chart_path = chart_paths.get(key, '')
        quality_score = result.get('enhanced_quality_score', result.get('quality_score', 0))
        
        # 检查是否为入场信号
        is_entry_signal = result.get('is_entry_signal', False)
        
        if is_entry_signal:
            # 入场信号信息
            entry_strength = result.get('entry_strength', 0)
            recent_trend = result.get('recent_trend', {})
            channel_analysis = result.get('channel_analysis', {})
            
            # 生成分析摘要
            analysis_summary = self._generate_analysis_summary(result)
            
            # 调整显示信息
            info_grid_html = f"""
                        <div class="info-item">
                            <div class="info-label">入场信号</div>
                            <div class="info-value" style="color: red; font-weight: bold;">{entry_strength:.3f}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">趋势斜率</div>
                            <div class="info-value">{recent_trend.get('slope', 0):.4f}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">趋势强度</div>
                            <div class="info-value">{recent_trend.get('r2', 0):.2f}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">价格变化</div>
                            <div class="info-value">{recent_trend.get('price_change', 0):.1%}</div>
                        </div>
            """
        else:
            # 传统通道信息
            channel_quality = result.get('channel_quality', {})
            channel_features = result.get('channel_features', {})
            
            # 生成分析摘要
            analysis_summary = self._generate_analysis_summary(result)
            
            # 传统信息网格
            info_grid_html = f"""
                        <div class="info-item">
                            <div class="info-label">持续时间</div>
                            <div class="info-value">{channel_quality.get('duration', 0)}周</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">通道宽度</div>
                            <div class="info-value">{channel_quality.get('channel_width_pct', 0):.1%}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">通道强度</div>
                            <div class="info-value">{channel_features.get('channel_strength', 0):.2f}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">突破次数</div>
                            <div class="info-value">{channel_features.get('breakout_attempts', 0)}次</div>
                        </div>
            """
        
        card_html = f"""
            <div class="result-card">
                <div class="chart-container">
                    <img src="images/{os.path.basename(chart_path)}" alt="上升通道图表 - {code}">
                </div>
                <div class="info-container">
                    <div class="stock-code">
                        <span>{code}</span>
                        <span class="score-badge">{quality_score:.3f}</span>
                    </div>
                    
                    <div class="info-grid">
                        {info_grid_html}
                    </div>
                    
                    <div class="analysis-summary">
                        <div class="summary-title">📊 技术分析摘要</div>
                        <ul class="summary-list">
"""
        
        for item in analysis_summary:
            card_html += f"<li>{item}</li>"
        
        card_html += """
                        </ul>
                    </div>
                </div>
            </div>
        """
        
        return card_html
    
    def _generate_analysis_summary(self, result):
        """生成分析摘要（优化版 - 支持入场信号）"""
        summary = []
        
        # 检查是否为入场信号
        is_entry_signal = result.get('is_entry_signal', False)
        
        if is_entry_signal:
            # 入场信号信息
            entry_strength = result.get('entry_strength', 0)
            recommendation = result.get('recommendation', '')
            summary.append(f"🎯 入场信号强度: {entry_strength:.3f}")
            summary.append(f"💡 投资建议: {recommendation}")
            
            if 'recent_trend' in result:
                trend = result['recent_trend']
                summary.append(f"📈 趋势斜率: {trend['slope']:.4f}")
                summary.append(f"📊 趋势强度: {trend['r2']:.2f}")
                summary.append(f"💰 价格变化: {trend['price_change']:.1%}")
            
            if 'channel_analysis' in result:
                analysis = result['channel_analysis']
                summary.append(f"📏 通道宽度: {analysis['channel_width']:.1%}")
                summary.append(f"📍 价格位置: {analysis['price_position']:.1%}")
                
                if analysis['price_position'] > 0.7:
                    summary.append("⚠️ 价格接近上轨，注意回调风险")
                elif analysis['price_position'] < 0.3:
                    summary.append("✅ 价格接近下轨，可能存在买入机会")
                else:
                    summary.append("✅ 价格在通道中部，趋势健康")
        else:
            # 传统通道信息
            channel_quality = result.get('channel_quality', {})
            channel_features = result.get('channel_features', {})
            
            if channel_quality.get('duration', 0) >= 20:
                summary.append("通道持续时间较长，形态稳定")
            else:
                summary.append("通道持续时间适中")
            
            if channel_quality.get('channel_width_pct', 0) >= 0.08:
                summary.append("通道宽度适中，交易空间充足")
            else:
                summary.append("通道宽度较窄，需要精确操作")
            
            if channel_features.get('channel_strength', 0) >= 0.7:
                summary.append("通道强度高，趋势明确")
            else:
                summary.append("通道强度中等")
            
            if channel_features.get('breakout_attempts', 0) <= 2:
                summary.append("突破尝试较少，通道边界有效")
            else:
                summary.append("多次突破尝试，需要关注突破信号")
        
        # 技术指标
        if 'talib_analysis' in result:
            talib_data = result['talib_analysis']
            
            if 'trend_strength' in talib_data:
                trend = talib_data['trend_strength']
                if trend.get('trend_strength') == 'strong':
                    summary.append("趋势强度高，上升动能充足")
                if trend.get('trend_direction') == 'bullish':
                    summary.append("趋势方向向上，符合上升通道特征")
            
            if 'momentum' in talib_data:
                momentum = talib_data['momentum']
                if momentum.get('macd_bullish'):
                    summary.append("MACD多头信号，动量支持上涨")
                
                rsi = momentum.get('rsi', 50)
                if 30 <= rsi <= 70:
                    summary.append("RSI处于健康区间")
                elif rsi > 70:
                    summary.append("RSI超买，注意回调风险")
                else:
                    summary.append("RSI超卖，可能存在反弹机会")
        
        return summary
    
    def _calculate_avg_score(self, sorted_results):
        """计算平均评分"""
        if not sorted_results:
            return 0.0
        
        scores = [result.get('enhanced_quality_score', result.get('quality_score', 0)) 
                 for _, result in sorted_results]
        return sum(scores) / len(scores)
    
    def _count_high_quality(self, sorted_results):
        """计算高质量通道数量"""
        count = 0
        for _, result in sorted_results:
            score = result.get('enhanced_quality_score', result.get('quality_score', 0))
            if score > 0.7:
                count += 1
        return count 