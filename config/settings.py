"""
项目配置文件
"""

import os

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据文件路径
DEFAULT_CSV_PATH = "/Users/kangfei/Downloads/result.csv"

# 输出目录配置
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
ARC_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "arc_output")
SIMILARITY_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "similarity_output")

# 缓存目录
CACHE_DIR = os.path.join(PROJECT_ROOT, "cache")

# 图片配置
IMAGE_CONFIG = {
    "width": 400,
    "height": 300,
    "margin": 20,
    "font_size": 12,
    "line_width": 1,
    "background_color": "white",
    "line_color": "blue"
}

# 圆弧底分析配置
ARC_CONFIG = {
    "min_window_size": 20,
    "max_window_size": 100,
    "min_r2_threshold": 0.7,
    "min_curvature": 0.01
}

# 图像相似度配置
SIMILARITY_CONFIG = {
    "hash_size": 8,
    "max_similar_images": 100,
    "similarity_threshold": 0.8
}

# 多进程配置
MULTIPROCESS_CONFIG = {
    "max_workers": 8,
    "batch_size": 200
}

# 确保目录存在
def ensure_directories():
    """确保所有必要的目录都存在"""
    directories = [
        OUTPUT_DIR,
        ARC_OUTPUT_DIR,
        SIMILARITY_OUTPUT_DIR,
        CACHE_DIR,
        os.path.join(OUTPUT_DIR, "images"),
        os.path.join(ARC_OUTPUT_DIR, "images")
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# 初始化时创建目录
ensure_directories() 