"""
项目配置文件
"""

import os

"""全局配置与标准输出目录管理"""

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 已弃用：CSV 数据路径（保留占位便于搜索定位）
DEFAULT_CSV_PATH = None

# 输出目录配置（统一到 output/* 子目录）
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
ARC_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "arc")
SIMILARITY_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "similarity")

# 缓存目录
CACHE_DIR = os.path.join(PROJECT_ROOT, "cache")

# 数据库配置
DATABASE_CONFIG = {
    "host": "rm-0jl8p6ell797x1h5ozo.mysql.rds.aliyuncs.com",
    "port": 3308,
    "database": "lianghua",
    "username": "lianghua",
    "password": "Aa123456",
    "charset": "utf8mb4"
}

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
    """确保所有必要的目录都存在（标准化输出结构）"""
    directories = [
        # 根输出与缓存
        OUTPUT_DIR,
        CACHE_DIR,

        # 标准化的功能输出目录
        ARC_OUTPUT_DIR,
        os.path.join(ARC_OUTPUT_DIR, "images"),

        os.path.join(OUTPUT_DIR, "uptrend"),
        os.path.join(OUTPUT_DIR, "uptrend", "images"),

        os.path.join(OUTPUT_DIR, "volatility"),
        os.path.join(OUTPUT_DIR, "volatility", "images"),

        os.path.join(OUTPUT_DIR, "kline"),
        os.path.join(OUTPUT_DIR, "kline_images"),

        SIMILARITY_OUTPUT_DIR,
        os.path.join(SIMILARITY_OUTPUT_DIR, "images"),
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# 初始化时创建目录
ensure_directories() 