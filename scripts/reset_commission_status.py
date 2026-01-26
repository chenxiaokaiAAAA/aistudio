#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
重置分佣状态
将分佣记录状态重置为pending，让API根据订单状态动态计算
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order, Commission, PromotionUser
from datetime import datetime

def reset_commission_status():
    """重置分佣状态"""
    print("🔄 重置分佣状态")
    print("=" * 50)
    
    with app.app_context():
        # 获取所有分佣记录
        commissions = Commission.query.all()
        print(f"找到 {len(commissions)} 条分佣记录")
        
        print(f"\n📊 重置前状态:")
        print("-" * 40)
        
        for i, commission in enumerate(commissions, 1):
            order = Order.query.filter_by(order_number=commission.order_id).first()
            if order:
                print(f"{i:2d}. {commission.order_id}: 订单状态={order.status}, 分佣状态={commission.status}")
            else:
                print(f"{i:2d}. {commission.order_id}: 订单不存在, 分佣状态={commission.status}")
        
        # 重置所有分佣记录状态为pending
        print(f"\n🔄 重置分佣记录状态...")
        print("-" * 40)
        
        reset_count = 0
        for commission in commissions:
            if commission.status != 'pending':
                old_status = commission.status
                commission.status = 'pending'
                commission.complete_time = None
                reset_count += 1
                print(f"  ✅ {commission.order_id}: {old_status} → pending")
            else:
                print(f"  ✅ {commission.order_id}: 已是pending状态")
        
        if reset_count > 0:
            db.session.commit()
            print(f"\n✅ 成功重置 {reset_count} 个分佣记录状态")
        else:
            print(f"\n✅ 所有分佣记录状态都已是pending")
        
        # 验证重置结果
        print(f"\n📊 重置后状态:")
        print("-" * 40)
        
        for i, commission in enumerate(commissions, 1):
            order = Order.query.filter_by(order_number=commission.order_id).first()
            if order:
                # 根据订单状态计算分佣状态
                if order.status in ['shipped', 'manufacturing']:
                    calculated_status = 'completed'
                    calculated_status_text = '已结算'
                else:
                    calculated_status = 'pending'
                    calculated_status_text = '待结算'
                
                print(f"{i:2d}. {commission.order_id}: 订单状态={order.status}, 分佣记录={commission.status}, 计算状态={calculated_status_text}")
            else:
                print(f"{i:2d}. {commission.order_id}: 订单不存在, 分佣记录={commission.status}")
        
        # 测试API调用
        print(f"\n🌐 测试API调用结果:")
        print("-" * 40)
        
        for commission in commissions:
            order = Order.query.filter_by(order_number=commission.order_id).first()
            if order:
                if order.status in ['shipped', 'manufacturing']:
                    api_status = 'completed'
                    api_status_text = '已结算'
                else:
                    api_status = 'pending'
                    api_status_text = '待结算'
                
                print(f"  {commission.order_id}: API返回 {api_status_text} (订单状态: {order.status})")

if __name__ == '__main__':
    reset_commission_status()
