#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内网环境冲印系统测试分析
"""

def analyze_network_issue():
    """分析内网环境问题"""
    
    print("=== 内网环境冲印系统测试分析 ===")
    print()
    
    print("🔍 问题分析：")
    print("1. 您的服务器在内网 (192.168.1.66)")
    print("2. 厂家系统在外网，无法直接访问您的内网IP")
    print("3. 冲印系统需要下载您的高清图片文件")
    print("4. 当前配置的文件URL: http://photogooo/media/hd/xxx.jpg")
    print("   ↑ 厂家无法访问这个地址")
    print()
    
    print("💡 解决方案：")
    print()
    
    print("方案一：内网穿透（推荐）")
    print("  ✅ 使用内网穿透工具，如：")
    print("     - ngrok: https://ngrok.com/")
    print("     - frp: https://github.com/fatedier/frp")
    print("     - natapp: https://natapp.cn/")
    print("  ✅ 将内网服务映射到公网")
    print("  ✅ 厂家可以正常访问图片文件")
    print()
    
    print("方案二：云存储（推荐）")
    print("  ✅ 将高清图片上传到云存储")
    print("  ✅ 使用云存储的公开URL")
    print("  ✅ 支持的服务：阿里云OSS、腾讯云COS、七牛云等")
    print()
    
    print("方案三：临时公网IP")
    print("  ✅ 申请临时公网IP")
    print("  ✅ 配置路由器端口转发")
    print("  ✅ 厂家可以直接访问")
    print()
    
    print("方案四：测试模式")
    print("  ✅ 使用本地文件路径（仅测试API格式）")
    print("  ✅ 不测试实际文件传输")
    print("  ✅ 验证订单数据格式是否正确")
    print()

def test_api_format_only():
    """仅测试API格式（不涉及文件传输）"""
    
    print("=== API格式测试（内网可用）===")
    print()
    
    try:
        from printer_client import PrinterSystemClient
        from printer_config import PRINTER_SYSTEM_CONFIG
        
        # 检查配置
        if PRINTER_SYSTEM_CONFIG['shop_id'] == 'YOUR_SHOP_ID':
            print("❌ 请先配置 shop_id 和 shop_name")
            return False
        
        print("✅ 配置检查通过")
        print(f"API地址: {PRINTER_SYSTEM_CONFIG['api_url']}")
        print(f"影楼编号: {PRINTER_SYSTEM_CONFIG['shop_id']}")
        print(f"影楼名称: {PRINTER_SYSTEM_CONFIG['shop_name']}")
        print()
        
        # 创建测试订单数据（不涉及文件）
        test_order_data = {
            'source_app_id': PRINTER_SYSTEM_CONFIG['source_app_id'],
            'order_id': 'TEST_20250915_001',
            'order_no': 'TEST_20250915_001',
            'order_time': '2025-09-15 12:00:00',
            'push_time': '2025-09-15 12:00:00',
            'remark': '内网测试订单',
            'shop_id': PRINTER_SYSTEM_CONFIG['shop_id'],
            'shop_name': PRINTER_SYSTEM_CONFIG['shop_name'],
            'shipping_receiver': {
                'name': '测试客户',
                'mobile': '13800138000',
                'province': '广东省',
                'city': '深圳市',
                'city_part': '南山区',
                'street': '测试地址',
                'corp_name': ''
            },
            'sub_orders': [{
                'sub_order_id': 'TEST_20250915_001_1',
                'complex_product': None,
                'customer_name': '测试客户',
                'props': [],
                'product_id': 'P001',
                'product_name': '测试产品',
                'shop_product_sn': 'TEST_20250915_001',
                'remark': '内网测试订单',
                'num': 1,
                'photos': [{
                    'page_type': 0,
                    'index': 1,
                    'num': 1,
                    'file_name': 'test_image.jpg',
                    'pix_width': 2480,
                    'pix_height': 3508,
                    'dpi': 300,
                    'width': 21.0,
                    'height': 29.7,
                    'file_url': 'http://example.com/test_image.jpg'  # 测试URL
                }]
            }]
        }
        
        print("📤 发送测试订单数据...")
        print(f"订单号: {test_order_data['order_no']}")
        print(f"客户: {test_order_data['shipping_receiver']['name']}")
        print(f"产品: {test_order_data['sub_orders'][0]['product_name']}")
        print()
        
        # 发送测试请求
        import requests
        import json
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        response = requests.post(
            PRINTER_SYSTEM_CONFIG['api_url'],
            json=test_order_data,
            headers=headers,
            timeout=30
        )
        
        print(f"📥 响应状态码: {response.status_code}")
        print(f"📥 响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✅ API格式测试成功！")
            print("   订单数据格式正确，厂家系统可以接收")
            print("   注意：图片文件URL需要是可访问的公网地址")
        else:
            print("❌ API格式测试失败")
            print("   请检查订单数据格式或联系厂家")
        
        return response.status_code == 200
        
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def suggest_solutions():
    """建议解决方案"""
    
    print("=== 推荐解决方案 ===")
    print()
    
    print("🎯 方案一：使用ngrok内网穿透（最简单）")
    print("1. 下载ngrok: https://ngrok.com/download")
    print("2. 注册账号获取authtoken")
    print("3. 运行命令:")
    print("   ngrok http 8000")
    print("4. 获得公网地址，如: https://abc123.ngrok.io")
    print("5. 更新配置文件:")
    print("   'file_access_base_url': 'https://abc123.ngrok.io'")
    print()
    
    print("🎯 方案二：使用云存储（最稳定）")
    print("1. 注册阿里云OSS或腾讯云COS")
    print("2. 创建存储桶，设置为公开读取")
    print("3. 上传高清图片到云存储")
    print("4. 使用云存储的公开URL")
    print("5. 修改printer_client.py使用云存储URL")
    print()
    
    print("🎯 方案三：申请公网IP（最直接）")
    print("1. 联系网络运营商申请公网IP")
    print("2. 配置路由器端口转发: 8000端口")
    print("3. 更新配置文件:")
    print("   'file_access_base_url': 'http://您的公网IP:8000'")
    print()
    
    print("🎯 方案四：仅测试API格式（当前可用）")
    print("1. 运行API格式测试")
    print("2. 验证订单数据格式")
    print("3. 确认厂家系统可以接收")
    print("4. 后续再解决文件访问问题")

if __name__ == '__main__':
    analyze_network_issue()
    print()
    suggest_solutions()
    print()
    
    # 询问是否进行API格式测试
    print("=== 是否进行API格式测试？ ===")
    print("这个测试不需要文件传输，仅验证订单数据格式")
    print("输入 'y' 开始测试，其他键跳过:")
    
    try:
        choice = input().strip().lower()
        if choice == 'y':
            print()
            test_api_format_only()
    except:
        print("跳过API格式测试")

