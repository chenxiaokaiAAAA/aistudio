#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
定期清理用户上传的原图
删除条件：
1. 订单创建时间超过1个月
2. 订单状态为已发货（shipped）
3. 只删除用户上传的原图（uploads文件夹），保留订单未完成的图片
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order, OrderImage

def cleanup_old_uploaded_images(dry_run=True, days=30):
    """
    清理指定天数以前已发货订单的用户上传原图
    
    Args:
        dry_run: 如果为True，只显示将要删除的文件，不实际删除
        days: 清理多少天以前的订单（默认30天）
    """
    with app.app_context():
        # 计算指定天数前的日期
        cutoff_date = datetime.now() - timedelta(days=days)
        
        print("=" * 60)
        print("开始清理用户上传的原图")
        print("=" * 60)
        print(f"清理条件：")
        print(f"  - 订单创建时间：{cutoff_date.strftime('%Y-%m-%d %H:%M:%S')} 之前（{days}天前）")
        print(f"  - 订单状态：已发货（shipped）")
        print(f"  - 清理目录：uploads/")
        print(f"模式：{'预览模式（不会实际删除）' if dry_run else '执行模式（将删除文件）'}")
        print("=" * 60)
        
        # 查询符合条件的订单
        orders = Order.query.filter(
            Order.created_at < cutoff_date,
            Order.status == 'shipped'
        ).all()
        
        print(f"\n找到 {len(orders)} 个符合条件的订单")
        
        if not orders:
            print("没有需要清理的订单")
            return
        
        # 获取uploads文件夹路径
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        upload_path = Path(upload_folder)
        
        if not upload_path.exists():
            print(f"警告：uploads文件夹不存在: {upload_path}")
            return
        
        deleted_count = 0
        not_found_count = 0
        error_count = 0
        total_size = 0
        
        print(f"\n开始处理订单图片...")
        print("-" * 60)
        
        for order in orders:
            print(f"\n订单号: {order.order_number}")
            print(f"  创建时间: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  状态: {order.status}")
            
            # 处理 Order.original_image 字段
            if order.original_image:
                image_path = upload_path / order.original_image
                if image_path.exists():
                    file_size = image_path.stat().st_size
                    total_size += file_size
                    print(f"  ✓ 找到原图: {order.original_image} ({file_size / 1024:.2f} KB)")
                    
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
                    print(f"  ⚠ 文件不存在: {order.original_image}")
            
            # 处理 OrderImage 表中的图片
            order_images = OrderImage.query.filter_by(order_id=order.id).all()
            for order_image in order_images:
                if order_image.path:
                    image_path = upload_path / order_image.path
                    if image_path.exists():
                        file_size = image_path.stat().st_size
                        total_size += file_size
                        print(f"  ✓ 找到图片: {order_image.path} ({file_size / 1024:.2f} KB)")
                        
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
                        print(f"  ⚠ 文件不存在: {order_image.path}")
        
        print("\n" + "=" * 60)
        print("清理完成统计：")
        print(f"  处理的订单数: {len(orders)}")
        print(f"  找到的文件数: {deleted_count}")
        print(f"  未找到的文件数: {not_found_count}")
        print(f"  删除失败数: {error_count}")
        print(f"  释放空间: {total_size / 1024 / 1024:.2f} MB")
        print("=" * 60)
        
        if dry_run:
            print("\n注意：这是预览模式，文件并未实际删除")
            print("要执行实际删除，请运行: python cleanup_old_uploaded_images.py --execute")
        else:
            print("\n✓ 文件已实际删除")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='清理1个月以前已发货订单的用户上传原图')
    parser.add_argument('--execute', action='store_true', help='执行实际删除（默认是预览模式）')
    parser.add_argument('--days', type=int, default=30, help='清理多少天以前的订单（默认30天）')
    
    args = parser.parse_args()
    
    cleanup_old_uploaded_images(dry_run=not args.execute, days=args.days)

