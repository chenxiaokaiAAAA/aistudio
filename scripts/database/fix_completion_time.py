#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复完成时间问题
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order, Commission
from datetime import datetime

def fix_completion_time():
    """修复完成时间"""
    print("🔧 修复完成时间")
    print("=" * 50)
    
    with app.app_context():
        # 查找所有已发货但完成时间为空的订单
        orders = Order.query.filter_by(status='delivered').all()
        print(f"找到 {len(orders)} 个已发货订单")
        
        fixed_count = 0
        
        for order in orders:
            print(f"\n检查订单: {order.order_number}")
            print(f"  状态: {order.status}")
            print(f"  完成时间: {order.completed_at}")
            
            # 如果完成时间为空，设置为当前时间
            if not order.completed_at:
                order.completed_at = datetime.utcnow()
                fixed_count += 1
                print(f"  ✅ 设置完成时间: {order.completed_at}")
            else:
                print(f"  ✅ 完成时间已存在")
            
            # 检查分佣记录
            commission = Commission.query.filter_by(order_id=order.order_number).first()
            if commission:
                print(f"  分佣状态: {commission.status}")
                print(f"  分佣完成时间: {commission.complete_time}")
                
                # 如果分佣状态为completed但完成时间为空，设置完成时间
                if commission.status == 'completed' and not commission.complete_time:
                    commission.complete_time = order.completed_at
                    print(f"  ✅ 设置分佣完成时间: {commission.complete_time}")
                elif commission.status == 'completed' and commission.complete_time:
                    print(f"  ✅ 分佣完成时间已存在")
                else:
                    print(f"  ⚠️  分佣状态为: {commission.status}")
            else:
                print(f"  ❌ 没有分佣记录")
        
        if fixed_count > 0:
            db.session.commit()
            print(f"\n✅ 修复完成，共修复 {fixed_count} 个订单的完成时间")
        else:
            print(f"\n✅ 所有订单的完成时间都已正确")

def verify_fix():
    """验证修复结果"""
    print(f"\n✅ 验证修复结果")
    print("=" * 50)
    
    with app.app_context():
        # 检查所有已发货订单
        orders = Order.query.filter_by(status='delivered').all()
        print(f"已发货订单: {len(orders)} 个")
        
        for order in orders:
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
            else:
                print(f"  ❌ 没有分佣记录")

def main():
    """主函数"""
    print("🚀 修复完成时间问题")
    print("=" * 60)
    
    fix_completion_time()
    verify_fix()
    
    print("\n🎉 修复完成")

if __name__ == '__main__':
    main()
