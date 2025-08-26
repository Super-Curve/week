# -*- coding: utf-8 -*-
"""
简单的日志系统
专为单人开发设计，易于使用和维护
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

# 创建日志目录
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(name, level=logging.INFO, log_to_file=True):
    """
    设置简单的日志器
    
    Args:
        name: 日志器名称（通常使用 __name__）
        level: 日志级别
        log_to_file: 是否同时输出到文件
        
    Returns:
        logger: 配置好的日志器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 格式化器 - 简洁明了
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器 - 始终启用
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器 - 可选
    if log_to_file:
        log_file = os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# 性能监控装饰器
import time
from functools import wraps

def log_performance(logger=None):
    """
    简单的性能监控装饰器
    
    使用示例:
        @log_performance(logger)
        def my_function():
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            func_logger = logger or logging.getLogger(func.__module__)
            
            func_logger.info(f"开始执行: {func.__name__}")
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                func_logger.info(f"执行完成: {func.__name__} - 耗时: {duration:.2f}秒")
                return result
            except Exception as e:
                duration = time.time() - start_time
                func_logger.error(f"执行失败: {func.__name__} - 耗时: {duration:.2f}秒 - 错误: {str(e)}")
                raise
        return wrapper
    return decorator

# 内存使用记录
try:
    import psutil
    import os
    
    def log_memory_usage(logger, operation_name=""):
        """记录当前内存使用情况"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        logger.info(f"{operation_name} - 内存使用: {memory_mb:.2f} MB")
except ImportError:
    # 如果没有安装psutil，提供一个空实现
    def log_memory_usage(logger, operation_name=""):
        pass

# 预设的日志器（方便直接使用）
def get_logger(name=None):
    """获取一个配置好的日志器"""
    if name is None:
        name = "week_analysis"
    return setup_logger(name)

# 全局默认日志器
default_logger = get_logger()
