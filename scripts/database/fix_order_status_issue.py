#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复订单状态问题
1. 不应该把所有订单都改成已发货
2. 分佣状态应该根据实际订单状态计算
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order, Commission, PromotionUser
from datetime import datetime

def fix_order_status_issue():
    """修复订单状态问题"""
    print("🔧 修复订单状态问题")
    print("=" * 60)
    
    with app.app_context():
        # 1. 检查所有订单状态
        print("1️⃣ 检查所有订单状态")
        print("-" * 40)
        
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
        
        # 2. 检查分佣记录状态
        print(f"\n2️⃣ 检查分佣记录状态")
        print("-" * 40)
        
        commissions = Commission.query.all()
        print(f"总分佣记录数: {len(commissions)}")
        
        commission_status_count = {}
        for commission in commissions:
            status = commission.status
            if status not in commission_status_count:
                commission_status_count[status] = 0
            commission_status_count[status] += 1
        
        print("分佣记录状态统计:")
        for status, count in commission_status_count.items():
            print(f"  {status}: {count} 个")
        
        # 3. 分析问题
        print(f"\n3️⃣ 问题分析")
        print("-" * 40)
        
        print("问题1: 自动更新服务把所有有发货信息的订单都改成了已发货")
        print("问题2: 分佣状态应该根据实际订单状态计算，而不是固定为已结算")
        
        # 4. 修复方案
        print(f"\n4️⃣ 修复方案")
        print("-" * 40)
        
        print("方案1: 修改自动更新逻辑，只更新真正已发货的订单")
        print("方案2: 分佣状态根据订单状态动态计算，不修改分佣记录")
        
        # 5. 检查特定订单
        target_order = "PET17588585922087896"
        print(f"\n5️⃣ 检查特定订单: {target_order}")
        print("-" * 40)
        
        order = Order.query.filter_by(order_number=target_order).first()
        commission = Commission.query.filter_by(order_id=target_order).first()
        
        if order and commission:
            print(f"订单状态: {order.status}")
            print(f"分佣记录状态: {commission.status}")
            print(f"发货信息: {order.shipping_info[:100] if order.shipping_info else '无'}...")
            
            # 分析发货信息
            if order.shipping_info:
                try:
                    import json
                    shipping_data = json.loads(order.shipping_info)
                    print(f"发货信息解析: {shipping_data}")
                    
                    # 判断是否真的已发货
                    has_receiver = bool(shipping_data.get('receiver'))
                    has_address = bool(shipping_data.get('address'))
                    
                    print(f"有收货人: {has_receiver}")
                    print(f"有地址: {has_address}")
                    
                    if has_receiver and has_address:
                        print("✅ 这个订单确实已发货")
                    else:
                        print("❌ 这个订单可能未真正发货")
                except:
                    print("发货信息格式异常")
            else:
                print("❌ 没有发货信息")
        
        # 6. 修复分佣状态逻辑
        print(f"\n6️⃣ 修复分佣状态逻辑")
        print("-" * 40)
        
        print("当前问题: 分佣记录状态被固定为completed")
        print("正确逻辑: 分佣状态应该根据订单状态动态计算")
        
        # 检查分佣状态计算逻辑
        if order and commission:
            if order.status in ['shipped', 'manufacturing']:
                calculated_status = 'completed'
                calculated_status_text = '已结算'
            else:
                calculated_status = 'pending'
                calculated_status_text = '待结算'
            
            print(f"订单状态: {order.status}")
            print(f"分佣记录状态: {commission.status}")
            print(f"计算得出的分佣状态: {calculated_status_text}")
            
            if commission.status != calculated_status:
                print("❌ 分佣记录状态与计算状态不一致")
                print("需要修复分佣记录状态")
            else:
                print("✅ 分佣记录状态正确")

def fix_commission_status():
    """修复分佣状态"""
    print(f"\n🔧 修复分佣状态")
    print("-" * 40)
    
    with app.app_context():
        # 获取所有分佣记录
        commissions = Commission.query.all()
        
        print(f"开始修复 {len(commissions)} 个分佣记录状态...")
        
        fixed_count = 0
        for commission in commissions:
            # 查找对应的订单
            order = Order.query.filter_by(order_number=commission.order_id).first()
            
            if order:
                # 根据订单状态计算正确的分佣状态
                if order.status in ['shipped', 'manufacturing']:
                    correct_status = 'completed'
                else:
                    correct_status = 'pending'
                
                # 如果分佣记录状态不正确，则修复
                if commission.status != correct_status:
                    old_status = commission.status
                    commission.status = correct_status
                    
                    if correct_status == 'completed' and not commission.complete_time:
                        commission.complete_time = datetime.now()
                    elif correct_status == 'pending':
                        commission.complete_time = None
                    
                    print(f"  ✅ 修复 {commission.order_id}: {old_status} → {correct_status}")
                    fixed_count += 1
                else:
                    print(f"  ✅ {commission.order_id}: 状态正确 ({correct_status})")
            else:
                print(f"  ❌ {commission.order_id}: 订单不存在")
        
        if fixed_count > 0:
            db.session.commit()
            print(f"\n✅ 成功修复 {fixed_count} 个分佣记录状态")
        else:
            print(f"\n✅ 所有分佣记录状态都已正确")

def fix_auto_update_logic():
    """修复自动更新逻辑"""
    print(f"\n🔧 修复自动更新逻辑")
    print("-" * 40)
    
    print("需要修改自动更新服务，使其:")
    print("1. 只更新真正已发货的订单")
    print("2. 不强制更新分佣记录状态")
    print("3. 分佣状态由API动态计算")
    
    # 读取当前自动更新服务文件
    service_file = "auto_status_update_service.py"
    if os.path.exists(service_file):
        with open(service_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"\n当前自动更新服务问题:")
        print("- 把所有有发货信息的订单都改成已发货")
        print("- 强制更新分佣记录状态为completed")
        
        print(f"\n需要修改为:")
        print("- 只更新真正已发货的订单")
        print("- 不修改分佣记录状态")
        print("- 分佣状态由API根据订单状态动态计算")

if __name__ == '__main__':
    fix_order_status_issue()
    fix_commission_status()
    fix_auto_update_logic()
