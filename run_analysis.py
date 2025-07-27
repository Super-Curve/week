#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A股技术分析平台 - 统一启动脚本
快速运行各种技术分析模块
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime

def print_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    📈 A股技术分析平台                          ║
    ║              Professional Stock Technical Analysis            ║
    ║                                                              ║
    ║  🎯 大弧底检测  📈 上升通道  📊 波动率分析  📈 K线图表  🔄 相似度分析  ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_environment():
    """检查运行环境"""
    print("🔍 检查运行环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        return False
    
    # 检查必要的模块
    required_modules = ['numpy', 'pandas', 'scipy', 'PIL']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"❌ 缺少模块: {', '.join(missing_modules)}")
        print("💡 请运行: pip install -r requirements.txt")
        return False
    
    # 检查TA-Lib
    try:
        import talib
        print("✅ TA-Lib 可用")
    except ImportError:
        print("⚠️  TA-Lib 不可用，将使用基础分析方法")
    
    print("✅ 环境检查完成")
    return True

def run_kline_analysis(args):
    """运行K线图分析"""
    print("\n📈 启动K线图分析...")
    
    cmd = [
        sys.executable, 'main_kline.py',
        '--csv', args.csv,
        '--output', 'output/kline'
    ]
    
    if args.max:
        cmd.extend(['--max', str(args.max)])
    
    if args.clear_cache:
        cmd.append('--clear-cache')
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ K线图分析完成")
        print(f"📁 输出目录: output/kline/")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ K线图分析失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def run_arc_analysis(args):
    """运行大弧底形态分析"""
    print("\n🎯 启动大弧底形态分析...")
    
    cmd = [
        sys.executable, 'main_arc.py',
        '--csv', args.csv,
        '--output', 'output/arc'
    ]
    
    if args.max:
        cmd.extend(['--max', str(args.max)])
    
    if args.clear_cache:
        cmd.append('--clear-cache')
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 大弧底形态分析完成")
        print(f"📁 输出目录: output/arc/")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 大弧底形态分析失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def run_uptrend_analysis(args):
    """运行上升通道分析"""
    print("\n📈 启动上升通道分析...")
    
    cmd = [
        sys.executable, 'main_uptrend.py',
        '--csv', args.csv,
        '--output', 'output/uptrend'
    ]
    
    if args.max:
        cmd.extend(['--max', str(args.max)])
    
    if args.clear_cache:
        cmd.append('--clear-cache')
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 上升通道分析完成")
        print(f"📁 输出目录: output/uptrend/")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 上升通道分析失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def run_volatility_analysis(args):
    """运行波动率分析"""
    print("\n📊 启动波动率分析...")
    
    cmd = [
        sys.executable, 'main_volatility.py',
        '--csv', args.csv,
        '--output', 'output/volatility'
    ]
    
    if args.max:
        cmd.extend(['--max', str(args.max)])
    
    if args.clear_cache:
        cmd.append('--clear-cache')
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 波动率分析完成")
        print(f"📁 输出目录: output/volatility/")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 波动率分析失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def run_similarity_analysis(args):
    """运行相似度分析"""
    print("\n🔄 启动相似度分析...")
    
    cmd = [
        sys.executable, 'main_similarity.py',
        '--csv', args.csv,
        '--output', 'output/similarity'
    ]
    
    if args.max:
        cmd.extend(['--max', str(args.max)])
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 相似度分析完成")
        print(f"📁 输出目录: output/similarity/")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 相似度分析失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def run_all_analysis(args):
    """运行所有分析"""
    print("\n🚀 启动完整分析流程...")
    
    success_count = 0
    total_count = 5
    
    # 按顺序运行所有分析
    analyses = [
        ('K线图分析', run_kline_analysis),
        ('大弧底分析', run_arc_analysis),
        ('上升通道分析', run_uptrend_analysis),
        ('波动率分析', run_volatility_analysis),
        ('相似度分析', run_similarity_analysis)
    ]
    
    for name, func in analyses:
        print(f"\n{'='*60}")
        print(f"开始 {name}")
        print(f"{'='*60}")
        
        if func(args):
            success_count += 1
        
        print(f"进度: {success_count}/{len(analyses)} 完成")
    
    print(f"\n🎉 分析完成! 成功: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("✅ 所有分析都已成功完成")
        print("🌐 请打开 index.html 查看结果")
    else:
        print("⚠️  部分分析失败，请检查错误信息")

def open_browser():
    """打开浏览器查看结果"""
    import webbrowser
    
    # 获取index.html的绝对路径（现在在output目录）
    index_path = os.path.abspath('output/index.html')
    
    if os.path.exists(index_path):
        print(f"\n🌐 正在打开浏览器: file://{index_path}")
        webbrowser.open(f'file://{index_path}')
    else:
        print("❌ output/index.html 文件不存在")

def main():
    parser = argparse.ArgumentParser(
        description='A股技术分析平台 - 统一启动脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python run_analysis.py all                    # 运行所有分析
  python run_analysis.py kline --max 100        # 只运行K线分析，限制100只股票
  python run_analysis.py arc --clear-cache      # 运行大弧底分析并清除缓存
  python run_analysis.py uptrend --max 50       # 运行上升通道分析，限制50只股票
  python run_analysis.py volatility             # 只运行波动率分析
  python run_analysis.py similarity             # 只运行相似度分析
  python run_analysis.py --open-browser         # 只打开浏览器查看结果
        """
    )
    
    parser.add_argument(
        'analysis_type',
        choices=['all', 'kline', 'arc', 'uptrend', 'volatility', 'similarity'],
        nargs='?',
        default='all',
        help='要运行的分析类型 (默认: all)'
    )
    
    parser.add_argument(
        '--csv',
        type=str,
        default='/Users/kangfei/Downloads/result.csv',
        help='CSV数据文件路径'
    )
    
    parser.add_argument(
        '--max',
        type=int,
        help='最多处理的股票数量（用于测试）'
    )
    
    parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='清除缓存，重新处理数据'
    )
    
    parser.add_argument(
        '--open-browser',
        action='store_true',
        help='运行完成后自动打开浏览器'
    )
    
    args = parser.parse_args()
    
    # 打印横幅
    print_banner()
    
    # 如果只是打开浏览器
    if args.open_browser and len(sys.argv) == 2:
        open_browser()
        return
    
    # 检查环境
    if not check_environment():
        sys.exit(1)
    
    # 创建输出目录
    os.makedirs('output', exist_ok=True)
    
    # 记录开始时间
    start_time = datetime.now()
    print(f"\n⏰ 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 根据选择运行分析
    success = False
    
    if args.analysis_type == 'all':
        run_all_analysis(args)
        success = True
    elif args.analysis_type == 'kline':
        success = run_kline_analysis(args)
    elif args.analysis_type == 'arc':
        success = run_arc_analysis(args)
    elif args.analysis_type == 'uptrend':
        success = run_uptrend_analysis(args)
    elif args.analysis_type == 'volatility':
        success = run_volatility_analysis(args)
    elif args.analysis_type == 'similarity':
        success = run_similarity_analysis(args)
    
    # 计算耗时
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n⏰ 结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  总耗时: {duration}")
    
    # 如果成功且设置了自动打开浏览器
    if success and args.open_browser:
        open_browser()
    
    print(f"\n{'='*60}")
    print("🎊 分析完成! 感谢使用A股技术分析平台")
    print("📚 更多信息请查看项目文档: README.md")
    print(f"{'='*60}")

if __name__ == '__main__':
    main() 