#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
诊断冲印系统图片URL问题
提供多种解决方案
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order
from printer_client import PrinterSystemClient
from printer_config import PRINTER_SYSTEM_CONFIG
import requests
import base64

def diagnose_image_access():
    """诊断图片访问问题"""
    print("🔍 诊断图片访问问题...")
    
    with app.app_context():
        order_number = "PET20250917175858D53F"
        order = Order.query.filter_by(order_number=order_number).first()
        
        if not order or not order.hd_image:
            print(f"❌ 订单或高清图片不存在")
            return
        
        print(f"📋 订单信息:")
        print(f"   - 订单号: {order.order_number}")
        print(f"   - 高清图片: {order.hd_image}")
        
        # 检查图片文件
        hd_image_path = os.path.join('hd_images', order.hd_image)
        if not os.path.exists(hd_image_path):
            print(f"❌ 图片文件不存在: {hd_image_path}")
            return
        
        print(f"✅ 图片文件存在: {hd_image_path}")
        print(f"   文件大小: {os.path.getsize(hd_image_path)} bytes")
        
        # 生成图片URL
        printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
        image_url = printer_client._get_file_url(hd_image_path)
        
        print(f"\n🔗 图片URL信息:")
        print(f"   - URL: {image_url}")
        print(f"   - 基础URL: {PRINTER_SYSTEM_CONFIG.get('file_access_base_url')}")
        
        # 测试URL可访问性
        print(f"\n🌐 URL访问测试:")
        try:
            response = requests.get(image_url, timeout=10)
            print(f"   - 状态码: {response.status_code}")
            print(f"   - 内容类型: {response.headers.get('content-type', 'unknown')}")
            print(f"   - 文件大小: {len(response.content)} bytes")
            
            if response.status_code == 200:
                print(f"  ✅ 图片URL可正常访问")
            else:
                print(f"  ❌ 图片URL访问失败: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ 图片URL访问异常: {str(e)}")

def test_alternative_urls():
    """测试替代URL方案"""
    print(f"\n🔍 测试替代URL方案...")
    
    base_url = PRINTER_SYSTEM_CONFIG.get('file_access_base_url')
    test_image = "hd_8b6230e1-840a-4e9d-9df8-f85f7866d0cf_-2.jpg"
    
    # 测试不同的路径
    alternative_paths = [
        f"{base_url}/public/hd/{test_image}",
        f"{base_url}/static/hd/{test_image}",
        f"{base_url}/hd_images/{test_image}",
        f"{base_url}/uploads/hd/{test_image}",
        f"{base_url}/media/hd/{test_image}",
        f"{base_url}/files/hd/{test_image}",
    ]
    
    working_urls = []
    
    for url in alternative_paths:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ 可用: {url}")
                working_urls.append(url)
            else:
                print(f"  ❌ 不可用: {url} (状态码: {response.status_code})")
        except Exception as e:
            print(f"  ❌ 测试失败: {url} - {str(e)}")
    
    return working_urls

def create_base64_solution():
    """创建Base64编码解决方案"""
    print(f"\n🔧 创建Base64编码解决方案...")
    
    with app.app_context():
        order_number = "PET20250917175858D53F"
        order = Order.query.filter_by(order_number=order_number).first()
        
        if not order or not order.hd_image:
            print(f"❌ 订单或高清图片不存在")
            return None
        
        # 读取图片文件
        hd_image_path = os.path.join('hd_images', order.hd_image)
        try:
            with open(hd_image_path, 'rb') as f:
                image_data = f.read()
            
            # 转换为Base64
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
            print(f"✅ Base64编码完成")
            print(f"   - 原文件大小: {len(image_data)} bytes")
            print(f"   - Base64大小: {len(base64_data)} bytes")
            
            # 创建Data URL
            data_url = f"data:image/jpeg;base64,{base64_data}"
            print(f"   - Data URL长度: {len(data_url)} 字符")
            
            return data_url
            
        except Exception as e:
            print(f"❌ Base64编码失败: {str(e)}")
            return None

def create_download_script():
    """创建图片下载脚本"""
    print(f"\n📥 创建图片下载脚本...")
    
    script_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
