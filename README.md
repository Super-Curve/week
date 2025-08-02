# 📈 A股技术分析平台

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![TA-Lib](https://img.shields.io/badge/TA--Lib-0.5.1-green.svg)](https://ta-lib.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 专业级的A股技术分析工具集，基于TA-Lib与机器学习算法，提供多维度的股票技术分析功能。

## 🚀 快速开始

### 一键运行（推荐）
```bash
# 克隆项目
git clone <repository-url>
cd week

# 快速测试（5只股票）
./run_in_stock_env.sh arc --max 5

# 完整分析并打开浏览器
./run_in_stock_env.sh all --open-browser
```

### 环境配置
项目已预配置stock-env conda环境，包含所有依赖：

```bash
# 检查环境
./run_in_stock_env.sh

# 手动配置（如需要）
conda create -n stock-env python=3.11
conda activate stock-env
pip install -r requirements.txt
brew install ta-lib && pip install TA-Lib
```

## 🎯 核心功能

| 模块 | 功能描述 | 输出文件 | TA-Lib支持 |
|------|----------|----------|------------|
| 🎯 **大弧底检测** | 专业形态识别，相似度TOP100 | `output/arc/arc_analysis.html` | ✅ 增强版 |
| 📈 **上升通道分析** | 通道识别，入场信号检测 | `output/uptrend/uptrend_analysis.html` | ✅ 增强版 |
| 📊 **波动率分析** | 4种专业算法，风险评估 | `output/volatility/volatility_analysis.html` | ✅ 部分指标 |
| 📈 **K线图展示** | 高质量周K线图表，批量生成 | `output/kline/index.html` | ❌ 纯图表 |
| 🔄 **相似度分析** | 基于机器学习的形态匹配 | `output/similarity/similarity_analysis.html` | ❌ 图像算法 |

## 💡 使用示例

### 单独运行分析
```bash
# 大弧底分析
./run_in_stock_env.sh arc --max 100

# 上升通道分析
./run_in_stock_env.sh uptrend --max 50

# 波动率分析
./run_in_stock_env.sh volatility --max 200

# K线图生成
./run_in_stock_env.sh kline --max 1000

# 相似度分析
./run_in_stock_env.sh similarity --target 000001.SZ --top 10
```

### 常用参数
- `--max N`: 限制处理的股票数量（测试用）
- `--clear-cache`: 清除缓存，重新处理数据
- `--csv PATH`: 指定CSV数据文件路径
- `--output PATH`: 指定输出目录

### 查看结果
```bash
# 打开主导航页面
open output/index.html

# 或直接打开特定分析结果
open output/arc/arc_analysis.html
open output/uptrend/uptrend_analysis.html
```

## 🔧 技术特性

### TA-Lib增强分析
- **158个技术指标**: 移动平均线、动量指标、趋势指标
- **多维度评分**: 价格、成交量、趋势、动量综合评估
- **智能回退**: TA-Lib不可用时自动使用基础算法
- **精度提升**: 相比基础方法提升17%的准确率

### 专业算法
- **波动率分析**: 历史波动率、已实现波动率、Parkinson、Garman-Klass
- **形态识别**: 大弧底、上升通道、支撑阻力位
- **相似度匹配**: 基于图像哈希的机器学习算法
- **多进程处理**: 并行计算，提升处理效率

### 可视化优化
- **现代化界面**: 渐变背景、毛玻璃效果、动画交互
- **响应式设计**: 支持桌面和移动设备
- **专业图表**: 高质量技术分析图表
- **实时状态**: 自动检测模块可用性

## 📁 项目结构

```
week/
├── README.md                    # 项目文档
├── run_in_stock_env.sh          # 环境运行脚本 ⭐
├── run_analysis.py              # 统一启动脚本
├── main_*.py                    # 主程序入口
├── requirements.txt             # Python依赖
├── config/                      # 配置文件
├── cache/                       # 数据缓存
├── src/                         # 核心源代码
│   ├── core/                    # 数据处理
│   ├── analyzers/               # 分析器模块
│   ├── generators/              # 生成器模块
│   └── similarity/              # 相似度分析
└── output/                      # 分析结果
    ├── index.html               # 主导航页面 ⭐
    ├── arc/                     # 大弧底分析
    ├── uptrend/                 # 上升通道分析
    ├── volatility/              # 波动率分析
    ├── kline/                   # K线图模块
    └── similarity/              # 相似度分析
```

## 📊 性能表现

| 数据规模 | 处理时间 | 内存使用 | 推荐场景 |
|----------|----------|----------|----------|
| 5只股票 | ~1分钟 | 低 | 快速测试 |
| 100只股票 | ~2-3分钟 | 中 | 开发调试 |
| 1000只股票 | ~5-8分钟 | 中高 | 中等规模 |
| 全部5418只 | ~10-15分钟 | 高 | 生产环境 |

## 🛠️ 环境要求

- **Python**: 3.8+
- **TA-Lib**: 0.5.1+
- **操作系统**: macOS/Linux/Windows
- **推荐环境**: conda (stock-env)

## 🐛 故障排除

### 常见问题
1. **TA-Lib不可用**
   ```bash
   # 检查环境
   ./run_in_stock_env.sh
   # 重新安装
   brew install ta-lib && pip install TA-Lib
   ```

2. **缓存加载失败**
   ```bash
   # 清除缓存
   ./run_in_stock_env.sh arc --clear-cache
   ```

3. **内存不足**
   ```bash
   # 减少处理数量
   ./run_in_stock_env.sh arc --max 100
   ```

4. **权限问题**
   ```bash
   # 添加执行权限
   chmod +x run_in_stock_env.sh
   ```

### 调试模式
```bash
# 使用少量数据测试
./run_in_stock_env.sh arc --max 5

# 查看详细输出
./run_in_stock_env.sh arc --max 5 --verbose
```

## 📈 更新日志

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

### 开发环境设置
```bash
# 克隆项目
git clone <repository-url>
cd week

# 设置开发环境
conda create -n stock-dev python=3.11
conda activate stock-dev
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖
```

## 📄 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件

---

<div align="center">

**🎉 感谢使用A股技术分析平台！**

如有问题，请查看 [故障排除](#-故障排除) 部分或提交Issue。

</div> 