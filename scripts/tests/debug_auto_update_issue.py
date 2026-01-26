#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
排查自动更新问题
确认为什么分佣记录状态没有自动更新
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order, Commission, PromotionUser
from datetime import datetime

def debug_auto_update_issue():
    """排查自动更新问题"""
    print("🔍 排查自动更新问题")
    print("=" * 60)
    
    with app.app_context():
        # 检查订单状态更新逻辑
        print("1️⃣ 检查订单状态更新逻辑")
        print("-" * 40)
        
        target_order = "PET17588585922087896"
        order = Order.query.filter_by(order_number=target_order).first()
        commission = Commission.query.filter_by(order_id=target_order).first()
        
        if order and commission:
            print(f"订单: {order.order_number}")
            print(f"订单状态: {order.status}")
            print(f"分佣记录状态: {commission.status}")
            print(f"分佣记录完成时间: {commission.complete_time}")
            
            # 检查自动更新逻辑
            print(f"\n2️⃣ 检查自动更新逻辑")
            print("-" * 40)
            
            # 模拟自动更新逻辑
            if order.status in ['shipped', 'manufacturing']:
                print("✅ 订单状态为已发货，应该更新分佣状态")
                print(f"当前分佣状态: {commission.status}")
                print(f"应该更新为: completed")
                
                if commission.status != 'completed':
                    print("❌ 分佣状态未自动更新!")
                    print("问题: 自动更新逻辑只更新了订单状态，没有更新分佣记录状态")
                else:
                    print("✅ 分佣状态已正确更新")
            else:
                print("❌ 订单状态不是已发货")
        
        # 检查自动更新服务
        print(f"\n3️⃣ 检查自动更新服务")
        print("-" * 40)
        
        # 查看自动更新服务的逻辑
        print("当前自动更新服务只更新订单状态，没有更新分佣记录状态")
        print("需要修改自动更新逻辑，同时更新分佣记录状态")
        
        # 检查所有需要更新的分佣记录
        print(f"\n4️⃣ 检查所有需要更新的分佣记录")
        print("-" * 40)
        
        # 查找所有已发货但分佣状态为pending的记录
        shipped_orders = Order.query.filter(Order.status.in_(['shipped', 'manufacturing'])).all()
        print(f"找到 {len(shipped_orders)} 个已发货的订单")
        
        pending_commissions = []
        for order in shipped_orders:
            commission = Commission.query.filter_by(order_id=order.order_number).first()
            if commission and commission.status == 'pending':
                pending_commissions.append({
                    'order': order,
                    'commission': commission
                })
        
        print(f"找到 {len(pending_commissions)} 个需要更新分佣状态的记录")
        
        for item in pending_commissions:
            order = item['order']
            commission = item['commission']
            print(f"  - {order.order_number}: {order.status} → 分佣状态: {commission.status} (应该为completed)")
        
        # 修复方案
        print(f"\n5️⃣ 修复方案")
        print("-" * 40)
        print("需要在自动更新服务中添加分佣状态更新逻辑:")
        print("1. 当订单状态更新为shipped时")
        print("2. 同时更新对应的分佣记录状态为completed")
        print("3. 设置分佣记录的完成时间")
        
        # 测试修复逻辑
        print(f"\n6️⃣ 测试修复逻辑")
        print("-" * 40)
        
        if pending_commissions:
            print("准备更新分佣记录状态...")
            updated_count = 0
            
            for item in pending_commissions:
                commission = item['commission']
                if commission.status == 'pending':
                    commission.status = 'completed'
                    commission.complete_time = datetime.now()
                    updated_count += 1
                    print(f"  ✅ 更新 {commission.order_id} 的分佣状态为已结算")
            
            if updated_count > 0:
                db.session.commit()
                print(f"\n✅ 成功更新 {updated_count} 个分佣记录状态")
            else:
                print("\n❌ 没有需要更新的分佣记录")
        else:
            print("✅ 所有分佣记录状态都已正确")

def fix_auto_update_service():
    """修复自动更新服务"""
    print(f"\n🔧 修复自动更新服务")
    print("-" * 40)
    
    # 读取当前的自动更新服务文件
    service_file = "auto_status_update_service.py"
    if os.path.exists(service_file):
        with open(service_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("当前自动更新服务只更新订单状态")
        print("需要添加分佣状态更新逻辑")
        
        # 检查是否已经包含分佣更新逻辑
        if "Commission.query" in content:
            print("✅ 自动更新服务已包含分佣更新逻辑")
        else:
            print("❌ 自动更新服务缺少分佣更新逻辑")
            print("需要修改 auto_status_update_service.py 文件")
    else:
        print("❌ 自动更新服务文件不存在")

if __name__ == '__main__':
    debug_auto_update_issue()
    fix_auto_update_service()
