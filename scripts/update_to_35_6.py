#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将订单更新为35.6x45.6cm产品ID
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order

def update_to_30x40():
    """将订单更新为30x40cm产品ID 33674"""
    
    order_number = "PET2025091517140169B1"
    
    with app.app_context():
        order = Order.query.filter_by(order_number=order_number).first()
        
        if not order:
            print(f"❌ 订单 {order_number} 不存在")
            return
        
        print(f"📋 更新前订单信息:")
        print(f"   订单号: {order.order_number}")
        print(f"   尺寸: {order.size}")
        print(f"   产品名称: {order.product_name}")
        
        # 更新为30x40cm产品
        order.size = '1'  # 对应产品ID 33674
        order.product_name = '梵高油画框30x40cm肌理画框'
        
        db.session.commit()
        
        print(f"\n✅ 更新后订单信息:")
        print(f"   订单号: {order.order_number}")
        print(f"   尺寸: {order.size}")
        print(f"   产品名称: {order.product_name}")
        print(f"   对应产品ID: 33674")
        print(f"   厂家要求尺寸: 30.00cm x 40.00cm")
        print(f"   实际输出: 35.6cm x 45.6cm (厂家会自动调整)")

if __name__ == "__main__":
    update_to_30x40()
