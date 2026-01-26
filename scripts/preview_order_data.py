#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预览订单发送数据包
订单ID: PET2025091517140169B1
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order
from printer_client import PrinterSystemClient
from printer_config import PRINTER_SYSTEM_CONFIG, SIZE_MAPPING

def preview_order_data():
    """预览订单发送数据包"""
    
    # 目标订单ID
    order_number = "PET2025091517140169B1"
    
    print(f"🔍 查找订单: {order_number}")
    
    with app.app_context():
        # 查找订单
        order = Order.query.filter_by(order_number=order_number).first()
        
        if not order:
            print(f"❌ 订单 {order_number} 不存在")
            return False
            
        print(f"✅ 找到订单: {order_number}")
        print(f"📋 订单基本信息:")
        print(f"   - 订单ID: {order.id}")
        print(f"   - 状态: {order.status}")
        print(f"   - 尺寸代码: {order.size}")
        print(f"   - 产品名称: {order.product_name}")
        print(f"   - 客户姓名: {order.customer_name}")
        print(f"   - 客户电话: {order.customer_phone}")
        print(f"   - 收货地址: {order.shipping_info}")
        print(f"   - 原图: {order.original_image}")
        print(f"   - 完成图: {order.final_image}")
        print(f"   - 高清图: {order.hd_image}")
        
        # 检查尺寸配置
        print(f"\n🎯 尺寸配置信息:")
        if order.size in SIZE_MAPPING:
            size_info = SIZE_MAPPING[order.size]
            print(f"   - 产品ID: {size_info['product_id']}")
            print(f"   - 产品名称: {size_info['product_name']}")
            print(f"   - 配置尺寸: {size_info['width_cm']}cm x {size_info['height_cm']}cm")
        else:
            print(f"   ❌ 尺寸代码 '{order.size}' 未在SIZE_MAPPING中找到")
        
        # 检查图片文件
        print(f"\n📁 图片文件检查:")
        hd_image_path = os.path.join(app.config['HD_FOLDER'], order.hd_image) if order.hd_image else None
        if hd_image_path and os.path.exists(hd_image_path):
            print(f"   ✅ 高清图片存在: {hd_image_path}")
            
            # 获取图片信息
            try:
                from PIL import Image
                with Image.open(hd_image_path) as img:
                    width, height = img.size
                    print(f"   - 像素尺寸: {width} x {height}")
                    print(f"   - 文件大小: {os.path.getsize(hd_image_path)} bytes")
            except Exception as e:
                print(f"   ❌ 无法读取图片信息: {e}")
        else:
            print(f"   ❌ 高清图片不存在: {hd_image_path}")
            return False
        
        # 创建冲印系统客户端并构建数据包
        print(f"\n📦 构建发送数据包...")
        printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
        
        # 构建订单数据（不发送）
        order_data = printer_client._build_order_data(order, hd_image_path)
        
        print(f"\n📋 完整发送数据包:")
        print("=" * 80)
        print(json.dumps(order_data, ensure_ascii=False, indent=2))
        print("=" * 80)
        
        # 重点显示尺寸相关字段
        print(f"\n🔍 尺寸相关字段详情:")
        if 'sub_orders' in order_data and order_data['sub_orders']:
            sub_order = order_data['sub_orders'][0]
            if 'photos' in sub_order and sub_order['photos']:
                photo = sub_order['photos'][0]
                print(f"   - product_id: {sub_order.get('product_id', 'N/A')}")
                print(f"   - product_name: {sub_order.get('product_name', 'N/A')}")
                print(f"   - pix_width: {photo.get('pix_width', 'N/A')}")
                print(f"   - pix_height: {photo.get('pix_height', 'N/A')}")
                print(f"   - dpi: {photo.get('dpi', 'N/A')}")
                print(f"   - width: {photo.get('width', 'N/A')}")
                print(f"   - height: {photo.get('height', 'N/A')}")
                print(f"   - size: {photo.get('size', 'N/A')}")
                print(f"   - size_width: {photo.get('size_width', 'N/A')}")
                print(f"   - size_height: {photo.get('size_height', 'N/A')}")
        
        # 显示冲印系统配置
        print(f"\n⚙️ 冲印系统配置:")
        print(f"   - API地址: {PRINTER_SYSTEM_CONFIG.get('api_url', 'N/A')}")
        print(f"   - 影楼ID: {PRINTER_SYSTEM_CONFIG.get('shop_id', 'N/A')}")
        print(f"   - 影楼名称: {PRINTER_SYSTEM_CONFIG.get('shop_name', 'N/A')}")
        print(f"   - 应用ID: {PRINTER_SYSTEM_CONFIG.get('source_app_id', 'N/A')}")
        
        return True

if __name__ == "__main__":
    print("🔍 预览订单发送数据包...")
    print("=" * 50)
    
    success = preview_order_data()
    
    print("=" * 50)
    if success:
        print("✅ 数据包预览完成!")
    else:
        print("❌ 数据包预览失败!")
