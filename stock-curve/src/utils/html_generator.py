#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
from datetime import datetime

class SimilarityHTMLGenerator:
    """相似度分析HTML报告生成器"""
    
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_similarity_report(self, target_code, similar_stocks, target_img_path):
        """生成相似度分析HTML报告"""
        
        # 复制目标图片到输出目录
        target_img_name = f'{target_code}.png'
        target_img_dest = os.path.join(self.output_dir, target_img_name)
        shutil.copy2(target_img_path, target_img_dest)
        
        # 复制相似股票图片到输出目录
        similar_img_names = []
        for code, score, img_path in similar_stocks:
            img_name = f'{code}.png'
            img_dest = os.path.join(self.output_dir, img_name)
            shutil.copy2(img_path, img_dest)
            similar_img_names.append(img_name)
        
        # 生成HTML内容
        html_content = self._generate_html_content(
            target_code, similar_stocks, target_img_name, similar_img_names
        )
        
        # 保存HTML文件
        html_filename = f'similarity_{target_code}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        html_path = os.path.join(self.output_dir, html_filename)
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_path
    
    def _generate_html_content(self, target_code, similar_stocks, target_img_name, similar_img_names):
        """生成HTML内容"""
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>股票K线图相似度分析 - {target_code}</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .target-section {{
            padding: 30px;
            border-bottom: 1px solid #eee;
            text-align: center;
        }}
        .target-section h2 {{
            color: #333;
            margin-bottom: 20px;
        }}
        .target-image {{
            max-width: 600px;
            border: 2px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .similar-section {{
            padding: 30px;
        }}
        .similar-section h2 {{
            color: #333;
            margin-bottom: 30px;
            text-align: center;
        }}
        .similar-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .similar-item {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .similar-item:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        .similar-item img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            margin-bottom: 10px;
        }}
        .stock-code {{
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }}
        .similarity-score {{
            font-size: 1.1em;
            color: #667eea;
            font-weight: bold;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #eee;
        }}
        .stats {{
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>股票K线图相似度分析</h1>
            <p>基于图像哈希算法的K线图相似度分析报告</p>
        </div>
        
        <div class="target-section">
            <h2>目标股票: {target_code}</h2>
            <img src="{target_img_name}" alt="{target_code} K线图" class="target-image">
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value">{len(similar_stocks)}</div>
                <div class="stat-label">相似股票数量</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{similar_stocks[0][1]:.1f}%</div>
                <div class="stat-label">最高相似度</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{sum(s[1] for s in similar_stocks) / len(similar_stocks):.1f}%</div>
                <div class="stat-label">平均相似度</div>
            </div>
        </div>
        
        <div class="similar-section">
            <h2>相似股票列表</h2>
            <div class="similar-grid">
'''
        
        for i, ((code, score, img_path), img_name) in enumerate(zip(similar_stocks, similar_img_names)):
            html += f'''
                <div class="similar-item">
                    <img src="{img_name}" alt="{code} K线图">
                    <div class="stock-code">{code}</div>
                    <div class="similarity-score">相似度: {score:.2f}%</div>
                </div>'''
        
        html += '''
            </div>
        </div>
        
        <div class="footer">
            <p>报告生成时间: ''' + datetime.now().strftime("%Y年%m月%d日 %H:%M:%S") + '''</p>
            <p>基于图像哈希算法的K线图相似度分析</p>
        </div>
    </div>
</body>
</html>'''
        
        return html 