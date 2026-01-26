# -*- coding: utf-8 -*-
"""
诊断清理脚本问题
检查为什么文件没有被删除
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量避免编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'

try:
    from test_server import app, db, Order
    
    with app.app_context():
        # 计算30天前的日期
        cutoff_date = datetime.now() - timedelta(days=30)
        
        print("=" * 80)
        print("诊断清理脚本问题")
        print("=" * 80)
        print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"清理条件: 订单创建时间在 {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')} 之前")
        print(f"清理条件: 订单状态为 'shipped'")
        print("=" * 80)
        
        # 查询所有已发货的订单
        all_shipped = Order.query.filter(Order.status == 'shipped').all()
        print(f"\n数据库中总共有 {len(all_shipped)} 个已发货订单")
        
        # 查询符合条件的订单
        orders_to_clean = Order.query.filter(
            Order.created_at < cutoff_date,
            Order.status == 'shipped'
        ).all()
        
        print(f"其中 {len(orders_to_clean)} 个订单符合清理条件")
        
        if len(orders_to_clean) == 0:
            print("\n没有符合条件的订单，所以没有文件被删除")
            print("\n可能的原因：")
            print("1. 所有已发货的订单都是最近30天内创建的")
            print("2. 没有已发货的订单")
            exit(0)
        
        # 检查 final_works 文件夹
        final_path = Path('final_works')
        if not final_path.exists():
            print(f"\n错误: final_works 文件夹不存在")
            exit(1)
        
        # 统计文件
        all_files = list(final_path.glob('*.jpg')) + list(final_path.glob('*.png'))
        print(f"\nfinal_works 文件夹中有 {len(all_files)} 个文件")
        
        # 检查每个符合条件的订单对应的文件
        print("\n检查符合条件的订单对应的文件...")
        print("-" * 80)
        
        found_files = 0
        missing_files = 0
        
        for order in orders_to_clean[:10]:  # 只检查前10个
            print(f"\n订单号: {order.order_number}")
            print(f"  创建时间: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  状态: {order.status}")
            print(f"  final_image: {order.final_image or '无'}")
            print(f"  final_image_clean: {order.final_image_clean or '无'}")
            
            # 检查 final_image 文件
            if order.final_image:
                final_file = final_path / order.final_image
                if final_file.exists():
                    found_files += 1
                    print(f"  ✓ final_image 文件存在: {order.final_image}")
                else:
                    missing_files += 1
                    print(f"  ✗ final_image 文件不存在: {order.final_image}")
            
            # 检查 final_image_clean 文件
            if order.final_image_clean:
                clean_file = final_path / order.final_image_clean
                if clean_file.exists():
                    found_files += 1
                    print(f"  ✓ final_image_clean 文件存在: {order.final_image_clean}")
                else:
                    missing_files += 1
                    print(f"  ✗ final_image_clean 文件不存在: {order.final_image_clean}")
            
            # 检查 clean_{final_image} 格式的文件
            if order.final_image:
                clean_filename = f"clean_{order.final_image}"
                clean_file = final_path / clean_filename
                if clean_file.exists():
                    if not order.final_image_clean or order.final_image_clean != clean_filename:
                        found_files += 1
                        print(f"  ✓ clean_{order.final_image} 文件存在（但数据库中没有记录）")
        
        print("\n" + "=" * 80)
        print(f"检查结果: 找到 {found_files} 个应该被删除的文件，{missing_files} 个文件不存在")
        print("=" * 80)
        
        if found_files > 0:
            print("\n建议：运行清理脚本删除这些文件")
            print("命令: python cleanup_old_final_images.py --execute")
        
except Exception as e:
    print(f"错误: {str(e)}")
    import traceback
    traceback.print_exc()

