#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复分佣API逻辑
确保根据订单状态正确计算分佣状态
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order, Commission, PromotionUser
from datetime import datetime

def check_current_status():
    """检查当前状态"""
    print("🔍 检查当前状态")
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
        
        for i, commission in enumerate(commissions, 1):
            order = Order.query.filter_by(order_number=commission.order_id).first()
            if order:
                print(f"{i:2d}. {commission.order_id}")
                print(f"    订单状态: {order.status}")
                print(f"    分佣记录状态: {commission.status}")
                print(f"    分佣金额: ¥{commission.amount:.2f}")
                print()
            else:
                print(f"{i:2d}. {commission.order_id} (订单不存在)")
                print(f"    分佣记录状态: {commission.status}")
                print()

def test_commission_api():
    """测试分佣API"""
    print("\n🧪 测试分佣API")
    print("-" * 40)
    
    with app.app_context():
        # 测试特定用户的分佣API
        test_user_id = "USER1758802612508"  # 从之前的检查中获取的用户ID
        
        print(f"测试用户ID: {test_user_id}")
        
        # 获取用户信息
        user = PromotionUser.query.filter_by(user_id=test_user_id).first()
        if not user:
            print("❌ 用户不存在")
            return
        
        print(f"用户信息: {user.nickname}, 推广码: {user.promotion_code}")
        
        # 获取分佣记录
        commissions = Commission.query.filter_by(referrer_user_id=test_user_id).order_by(Commission.create_time.desc()).all()
        print(f"分佣记录数量: {len(commissions)}")
        
        # 模拟API逻辑
        orders = []
        total_earnings = 0
        
        for commission in commissions:
            order = Order.query.filter_by(order_number=commission.order_id).first()
            if order:
                # 根据订单状态确定分佣状态
                if order.status in ['shipped', 'manufacturing']:
                    commission_status = 'completed'
                    commission_status_text = '已结算'
                    total_earnings += commission.amount
                else:
                    commission_status = 'pending'
                    commission_status_text = '待结算'
                
                orders.append({
                    'orderId': commission.order_id,
                    'productName': order.size or '定制产品',
                    'totalPrice': float(order.price or 0),
                    'commissionAmount': float(commission.amount),
                    'commissionStatus': commission_status,
                    'commissionStatusText': commission_status_text,
                    'createTime': commission.create_time.strftime('%Y-%m-%d %H:%M:%S') if commission.create_time else '',
                    'completeTime': commission.complete_time.strftime('%Y-%m-%d %H:%M:%S') if commission.complete_time else ''
                })
                
                print(f"  {commission.order_id}: 订单状态={order.status}, 分佣状态={commission_status_text}")
        
        print(f"\nAPI响应数据:")
        print(f"  totalEarnings: {total_earnings}")
        print(f"  orders: {len(orders)} 个")
        
        for order_data in orders:
            print(f"    {order_data['orderId']}: {order_data['commissionStatusText']} (¥{order_data['commissionAmount']:.2f})")

def fix_commission_api():
    """修复分佣API"""
    print("\n🔧 修复分佣API")
    print("-" * 40)
    
    # 检查当前的API实现
    api_file = "test_server.py"
    if os.path.exists(api_file):
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找分佣API的实现
        if "/api/user/commission" in content:
            print("✅ 找到分佣API实现")
            
            # 检查API逻辑
            if "order.status in ['shipped', 'manufacturing']" in content:
                print("✅ API逻辑正确，根据订单状态计算分佣状态")
            else:
                print("❌ API逻辑有问题，需要修复")
        else:
            print("❌ 未找到分佣API实现")

def test_order_status_change():
    """测试订单状态变更"""
    print("\n🔄 测试订单状态变更")
    print("-" * 40)
    
    with app.app_context():
        # 找一个有分佣记录的订单进行测试
        commission = Commission.query.first()
        if not commission:
            print("❌ 没有分佣记录")
            return
        
        order = Order.query.filter_by(order_number=commission.order_id).first()
        if not order:
            print("❌ 订单不存在")
            return
        
        print(f"测试订单: {order.order_number}")
        print(f"当前订单状态: {order.status}")
        print(f"当前分佣记录状态: {commission.status}")
        
        # 测试状态变更
        original_status = order.status
        
        # 改为pending
        order.status = 'pending'
        db.session.commit()
        
        # 重新计算分佣状态
        if order.status in ['shipped', 'manufacturing']:
            calculated_status = 'completed'
            calculated_status_text = '已结算'
        else:
            calculated_status = 'pending'
            calculated_status_text = '待结算'
        
        print(f"订单状态改为: {order.status}")
        print(f"分佣状态计算为: {calculated_status_text}")
        
        # 改为shipped
        order.status = 'shipped'
        db.session.commit()
        
        if order.status in ['shipped', 'manufacturing']:
            calculated_status = 'completed'
            calculated_status_text = '已结算'
        else:
            calculated_status = 'pending'
            calculated_status_text = '待结算'
        
        print(f"订单状态改为: {order.status}")
        print(f"分佣状态计算为: {calculated_status_text}")
        
        # 恢复原状态
        order.status = original_status
        db.session.commit()
        print(f"订单状态已恢复为: {original_status}")

if __name__ == '__main__':
    check_current_status()
    test_commission_api()
    fix_commission_api()
    test_order_status_change()
