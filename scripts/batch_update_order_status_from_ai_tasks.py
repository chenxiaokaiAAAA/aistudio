#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
批量更新订单状态脚本
检查所有有AI任务的订单，如果所有任务都已完成，将订单状态更新为"待选片"
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_server import app, db, Order, AITask
from datetime import datetime

def batch_update_order_status():
    """批量更新订单状态"""
    print("🔄 批量更新订单状态（基于AI任务完成情况）")
    print("=" * 60)
    
    with app.app_context():
        # 查找所有状态为"AI任务处理中"的订单
        orders_to_check = Order.query.filter(
            Order.status.in_(['ai_processing', 'retouching', 'shooting', 'processing'])
        ).all()
        
        print(f"找到 {len(orders_to_check)} 个需要检查的订单\n")
        
        updated_count = 0
        skipped_count = 0
        
        for order in orders_to_check:
            print(f"📋 检查订单: {order.order_number}")
            print(f"   当前状态: {order.status}")
            
            # 查询该订单的所有AI任务
            all_tasks = AITask.query.filter_by(order_id=order.id).all()
            
            if len(all_tasks) == 0:
                print(f"   ⚠️  该订单没有AI任务，跳过")
                skipped_count += 1
                print()
                continue
            
            print(f"   AI任务数量: {len(all_tasks)}")
            
            # 过滤掉失败和取消的任务，只统计有效任务
            valid_tasks = [t for t in all_tasks if t.status not in ['failed', 'cancelled']]
            completed_tasks = [t for t in valid_tasks if t.status == 'completed' and t.output_image_path]
            
            print(f"   有效任务数: {len(valid_tasks)}")
            print(f"   已完成任务数: {len(completed_tasks)}")
            
            # 显示任务状态详情
            for task in all_tasks:
                status_icon = "✅" if task.status == 'completed' else "⏳" if task.status == 'processing' else "❌"
                has_image = "有图" if task.output_image_path else "无图"
                print(f"      {status_icon} 任务 {task.id}: {task.status} ({has_image})")
            
            # 如果所有有效任务都已完成，更新订单状态为"待选片"
            if len(valid_tasks) > 0 and len(completed_tasks) == len(valid_tasks):
                old_status = order.status
                order.status = 'pending_selection'  # 待选片
                updated_count += 1
                print(f"   ✅ 订单状态已更新: {old_status} → pending_selection (待选片)")
            else:
                print(f"   ⏳ 订单还有未完成的任务，保持当前状态")
                skipped_count += 1
            
            print()
        
        if updated_count > 0:
            db.session.commit()
            print("=" * 60)
            print(f"✅ 批量更新完成！")
            print(f"   - 更新了 {updated_count} 个订单状态为'待选片'")
            print(f"   - 跳过了 {skipped_count} 个订单（无任务或任务未全部完成）")
        else:
            print("=" * 60)
            print(f"ℹ️  没有订单需要更新")
            print(f"   - 跳过了 {skipped_count} 个订单（无任务或任务未全部完成）")

if __name__ == '__main__':
    batch_update_order_status()
