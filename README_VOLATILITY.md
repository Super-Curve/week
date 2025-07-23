# 股票波动率和波幅分析工具

这是一个基于周K线数据的股票波动率和波幅分析工具，可以帮助投资者分析股票的风险特征。

## 🆕 最新更新

- ✅ **下拉框多选股票**: 支持在HTML界面中多选股票进行分析
- ✅ **默认展示前10只股票**: 自动选择前10只股票进行默认分析
- ✅ **快速选择按钮**: 提供全选、清空、选择前10等快捷操作
- ✅ **实时选择计数**: 显示当前选中的股票数量
- ✅ **动态数据切换**: 选择股票后实时更新统计数据和图表显示
- ✅ **自定义下拉组件**: 美观的下拉多选界面，支持标签式显示
- ✅ **图表显示修复**: 修复了波动率图表无法显示的问题
- ✅ **波动率计算方式说明**: 在页面顶部添加了四种波动率计算方式的详细说明
- ✅ **横坐标优化**: 优化了图表横坐标显示，避免时间标签重叠
- ✅ **公式卡片布局**: 美观的公式展示卡片，包含计算方式和解释
- ✅ **图表内公式说明**: 在每个波动率图表的右下角添加了计算方式说明

## 功能特点

### 📊 波动率分析
- **历史波动率**: 基于收盘价计算的标准差波动率
- **已实现波动率**: 基于收益率平方和的波动率
- **Parkinson波动率**: 基于高低价的波动率估计
- **Garman-Klass波动率**: 综合开盘、收盘、最高、最低价的波动率

### 📈 波幅分析
- **日内波幅**: 单日最高价与最低价的相对变化
- **期间波幅**: 指定期间内价格区间的相对变化

### 🎯 风险评估
- 自动计算风险等级（低风险、中等风险、中高风险、高风险）
- 基于波动率和波幅的百分位排名
- 可视化风险指标展示

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
# 分析前10只股票的波动率和波幅（默认）
python3 main_volatility.py

# 分析指定数量的股票
python3 main_volatility.py --max 20

# 分析指定的股票
python3 main_volatility.py --stocks "000001.SZ,000002.SZ,000004.SZ"

# 指定时间范围
python3 main_volatility.py --start-date "2023-01-01" --end-date "2024-01-01"
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--csv` | CSV数据文件路径 | `/Users/kangfei/Downloads/result.csv` |
| `--output` | 输出目录 | `output/volatility` |
| `--stocks` | 要分析的股票代码，用逗号分隔 | 前50只股票 |
| `--start-date` | 开始日期 (YYYY-MM-DD) | 2年前 |
| `--end-date` | 结束日期 (YYYY-MM-DD) | 今天 |
| `--max` | 最多分析多少只股票 | 10 |

## 输出结果

### 📁 文件结构
```
output/volatility/
├── volatility_analysis_YYYYMMDD_HHMMSS.html  # 主HTML报告
└── images/
    ├── volatility_000001.SZ.png              # 股票波动率图表
    ├── volatility_000002.SZ.png
    └── ...
