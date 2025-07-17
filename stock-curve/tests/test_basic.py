#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基本功能测试
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.stock_data_processor import StockDataProcessor
from src.generators.chart_generator import FastChartGenerator
from src.analyzers.pattern_analyzer import PatternAnalyzer

class TestStockDataProcessor:
    """测试股票数据处理器"""
    
    def test_initialization(self):
        """测试初始化"""
        processor = StockDataProcessor("test.csv")
        assert processor.csv_file_path == "test.csv"
        assert processor.cache_dir == "cache"
    
    def test_cache_directory_creation(self):
        """测试缓存目录创建"""
        processor = StockDataProcessor("test.csv")
        cache_dir = Path(processor.cache_dir)
        assert cache_dir.exists()

class TestChartGenerator:
    """测试图表生成器"""
    
    def test_initialization(self):
        """测试初始化"""
        generator = FastChartGenerator()
        assert generator.width == 400
        assert generator.height == 300
    
    def test_normalize_data_empty(self):
        """测试空数据标准化"""
        generator = FastChartGenerator()
        x_coords, y_coords = generator.normalize_data({})
        assert len(x_coords) == 0
        assert len(y_coords) == 0

class TestPatternAnalyzer:
    """测试模式分析器"""
    
    def test_initialization(self):
        """测试初始化"""
        analyzer = PatternAnalyzer()
        assert analyzer is not None
    
    def test_detect_arc_bottom_simple_empty(self):
        """测试空数据圆弧底检测"""
        analyzer = PatternAnalyzer()
        result = analyzer.detect_arc_bottom_simple([])
        assert result is None

if __name__ == "__main__":
    pytest.main([__file__]) 