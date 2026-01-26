#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复分佣状态逻辑
正确的逻辑：
- 待制作 → 未结算
- 厂家制作中/已发货 → 已结算
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order, Commission, PromotionUser
from datetime import datetime

def check_current_logic():
    """检查当前逻辑"""
    print("🔍 检查当前分佣状态逻辑")
    print("=" * 50)
    
    with app.app_context():
        # 检查所有订单状态
        all_orders = Order.query.all()
        print(f"总订单数: {len(all_orders)}")
        
        status_count = {}
        for order in all_orders:
            status = order.status
            if status not in status_count:
                status_count[status] = 0
            status_count[status] += 1
        
        print("订单状态统计:")
        for status, count in status_count.items():
            print(f"  {status}: {count} 个")
        
        # 检查分佣记录
        commissions = Commission.query.all()
        print(f"\n总分佣记录数: {len(commissions)}")
        
        print("\n当前分佣状态逻辑:")
        print("-" * 40)
        
        for i, commission in enumerate(commissions, 1):
            order = Order.query.filter_by(order_number=commission.order_id).first()
            if order:
                # 当前错误的逻辑
                if order.status in ['shipped', 'manufacturing']:
                    current_wrong_status = 'completed'
                    current_wrong_text = '已结算'
                else:
                    current_wrong_status = 'pending'
                    current_wrong_text = '待结算'
                
                # 正确的逻辑
                if order.status in ['manufacturing', 'shipped']:
                    correct_status = 'completed'
                    correct_text = '已结算'
                else:
                    correct_status = 'pending'
                    correct_text = '待结算'
                
                print(f"{i:2d}. {commission.order_id}")
                print(f"    订单状态: {order.status}")
                print(f"    当前错误逻辑: {current_wrong_text}")
                print(f"    正确逻辑: {correct_text}")
                print(f"    分佣金额: ¥{commission.amount:.2f}")
                print()

def fix_commission_logic():
    """修复分佣逻辑"""
    print("\n🔧 修复分佣状态逻辑")
    print("-" * 40)
    
    print("正确的分佣状态逻辑:")
    print("- 订单状态为 'manufacturing' (厂家制作中) → 分佣状态: 已结算")
    print("- 订单状态为 'shipped' (已发货) → 分佣状态: 已结算")
    print("- 订单状态为 'pending' (待制作) → 分佣状态: 待结算")
    print("- 订单状态为 'processing' (处理中) → 分佣状态: 待结算")
    print("- 其他订单状态 → 分佣状态: 待结算")

def test_correct_logic():
    """测试正确的逻辑"""
    print("\n🧪 测试正确的分佣状态逻辑")
    print("-" * 40)
    
    with app.app_context():
        commissions = Commission.query.all()
        
        print("测试结果:")
        for i, commission in enumerate(commissions, 1):
            order = Order.query.filter_by(order_number=commission.order_id).first()
            if order:
                # 正确的逻辑
                if order.status in ['manufacturing', 'shipped']:
                    correct_status = 'completed'
                    correct_text = '已结算'
                else:
                    correct_status = 'pending'
                    correct_text = '待结算'
                
                print(f"{i:2d}. {commission.order_id}")
                print(f"    订单状态: {order.status}")
                print(f"    分佣状态: {correct_text}")
                print(f"    分佣金额: ¥{commission.amount:.2f}")
                print()

if __name__ == '__main__':
    check_current_logic()
    fix_commission_logic()
    test_correct_logic()
