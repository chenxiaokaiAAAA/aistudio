#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复冲印系统脚本中的文件访问URL配置
更新为正确的后台地址
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_file_access_url():
    """修复文件访问URL配置"""
    print("🔧 修复冲印系统脚本中的文件访问URL配置...")
    
    # 读取当前配置
    config_file = 'printer_config.py'
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📋 当前配置内容:")
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "'file_access_base_url':" in line:
                print(f"   第{i+1}行: {line.strip()}")
                break
        
        # 获取新的URL
        print(f"\n🌐 请输入正确的后台地址:")
        print(f"当前使用的是: https://released-athletic-mime-shadow.trycloudflare.com")
        print(f"请确认这是否是正确的地址，或者输入新的地址")
        
        new_url = input("新的后台地址 (直接回车使用当前地址): ").strip()
        if not new_url:
            new_url = "https://released-athletic-mime-shadow.trycloudflare.com"
            print(f"使用当前地址: {new_url}")
        
        # 更新配置
        updated_content = content.replace(
            f"'file_access_base_url': 'https://released-athletic-mime-shadow.trycloudflare.com',",
            f"'file_access_base_url': '{new_url}',"
        )
        
        # 写回文件
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"✅ 配置文件已更新!")
        print(f"新的文件访问基础URL: {new_url}")
        
        # 测试URL生成
        test_url_generation(new_url)
        
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {str(e)}")
        return False

def test_url_generation(base_url):
    """测试URL生成逻辑"""
    print(f"\n🧪 测试URL生成逻辑:")
    
    # 模拟不同的图片文件名
    test_files = [
        "hd_8b6230e1-840a-4e9d-9df8-f85f7866d0cf_-2.jpg",  # 高清图片
        "final_test_image.jpg",  # 成品图片
        "original_upload.jpg"   # 原图
    ]
    
    for filename in test_files:
        if 'hd_' in filename:
            url = f"{base_url}/public/hd/{filename}"
            print(f"  高清图片: {url}")
        elif 'final_' in filename:
            url = f"{base_url}/media/final/{filename}"
            print(f"  成品图片: {url}")
        else:
            url = f"{base_url}/media/original/{filename}"
            print(f"  原图: {url}")
    
    # 测试实际订单的URL
    print(f"\n📋 实际订单URL测试:")
    order_hd_image = "hd_8b6230e1-840a-4e9d-9df8-f85f7866d0cf_-2.jpg"
    actual_url = f"{base_url}/public/hd/{order_hd_image}"
    print(f"订单 PET20250917175858D53F 的高清图片URL:")
    print(f"  {actual_url}")

def test_url_accessibility():
    """测试URL可访问性"""
    print(f"\n🌐 测试URL可访问性:")
    
    import requests
    
    # 读取配置获取URL
    try:
        from printer_config import PRINTER_SYSTEM_CONFIG
        base_url = PRINTER_SYSTEM_CONFIG.get('file_access_base_url')
        
        # 测试基础URL
        print(f"测试基础URL: {base_url}")
        try:
            response = requests.get(base_url, timeout=10)
            print(f"  状态码: {response.status_code}")
            if response.status_code == 200:
                print(f"  ✅ 基础URL可访问")
            else:
                print(f"  ⚠️  基础URL返回状态码: {response.status_code}")
        except Exception as e:
            print(f"  ❌ 基础URL无法访问: {str(e)}")
        
        # 测试高清图片URL
        test_image = "hd_8b6230e1-840a-4e9d-9df8-f85f7866d0cf_-2.jpg"
        test_url = f"{base_url}/public/hd/{test_image}"
        print(f"测试高清图片URL: {test_url}")
        try:
            response = requests.get(test_url, timeout=10)
            print(f"  状态码: {response.status_code}")
            if response.status_code == 200:
                print(f"  ✅ 高清图片URL可访问")
            else:
                print(f"  ⚠️  高清图片URL返回状态码: {response.status_code}")
        except Exception as e:
            print(f"  ❌ 高清图片URL无法访问: {str(e)}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

if __name__ == '__main__':
    print("🚀 冲印系统文件访问URL修复工具")
    print("=" * 50)
    
    # 修复配置
    success = fix_file_access_url()
    
    if success:
        # 测试URL可访问性
        test_url_accessibility()
        
        print(f"\n🎯 修复完成!")
        print(f"现在可以重新测试冲印系统发送订单功能")
        print(f"运行命令: python resend_order.py")
    else:
        print(f"\n❌ 修复失败，请手动检查配置文件")
