# A股周K线图分析与形态识别系统

## 项目简介

本项目是一个专业的A股技术分析工具，支持三大核心功能：

1. **批量生成所有股票的周K线图** - 生成高质量的技术分析图表
2. **批量检测圆弧底形态** - 识别"严重下降→横盘→轻微上涨"的圆弧底形态
3. **K线图像相似度分析** - 基于图像哈希算法查找相似走势的股票

## 功能特点

- 🚀 **高性能**：多进程并行处理，支持5000+股票批量分析
- 📊 **智能检测**：基于数学模型的圆弧底形态识别算法
- 🔍 **图像相似度**：使用感知哈希算法进行K线图相似度分析
- 📱 **可视化报告**：生成美观的HTML报告，支持分页浏览
- 💾 **缓存优化**：智能缓存机制，避免重复计算
- 🎯 **精确分析**：支持R²拟合度、质量评分等多维度分析

---

## 环境要求

- **Python版本**：3.7+
- **操作系统**：Windows/macOS/Linux
- **推荐环境**：conda环境管理
- **内存要求**：建议8GB+（处理5000+股票时）

## 安装步骤

### 1. 克隆项目
```bash
git clone <repository-url>
cd week
```

### 2. 创建conda环境
```bash
conda create -n stock-env python=3.8
conda activate stock-env
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 准备数据文件
将您的股票数据CSV文件放在指定位置（默认：`/Users/kangfei/Downloads/result.csv`）

---

## 目录结构

```
stock-curve/
├── src/                          # 核心源代码
│   ├── core/                     # 数据处理核心模块
│   │   └── stock_data_processor.py
│   ├── analyzers/                # 形态分析模块
│   │   └── pattern_analyzer.py
│   ├── generators/               # 图表生成模块
│   │   ├── chart_generator.py
│   │   ├── arc_chart_generator.py
│   │   └── html_generator.py
│   ├── similarity/               # 图像相似度分析
│   │   └── image_similarity.py
│   └── utils/                    # 工具模块
│       └── html_generator.py
├── main_kline.py                 # K线图生成入口
├── main_arc.py                   # 圆弧底分析入口
├── main_similarity.py            # 相似度分析入口
├── config/                       # 配置文件
├── tests/                        # 测试文件
├── output/                       # K线图输出目录
├── arc_output/                   # 圆弧底分析输出目录
├── cache/                        # 数据缓存目录
└── README.md
```

---

## 使用指南

### 1. 批量生成周K线图

**基本用法：**
```bash
python main_kline.py
```

**高级选项：**
```bash
# 指定CSV文件路径
python main_kline.py --csv /path/to/your/data.csv

# 限制生成数量（调试用）
python main_kline.py --max 100

# 指定输出目录
python main_kline.py --output my_output
```

**输出结果：**
- `output/kline_images/` - 所有股票的K线图PNG文件
- `output/index.html` - 可浏览的静态网页（支持分页）

### 2. 圆弧底形态检测

**基本用法：**
```bash
python main_arc.py
```

**高级选项：**
```bash
# 限制分析数量
python main_arc.py --max 1000

# 指定输出目录
python main_arc.py --output output/arc
```

**检测算法特点：**
- 识别"严重下降→横盘→轻微上涨"的圆弧底形态
- 支持R²拟合度评估（默认阈值0.7）
- 质量评分系统（0-100分）
- 自动识别三个阶段：下降、横盘、上涨

**输出结果：**
- `output/arc/images/` - 检测到圆弧底的股票图表
- `output/arc/arc_analysis.html` - 详细分析报告

### 3. K线图像相似度分析

**基本用法：**
```bash
python main_similarity.py --target 603127.SH
```

**高级选项：**
```bash
# 指定返回数量
python main_similarity.py --target 603127.SH --top 20

# 强制重新生成图片
python main_similarity.py --target 603127.SH --force-regenerate

# 指定图片目录
python main_similarity.py --target 603127.SH --imgdir output/kline_images
```

**性能优化：**
- 自动检测现有图片，避免重复生成
- 首次运行需要生成图片，后续运行速度显著提升
- 使用`--force-regenerate`可强制重新生成

**输出结果：**
- 控制台显示相似股票列表
- `output/similarity/` - HTML分析报告（包含图片对比）

---

## 使用流程建议

### 首次使用
```bash
# 1. 生成所有K线图
python main_kline.py

