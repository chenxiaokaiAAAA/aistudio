#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自动更新订单状态机制
当订单有发货信息时，自动将状态更新为已发货
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order, Commission, PromotionUser
from datetime import datetime

def auto_update_order_status():
    """自动更新订单状态"""
    print("🔄 自动更新订单状态机制")
    print("=" * 50)
    
    with app.app_context():
        # 查找所有有发货信息但状态不是已发货的订单
        orders_with_shipping = Order.query.filter(
            Order.shipping_info.isnot(None),
            Order.shipping_info != '',
            ~Order.status.in_(['shipped', 'manufacturing'])
        ).all()
        
        print(f"找到 {len(orders_with_shipping)} 个有发货信息但状态未更新的订单")
        
        if not orders_with_shipping:
            print("✅ 所有订单状态都已正确")
            return
        
        updated_count = 0
        
        for order in orders_with_shipping:
            print(f"\n📦 检查订单: {order.order_number}")
            print(f"  当前状态: {order.status}")
            print(f"  发货信息: {order.shipping_info[:100]}..." if len(order.shipping_info) > 100 else f"  发货信息: {order.shipping_info}")
            
            # 检查发货信息是否有效
            if order.shipping_info and order.shipping_info.strip():
                try:
                    import json
                    shipping_data = json.loads(order.shipping_info)
                    # 如果有收货人信息，说明已发货
                    if shipping_data.get('receiver') or shipping_data.get('address'):
                        print(f"  ✅ 检测到有效发货信息，更新状态为已发货")
                        order.status = 'shipped'
                        order.completed_at = datetime.now()
                        updated_count += 1
                    else:
                        print(f"  ⚠️  发货信息不完整，跳过")
                except:
                    # 如果不是JSON格式，但有内容，也认为已发货
                    if order.shipping_info.strip():
                        print(f"  ✅ 检测到发货信息，更新状态为已发货")
                        order.status = 'shipped'
                        order.completed_at = datetime.now()
                        updated_count += 1
            else:
                print(f"  ⚠️  发货信息为空，跳过")
        
        if updated_count > 0:
            db.session.commit()
            print(f"\n✅ 成功更新 {updated_count} 个订单状态为已发货")
        else:
            print(f"\n❌ 没有订单需要更新")

def check_commission_auto_update():
    """检查分佣状态自动更新效果"""
    print(f"\n💰 检查分佣状态自动更新效果:")
    print("-" * 40)
    
    with app.app_context():
        # 获取所有分佣记录
        commissions = Commission.query.all()
        
        auto_settled_count = 0
        pending_count = 0
        
        for commission in commissions:
            order = Order.query.filter_by(order_number=commission.order_id).first()
            if order:
                if order.status in ['shipped', 'manufacturing']:
                    auto_settled_count += 1
                    print(f"✅ {commission.order_id}: {order.status} → 已结算 (¥{commission.amount:.2f})")
                else:
                    pending_count += 1
                    print(f"⏳ {commission.order_id}: {order.status} → 待结算 (¥{commission.amount:.2f})")
        
        print(f"\n📊 统计结果:")
        print(f"  已结算: {auto_settled_count} 个")
        print(f"  待结算: {pending_count} 个")
        print(f"  总计: {len(commissions)} 个")

if __name__ == '__main__':
    auto_update_order_status()
    check_commission_auto_update()
