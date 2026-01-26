#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
诊断 final_works 文件夹中的文件情况
检查为什么文件没有被清理
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 设置编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order

def diagnose_final_works():
    """诊断 final_works 文件夹"""
    with app.app_context():
        final_folder = app.config.get('FINAL_FOLDER', 'final_works')
        final_path = Path(final_folder)
        
        if not final_path.exists():
            print(f"错误：final_works文件夹不存在: {final_path}")
            return
        
        print("=" * 80)
        print("诊断 final_works 文件夹")
        print("=" * 80)
        
        # 获取所有图片文件
        image_files = list(final_path.glob('*.jpg')) + list(final_path.glob('*.png')) + list(final_path.glob('*.jpeg'))
        print(f"\n总文件数: {len(image_files)}")
        
        # 统计成对的文件
        clean_files = [f for f in image_files if f.name.startswith('clean_')]
        final_files = [f for f in image_files if not f.name.startswith('clean_')]
        print(f"  - clean_ 开头的文件: {len(clean_files)}")
        print(f"  - final_ 开头的文件: {len(final_files)}")
        
        # 计算1个月前的日期
        one_month_ago = datetime.now() - timedelta(days=30)
        
        # 统计信息
        shipped_old_count = 0
        shipped_new_count = 0
        not_shipped_count = 0
        no_order_count = 0
        status_count = {}
        
        print("\n" + "-" * 80)
        print("检查文件对应的订单状态（前30个文件作为示例）:")
        print("-" * 80)
        
        for i, image_file in enumerate(image_files[:30]):
            filename = image_file.name
            file_size = image_file.stat().st_size / 1024  # KB
            
            # 尝试从文件名查找订单
            order = Order.query.filter_by(final_image=filename).first()
            
            if not order and filename.startswith('clean_'):
                original_filename = filename[6:]
                order = Order.query.filter_by(final_image=original_filename).first()
            
            if not order:
                order = Order.query.filter_by(final_image_clean=filename).first()
            
            if order:
                age_days = (datetime.now() - order.created_at).days
                is_old = order.created_at < one_month_ago
                status = order.status
                
                # 统计状态
                if status not in status_count:
                    status_count[status] = 0
                status_count[status] += 1
                
                if status == 'shipped':
                    if is_old:
                        shipped_old_count += 1
                        marker = " [符合清理条件]"
                    else:
                        shipped_new_count += 1
                        marker = " [已发货但未超过1个月]"
                else:
                    not_shipped_count += 1
                    marker = f" [状态: {status}]"
                
                print(f"\n{i+1}. {filename[:60]}... ({file_size:.1f} KB)")
                print(f"   订单号: {order.order_number}")
                print(f"   创建时间: {order.created_at.strftime('%Y-%m-%d')} ({age_days}天前)")
                print(f"   状态: {status}{marker}")
            else:
                no_order_count += 1
                print(f"\n{i+1}. {filename[:60]}... ({file_size:.1f} KB)")
                print(f"   [找不到对应订单]")
        
        print("\n" + "=" * 80)
        print("统计结果（前30个文件）:")
        print(f"  符合清理条件（已发货且超过1个月）: {shipped_old_count}")
        print(f"  已发货但未超过1个月: {shipped_new_count}")
        print(f"  订单未完成（保留）: {not_shipped_count}")
        print(f"  找不到对应订单: {no_order_count}")
        
        if status_count:
            print(f"\n订单状态分布:")
            for status, count in sorted(status_count.items()):
                print(f"  {status}: {count}")
        
        # 查询数据库中的订单统计
        print("\n" + "=" * 80)
        print("数据库订单统计:")
        all_orders = Order.query.count()
        shipped_orders = Order.query.filter_by(status='shipped').count()
        old_shipped = Order.query.filter(
            Order.status == 'shipped',
            Order.created_at < one_month_ago
        ).count()
        
        print(f"  总订单数: {all_orders}")
        print(f"  已发货订单数: {shipped_orders}")
        print(f"  超过1个月的已发货订单数: {old_shipped}")
        
        print("\n" + "=" * 80)
        print("诊断结论:")
        if old_shipped == 0:
            print("  - 数据库中没有超过1个月的已发货订单")
            print("  - 这就是为什么文件没有被清理的原因")
        else:
            print(f"  - 数据库中有 {old_shipped} 个超过1个月的已发货订单")
            print(f"  - 但只有 {shipped_old_count} 个文件在前30个示例中符合清理条件")
            print("  - 可能原因：")
            print("    1. 文件名格式不匹配（数据库中的文件名与文件系统中的文件名不一致）")
            print("    2. 文件已被删除但数据库记录还在")
            print("    3. 文件对应的订单状态不是 'shipped'")

if __name__ == '__main__':
    diagnose_final_works()

