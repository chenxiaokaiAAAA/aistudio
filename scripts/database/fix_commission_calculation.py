#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复现有订单的佣金计算逻辑
按照新规则：只有在"高清放大"或"已发货"状态时才计算佣金
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order, User

def fix_commission_calculation():
    """修复现有订单的佣金计算逻辑"""
    print("🔧 修复现有订单的佣金计算逻辑...")
    
    with app.app_context():
        # 获取所有有商家的订单
        orders = Order.query.filter(Order.merchant_id.isnot(None)).all()
        print(f"找到 {len(orders)} 个有商家的订单")
        
        fixed_count = 0
        
        for order in orders:
            print(f"\n处理订单 {order.order_number}:")
            print(f"  当前状态: {order.status}")
            print(f"  当前佣金: {order.commission}")
            
            # 根据新规则重新计算佣金
            if order.status in ['hd_ready', 'shipped']:
                # 应该计算佣金
                if order.merchant and order.commission == 0.0:
                    base_price = order.price or 0.0
                    new_commission = base_price * (order.merchant.commission_rate or 0.0)
                    order.commission = new_commission
                    print(f"  ✅ 计算佣金: {new_commission} (价格: {base_price}, 分佣比例: {order.merchant.commission_rate})")
                    fixed_count += 1
                elif order.commission > 0:
                    print(f"  ✅ 佣金已存在: {order.commission}")
            else:
                # 不应该计算佣金
                if order.commission > 0:
                    print(f"  ⚠️  状态为 {order.status}，但已有佣金 {order.commission}，保持不变")
                else:
                    print(f"  ✅ 状态为 {order.status}，无需计算佣金")
        
        # 提交更改
        db.session.commit()
        print(f"\n✅ 修复完成，共处理 {fixed_count} 个订单的佣金计算")

if __name__ == "__main__":
    fix_commission_calculation()
