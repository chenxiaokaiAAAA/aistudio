#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
重置订单状态
将所有订单状态重置为 pending (待制作)
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order, Commission, PromotionUser
from datetime import datetime

def reset_order_status():
    """重置订单状态"""
    print("🔄 重置订单状态")
    print("=" * 50)
    
    with app.app_context():
        # 获取所有订单
        all_orders = Order.query.all()
        print(f"总订单数: {len(all_orders)}")
        
        # 统计当前状态
        status_count = {}
        for order in all_orders:
            status = order.status
            if status not in status_count:
                status_count[status] = 0
            status_count[status] += 1
        
        print("重置前状态统计:")
        for status, count in status_count.items():
            print(f"  {status}: {count} 个")
        
        # 重置状态
        print(f"\n开始重置订单状态...")
        reset_count = 0
        
        for order in all_orders:
            if order.status != 'pending':
                old_status = order.status
                order.status = 'pending'
                order.completed_at = None  # 清除完成时间
                reset_count += 1
                print(f"  重置订单 {order.order_number}: {old_status} → pending")
        
        if reset_count > 0:
            db.session.commit()
            print(f"\n✅ 成功重置 {reset_count} 个订单状态为 pending")
        else:
            print(f"\n✅ 所有订单状态已经是 pending，无需重置")
        
        # 验证重置结果
        print(f"\n验证重置结果:")
        status_count_after = {}
        for order in all_orders:
            status = order.status
            if status not in status_count_after:
                status_count_after[status] = 0
            status_count_after[status] += 1
        
        for status, count in status_count_after.items():
            print(f"  {status}: {count} 个")
        
        # 检查分佣状态
        print(f"\n检查分佣状态:")
        commissions = Commission.query.all()
        for i, commission in enumerate(commissions, 1):
            order = Order.query.filter_by(order_number=commission.order_id).first()
            if order:
                if order.status == 'shipped':
                    commission_status = '已结算'
                else:
                    commission_status = '待结算'
                
                print(f"{i:2d}. {commission.order_id}")
                print(f"    订单状态: {order.status}")
                print(f"    分佣状态: {commission_status}")
                print(f"    分佣金额: ¥{commission.amount:.2f}")
                print()

if __name__ == '__main__':
    reset_order_status()
