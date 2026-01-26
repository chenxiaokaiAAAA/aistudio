#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
手动发送订单到冲印系统
使用方法: python manual_send_order.py <订单ID>
"""

import os
import sys
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order
from printer_config import PRINTER_SYSTEM_CONFIG
from printer_client import PrinterSystemClient

def manual_send_order(order_id):
    """手动发送订单到冲印系统"""
    with app.app_context():
        # 获取订单
        order = Order.query.get(order_id)
        if not order:
            print(f"❌ 订单 {order_id} 不存在")
            return False
        
        print(f"📋 订单信息:")
        print(f"   订单号: {order.order_number}")
        print(f"   状态: {order.status}")
        print(f"   产品名称: {order.product_name}")
        print(f"   尺寸: {order.size}")
        print(f"   高清图片: {order.hd_image}")
        print(f"   冲印发送状态: {order.printer_send_status}")
        
        # 检查高清图片
        if not order.hd_image:
            print("❌ 订单没有高清图片")
            return False
        
        hd_image_path = os.path.join(app.config['HD_FOLDER'], order.hd_image)
        if not os.path.exists(hd_image_path):
            print(f"❌ 高清图片文件不存在: {hd_image_path}")
            return False
        
        print(f"✅ 高清图片文件存在: {hd_image_path}")
        
        # 检查图片尺寸
        print(f"\n🔍 检查图片尺寸:")
        printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
        validation_result = printer_client._validate_image_size(hd_image_path, order)
        
        if validation_result['valid']:
            print(f"✅ 图片尺寸符合要求")
            print(f"   要求: {validation_result['required']['width_px']}x{validation_result['required']['height_px']}px")
            print(f"   实际: {validation_result['actual']['width']}x{validation_result['actual']['height']}px")
        else:
            print(f"❌ 图片尺寸不符合要求: {validation_result['message']}")
            print(f"   要求: {validation_result['required']['width_px']}x{validation_result['required']['height_px']}px")
            print(f"   实际: {validation_result['actual']['width']}x{validation_result['actual']['height']}px")
            
            # 询问是否继续
            response = input("\n是否继续发送？(y/N): ")
            if response.lower() != 'y':
                print("❌ 用户取消发送")
                return False
        
        # 检查冲印系统配置
        if not PRINTER_SYSTEM_CONFIG.get('enabled', False):
            print("❌ 冲印系统未启用")
            return False
        
        print("✅ 冲印系统已启用")
        print(f"   API地址: {PRINTER_SYSTEM_CONFIG['api_url']}")
        print(f"   影楼编号: {PRINTER_SYSTEM_CONFIG['shop_id']}")
        print(f"   影楼名称: {PRINTER_SYSTEM_CONFIG['shop_name']}")
        
        # 显示订单配置信息
        from printer_config import SIZE_MAPPING
        print(f"\n🎯 订单配置信息:")
        if order.size in SIZE_MAPPING:
            size_info = SIZE_MAPPING[order.size]
            print(f"   产品ID: {size_info['product_id']}")
            print(f"   产品名称: {size_info['product_name']}")
            print(f"   尺寸: {size_info['width_cm']}x{size_info['height_cm']}cm")
        else:
            print(f"   ⚠️ 尺寸 '{order.size}' 未在配置中找到")
        
        print(f"\n🚀 开始发送订单到冲印系统...")
        
        try:
            # 创建冲印系统客户端
            printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
            
            # 发送订单
            result = printer_client.send_order_to_printer(order, hd_image_path, order_obj=order)
            
            # 提交数据库更改
            db.session.commit()
            
            if result['success']:
                print(f"✅ 订单发送成功!")
                print(f"   响应: {result.get('message', '无消息')}")
                print(f"   订单状态: {order.printer_send_status}")
                print(f"   发送时间: {order.printer_send_time}")
                
                # 更新订单状态为厂家制作中
                order.status = 'manufacturing'
                db.session.commit()
                print(f"✅ 订单状态已更新为: 厂家制作中")
                
                return True
            else:
                print(f"❌ 订单发送失败!")
                print(f"   错误: {result.get('message', '未知错误')}")
                print(f"   错误类型: {result.get('error_type', '未知')}")
                print(f"   订单状态: {order.printer_send_status}")
                if order.printer_error_message:
                    print(f"   错误详情: {order.printer_error_message}")
                
                return False
                
        except Exception as e:
            print(f"❌ 发送过程中发生异常: {str(e)}")
            return False

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("使用方法: python manual_send_order.py <订单ID>")
        print("示例: python manual_send_order.py 1")
        sys.exit(1)
    
    try:
        order_id = int(sys.argv[1])
        success = manual_send_order(order_id)
        if success:
            print("\n🎉 发送完成!")
        else:
            print("\n💥 发送失败!")
            sys.exit(1)
    except ValueError:
        print("❌ 订单ID必须是数字")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")
        sys.exit(1)