# -*- coding: utf-8 -*-
"""
通用工具模块

提供项目中常用的工具函数，包括：
- 数据处理工具
- 文件操作工具  
- 图表生成工具
- JSON序列化工具
"""

from .common_utils import (
    setup_output_directories,
    clear_cache_if_needed,
    load_and_process_data,
    save_json_with_numpy_support,
    generate_similarity_chart,
    create_mock_arc_result
)

__all__ = [
    'setup_output_directories',
    'clear_cache_if_needed', 
    'load_and_process_data',
    'save_json_with_numpy_support',
    'generate_similarity_chart',
    'create_mock_arc_result'
]