图片下载脚本
供厂家下载订单图片
"""

import requests
import os
from datetime import datetime

def download_order_image():
    """下载订单图片"""
    
    # 订单信息
    order_number = "PET20250917175858D53F"
    image_filename = "hd_8b6230e1-840a-4e9d-9df8-f85f7866d0cf_-2.jpg"
    
    # 图片URL列表（按优先级排序）
    image_urls = [
        "http://photogooo/public/hd/hd_8b6230e1-840a-4e9d-9df8-f85f7866d0cf_-2.jpg",
        "http://photogooo/static/hd/hd_8b6230e1-840a-4e9d-9df8-f85f7866d0cf_-2.jpg",
        "http://photogooo/hd_images/hd_8b6230e1-840a-4e9d-9df8-f85f7866d0cf_-2.jpg",
    ]
    
    print(f"🔍 下载订单图片: {order_number}")
    print(f"📋 图片文件名: {image_filename}")
    
    # 尝试下载
    for i, url in enumerate(image_urls, 1):
        print(f"\\n🌐 尝试URL {i}: {url}")
        
        try:
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                # 保存图片
                filename = f"{order_number}_{image_filename}"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                print(f"✅ 下载成功!")
                print(f"   - 文件名: {filename}")
                print(f"   - 文件大小: {len(response.content)} bytes")
                print(f"   - 内容类型: {response.headers.get('content-type', 'unknown')}")
                
                return filename
            else:
                print(f"❌ 下载失败: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ 下载异常: {str(e)}")
    
    print(f"\\n💥 所有URL都无法下载")
    return None

if __name__ == '__main__':
    download_order_image()
'''
    
    with open('download_order_image.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"✅ 下载脚本已创建: download_order_image.py")

def create_manual_solution():
    """创建手动解决方案"""
    print(f"\n📋 创建手动解决方案...")
    
    with app.app_context():
        order_number = "PET20250917175858D53F"
        order = Order.query.filter_by(order_number=order_number).first()
        
        if not order or not order.hd_image:
            print(f"❌ 订单或高清图片不存在")
            return
        
        # 检查图片文件
        hd_image_path = os.path.join('hd_images', order.hd_image)
        if not os.path.exists(hd_image_path):
            print(f"❌ 图片文件不存在: {hd_image_path}")
            return
        
        print(f"📋 手动解决方案:")
        print(f"   订单号: {order_number}")
        print(f"   图片文件: {order.hd_image}")
        print(f"   文件路径: {hd_image_path}")
        print(f"   文件大小: {os.path.getsize(hd_image_path)} bytes")
        
        # 生成多种URL
        base_url = PRINTER_SYSTEM_CONFIG.get('file_access_base_url')
        image_filename = order.hd_image
        
        urls = [
            f"{base_url}/public/hd/{image_filename}",
            f"{base_url}/static/hd/{image_filename}",
            f"{base_url}/hd_images/{image_filename}",
        ]
        
        print(f"\\n🔗 可尝试的图片URL:")
        for i, url in enumerate(urls, 1):
            print(f"   {i}. {url}")
        
        print(f"\\n📥 解决方案:")
        print(f"   1. 直接访问上述URL下载图片")
        print(f"   2. 使用下载脚本: python download_order_image.py")
        print(f"   3. 联系技术支持获取图片文件")
        print(f"   4. 使用FTP或其他方式传输图片文件")

def main():
    """主函数"""
    print("🔧 冲印系统图片URL问题诊断工具")
    print("=" * 50)
    
    # 1. 诊断图片访问
    diagnose_image_access()
    
    # 2. 测试替代URL
    working_urls = test_alternative_urls()
    
    # 3. 创建Base64解决方案
    base64_data = create_base64_solution()
    
    # 4. 创建下载脚本
    create_download_script()
    
    # 5. 创建手动解决方案
    create_manual_solution()
    
    print(f"\\n🎯 推荐解决方案:")
    if working_urls:
        print(f"   1. 使用可用的URL: {working_urls[0]}")
    else:
        print(f"   1. 使用下载脚本: python download_order_image.py")
        print(f"   2. 手动传输图片文件")
        print(f"   3. 使用Base64编码传输")
    
    print(f"\\n📞 如果问题持续，请联系技术支持")

if __name__ == '__main__':
    main()
