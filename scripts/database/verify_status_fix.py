#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
验证状态修复结果
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order, Commission
from datetime import datetime

def verify_status_fix():
    """验证状态修复结果"""
    print("🔍 验证状态修复结果")
    print("=" * 50)
    
    with app.app_context():
        # 检查这两个订单
        orders_to_check = ['PET17588721358357693', 'PET17588707609962622']
        
        for order_number in orders_to_check:
            order = Order.query.filter_by(order_number=order_number).first()
            if order:
                print(f"\n订单: {order_number}")
                print(f"  数据库状态: {order.status}")
                
                # 查找分佣记录
                commission = Commission.query.filter_by(order_id=order_number).first()
                if commission:
                    print(f"  分佣状态: {commission.status}")
                    print(f"  分佣金额: ¥{commission.amount}")
                else:
                    print(f"  ❌ 没有分佣记录")
                
                # 前端显示逻辑
                print(f"\n  前端显示:")
                if order.status == 'delivered':
                    print(f"    状态显示: 已发货 (蓝色)")
                    print(f"    分佣显示: 已结算")
                elif order.status == 'processing':
                    print(f"    状态显示: 处理中 (黄色)")
                    print(f"    分佣显示: 未结算")
                else:
                    print(f"    状态显示: {order.status}")
                    print(f"    分佣显示: 未结算")
            else:
                print(f"❌ 未找到订单: {order_number}")

def check_all_orders():
    """检查所有订单状态"""
    print(f"\n📊 检查所有订单状态")
    print("=" * 50)
    
    with app.app_context():
        orders = Order.query.all()
        status_count = {}
        
        for order in orders:
            status = order.status
            if status not in status_count:
                status_count[status] = 0
            status_count[status] += 1
        
        print(f"订单状态统计:")
        for status, count in status_count.items():
            print(f"  {status}: {count} 个订单")
        
        # 检查分佣状态
        commissions = Commission.query.all()
        delivered_orders = 0
        completed_commissions = 0
        
        for commission in commissions:
            order = Order.query.filter_by(order_number=commission.order_id).first()
            if order and order.status == 'delivered':
                delivered_orders += 1
            if commission.status == 'completed':
                completed_commissions += 1
        
        print(f"\n分佣统计:")
        print(f"  已发货订单: {delivered_orders} 个")
        print(f"  已结算分佣: {completed_commissions} 个")
        
        if delivered_orders == completed_commissions:
            print(f"  ✅ 分佣逻辑正确")
        else:
            print(f"  ❌ 分佣逻辑错误")

def main():
    """主函数"""
    print("🚀 验证状态修复结果")
    print("=" * 60)
    
    verify_status_fix()
    check_all_orders()
    
    print("\n🎉 验证完成")

if __name__ == '__main__':
    main()