```

### 📊 HTML报告内容
1. **控制面板**: 
   - 多选股票下拉框（支持Ctrl/Cmd多选）
   - 快速选择按钮（全选、清空、选择前10）
   - 实时选择计数显示
   - 时间范围选择器
2. **统计摘要**: 平均波动率、平均波幅、风险分布
3. **图表展示**: 每只股票的详细波动率分析图表
4. **风险指标**: 颜色编码的风险等级标识

### 📈 图表内容
每个股票的波动率分析图表包含：
- 价格走势图
- 历史波动率（20周期和60周期）
- 不同波动率指标对比
- 日内波幅
- 期间波幅
- 统计信息摘要

## 波动率指标说明

### 1. 历史波动率 (Historical Volatility)
```python
# 计算公式
returns = log(price_t / price_{t-1})
volatility = std(returns) * sqrt(52)  # 年化
```

### 2. 已实现波动率 (Realized Volatility)
```python
# 计算公式
realized_vol = sqrt(sum(returns^2) / n) * sqrt(52)
```

### 3. Parkinson波动率
```python
# 计算公式
log_hl = log(high / low)
parkinson_vol = sqrt(sum(log_hl^2) / (4 * log(2) * n)) * sqrt(52)
```

### 4. Garman-Klass波动率
```python
# 计算公式
log_hl = log(high / low)
log_co = log(close / open)
gk_vol = sqrt(sum(0.5 * log_hl^2 - (2*log(2)-1) * log_co^2) / n) * sqrt(52)
```

## 波幅指标说明

### 1. 日内波幅 (Intraday Amplitude)
```python
# 计算公式
amplitude = (high - low) / close * 100%
```

### 2. 期间波幅 (Period Amplitude)
```python
# 计算公式
amplitude = (period_max - period_min) / period_mean * 100%
```

## 风险等级评估

| 风险等级 | 波动率百分位 | 波幅百分位 | 说明 |
|----------|-------------|------------|------|
| 低风险 | < 20% | < 20% | 波动较小，适合保守投资者 |
| 中等风险 | 20-60% | 20-60% | 正常波动范围 |
| 中高风险 | > 60% | > 60% | 波动较大，需要谨慎 |
| 高风险 | > 80% | > 80% | 波动剧烈，风险很高 |

## 使用示例

### 示例1: 分析特定股票
```bash
python3 main_volatility.py --stocks "000001.SZ,000002.SZ" --start-date "2023-01-01"
```

### 示例2: 批量分析
```bash
python3 main_volatility.py --max 50 --output "output/my_analysis"
```

### 示例3: 自定义时间范围
```bash
python3 main_volatility.py --start-date "2022-01-01" --end-date "2023-12-31"
```

## 🌐 HTML界面使用指南

### 股票选择功能
1. **下拉多选**: 点击下拉框选择股票，支持多选
2. **标签显示**: 选中的股票以标签形式显示，可单独删除
3. **快速选择**: 
   - 点击"全选"按钮选择所有股票
   - 点击"清空"按钮取消所有选择
   - 点击"选择前10"按钮选择前10只股票
4. **实时计数**: 界面会实时显示当前选中的股票数量
5. **动态更新**: 选择变化时自动更新统计数据和图表显示

### 时间范围设置
- 使用日期选择器设置分析的时间范围
- 支持精确到天的日期选择

### 重新分析
- 修改股票选择后，数据会自动更新显示
- 修改时间范围后，点击"重新分析"按钮重新生成报告
- 支持实时预览不同股票组合的分析结果

### 数据导出
- 点击"导出数据"按钮可以下载分析摘要
- 导出的JSON文件包含生成时间和分析统计

## 技术实现

### 核心类
- `VolatilityAnalyzer`: 波动率分析器
- `VolatilityHTMLGenerator`: HTML报告生成器

### 主要方法
- `calculate_historical_volatility()`: 计算历史波动率
- `calculate_intraday_amplitude()`: 计算日内波幅
- `analyze_stock_volatility()`: 综合分析股票波动率
- `generate_volatility_chart()`: 生成波动率图表

## 注意事项

1. **数据要求**: 需要包含OHLC（开盘、最高、最低、收盘）数据的CSV文件
2. **时间格式**: 日期格式为YYYY-MM-DD
3. **计算窗口**: 默认使用20个周期作为计算窗口
4. **字体支持**: 确保系统支持中文字体显示

## 扩展功能

### 自定义波动率计算
```python
from src.analyzers.volatility_analyzer import VolatilityAnalyzer

analyzer = VolatilityAnalyzer()
# 自定义计算窗口
volatility = analyzer.calculate_historical_volatility(prices, window=30)
```

### 添加新的波动率指标
```python
def calculate_custom_volatility(self, prices, window=20):
    # 实现自定义波动率计算逻辑
    pass
```

## 故障排除

### 常见问题

1. **中文字体显示问题**
   - 确保系统安装了中文字体
   - 修改matplotlib字体配置

2. **数据文件不存在**
   - 检查CSV文件路径是否正确
   - 确保文件格式正确

3. **内存不足**
   - 减少分析的股票数量
   - 缩短时间范围

## 更新日志

- v1.0.0: 初始版本，支持基本的波动率和波幅分析
- 支持多种波动率指标计算
- 提供交互式HTML报告
- 自动风险等级评估 