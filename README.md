### 📈 A股技术分析平台（数据库版）

面向实盘的多模块技术分析工具集。已统一为“仅数据库数据源”，移除 CSV 依赖；输出目录标准化到 `output/`。

### 🚀 快速开始
- 克隆并进入工程
  - git clone <repo> && cd week
- 一键运行（推荐使用内置脚本）
  - ./run_in_stock_env.sh arc --max 50

### 🧰 环境要求与安装
- Python 3.13（建议使用 conda 虚拟环境 `stock-env`）
- 可选：TA-Lib（部分形态分析会自动启用增强路径）

安装步骤（macOS 示例）
```bash
conda create -n stock-env python=3.13 -y
conda activate stock-env
pip install -r requirements.txt
# 可选（若需 TA-Lib 增强）
brew install ta-lib && pip install TA-Lib
```
说明：运行脚本默认使用 `CONDA_ENV_PATH=/Users/kangfei/miniconda3/envs/stock-env`，如环境路径不同，请编辑 `run_in_stock_env.sh` 顶部变量。

### 🗄️ 数据源与配置
- 唯一数据源：MySQL（实时）
  - 配置文件：`config/settings.py` 中的 `DATABASE_CONFIG`
  - 样例建表：`db.sql`
- 输出目录（统一）：`output/` 下分模块子目录（如 `output/arc`、`output/pivot` 等）
- 缓存：`cache/` 下按“选择集”分桶缓存，自动管理

### 📦 可用模块与命令
```bash
# 大弧底（全量扫描，生成 ARC TOP 列表）
./run_in_stock_env.sh arc --max 200

# 高低点（仅保留 ZigZag+ATR 方法；默认使用 ARC TOP≤200 小集合缓存）
./run_in_stock_env.sh pivot --max 200

# 上升通道（默认使用 ARC TOP≤200）
./run_in_stock_env.sh uptrend --max 200

# 波动率分析（可指定股票或数量）
./run_in_stock_env.sh volatility --max 200

# 批量周K线图库
./run_in_stock_env.sh kline --max 200
```

### ⚙️ 重要参数
- --max N：限制处理股票数量（调试/抽样）
- --clear-cache：清理缓存后重建
- --output PATH：指定输出目录（默认 `output/<module>`）
- pivot 专属：
  - --method zigzag_atr（唯一保留方法）
  - --sensitivity conservative|balanced|aggressive（密度/延迟权衡，推荐 balanced）

### 🔍 工作流建议
1) 先运行大弧底模块生成 `output/arc/top_100.json`
2) 再运行 pivot/uptrend，两者默认只加载 ARC 列表（≤200 只），显著加速并使用独立小缓存
3) 打开报告：
   - output/index.html（主导航）
   - output/arc/index.html
   - output/pivot/index.html
   - output/uptrend/uptrend_analysis.html

### 🧠 高低点识别（ZigZag+ATR）
- 思路：自适应阈值 = max(基础摆动%, ATR%×系数)，时间顺序构建 ZigZag，最小K线间隔与“同向更极端替换”降噪
- 适配交易用途：阈值更宽松、延迟更低；HTML 报告中预览每个枢轴的 prominence/confirm/Z-score 入选依据
- 调参建议：
  - 进出场参考：balanced
  - 信号更少更稳：conservative
  - 信号更密：aggressive

### 🧠 缓存策略（关键优化）
- 全量缓存：用于 ARC 全市场扫描
- 小集合缓存：当仅处理 ARC TOP 列表（≤200）时，按选择集生成带 md5 后缀的独立缓存文件，互不污染
- 常用操作：
```bash
# 清空所有缓存
rm -rf cache
# 或仅在运行时指定
./run_in_stock_env.sh pivot --clear-cache
```

### 🐛 故障排除
- 代码修改未生效：确保使用脚本运行同一环境；必要时清理字节码缓存
```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```
- 只加载到少量股票：多为缓存命中“ARC 小集合缓存”；如需全量请运行 ARC 或清理缓存
- 数据库连接失败：检查 `config/settings.py` 数据库配置与网络可达性

### 📁 目录概要
```
week/
├── run_in_stock_env.sh          # 统一运行入口（使用 conda 环境）
├── main_arc.py                  # 大弧底
├── main_pivot.py                # 高低点（ZigZag+ATR）
├── main_uptrend.py              # 上升通道
├── main_volatility.py           # 波动率
├── main_kline.py                # 周K线图库
├── config/                      # 全局/数据库/输出配置
├── src/                         # 源码（core/analyzers/generators/...）
├── cache/                       # 本地缓存（自动管理）
└── output/                      # 结果输出（标准化子目录）
```

### 📝 变更要点（当前版本）
- 仅保留数据库数据源，彻底移除 CSV 入口
- 高低点仅保留 `zigzag_atr` 方法；HTML 展示每个枢轴入选依据
- 统一输出目录至 `output/`；按选择集分桶缓存，提升速度与一致性

如需扩展或接入新方法，请参考各类顶部的类注释（用途/实现/优缺点/维护建议）。