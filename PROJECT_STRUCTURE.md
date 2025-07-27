# 项目结构说明

## 清理后的项目架构

```
week/                                    # 项目根目录
├── README.md                           # 主要项目文档
├── PROJECT_STRUCTURE.md                # 项目结构说明
├── run_analysis.py                     # 统一启动脚本 ⭐
├── .gitignore                          # Git忽略规则
├── requirements.txt                    # Python依赖
├── setup.py                           # 安装配置
├── install_dependencies.py            # 依赖安装脚本
│
├── main_*.py                          # 主程序入口
│   ├── main_arc.py                    # 大弧底分析
│   ├── main_uptrend.py                # 上升通道分析 ⭐
│   ├── main_kline.py                  # K线图生成
│   ├── main_volatility.py             # 波动率分析
│   └── main_similarity.py             # 相似度分析
│
├── config/                            # 配置文件
│   └── settings.py                    # 系统设置
│
├── cache/                             # 数据缓存
│   ├── cache_info.txt                 # 缓存信息
│   └── weekly_data.pkl                # 周K数据缓存
│
├── src/                               # 核心源代码
│   ├── __init__.py
│   ├── core/                          # 核心模块
│   │   ├── __init__.py
│   │   └── stock_data_processor.py    # 股票数据处理器
│   ├── analyzers/                     # 分析器模块
│   │   ├── __init__.py
│   │   ├── pattern_analyzer.py        # 形态分析器 (TA-Lib增强)
│   │   ├── uptrend_channel_analyzer.py # 上升通道分析器 ⭐
│   │   └── volatility_analyzer.py     # 波动率分析器
│   ├── generators/                    # 生成器模块
│   │   ├── __init__.py
│   │   ├── base_chart_generator.py    # 基础图表生成器
│   │   ├── chart_generator.py         # K线图生成器
│   │   ├── arc_chart_generator.py     # 大弧底图表生成器
│   │   ├── uptrend_chart_generator.py # 上升通道图表生成器 ⭐
│   │   ├── html_generator.py          # HTML生成器
│   │   ├── arc_html_generator.py      # 大弧底HTML生成器
│   │   ├── uptrend_html_generator.py  # 上升通道HTML生成器 ⭐
│   │   └── volatility_html_generator.py # 波动率HTML生成器
│   └── similarity/                    # 相似度分析
│       └── image_similarity.py        # 图像相似度算法
│
├── output/                            # 分析结果输出 (由程序生成)
│   ├── index.html                     # 主导航页面 ⭐
│   ├── kline/                         # K线图模块
│   │   └── index.html                 # K线图展示页面
│   ├── kline_images/                  # K线图片文件
│   │   └── *.png                      # 各股票K线图
│   ├── arc/                           # 大弧底分析模块
│   │   ├── arc_analysis.html          # 大弧底分析页面
│   │   └── images/                    # 大弧底图片
│   │       └── major_arc_*.png        # 大弧底图表
│   ├── uptrend/                       # 上升通道分析模块 ⭐
│   │   ├── uptrend_analysis.html      # 上升通道分析页面
│   │   └── images/                    # 上升通道图片
│   │       └── uptrend_*.png          # 上升通道图表
│   ├── volatility/                    # 波动率分析模块
│   │   ├── volatility_analysis_*.html # 波动率分析页面
│   │   └── images/                    # 波动率图片
│   │       └── volatility_*.png       # 波动率图表
│   └── similarity/                    # 相似度分析模块
│       ├── similarity_*.html          # 相似度分析页面
│       └── *.png                      # 相似度对比图
```

## 核心功能模块

### 1. 统一管理系统
- **output/index.html**: 美观的导航页面，实时检测模块状态
- **run_analysis.py**: 一键启动脚本，支持单独或全部运行

### 2. 技术分析模块
- **K线图生成**: 高质量周K线图批量生成
- **大弧底检测**: TA-Lib增强的专业形态识别
- **上升通道分析**: 通道识别和入场信号检测 ⭐
- **波动率分析**: 4种算法的风险评估
- **相似度分析**: 机器学习驱动的模式匹配

### 3. 数据处理层
- **数据缓存**: 智能缓存机制，提升处理速度
- **多进程处理**: 并行计算，提高分析效率
- **内存优化**: 大数据集的高效处理

## 清理内容总结

### 删除的文件/目录：
- ✅ `test_entry_signal.py` - 临时测试文件
- ✅ `QUICK_START.md` - 功能已整合到README.md
- ✅ `README_VOLATILITY.md` - 功能已整合到README.md
- ✅ `TALIB_VS_BASIC_ANALYSIS.md` - 功能已整合到README.md
- ✅ `README_TALIB_ENHANCEMENT.md` - 功能已整合到README.md
- ✅ 所有 `__pycache__/` 目录
- ✅ 所有 `.DS_Store` 文件

### 保留的核心文件：
- ✅ `README.md` - 主要项目文档（已整合所有功能说明）
- ✅ `PROJECT_STRUCTURE.md` - 项目结构说明
- ✅ `run_analysis.py` - 统一启动脚本
- ✅ `main_*.py` - 所有主程序入口
- ✅ `src/` - 完整源代码结构
- ✅ `config/` - 配置文件
- ✅ `cache/` - 数据缓存
- ✅ `output/` - 分析结果输出

## 新增功能模块

### 上升通道分析 (v2.0.0)
- **analyzer**: `src/analyzers/uptrend_channel_analyzer.py`
  - 关键点自动识别
  - 通道质量评估
  - 入场信号检测
  - TA-Lib技术指标集成

- **generator**: `src/generators/uptrend_chart_generator.py`
  - 通道边界绘制
  - 透明区域填充
  - 关键点标注
  - 入场信号显示

- **html**: `src/generators/uptrend_html_generator.py`
  - 响应式HTML报告
  - 动态数据展示
  - 交互式图表

- **main**: `main_uptrend.py`
  - 统一入口程序
  - 参数解析
  - 批量处理

## 技术栈

### 核心依赖
- **Python 3.8+**: 主要开发语言
- **TA-Lib**: 专业技术指标库
- **Pandas**: 数据处理
- **NumPy**: 数值计算
- **Matplotlib**: 图表生成
- **Pillow**: 图像处理
- **Scikit-learn**: 机器学习算法

### 开发工具
- **Conda**: 环境管理 (`stock-env`)
- **Git**: 版本控制
- **多进程**: 并行计算优化

## 使用流程

1. **环境准备**: 激活 `stock-env` 环境
2. **一键启动**: `python run_analysis.py all --open-browser`
3. **查看结果**: 浏览器自动打开 `output/index.html`
4. **模块选择**: 点击相应模块卡片查看详细分析
5. **数据更新**: 重新运行对应分析模块 