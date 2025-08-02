#!/bin/bash

# 在stock-env环境中运行股票分析程序
# 使用方法: ./run_in_stock_env.sh [分析类型] [参数]

# 设置conda环境路径
CONDA_ENV_PATH="/Users/kangfei/miniconda3/envs/stock-env"
PYTHON_PATH="$CONDA_ENV_PATH/bin/python"

# 检查Python是否存在
if [ ! -f "$PYTHON_PATH" ]; then
    echo "错误: 找不到stock-env环境中的Python: $PYTHON_PATH"
    exit 1
fi

# 获取分析类型，默认为arc
ANALYSIS_TYPE=${1:-arc}

case $ANALYSIS_TYPE in
    "arc")
        echo "运行大弧底分析..."
        $PYTHON_PATH main_arc.py "${@:2}"
        ;;
    "uptrend")
        echo "运行上升通道分析..."
        $PYTHON_PATH main_uptrend.py "${@:2}"
        ;;
    "kline")
        echo "运行K线图生成..."
        $PYTHON_PATH main_kline.py "${@:2}"
        ;;
    "volatility")
        echo "运行波动率分析..."
        $PYTHON_PATH main_volatility.py "${@:2}"
        ;;
    "similarity")
        echo "运行相似度分析..."
        $PYTHON_PATH main_similarity.py "${@:2}"
        ;;
    "all")
        echo "运行统一分析脚本..."
        $PYTHON_PATH run_analysis.py "${@:2}"
        ;;
    *)
        echo "支持的分析类型: arc, uptrend, kline, volatility, similarity, all"
        echo "使用方法: $0 [分析类型] [参数]"
        echo "示例: $0 arc --max 100"
        echo "示例: $0 all --clear-cache"
        exit 1
        ;;
esac 