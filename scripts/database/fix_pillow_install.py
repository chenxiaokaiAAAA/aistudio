#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复 Pillow 安装问题
尝试多种安装方式
"""
import subprocess
import sys
import os

def install_pillow():
    """尝试多种方式安装 Pillow"""
    methods = [
        # 方法1: 尝试安装最新版本（通常有预编译的 wheel）
        ("最新版本", ["pip", "install", "--upgrade", "Pillow"]),
        # 方法2: 尝试安装指定版本，使用预编译 wheel
        ("指定版本 (10.0.1)", ["pip", "install", "Pillow==10.0.1", "--only-binary", ":all:"]),
        # 方法3: 尝试安装稍新的稳定版本
        ("稳定版本 (10.1.0)", ["pip", "install", "Pillow==10.1.0"]),
        # 方法4: 尝试安装，允许从源码编译
        ("从源码编译", ["pip", "install", "Pillow==10.0.1", "--no-binary", ":all:"]),
        # 方法5: 使用国内镜像源
        ("使用清华镜像", ["pip", "install", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", "Pillow==10.0.1"]),
    ]
    
    print("=" * 60)
    print("开始尝试安装 Pillow...")
    print("=" * 60)
    print()
    
    for method_name, cmd in methods:
        print(f"尝试方法: {method_name}")
        print(f"命令: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                [sys.executable, "-m"] + cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                print(f"✅ 成功！使用方法: {method_name}")
                print()
                # 验证安装
                try:
                    import PIL
                    print(f"✅ Pillow 验证成功！版本: {PIL.__version__}")
                    return True
                except ImportError:
                    print("⚠️  安装完成但无法导入，可能需要重启 Python")
                    return True
            else:
                print(f"❌ 失败: {result.stderr[:200] if result.stderr else '未知错误'}")
        except subprocess.TimeoutExpired:
            print(f"❌ 超时（超过5分钟）")
        except Exception as e:
            print(f"❌ 异常: {str(e)}")
        
        print()
    
    print("=" * 60)
    print("所有方法都失败了")
    print("=" * 60)
    return False

if __name__ == "__main__":
    success = install_pillow()
    if not success:
        print("\n建议:")
        print("1. 检查 Python 版本是否兼容（建议 Python 3.8-3.11）")
        print("2. 尝试手动安装: pip install Pillow")
        print("3. 如果使用 Python 3.12+，可能需要安装更新版本的 Pillow")
        print("4. 检查是否有足够的磁盘空间和网络连接")
    sys.exit(0 if success else 1)
