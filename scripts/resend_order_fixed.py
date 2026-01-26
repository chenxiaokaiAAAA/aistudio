#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新发送订单到冲印系统（权限修复版）
订单ID: PET2025091517140169B1
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order
from printer_client import PrinterSystemClient
from printer_config import PRINTER_SYSTEM_CONFIG

def resend_order_fixed():
    """重新发送订单到冲印系统（权限修复版）"""
    
    order_number = "PET2025091517140169B1"
    
    print(f"🔍 查找订单: {order_number}")
    
    with app.app_context():
        # 查找订单
        order = Order.query.filter_by(order_number=order_number).first()
        
        if not order:
            print(f"❌ 订单 {order_number} 不存在")
            return False
            
        print(f"✅ 找到订单: {order.order_number}")
        print(f"📋 订单信息:")
        print(f"   - 状态: {order.status}")
        print(f"   - 尺寸: {order.size}")
        print(f"   - 高清图: {order.hd_image}")
        
        # 检查高清图片
        if not order.hd_image:
            print("❌ 缺少高清图片")
            return False
            
        hd_image_path = os.path.join(app.config['HD_FOLDER'], order.hd_image)
        if not os.path.exists(hd_image_path):
            print(f"❌ 高清图片文件不存在: {hd_image_path}")
            return False
            
        print(f"✅ 高清图片文件存在: {hd_image_path}")
        
        # 显示公开访问链接
        base_url = PRINTER_SYSTEM_CONFIG.get('file_access_base_url', "http://moeart.cc")
        public_url = f"{base_url}/public/hd/{order.hd_image}"
        print(f"🔗 公开访问链接: {public_url}")
        
        try:
            # 创建冲印系统客户端
            printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
            
            # 先构建数据包，显示给用户查看
            print(f"\n📦 构建发送数据包...")
            hd_image_path = os.path.join(app.config['HD_FOLDER'], order.hd_image)
            order_data = printer_client._build_order_data(order, hd_image_path)
            
            print(f"\n📋 完整发送数据包:")
            print("=" * 80)
            import json
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
                    print(f"   - file_url: {photo.get('file_url', 'N/A')}")
            
            # 确认是否继续发送
            confirm = input(f"\n❓ 确认发送以上数据包到冲印系统？(y/n): ")
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
    print("🚀 重新发送订单到冲印系统（权限修复版）...")
    print("=" * 60)
    
    success = resend_order_fixed()
    
    print("=" * 60)
    if success:
        print("🎉 发送完成 - 成功!")
        print("✅ 权限问题已解决，厂家现在可以正常访问图片!")
    else:
        print("💥 发送完成 - 失败!")
