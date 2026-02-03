#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调试小程序网络请求
检查实际请求的URL和响应
"""

import requests
import json
import time

def test_miniprogram_api():
    """测试小程序API接口"""
    base_url = "http://photogooo"
    
    print("🔍 测试小程序API接口...")
    
    # 测试轮播图接口
    print("\n1. 测试轮播图接口:")
    banners_url = f"{base_url}/api/admin/homepage/banners"
    try:
        response = requests.get(banners_url, timeout=5)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            banners = data.get('data', [])
            print(f"   轮播图数量: {len(banners)}")
            
            for i, banner in enumerate(banners):
                image_url = banner.get('image_url')
                print(f"   轮播图 {i+1}: {image_url}")
                
                # 测试图片访问
                try:
                    img_response = requests.get(image_url, timeout=5)
                    print(f"     图片状态码: {img_response.status_code}")
                    if img_response.status_code == 200:
                        print(f"     ✅ 图片可访问")
                    else:
                        print(f"     ❌ 图片不可访问")
                except Exception as e:
                    print(f"     ❌ 图片访问异常: {e}")
        else:
            print(f"   ❌ 轮播图接口失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 轮播图接口异常: {e}")
    
    # 测试风格库接口
    print("\n2. 测试风格库接口:")
    styles_url = f"{base_url}/api/miniprogram/styles"
    try:
        response = requests.get(styles_url, timeout=5)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            styles = data.get('data', [])
            print(f"   风格数量: {len(styles)}")
            
            for i, style in enumerate(styles[:2]):
                cover_image = style.get('cover_image')
                print(f"   风格 {i+1}: {cover_image}")
                
                # 测试图片访问
                try:
                    img_response = requests.get(cover_image, timeout=5)
                    print(f"     图片状态码: {img_response.status_code}")
                    if img_response.status_code == 200:
                        print(f"     ✅ 图片可访问")
                    else:
                        print(f"     ❌ 图片不可访问")
                except Exception as e:
                    print(f"     ❌ 图片访问异常: {e}")
        else:
            print(f"   ❌ 风格库接口失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 风格库接口异常: {e}")
    
    # 测试产品库接口
    print("\n3. 测试产品库接口:")
    products_url = f"{base_url}/api/miniprogram/products"
    try:
        response = requests.get(products_url, timeout=5)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            products = data.get('data', [])
            print(f"   产品数量: {len(products)}")
            
            for i, product in enumerate(products[:2]):
                image_url = product.get('image_url')
                print(f"   产品 {i+1}: {image_url}")
                
                # 测试图片访问
                try:
                    img_response = requests.get(image_url, timeout=5)
                    print(f"     图片状态码: {img_response.status_code}")
                    if img_response.status_code == 200:
                        print(f"     ✅ 图片可访问")
                    else:
                        print(f"     ❌ 图片不可访问")
                except Exception as e:
                    print(f"     ❌ 图片访问异常: {e}")
        else:
            print(f"   ❌ 产品库接口失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 产品库接口异常: {e}")

def test_image_formats():
    """测试不同图片格式的访问"""
    base_url = "http://photogooo"
    
    print("\n🖼️ 测试不同图片格式:")
    
    # 测试不同格式的图片
    test_images = [
        "/static/images/8-威廉国王.jpg",
        "/static/images/油画风格-梵高.jpg", 
        "/static/images/转绘风格-卡通.png",
        "/api/miniprogram/static/images/8-威廉国王.jpg",
        "/api/miniprogram/static/images/油画风格-梵高.jpg",
        "/api/miniprogram/static/images/转绘风格-卡通.png"
    ]
    
    for i, image_path in enumerate(test_images, 1):
        full_url = f"{base_url}{image_path}"
        print(f"\n{i}. 测试图片: {image_path}")
        
        try:
            response = requests.get(full_url, timeout=5)
            print(f"   状态码: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('Content-Type')}")
            print(f"   Content-Length: {response.headers.get('Content-Length')}")
            
            if response.status_code == 200:
                print(f"   ✅ 可访问")
                # 检查图片内容
                if response.content:
                    print(f"   图片大小: {len(response.content)} 字节")
                else:
                    print(f"   ⚠️ 图片内容为空")
            else:
                print(f"   ❌ 不可访问")
        except Exception as e:
            print(f"   ❌ 访问异常: {e}")

if __name__ == "__main__":
    test_miniprogram_api()
    test_image_formats()
