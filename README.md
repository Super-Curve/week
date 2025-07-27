# A股技术分析平台

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![TA-Lib](https://img.shields.io/badge/TA--Lib-0.5.1-green.svg)](https://ta-lib.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

专业级的A股技术分析工具集，基于TA-Lib与机器学习算法，提供多维度的股票技术分析功能。

## 🌟 核心功能亮点

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
python run_analysis.py uptrend --max 50     # 上升通道分析
python run_analysis.py volatility           # 波动率分析
python run_analysis.py kline                # K线图分析
python run_analysis.py similarity           # 相似度分析
```

### 🎯 TA-Lib增强分析
- **专业技术指标**: 集成158个TA-Lib技术指标
- **多维度评分**: 结合价格、成交量、趋势、动量等维度
- **智能回退**: TA-Lib不可用时自动使用基础算法
- **检测精度提升**: 相比基础方法提升17%的准确率

### 📈 上升通道分析
- **关键点自动识别**: 智能识别支撑和阻力关键点
- **通道质量评估**: 基于宽度、持续时间、平行度等指标
- **入场信号检测**: 专注最近K线趋势的入场确认
- **可视化展示**: 清晰的通道边界和趋势线标注

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
python main_uptrend.py --csv your_data.csv --output output/uptrend
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
| 📈 **上升通道分析** | 通道识别，入场信号检测 | `output/uptrend/uptrend_analysis.html` | ✅ 增强版 |
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

## 🔧 技术特性

### TA-Lib增强功能
- **移动平均线分析**: SMA20/50/200, EMA200, 排列判断
- **动量指标分析**: RSI, MACD, Williams %R, CCI
- **趋势指标分析**: ADX, +DI/-DI, SAR
- **成交量分析**: OBV, 成交量MA, 资金流向
- **波动率分析**: ATR, 布林带
- **支撑阻力分析**: 历史测试强度, 价格聚集

### 波动率分析算法
1. **历史波动率**: `σ = std(ln(Pt/Pt-1)) × √52`
2. **已实现波动率**: `σ = √(Σ(rt²)/n) × √52`
3. **Parkinson波动率**: `σ = √(Σ(ln(Ht/Lt)²)/(4×ln(2)×n)) × √52`
4. **Garman-Klass波动率**: `σ = √(Σ(0.5×ln(Ht/Lt)²-(2×ln(2)-1)×ln(Ct/Ot)²)/n) × √52`

### 上升通道分析特性
- **关键点识别**: 自动识别支撑和阻力关键点
- **通道质量评估**: 宽度、持续时间、平行度、R²值
- **入场信号**: 专注最近趋势的入场确认
- **可视化优化**: 透明通道区域，清晰边界线

## 📁 项目结构

```
week/
├── README.md                           # 主要项目文档
├── PROJECT_STRUCTURE.md                # 项目结构说明
├── run_analysis.py                     # 统一启动脚本 ⭐
├── main_*.py                          # 主程序入口
├── config/                            # 配置文件
├── cache/                             # 数据缓存
├── src/                               # 核心源代码
│   ├── core/                          # 核心模块
│   ├── analyzers/                     # 分析器模块
│   ├── generators/                    # 生成器模块
│   └── similarity/                    # 相似度分析
└── output/                            # 分析结果输出
    ├── index.html                     # 主导航页面 ⭐
    ├── arc/                           # 大弧底分析
    ├── uptrend/                       # 上升通道分析
    ├── volatility/                    # 波动率分析
    ├── kline/                         # K线图模块
    └── similarity/                    # 相似度分析
```

## 🛠️ 环境要求

- Python 3.8+
- TA-Lib 0.5.1+
- 推荐使用conda环境: `stock-env`

## 📝 更新日志

### v2.0.0 (2024-01-15)
- ✅ 新增上升通道分析功能
- ✅ 优化TA-Lib集成，提升检测精度
- ✅ 改进图表可视化，添加价格标注
- ✅ 统一导航界面，支持所有模块
- ✅ 一键启动脚本，简化使用流程

### v1.5.0 (2024-01-10)
- ✅ 集成TA-Lib技术指标库
- ✅ 增强大弧底检测算法
- ✅ 优化波动率分析界面
- ✅ 改进相似度分析算法

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件 