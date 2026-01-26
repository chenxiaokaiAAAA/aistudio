#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单的订单状态更新脚本
通过订单号更新状态，并自动更新分佣状态
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order, Commission
from datetime import datetime

def update_order_status(order_number, new_status):
    """更新订单状态"""
    print(f"🔄 更新订单状态")
    print("=" * 50)
    
    with app.app_context():
        # 查找订单
        order = Order.query.filter_by(order_number=order_number).first()
        if not order:
            print(f"❌ 未找到订单: {order_number}")
            return False
        
        print(f"订单: {order_number}")
        print(f"原状态: {order.status}")
        print(f"新状态: {new_status}")
        
        # 更新订单状态
        order.status = new_status
        if new_status == 'delivered':
            order.completed_at = datetime.utcnow()
        
        # 查找并更新分佣状态
        commission = Commission.query.filter_by(order_id=order_number).first()
        if commission:
            print(f"原分佣状态: {commission.status}")
            
            # 根据新状态更新分佣状态
            if new_status == 'delivered':
                commission.status = 'completed'
                commission.complete_time = datetime.utcnow()
            else:
                commission.status = 'pending'
                commission.complete_time = None
            
            print(f"新分佣状态: {commission.status}")
        else:
            print(f"⚠️  该订单没有分佣记录")
        
        # 提交更改
        db.session.commit()
        
        print(f"✅ 订单状态已更新为: {new_status}")
        if commission:
            print(f"✅ 分佣状态已更新为: {commission.status}")
        
        return True

def list_all_orders():
    """列出所有订单"""
    print(f"\n📋 所有订单列表")
    print("=" * 50)
    
    with app.app_context():
        orders = Order.query.all()
        print(f"总订单数: {len(orders)}")
        
        for i, order in enumerate(orders, 1):
            commission = Commission.query.filter_by(order_id=order.order_number).first()
            commission_status = commission.status if commission else "无分佣"
            
            print(f"{i:2d}. {order.order_number}")
            print(f"    状态: {order.status}")
            print(f"    分佣: {commission_status}")
            print(f"    价格: ¥{order.price}")
            print()

def main():
    """主函数"""
    print("🚀 订单状态更新工具")
    print("=" * 60)
    
    # 列出所有订单
    list_all_orders()
    
    # 交互式更新
    while True:
        print("\n" + "=" * 50)
        print("选择操作:")
        print("1. 更新订单状态")
        print("2. 列出所有订单")
        print("3. 退出")
        
        choice = input("\n请选择 (1-3): ").strip()
        
        if choice == '1':
            order_number = input("请输入订单号: ").strip()
            if not order_number:
                print("❌ 订单号不能为空")
                continue
            
            print("\n可选状态:")
            print("1. pending (待制作)")
            print("2. manufacturing (制作中)")
            print("3. completed (已完成)")
            print("4. delivered (已发货)")
            print("5. processing (处理中)")
            print("6. hd_ready (高清放大)")
            
            status_choice = input("请选择状态 (1-6): ").strip()
            status_map = {
                '1': 'pending',
                '2': 'manufacturing',
                '3': 'completed',
                '4': 'delivered',
                '5': 'processing',
                '6': 'hd_ready'
            }
            
            if status_choice in status_map:
                new_status = status_map[status_choice]
                update_order_status(order_number, new_status)
            else:
                print("❌ 无效选择")
        
        elif choice == '2':
            list_all_orders()
        
        elif choice == '3':
            print("👋 再见!")
            break
        
        else:
            print("❌ 无效选择")

if __name__ == '__main__':
    main()
