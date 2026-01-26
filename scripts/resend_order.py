#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新发送订单到冲印系统
订单ID: PET20250917175858D53F
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order
from printer_client import PrinterSystemClient
from printer_config import PRINTER_SYSTEM_CONFIG

def resend_order():
    """重新发送订单到冲印系统"""
    
    # 目标订单ID
    order_number = "PET20250917175858D53F"
    
    print(f"🔍 查找订单: {order_number}")
    
    with app.app_context():
        # 查找订单
        order = Order.query.filter_by(order_number=order_number).first()
        
        if not order:
            print(f"❌ 订单 {order_number} 不存在")
            return False
            
        print(f"✅ 找到订单: {order_number}")
        print(f"📋 订单信息:")
        print(f"   - 状态: {order.status}")
        print(f"   - 尺寸: {order.size}")
        print(f"   - 收货人: {order.shipping_info}")
        print(f"   - 原图: {order.original_image}")
        print(f"   - 完成图: {order.final_image}")
        print(f"   - 高清图: {order.hd_image}")
        print(f"   - 当前发送状态: {order.printer_send_status}")
        print(f"   - 上次发送时间: {order.printer_send_time}")
        
        # 检查必要文件
        if not order.final_image:
            print("❌ 缺少完成图片")
            return False
            
        if not order.hd_image:
            print("❌ 缺少高清图片")
            return False
            
        print(f"\n🎯 准备发送订单到冲印系统...")
        
        # 显示订单配置信息
        from printer_config import SIZE_MAPPING
        if order.size in SIZE_MAPPING:
            size_info = SIZE_MAPPING[order.size]
            print(f"   - 产品ID: {size_info['product_id']}")
            print(f"   - 产品名称: {size_info['product_name']}")
            print(f"   - 尺寸: {size_info['width_cm']}cm x {size_info['height_cm']}cm")
        else:
            print(f"   - 产品ID: 未配置")
            print(f"   - 产品名称: {order.product_name}")
            print(f"   - 尺寸: 未配置")
        
        print(f"\n📋 发送数据预览:")
        print(f"   - 订单号: {order.order_number}")
        print(f"   - 客户姓名: {order.customer_name}")
        print(f"   - 客户电话: {order.customer_phone}")
        print(f"   - 收货地址: {order.shipping_info}")
        print(f"   - 高清图片: {order.hd_image}")
        
        # 确认是否继续发送
        confirm = input(f"\n❓ 确认发送以上配置信息到冲印系统？(y/n): ")
        if confirm.lower() != 'y':
            print("❌ 用户取消发送")
            return False
        
        try:
            # 创建冲印系统客户端
            printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
            
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
    print("🚀 重新发送订单到冲印系统...")
    print("=" * 50)
    
    success = resend_order()
    
    print("=" * 50)
    if success:
        print("🎉 发送完成 - 成功!")
    else:
        print("💥 发送完成 - 失败!")
