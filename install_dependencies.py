#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
依赖安装脚本
自动安装波动率分析工具所需的所有依赖包
"""

import subprocess
import sys
import os

def install_package(package):
    """安装单个包"""
    try:
        print(f"📦 安装 {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package} 安装失败: {e}")
        return False

def check_package(package):
    """检查包是否已安装"""
    try:
        __import__(package)
        return True
    except ImportError:
        return False

def main():
    """主函数"""
    print("🚀 波动率分析工具依赖安装脚本")
    print("=" * 50)
    
    # 必需的依赖包
    required_packages = [
        "pandas",
        "numpy", 
        "matplotlib",
        "scipy",
        "scikit-learn",
        "Pillow",
        "opencv-python",
        "imagehash",
        "tqdm"
    ]
    
    print("🔍 检查已安装的包...")
    missing_packages = []
    
    for package in required_packages:
        if check_package(package.replace("-", "_")):
            print(f"✅ {package} 已安装")
        else:
            print(f"❌ {package} 未安装")
            missing_packages.append(package)
    
    if not missing_packages:
        print("\n🎉 所有依赖包都已安装！")
        print("💡 您现在可以运行波动率分析工具了")
        return True
    
    print(f"\n📦 需要安装 {len(missing_packages)} 个包:")
    for package in missing_packages:
        print(f"  - {package}")
    
    # 安装缺失的包
    print("\n🔧 开始安装缺失的包...")
    failed_packages = []
    
    for package in missing_packages:
        if not install_package(package):
            failed_packages.append(package)
    
    if failed_packages:
        print(f"\n❌ 以下包安装失败:")
        for package in failed_packages:
            print(f"  - {package}")
        print("\n💡 请手动安装这些包:")
        for package in failed_packages:
            print(f"  pip install {package}")
        return False
    
    print("\n🎊 所有依赖包安装完成！")
    print("💡 您现在可以运行以下命令来测试工具:")
    print("  python3 main_volatility.py --max 2")
    print("  python3 test_volatility_enhanced.py")
    
    return True

if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1) 