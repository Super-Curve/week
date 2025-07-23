# 🚀 波动率分析工具快速启动指南

## 📋 环境要求

- Python 3.7+
- 数据文件: `/Users/kangfei/Downloads/result.csv`

## ⚡ 快速开始

### 1. 安装依赖

```bash
# 自动安装所有依赖
python3 install_dependencies.py

# 或者手动安装
python3 -m pip install pandas numpy matplotlib scipy scikit-learn Pillow opencv-python imagehash tqdm
```

### 2. 运行波动率分析

```bash
# 基本用法 - 分析前10只股票
python3 main_volatility.py

# 分析指定数量的股票
python3 main_volatility.py --max 5

# 分析指定的股票
python3 main_volatility.py --stocks "000001.SZ,000002.SZ,000004.SZ"

# 指定时间范围
python3 main_volatility.py --start-date "2023-01-01" --end-date "2024-12-31"
```

### 3. 运行增强版测试

```bash
# 测试所有新功能
python3 test_volatility_enhanced.py
```

## 🎯 功能特点

### ✅ 新增功能
- **📚 波动率计算方式说明**: 页面顶部详细的计算公式和解释
- **📊 横坐标优化**: 避免时间标签重叠，清晰显示
- **🎨 公式卡片布局**: 美观的响应式公式展示
- **📈 图表内公式说明**: 每个图表右下角的计算方式说明
- **⚡ 下拉多选**: 支持多股票选择和动态数据切换

### 📊 波动率指标
1. **历史波动率**: `σ = std(ln(Pt/Pt-1)) × √52`
2. **已实现波动率**: `σ = √(Σ(rt²)/n) × √52`
3. **Parkinson波动率**: `σ = √(Σ(ln(Ht/Lt)²)/(4×ln(2)×n)) × √52`
4. **Garman-Klass波动率**: `σ = √(Σ(0.5×ln(Ht/Lt)²-(2×ln(2)-1)×ln(Ct/Ot)²)/n) × √52`

## 📁 输出文件

```
output/volatility/
├── volatility_analysis_YYYYMMDD_HHMMSS.html  # 主HTML报告
└── images/
    ├── volatility_000001.SZ.png              # 股票波动率图表
    ├── volatility_000002.SZ.png
    └── ...
```

## 🎮 使用说明

### HTML界面操作
1. **股票选择**: 点击下拉框选择要分析的股票
2. **快速选择**: 使用"全选"、"清空"、"选择前10"按钮
3. **动态切换**: 选择股票后数据自动更新
4. **时间范围**: 设置分析的时间范围
5. **查看图表**: 每个股票都有详细的波动率分析图表

### 图表内容
- **价格走势**: 股票价格变化趋势
- **历史波动率**: 20周期和60周期的波动率对比
- **波动率指标对比**: 四种不同波动率指标的比较
- **日内波幅**: 单日价格波动幅度
- **期间波幅**: 指定期间的价格波动幅度
- **统计信息**: 当前值、平均值、百分位等

## 🔧 故障排除

### 常见问题

1. **ModuleNotFoundError: No module named 'matplotlib'**
   ```bash
   python3 -m pip install matplotlib
   ```

2. **数据文件不存在**
   - 确保 `/Users/kangfei/Downloads/result.csv` 文件存在
   - 或者使用 `--csv` 参数指定数据文件路径

3. **字体警告**
   - 这是正常的，不影响功能
   - 警告是因为系统缺少某些emoji字体

4. **内存不足**
   - 减少分析的股票数量: `--max 5`
   - 缩短时间范围

### 验证安装

```bash
# 运行依赖检查
python3 install_dependencies.py

# 运行基本测试
python3 main_volatility.py --max 2

# 运行完整测试
python3 test_volatility_enhanced.py
```

## 📖 更多信息

- 详细文档: [README_VOLATILITY.md](README_VOLATILITY.md)
- 项目主页: [README.md](README.md)

## 🎉 开始使用

现在您可以开始使用增强版波动率分析工具了！

```bash
# 快速体验
python3 main_volatility.py --max 3

# 打开生成的HTML文件查看结果
open output/volatility/volatility_analysis_*.html
```

享受专业的股票波动率分析体验！ 📈✨ 