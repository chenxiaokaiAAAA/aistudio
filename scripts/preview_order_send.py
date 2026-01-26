#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
冲印系统发送前预览脚本
在发送前显示所有数据，确认无误后再发送
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order
from printer_client import PrinterSystemClient
from printer_config import PRINTER_SYSTEM_CONFIG
import json

def preview_order_data():
    """预览订单数据"""
    print("🔍 预览订单发送数据...")
    
    with app.app_context():
        order_number = "PET20250917175858D53F"
        order = Order.query.filter_by(order_number=order_number).first()
        
        if not order:
            print(f"❌ 订单 {order_number} 不存在")
            return False
        
        print(f"📋 订单基本信息:")
        print(f"   - 订单号: {order.order_number}")
        print(f"   - 客户姓名: {order.customer_name}")
        print(f"   - 客户电话: {order.customer_phone}")
        print(f"   - 收货地址: {order.shipping_info}")
        print(f"   - 产品尺寸: {order.size}")
        print(f"   - 高清图片: {order.hd_image}")
        
        # 检查图片文件
        hd_image_path = os.path.join('hd_images', order.hd_image)
        if not os.path.exists(hd_image_path):
            print(f"❌ 图片文件不存在: {hd_image_path}")
            return False
        
        print(f"✅ 图片文件存在: {hd_image_path}")
        
        # 创建冲印系统客户端
        printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
        
        # 生成图片URL
        image_url = printer_client._get_file_url(hd_image_path)
        print(f"\n🔗 图片URL信息:")
        print(f"   - 原始文件名: {order.hd_image}")
        print(f"   - 生成的URL: {image_url}")
        
        # 检查URL编码
        filename = os.path.basename(hd_image_path)
        if filename in image_url:
            print(f"   ✅ URL未编码")
        else:
            print(f"   ⚠️  URL可能被编码")
            # 尝试解码
            import urllib.parse
            decoded_url = urllib.parse.unquote(image_url)
            print(f"   - 解码后: {decoded_url}")
        
        # 构建订单数据
        print(f"\n📦 构建订单数据...")
        try:
            order_data = printer_client._build_order_data(order, hd_image_path)
            
            print(f"✅ 订单数据构建成功")
            print(f"\n📋 发送数据预览:")
            print(f"   - 订单号: {order_data.get('order_no')}")
            print(f"   - 客户姓名: {order_data.get('shipping_receiver', {}).get('name')}")
            print(f"   - 客户电话: {order_data.get('shipping_receiver', {}).get('mobile')}")
            print(f"   - 省份: {order_data.get('shipping_receiver', {}).get('province')}")
            print(f"   - 城市: {order_data.get('shipping_receiver', {}).get('city')}")
            print(f"   - 区县: {order_data.get('shipping_receiver', {}).get('city_part')}")
            print(f"   - 街道: {order_data.get('shipping_receiver', {}).get('street')}")
            
            # 检查产品信息
            if order_data.get('sub_orders'):
                sub_order = order_data['sub_orders'][0]
                print(f"   - 产品ID: {sub_order.get('product_id')}")
                print(f"   - 产品名称: {sub_order.get('product_name')}")
                
                # 检查图片信息
                if sub_order.get('photos'):
                    photo = sub_order['photos'][0]
                    print(f"   - 图片文件名: {photo.get('file_name')}")
                    print(f"   - 图片URL: {photo.get('file_url')}")
                    print(f"   - 图片尺寸: {photo.get('width')} x {photo.get('height')}")
                    print(f"   - DPI: {photo.get('dpi')}")
            
            # 显示完整JSON数据
            print(f"\n📄 完整JSON数据:")
            print(json.dumps(order_data, ensure_ascii=False, indent=2))
            
            return order_data
            
        except Exception as e:
            print(f"❌ 订单数据构建失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

def send_order_after_preview():
    """预览后发送订单"""
    print(f"\n❓ 是否发送订单到冲印系统？")
    confirm = input("输入 y 确认发送，其他键取消: ").strip().lower()
    
    if confirm != 'y':
        print(f"❌ 用户取消发送")
        return False
    
    with app.app_context():
        order_number = "PET20250917175858D53F"
        order = Order.query.filter_by(order_number=order_number).first()
        
        if not order:
            print(f"❌ 订单 {order_number} 不存在")
            return False
        
        try:
            # 创建冲印系统客户端
            printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
            
            # 检查高清图片文件
            hd_image_path = os.path.join('hd_images', order.hd_image)
            if not os.path.exists(hd_image_path):
                print(f"❌ 高清图片文件不存在: {hd_image_path}")
                return False
            
            print(f"📤 开始发送订单到冲印系统...")
            
            # 发送订单
            success = printer_client.send_order_to_printer(order, order.hd_image, order)
            
            if success:
                print(f"✅ 订单发送成功!")
                print(f"📊 发送状态: {order.printer_send_status}")
                print(f"⏰ 发送时间: {order.printer_send_time}")
                
                if order.printer_response_data:
                    print(f"📄 厂家响应:")
                    print(f"   {order.printer_response_data}")
            else:
                print(f"❌ 订单发送失败!")
                print(f"📊 发送状态: {order.printer_send_status}")
                print(f"❌ 错误信息: {order.printer_error_message}")
                
                if order.printer_response_data:
                    print(f"📄 厂家响应:")
                    print(f"   {order.printer_response_data}")
            
            # 提交数据库更改
            db.session.commit()
            print(f"💾 数据库已更新")
            
            return success
            
        except Exception as e:
            print(f"❌ 发送过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.commit()
            return False

if __name__ == '__main__':
    print("🔍 冲印系统发送前预览工具")
    print("=" * 50)
    
    # 预览订单数据
    order_data = preview_order_data()
    
    if order_data:
        # 发送订单
        send_order_after_preview()
    else:
        print(f"❌ 无法预览订单数据")
