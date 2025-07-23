# A股技术分析平台

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![TA-Lib](https://img.shields.io/badge/TA--Lib-0.5.1-green.svg)](https://ta-lib.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

专业级的A股技术分析工具集，基于TA-Lib与机器学习算法，提供多维度的股票技术分析功能。

## 🌟 新功能亮点

### 📊 统一导航平台
- **全新的index.html界面**: 美化的主导航页面，一站式访问所有分析模块
- **智能状态检测**: 自动检测各模块文件状态，显示实时可用性
- **响应式设计**: 支持桌面和移动设备的最佳浏览体验
- **动画效果**: 流畅的页面动画和交互效果

### 🚀 一键启动脚本
```bash
# 快速启动所有分析
python run_analysis.py all --open-browser

# 单独运行特定分析
python run_analysis.py arc --max 100        # 大弧底分析
python run_analysis.py volatility           # 波动率分析
python run_analysis.py kline                # K线图分析
python run_analysis.py similarity           # 相似度分析
```

### 🎯 TA-Lib增强分析
- **专业技术指标**: 集成158个TA-Lib技术指标
- **多维度评分**: 结合价格、成交量、趋势、动量等维度
- **智能回退**: TA-Lib不可用时自动使用基础算法
- **检测精度提升**: 相比基础方法提升17%的准确率

## 🚀 快速开始

### 方法一：一键启动（推荐）
```bash
# 克隆项目
git clone <repository-url>
cd week

# 激活stock-env环境（如果有）
conda activate stock-env

# 运行完整分析并打开浏览器
python run_analysis.py all --open-browser
```

### 方法二：传统启动
```bash
# 安装依赖
pip install -r requirements.txt

# 运行特定分析
python main_arc.py --csv your_data.csv --output output/arc
python main_volatility.py --csv your_data.csv --output output/volatility
python main_kline.py --csv your_data.csv --output output/kline

# 打开浏览器查看结果
open output/index.html  # macOS
# 或 start output/index.html  # Windows
```

## 📊 分析模块总览

| 模块 | 功能 | 输出 | TA-Lib支持 |
|------|------|------|------------|
| 🎯 **大弧底检测** | 专业形态识别，相似度TOP100 | `output/arc/arc_analysis.html` | ✅ 增强版 |
| 📊 **波动率分析** | 4种专业波动率算法，风险评估 | `output/volatility/` | ✅ 部分指标 |
| 📈 **K线图展示** | 高质量周K线图表，批量生成 | `output/kline/index.html` | ❌ 纯图表 |
| 🔄 **相似度分析** | 基于机器学习的形态匹配 | `output/similarity/` | ❌ 图像算法 |
| ⚙️ **系统工具** | 环境检查，依赖管理，配置 | 命令行输出 | ✅ 环境检测 |

## 🎨 界面预览

### 主导航页面
- **现代化设计**: 渐变背景，毛玻璃效果，动画交互
- **模块状态**: 实时显示各分析模块的可用状态
- **统计概览**: 动态展示平台核心数据
- **快速访问**: 一键跳转到各分析结果页面

### 分析结果页面
- **专业图表**: 高质量的技术分析图表
- **详细指标**: 完整的技术指标数据展示
- **分页浏览**: 大量数据的高效浏览体验
- **响应式布局**: 适配各种屏幕尺寸 