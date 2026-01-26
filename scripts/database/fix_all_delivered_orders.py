#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复所有已发货订单的分佣状态
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order, Commission
from datetime import datetime

def fix_all_delivered_orders():
    """修复所有已发货订单的分佣状态"""
    print("🔧 修复所有已发货订单的分佣状态")
    print("=" * 50)
    
    with app.app_context():
        # 查找所有已发货的订单
        delivered_orders = Order.query.filter_by(status='delivered').all()
        print(f"找到 {len(delivered_orders)} 个已发货订单")
        
        if not delivered_orders:
            print("❌ 没有找到已发货订单")
            return
        
        fixed_count = 0
        
        for order in delivered_orders:
            print(f"\n处理订单: {order.order_number}")
            print(f"  状态: {order.status}")
            
            # 查找分佣记录
            commission = Commission.query.filter_by(order_id=order.order_number).first()
            if commission:
                print(f"  原分佣状态: {commission.status}")
                
                # 设置为已结算
                if commission.status != 'completed':
                    commission.status = 'completed'
                    commission.complete_time = datetime.utcnow()
                    fixed_count += 1
                    print(f"  ✅ 分佣状态已更新为: {commission.status}")
                else:
                    print(f"  ✅ 分佣状态已正确: {commission.status}")
            else:
                print(f"  ⚠️  该订单没有分佣记录")
        
        if fixed_count > 0:
            db.session.commit()
            print(f"\n✅ 修复完成，共修复 {fixed_count} 个分佣记录")
        else:
            print(f"\n✅ 所有已发货订单的分佣状态都已正确")

def check_all_orders_status():
    """检查所有订单状态"""
    print(f"\n📊 检查所有订单状态")
    print("=" * 50)
    
    with app.app_context():
        # 获取所有有分佣记录的订单
        commissions = Commission.query.all()
        print(f"分佣记录总数: {len(commissions)}")
        
        status_summary = {
            'delivered': {'count': 0, 'completed': 0, 'pending': 0},
            'other': {'count': 0, 'completed': 0, 'pending': 0}
        }
        
        for commission in commissions:
            order = Order.query.filter_by(order_number=commission.order_id).first()
            if order:
                if order.status == 'delivered':
                    status_summary['delivered']['count'] += 1
                    if commission.status == 'completed':
                        status_summary['delivered']['completed'] += 1
                    else:
                        status_summary['delivered']['pending'] += 1
                else:
                    status_summary['other']['count'] += 1
                    if commission.status == 'completed':
                        status_summary['other']['completed'] += 1
                    else:
                        status_summary['other']['pending'] += 1
        
        print(f"\n统计结果:")
        print(f"已发货订单: {status_summary['delivered']['count']} 个")
        print(f"  - 已结算: {status_summary['delivered']['completed']} 个")
        print(f"  - 未结算: {status_summary['delivered']['pending']} 个")
        
        print(f"其他状态订单: {status_summary['other']['count']} 个")
        print(f"  - 已结算: {status_summary['other']['completed']} 个")
        print(f"  - 未结算: {status_summary['other']['pending']} 个")
        
        # 验证逻辑
        if status_summary['delivered']['pending'] == 0:
            print(f"\n✅ 所有已发货订单的分佣状态都已正确")
        else:
            print(f"\n❌ 还有 {status_summary['delivered']['pending']} 个已发货订单的分佣状态未结算")

def main():
    """主函数"""
    print("🚀 修复所有已发货订单的分佣状态")
    print("=" * 60)
    
    check_all_orders_status()
    fix_all_delivered_orders()
    check_all_orders_status()
    
    print("\n🎉 修复完成")

if __name__ == '__main__':
    main()
