#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
定期清理效果图（final_works文件夹）
删除条件：
1. 订单创建时间超过1个月
2. 订单状态为已发货（shipped）
3. 只删除效果图（final_works文件夹），保留订单未完成的图片
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order

def cleanup_old_final_images(dry_run=True, days=30):
    """
    清理指定天数以前已发货订单的效果图
    
    Args:
        dry_run: 如果为True，只显示将要删除的文件，不实际删除
        days: 清理多少天以前的订单（默认30天）
    """
    with app.app_context():
        # 计算指定天数前的日期
        cutoff_date = datetime.now() - timedelta(days=days)
        
        print("=" * 60)
        print("开始清理效果图（final_works文件夹）")
        print("=" * 60)
        print(f"清理条件：")
        print(f"  - 订单创建时间：{cutoff_date.strftime('%Y-%m-%d %H:%M:%S')} 之前（{days}天前）")
        print(f"  - 订单状态：已发货（shipped）")
        print(f"  - 清理目录：final_works/")
        print(f"模式：{'预览模式（不会实际删除）' if dry_run else '执行模式（将删除文件）'}")
        print("=" * 60)
        
        # 查询符合条件的订单
        # 先查询所有已发货的订单（不管时间）
        all_shipped_orders = Order.query.filter(Order.status == 'shipped').all()
        print(f"数据库中总共有 {len(all_shipped_orders)} 个已发货订单")
        
        # 再查询符合条件的订单（超过指定天数且已发货）
        orders = Order.query.filter(
            Order.created_at < cutoff_date,
            Order.status == 'shipped'
        ).all()
        
        print(f"其中 {len(orders)} 个订单符合清理条件（超过{days}天且已发货）")
        
        # 统计信息
        if len(all_shipped_orders) > 0:
            old_shipped = [o for o in all_shipped_orders if o.created_at < cutoff_date]
            new_shipped = [o for o in all_shipped_orders if o.created_at >= cutoff_date]
            print(f"  - 超过{days}天的已发货订单: {len(old_shipped)}")
            print(f"  - 未超过{days}天的已发货订单: {len(new_shipped)}")
        
        if not orders:
            print("没有需要清理的订单")
            return
        
        # 获取final_works文件夹路径
        final_folder = app.config.get('FINAL_FOLDER', 'final_works')
        final_path = Path(final_folder)
        
        if not final_path.exists():
            print(f"警告：final_works文件夹不存在: {final_path}")
            return
        
        deleted_count = 0
        not_found_count = 0
        error_count = 0
        total_size = 0
        
        print(f"\n开始处理订单效果图...")
        print("-" * 60)
        
        for order in orders:
            print(f"\n订单号: {order.order_number}")
            print(f"  创建时间: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  状态: {order.status}")
            
            # 处理 Order.final_image 字段（有水印版本）
            if order.final_image:
                image_path = final_path / order.final_image
                if image_path.exists():
                    file_size = image_path.stat().st_size
                    total_size += file_size
                    print(f"  ✓ 找到效果图（有水印）: {order.final_image} ({file_size / 1024:.2f} KB)")
                    
                    if not dry_run:
                        try:
                            image_path.unlink()
                            deleted_count += 1
                            print(f"    → 已删除")
                        except Exception as e:
                            error_count += 1
                            print(f"    ✗ 删除失败: {str(e)}")
                    else:
                        deleted_count += 1
                        print(f"    → 将删除（预览模式）")
                else:
                    not_found_count += 1
                    print(f"  ⚠ 文件不存在: {order.final_image}")
            
            # 处理 Order.final_image_clean 字段（无水印版本，如果数据库中有记录）
            if order.final_image_clean:
                clean_image_path = final_path / order.final_image_clean
                if clean_image_path.exists():
                    file_size = clean_image_path.stat().st_size
                    total_size += file_size
                    print(f"  ✓ 找到效果图（无水印，数据库记录）: {order.final_image_clean} ({file_size / 1024:.2f} KB)")
                    
                    if not dry_run:
                        try:
                            clean_image_path.unlink()
                            deleted_count += 1
                            print(f"    → 已删除")
                        except Exception as e:
                            error_count += 1
                            print(f"    ✗ 删除失败: {str(e)}")
                    else:
                        deleted_count += 1
                        print(f"    → 将删除（预览模式）")
                else:
                    not_found_count += 1
                    print(f"  ⚠ 文件不存在: {order.final_image_clean}")
            
            # 无论 final_image_clean 字段是否存在，都检查 clean_{final_image} 格式的文件
            # 这样可以确保即使数据库字段没有设置，也能删除对应的 clean_ 版本
            if order.final_image:
                clean_filename = f"clean_{order.final_image}"
                clean_image_path = final_path / clean_filename
                
                # 只有当文件存在且没有被上面的逻辑处理过时，才删除
                if clean_image_path.exists():
                    # 检查是否已经在上面处理过（通过 final_image_clean 字段）
                    already_processed = False
                    if order.final_image_clean:
                        # 如果数据库中有记录，且文件名匹配，说明已在上面处理过
                        if order.final_image_clean == clean_filename:
                            already_processed = True
                    
                    if not already_processed:
                        # 这是一个 clean_ 版本文件，但数据库中没有记录或记录不匹配，需要删除
                        file_size = clean_image_path.stat().st_size
                        total_size += file_size
                        print(f"  ✓ 找到效果图（无水印，自动检测）: {clean_filename} ({file_size / 1024:.2f} KB)")
                        
                        if not dry_run:
                            try:
                                clean_image_path.unlink()
                                deleted_count += 1
                                print(f"    → 已删除")
                            except Exception as e:
                                error_count += 1
                                print(f"    ✗ 删除失败: {str(e)}")
                        else:
                            deleted_count += 1
                            print(f"    → 将删除（预览模式）")
        
        print("\n" + "=" * 60)
        print("清理完成统计：")
        print(f"  处理的订单数: {len(orders)}")
        print(f"  找到的文件数: {deleted_count}")
        print(f"  未找到的文件数: {not_found_count}")
        print(f"  删除失败数: {error_count}")
        print(f"  释放空间: {total_size / 1024 / 1024:.2f} MB")
        print("=" * 60)
        
        # 额外诊断：检查文件夹中还有多少文件
        if final_path.exists():
            remaining_files = list(final_path.glob('*.jpg')) + list(final_path.glob('*.png')) + list(final_path.glob('*.jpeg'))
            print(f"\n诊断信息：")
            print(f"  final_works文件夹中剩余文件数: {len(remaining_files)}")
            
            # 统计成对的文件
            clean_files = [f for f in remaining_files if f.name.startswith('clean_')]
            final_files = [f for f in remaining_files if not f.name.startswith('clean_')]
            print(f"  - clean_ 开头的文件: {len(clean_files)}")
            print(f"  - final_ 开头的文件: {len(final_files)}")
            
            # 检查有多少文件找不到对应订单
            orphan_files = []
            for img_file in remaining_files[:20]:  # 只检查前20个作为示例
                filename = img_file.name
                # 尝试查找订单
                order = Order.query.filter_by(final_image=filename).first()
                if not order and filename.startswith('clean_'):
                    original_filename = filename[6:]
                    order = Order.query.filter_by(final_image=original_filename).first()
                if not order:
                    order = Order.query.filter_by(final_image_clean=filename).first()
                
                if not order:
                    orphan_files.append(filename)
            
            if orphan_files:
                print(f"  - 找不到对应订单的文件（示例，前20个）: {len(orphan_files)}")
                print(f"    示例: {', '.join(orphan_files[:5])}")
            
            print(f"\n提示：如果文件没有被删除，可能原因：")
            print(f"  1. 订单状态不是 'shipped'（已发货）")
            print(f"  2. 订单创建时间未超过 {days} 天")
            print(f"  3. 文件在数据库中找不到对应订单记录")
        
        if dry_run:
            print("\n注意：这是预览模式，文件并未实际删除")
            print("要执行实际删除，请运行: python cleanup_old_final_images.py --execute")
        else:
            print("\n✓ 文件已实际删除")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='清理1个月以前已发货订单的效果图')
    parser.add_argument('--execute', action='store_true', help='执行实际删除（默认是预览模式）')
    parser.add_argument('--days', type=int, default=30, help='清理多少天以前的订单（默认30天）')
    
    args = parser.parse_args()
    
    cleanup_old_final_images(dry_run=not args.execute, days=args.days)

