#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动安装依赖包脚本
"""
import subprocess
import sys
import os

def install_package(package):
    """安装单个包"""
    try:
        print(f"正在安装 {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package} 安装失败: {e}")
        
        # 特殊处理 Pillow 安装失败
        if "Pillow" in package:
            print("   尝试使用替代方法安装 Pillow...")
            try:
                # 尝试安装最新版本
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "Pillow"])
                print(f"✅ Pillow (最新版本) 安装成功")
                return True
            except:
                try:
                    # 尝试使用国内镜像
                    subprocess.check_call([
                        sys.executable, "-m", "pip", "install", 
                        "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", 
                        "Pillow"
                    ])
                    print(f"✅ Pillow (使用镜像源) 安装成功")
                    return True
                except:
                    print(f"❌ Pillow 所有安装方法都失败")
        
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("开始安装 Python 依赖包...")
    print("=" * 50)
    
    # 读取 requirements.txt
    requirements_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    
    if not os.path.exists(requirements_file):
        print(f"❌ 未找到 requirements.txt 文件: {requirements_file}")
        return
    
    # 读取所有依赖
    with open(requirements_file, 'r', encoding='utf-8') as f:
        packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"找到 {len(packages)} 个依赖包")
    print()
    
    # 安装所有包
    failed = []
    for package in packages:
        if not install_package(package):
            failed.append(package)
        print()
    
    # 总结
    print("=" * 50)
    if failed:
        print(f"⚠️  有 {len(failed)} 个包安装失败:")
        for pkg in failed:
            print(f"   - {pkg}")
    else:
        print("✅ 所有依赖包安装成功！")
    print("=" * 50)

if __name__ == "__main__":
    main()
