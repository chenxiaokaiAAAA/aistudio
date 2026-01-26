#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
更新订单状态为厂家制作中
处理厂家冲印测试流程
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order
from datetime import datetime

def update_order_to_manufacturing(order_number):
    """更新订单状态为厂家制作中"""
    print(f"🏭 更新订单 {order_number} 状态为厂家制作中...")
    
    with app.app_context():
        order = Order.query.filter_by(order_number=order_number).first()
        if not order:
            print(f"❌ 未找到订单 {order_number}")
            return False
        
        print(f"当前状态: {order.status}")
        
        # 更新状态为厂家制作中
        order.status = 'manufacturing'
        db.session.commit()
        
        print(f"✅ 订单状态已更新为: {order.status}")
        print(f"订单信息:")
        print(f"  订单号: {order.order_number}")
        print(f"  客户: {order.customer_name}")
        print(f"  产品: 梵高油画框30x30cm肌理画框")
        print(f"  厂家产品ID: 33673")
        print(f"  状态: 厂家制作中")
        
        return True

def create_manufacturer_feedback_template():
    """创建厂家回传信息的模板"""
    print(f"\n📋 厂家回传信息模板:")
    print("=" * 50)
    print("订单号: PET20250917175858D53F")
    print("状态: 厂家制作中")
    print("")
    print("请厂家回传以下信息:")
    print("1. 物流单号: [请填写]")
    print("2. 物流公司: [请填写]")
    print("3. 预计送达时间: [请填写，格式：YYYY-MM-DD]")
    print("4. 制作完成照片: [可选，上传照片]")
    print("")
    print("收货信息:")
    print("收货人: chenxiaokai")
    print("联系电话: 13799319030")
    print("收货地址: [需要商家提供具体地址]")
    print("")
    print("产品信息:")
    print("产品ID: 33673")
    print("产品名称: 梵高油画框30x30cm肌理画框")
    print("画框尺寸: 35.6x35.6cm")

if __name__ == '__main__':
    order_number = "PET20250917175858D53F"
    
    # 更新订单状态
    success = update_order_to_manufacturing(order_number)
    
    if success:
        # 创建厂家回传模板
        create_manufacturer_feedback_template()
        
        print(f"\n🎯 下一步操作:")
        print("1. 将订单信息发送给厂家")
        print("2. 等待厂家制作完成")
        print("3. 厂家回传物流单号")
        print("4. 更新订单状态为'已发货'")
        print("5. 通知商家订单已发货")
