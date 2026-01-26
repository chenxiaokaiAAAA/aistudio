#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
处理厂家回传物流信息
更新订单状态为已发货
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order
from datetime import datetime

def update_order_shipped(order_number, tracking_number, logistics_company, estimated_delivery=None):
    """更新订单状态为已发货"""
    print(f"🚚 更新订单 {order_number} 状态为已发货...")
    
    with app.app_context():
        order = Order.query.filter_by(order_number=order_number).first()
        if not order:
            print(f"❌ 未找到订单 {order_number}")
            return False
        
        print(f"当前状态: {order.status}")
        
        # 更新状态为已发货
        order.status = 'shipped'
        
        # 更新物流信息
        logistics_info = f"物流公司: {logistics_company}\n物流单号: {tracking_number}"
        if estimated_delivery:
            logistics_info += f"\n预计送达: {estimated_delivery}"
        
        order.shipping_info = logistics_info
        
        # 更新完成时间和发货时间
        current_time = datetime.now()
        order.completed_at = current_time
        
        # 添加发货时间字段（如果不存在则使用completed_at）
        if hasattr(order, 'shipped_at'):
            order.shipped_at = current_time
        
        # 重新计算佣金（因为状态变为shipped）
        if order.merchant and order.status in ['hd_ready', 'shipped']:
            base_price = order.price or 0.0
            order.commission = base_price * (order.merchant.commission_rate or 0.0)
            print(f"✅ 重新计算佣金: ¥{order.commission:.2f}")
        
        db.session.commit()
        
        print(f"✅ 订单状态已更新为: {order.status}")
        print(f"物流信息已更新:")
        print(f"  物流公司: {logistics_company}")
        print(f"  物流单号: {tracking_number}")
        if estimated_delivery:
            print(f"  预计送达: {estimated_delivery}")
        
        return True

def simulate_manufacturer_feedback():
    """模拟厂家回传信息"""
    print(f"\n📦 模拟厂家回传物流信息:")
    print("=" * 50)
    
    order_number = "PET20250917175858D53F"
    tracking_number = "SF1234567890"
    logistics_company = "顺丰速运"
    estimated_delivery = "2025-09-20"
    
    print(f"订单号: {order_number}")
    print(f"物流单号: {tracking_number}")
    print(f"物流公司: {logistics_company}")
    print(f"预计送达: {estimated_delivery}")
    
    # 更新订单状态
    success = update_order_shipped(order_number, tracking_number, logistics_company, estimated_delivery)
    
    if success:
        print(f"\n🎉 订单处理完成!")
        print(f"商家 {order_number} 的订单已发货")
        print(f"商家可以查看物流信息并通知客户")

def manual_update():
    """手动更新订单状态"""
    print(f"\n🔧 手动更新订单状态:")
    print("请输入以下信息:")
    
    order_number = input("订单号: ").strip()
    if not order_number:
        order_number = "PET20250917175858D53F"
        print(f"使用默认订单号: {order_number}")
    
    tracking_number = input("物流单号: ").strip()
    if not tracking_number:
        tracking_number = "SF1234567890"
        print(f"使用示例物流单号: {tracking_number}")
    
    logistics_company = input("物流公司: ").strip()
    if not logistics_company:
        logistics_company = "顺丰速运"
        print(f"使用示例物流公司: {logistics_company}")
    
    estimated_delivery = input("预计送达时间 (YYYY-MM-DD，可选): ").strip()
    
    # 更新订单状态
    success = update_order_shipped(order_number, tracking_number, logistics_company, estimated_delivery)
    
    if success:
        print(f"\n✅ 订单更新成功!")

if __name__ == '__main__':
    print("选择操作模式:")
    print("1. 模拟厂家回传信息")
    print("2. 手动输入物流信息")
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == "1":
        simulate_manufacturer_feedback()
    elif choice == "2":
        manual_update()
    else:
        print("无效选择，使用模拟模式")
        simulate_manufacturer_feedback()
