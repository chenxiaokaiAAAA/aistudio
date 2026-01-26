#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发送订单到冲印系统（带数据包预览）
订单ID: PET20250915185609C68D
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order
from printer_client import PrinterSystemClient
from printer_config import PRINTER_SYSTEM_CONFIG, SIZE_MAPPING

def send_order_with_preview():
    """发送订单到冲印系统（带数据包预览）"""
    
    order_number = "PET20250915185609C68D"
    
    print(f"🔍 查找订单: {order_number}")
    
    with app.app_context():
        # 查找订单
        order = Order.query.filter_by(order_number=order_number).first()
        
        if not order:
            print(f"❌ 订单 {order_number} 不存在")
            return False
            
        print(f"✅ 找到订单: {order.order_number}")
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
        
        # 显示公开访问链接
        base_url = PRINTER_SYSTEM_CONFIG.get('file_access_base_url', "http://moeart.cc")
        public_url = f"{base_url}/public/hd/{order.hd_image}"
        print(f"\n🔗 公开访问链接: {public_url}")
        
        try:
            # 创建冲印系统客户端
            printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
            
            # 构建数据包
            print(f"\n📦 构建发送数据包...")
            order_data = printer_client._build_order_data(order, hd_image_path)
            
            print(f"\n📋 完整发送数据包:")
            print("=" * 100)
            print(json.dumps(order_data, ensure_ascii=False, indent=2))
            print("=" * 100)
            
            # 重点显示关键字段
            print(f"\n🔍 关键字段详情:")
            if 'sub_orders' in order_data and order_data['sub_orders']:
                sub_order = order_data['sub_orders'][0]
                print(f"   📦 子订单信息:")
                print(f"      - sub_order_id: {sub_order.get('sub_order_id', 'N/A')}")
                print(f"      - customer_name: {sub_order.get('customer_name', 'N/A')}")
                print(f"      - product_id: {sub_order.get('product_id', 'N/A')}")
                print(f"      - product_name: {sub_order.get('product_name', 'N/A')}")
                print(f"      - shop_product_sn: {sub_order.get('shop_product_sn', 'N/A')}")
                print(f"      - remark: {sub_order.get('remark', 'N/A')}")
                
                if 'photos' in sub_order and sub_order['photos']:
                    photo = sub_order['photos'][0]
                    print(f"   📸 图片信息:")
                    print(f"      - file_name: {photo.get('file_name', 'N/A')}")
                    print(f"      - pix_width: {photo.get('pix_width', 'N/A')}")
                    print(f"      - pix_height: {photo.get('pix_height', 'N/A')}")
                    print(f"      - dpi: {photo.get('dpi', 'N/A')}")
                    print(f"      - width: {photo.get('width', 'N/A')}")
                    print(f"      - height: {photo.get('height', 'N/A')}")
                    print(f"      - size: {photo.get('size', 'N/A')}")
                    print(f"      - size_width: {photo.get('size_width', 'N/A')}")
                    print(f"      - size_height: {photo.get('size_height', 'N/A')}")
                    print(f"      - file_url: {photo.get('file_url', 'N/A')}")
            
            print(f"\n🏪 店铺信息:")
            print(f"   - shop_id: {order_data.get('shop_id', 'N/A')}")
            print(f"   - shop_name: {order_data.get('shop_name', 'N/A')}")
            print(f"   - source_app_id: {order_data.get('source_app_id', 'N/A')}")
            
            print(f"\n📮 收货信息:")
            if 'shipping_receiver' in order_data:
                receiver = order_data['shipping_receiver']
                print(f"   - name: {receiver.get('name', 'N/A')}")
                print(f"   - mobile: {receiver.get('mobile', 'N/A')}")
                print(f"   - province: {receiver.get('province', 'N/A')}")
                print(f"   - city: {receiver.get('city', 'N/A')}")
                print(f"   - city_part: {receiver.get('city_part', 'N/A')}")
                print(f"   - street: {receiver.get('street', 'N/A')}")
            
            # 确认是否继续发送
            print(f"\n" + "="*60)
            confirm = input(f"❓ 确认发送以上数据包到冲印系统？(y/n): ")
            if confirm.lower() != 'y':
                print("❌ 用户取消发送")
                return False
            
            print(f"\n📤 开始发送订单到冲印系统...")
            
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

if __name__ == "__main__":
    print("🚀 发送订单到冲印系统（带数据包预览）...")
    print("=" * 60)
    print(f"📋 目标订单: PET20250915185609C68D")
    print("=" * 60)
    
    success = send_order_with_preview()
    
    print("=" * 60)
    if success:
        print("🎉 发送完成 - 成功!")
        print("✅ 权限问题已解决，厂家现在可以正常访问图片!")
    else:
        print("💥 发送完成 - 失败!")
