#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
最终修复分佣状态
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order, Commission
from datetime import datetime

def fix_commission_status_final():
    """最终修复分佣状态"""
    print("🔧 最终修复分佣状态")
    print("=" * 50)
    
    with app.app_context():
        # 查找所有已发货订单
        delivered_orders = Order.query.filter_by(status='delivered').all()
        print(f"找到 {len(delivered_orders)} 个已发货订单")
        
        fixed_count = 0
        
        for order in delivered_orders:
            print(f"\n处理订单: {order.order_number}")
            print(f"  订单状态: {order.status}")
            print(f"  完成时间: {order.completed_at}")
            
            # 查找分佣记录
            commission = Commission.query.filter_by(order_id=order.order_number).first()
            if commission:
                print(f"  原分佣状态: {commission.status}")
                
                # 如果分佣状态不是completed，则修复
                if commission.status != 'completed':
                    commission.status = 'completed'
                    commission.complete_time = order.completed_at or datetime.utcnow()
                    fixed_count += 1
                    print(f"  ✅ 分佣状态已修复为: {commission.status}")
                    print(f"  ✅ 分佣完成时间: {commission.complete_time}")
                else:
                    print(f"  ✅ 分佣状态已正确: {commission.status}")
            else:
                print(f"  ❌ 没有分佣记录")
        
        if fixed_count > 0:
            db.session.commit()
            print(f"\n✅ 修复完成，共修复 {fixed_count} 个分佣记录")
        else:
            print(f"\n✅ 所有分佣状态都已正确")

def verify_final_fix():
    """验证最终修复结果"""
    print(f"\n✅ 验证最终修复结果")
    print("=" * 50)
    
    with app.app_context():
        # 检查所有已发货订单
        delivered_orders = Order.query.filter_by(status='delivered').all()
        print(f"已发货订单: {len(delivered_orders)} 个")
        
        all_correct = True
        
        for order in delivered_orders:
            print(f"\n订单: {order.order_number}")
            print(f"  状态: {order.status}")
            print(f"  完成时间: {order.completed_at}")
            
            # 检查分佣记录
            commission = Commission.query.filter_by(order_id=order.order_number).first()
            if commission:
                print(f"  分佣状态: {commission.status}")
                print(f"  分佣完成时间: {commission.complete_time}")
                
                # 验证逻辑
                if order.status == 'delivered' and commission.status == 'completed':
                    print(f"  ✅ 状态和分佣都正确")
                else:
                    print(f"  ❌ 状态或分佣不正确")
                    all_correct = False
            else:
                print(f"  ❌ 没有分佣记录")
                all_correct = False
        
        if all_correct:
            print(f"\n🎉 所有已发货订单的分佣状态都已正确！")
        else:
            print(f"\n⚠️  还有问题需要修复")

def main():
    """主函数"""
    print("🚀 最终修复分佣状态")
    print("=" * 60)
    
    fix_commission_status_final()
    verify_final_fix()
    
    print("\n🎉 修复完成")

if __name__ == '__main__':
    main()
