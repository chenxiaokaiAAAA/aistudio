#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
验证分佣修复结果
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order, Commission
from datetime import datetime

def verify_commission_fix():
    """验证分佣修复结果"""
    print("🔍 验证分佣修复结果")
    print("=" * 50)
    
    with app.app_context():
        # 获取所有分佣记录
        commissions = Commission.query.all()
        print(f"分佣记录总数: {len(commissions)}")
        
        delivered_count = 0
        pending_count = 0
        completed_count = 0
        
        for commission in commissions:
            # 查找对应的订单
            order = Order.query.filter_by(order_number=commission.order_id).first()
            if order:
                print(f"\n订单: {commission.order_id}")
                print(f"  订单状态: {order.status}")
                print(f"  分佣状态: {commission.status}")
                print(f"  分佣金额: ¥{commission.amount:.2f}")
                
                # 统计状态
                if order.status == 'delivered':
                    delivered_count += 1
                else:
                    pending_count += 1
                
                if commission.status == 'completed':
                    completed_count += 1
                
                # 验证逻辑
                if order.status == 'delivered':
                    expected_status = 'completed'
                    expected_text = '已结算'
                else:
                    expected_status = 'pending'
                    expected_text = '未结算'
                
                print(f"  期望分佣状态: {expected_status} ({expected_text})")
                
                if commission.status == expected_status:
                    print(f"  ✅ 状态正确")
                else:
                    print(f"  ❌ 状态错误")
        
        print(f"\n📊 统计结果:")
        print(f"  已发货订单: {delivered_count} 个")
        print(f"  其他状态订单: {pending_count} 个")
        print(f"  已结算分佣: {completed_count} 个")
        print(f"  未结算分佣: {len(commissions) - completed_count} 个")
        
        # 验证逻辑
        if delivered_count == completed_count:
            print(f"\n✅ 分佣逻辑正确: 已发货订单数量 = 已结算分佣数量")
        else:
            print(f"\n❌ 分佣逻辑错误: 已发货订单数量 ≠ 已结算分佣数量")

def test_commission_api():
    """测试分佣API"""
    print(f"\n🌐 测试分佣API")
    print("=" * 50)
    
    with app.app_context():
        # 模拟分佣API逻辑
        commissions = Commission.query.all()
        orders = []
        total_earnings = 0
        
        for commission in commissions:
            order = Order.query.filter_by(order_number=commission.order_id).first()
            if order:
                # 根据订单状态确定分佣状态
                if order.status == 'delivered':
                    commission_status = 'completed'
                    commission_status_text = '已结算'
                    total_earnings += commission.amount
                else:
                    commission_status = 'pending'
                    commission_status_text = '未结算'
                
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
        
        print(f"API返回数据:")
        print(f"  总收益: ¥{total_earnings:.2f}")
        print(f"  订单数量: {len(orders)}")
        
        for order in orders:
            print(f"  订单 {order['orderId']}: {order['commissionStatusText']} (¥{order['commissionAmount']:.2f})")

def main():
    """主函数"""
    print("🚀 验证分佣修复结果")
    print("=" * 60)
    
    verify_commission_fix()
    test_commission_api()
    
    print("\n🎉 验证完成")

if __name__ == '__main__':
    main()
