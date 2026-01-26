#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复现有订单的价格和分佣问题
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order, ProductSize, User
from printer_config import SIZE_MAPPING

def fix_existing_orders():
    """修复现有订单的价格和分佣问题"""
    print("🔧 修复现有订单的价格和分佣问题...")
    
    with app.app_context():
        # 获取所有需要修复的订单
        orders = Order.query.filter(Order.price == 50.0).all()
        print(f"找到 {len(orders)} 个需要修复的订单")
        
        for order in orders:
            print(f"\n处理订单 {order.order_number}:")
            print(f"  当前: size={order.size}, price={order.price}, product_name={order.product_name}")
            
            # 修复价格
            new_price = 50.0
            new_product_name = None
            
            if order.size:
                # 通过SIZE_MAPPING查找
                if order.size in SIZE_MAPPING:
                    mapping = SIZE_MAPPING[order.size]
                    printer_product_id = mapping['product_id']
                    new_product_name = mapping['product_name']
                    # 通过printer_product_id查找对应的尺寸配置
                    size_config = ProductSize.query.filter_by(printer_product_id=printer_product_id).first()
                    if size_config:
                        new_price = size_config.price
                        print(f"  通过SIZE_MAPPING找到: {size_config.size_name} (¥{size_config.price})")
                
                # 如果没找到，尝试直接通过尺寸名称查找
                if new_price == 50.0:
                    size_config = ProductSize.query.filter_by(size_name=order.size).first()
                    if size_config:
                        new_price = size_config.price
                        new_product_name = size_config.size_name
                        print(f"  通过尺寸名称找到: {size_config.size_name} (¥{size_config.price})")
            
            # 更新订单
            if new_price != 50.0:
                order.price = new_price
                if new_product_name:
                    order.product_name = new_product_name
                print(f"  更新价格: {order.price}")
                print(f"  更新产品名称: {order.product_name}")
            
            # 修复分佣（如果订单状态是hd_ready且有商家）
            if order.status == 'hd_ready' and order.merchant and order.commission == 0.0:
                base_price = order.price or 0.0
                order.commission = base_price * (order.merchant.commission_rate or 0.0)
                print(f"  计算分佣: {order.commission} (商家分佣比例: {order.merchant.commission_rate})")
        
        # 提交更改
        db.session.commit()
        print(f"\n✅ 已修复 {len(orders)} 个订单")

if __name__ == "__main__":
    fix_existing_orders()
