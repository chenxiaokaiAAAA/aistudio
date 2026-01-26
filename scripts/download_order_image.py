#!/usr/bin/env python3
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
        "http://moeart.cc/public/hd/hd_8b6230e1-840a-4e9d-9df8-f85f7866d0cf_-2.jpg",
        "http://moeart.cc/static/hd/hd_8b6230e1-840a-4e9d-9df8-f85f7866d0cf_-2.jpg",
        "http://moeart.cc/hd_images/hd_8b6230e1-840a-4e9d-9df8-f85f7866d0cf_-2.jpg",
    ]
    
    print(f"🔍 下载订单图片: {order_number}")
    print(f"📋 图片文件名: {image_filename}")
    
    # 尝试下载
    for i, url in enumerate(image_urls, 1):
        print(f"\n🌐 尝试URL {i}: {url}")
        
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
    
    print(f"\n💥 所有URL都无法下载")
    return None

if __name__ == '__main__':
    download_order_image()