# 2. 检测圆弧底形态
python main_arc.py

# 3. 分析特定股票相似度
python main_similarity.py --target 000001.SZ
```

### 日常使用
```bash
# 直接进行相似度分析（使用现有图片）
python main_similarity.py --target 股票代码

# 更新圆弧底分析
python main_arc.py
```

---

## 配置说明

### 数据文件格式
CSV文件应包含以下列：
- `code`: 股票代码
- `date`: 日期
- `open`: 开盘价
- `high`: 最高价
- `low`: 最低价
- `close`: 收盘价
- `volume`: 成交量

### 算法参数调整
在 `config/settings.py` 中可以调整：
- 圆弧底检测的R²阈值
- 图像相似度阈值
- 多进程配置
- 输出目录设置

---

## 测试

### 运行基本测试
```bash
python -m pytest tests/test_basic.py
```

### 运行圆弧底算法测试
```bash
python test_arc_improved.py
```

### 功能验证
```bash
# 测试小规模数据
python main_kline.py --max 10
python main_arc.py --max 10
python main_similarity.py --target 603127.SH --top 3
```

---

## 常见问题与解决方案

### 1. 依赖安装问题
**问题**：`ModuleNotFoundError: No module named 'pandas'`
**解决**：
```bash
conda activate stock-env
pip install -r requirements.txt
```

### 2. OpenCV安装问题（macOS）
**问题**：OpenCV安装失败
**解决**：
```bash
pip install opencv-python==4.5.5.64
```

### 3. 内存不足
**问题**：处理大量股票时内存不足
**解决**：
```bash
# 分批处理
python main_kline.py --max 1000
```

### 4. 图片生成失败
**问题**：图片或HTML未生成
**解决**：
- 检查CSV文件路径是否正确
- 确认输出目录有写入权限
- 检查磁盘空间是否充足

### 5. 相似度分析慢
**问题**：首次运行相似度分析很慢
**解决**：
- 首次运行需要生成图片，后续运行会使用缓存
- 使用`--force-regenerate`可强制重新生成

### 6. 圆弧底检测率低
**问题**：检测到的圆弧底形态很少
**解决**：
- 圆弧底是相对罕见的形态，检测率低是正常的
- 可以调整`config/settings.py`中的参数
- 使用`test_arc_improved.py`测试不同参数

---

## 性能指标

### 处理速度
- **K线图生成**：约30-35图表/秒（8进程并行）
- **圆弧底分析**：约100-200股票/秒
- **相似度分析**：约1000图片/秒（首次运行需要生成图片）

### 资源消耗
- **内存使用**：约2-4GB（处理5000+股票）
- **磁盘空间**：约500MB（图片+HTML文件）
- **CPU使用**：8核心并行处理

---

## 技术架构

### 核心算法
- **圆弧底检测**：基于二次函数拟合的形态识别
- **图像相似度**：感知哈希（pHash）算法
- **数据处理**：pandas + numpy高效数据处理
- **图表生成**：PIL图像处理库

### 设计模式
- **模块化设计**：功能分离，易于维护
- **缓存机制**：避免重复计算
- **多进程处理**：提高处理效率
- **配置驱动**：参数可配置

---

## 更新日志

### v1.0.0 (2024-07-17)
- ✅ 完成三大核心功能开发
- ✅ 优化性能，解决重复生成问题
- ✅ 清理冗余代码，优化项目结构
- ✅ 完善文档和使用说明

---

## 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境设置
```bash
git clone <repository-url>
cd stock-curve
conda create -n stock-dev python=3.8
conda activate stock-dev
pip install -r requirements.txt
pip install pytest black flake8
```

### 代码规范
- 使用Python 3.7+语法
- 遵循PEP 8代码风格
- 添加适当的注释和文档字符串
- 编写单元测试

---

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

---

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至：[your-email@example.com]

---

## 致谢

感谢以下开源项目的支持：
- pandas - 数据处理
- numpy - 数值计算
- scipy - 科学计算
- PIL - 图像处理
- matplotlib - 图表生成 