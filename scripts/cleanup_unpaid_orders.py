#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('.')

from test_server import app, db, Order, OrderImage, Commission
from datetime import datetime, timedelta
import sqlite3

def cleanup_unpaid_orders(hours=24):
    """清理超过指定小时的未支付订单"""
    
    print(f"🧹 开始清理超过 {hours} 小时的未支付订单")
    print("=" * 50)
    
    with app.app_context():
        # 计算截止时间
        cutoff_time = datetime.now() - timedelta(hours=hours)
        print(f"📅 截止时间: {cutoff_time}")
        
        # 查找需要清理的订单
        expired_orders = Order.query.filter(
            Order.status == 'unpaid',
            Order.created_at < cutoff_time
        ).all()
        
        print(f"📋 找到 {len(expired_orders)} 个过期未支付订单")
        
        if not expired_orders:
            print("✅ 没有需要清理的过期订单")
            return
        
        # 显示即将清理的订单
        print(f"\n📝 即将清理的订单:")
        for order in expired_orders:
            print(f"  - {order.order_number} ({order.customer_name}) - {order.created_at}")
        
        # 用户确认
        confirm = input(f"\n❓ 确认删除这 {len(expired_orders)} 个过期未支付订单？(y/N): ")
        
        if confirm.lower() != 'y':
            print("❌ 用户取消清理操作")
            return
        
        deleted_count = 0
        deleted_commissions = 0
        deleted_images = 0
        
        try:
            for order in expired_orders:
                print(f"🗑️ 删除订单: {order.order_number}")
                
                # 1. 删除关联的订单图片记录
                order_images = OrderImage.query.filter_by(order_id=order.id).all()
                for img in order_images:
                    db.session.delete(img)
                    deleted_images += 1
                
                # 2. 删除推广佣金记录
                commissions = Commission.query.filter_by(order_id=order.order_number).all()
                for commission in commissions:
                    db.session.delete(commission)
                    deleted_commissions += 1
                
                # 3. 删除订单本身
                db.session.delete(order)
                deleted_count += 1
            
            # 提交所有删除操作
            db.session.commit()
            
            print(f"\n✅ 清理完成!")
            print(f"  删除订单: {deleted_count} 个")
            print(f"  删除图片记录: {deleted_images} 个")
            print(f"  删除佣金记录: {deleted_commissions} 个")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 清理过程中出错: {e}")
            return
        
        # 验证清理结果
        remaining_unpaid = Order.query.filter(
            Order.status == 'unpaid',
            Order.created_at < cutoff_time
        ).count()
        
        if remaining_unpaid == 0:
            print(f"✅ 验证通过: 没有剩余的过期未支付订单")
        else:
            print(f"⚠️ 警告: 仍有 {remaining_unpaid} 个过期未支付订单")

def show_unpaid_statistics():
    """显示未支付订单统计"""
    
    print(f"\n📊 未支付订单统计")
    print("=" * 30)
    
    with app.app_context():
        # 总未支付订单
        total_unpaid = Order.query.filter_by(status='unpaid').count()
        print(f"总未支付订单: {total_unpaid} 个")
        
        # 按时间分组统计
        now = datetime.now()
        groups = [
            ("1小时内", now - timedelta(hours=1)),
            ("24小时内", now - timedelta(hours=24)),
            ("7天内", now - timedelta(days=7)),
            ("超过7天", now - timedelta(days=365))  # 显示所有
        ]
        
        for period, start_time in groups:
            count = Order.query.filter(
                Order.status == 'unpaid',
                Order.created_at >= start_time
            ).count()
            print(f"{period}: {count} 个")

def manual_cleanup():
    """手动清理模式"""
    
    print(f"🛠️ 手动清理未支付订单")
    print("=" * 30)
    
    show_unpaid_statistics()
    
    print(f"\n🎯 清理选项:")
    print(f"1. 清理超过24小时的未支付订单")
    print(f"2. 清理超过7天的未支付订单")
    print(f"3. 清理所有未支付订单")
    print(f"4. 自定义小时数清理")
    print(f"0. 退出")
    
    choice = input("\n请选择 (0-4): ")
    
    if choice == '1':
        cleanup_unpaid_orders(24)
    elif choice == '2':
        cleanup_unpaid_orders(24 * 7)
    elif choice == '3':
        confirm_all = input("⚠️ 确认删除所有未支付订单？(y/N): ")
        if confirm_all.lower() == 'y':
            cleanup_unpaid_orders(0)  # 0小时表示删除所有
    elif choice == '4':
        try:
            hours = int(input("请输入要清理的小时数: "))
            cleanup_unpaid_orders(hours)
        except ValueError:
            print("❌ 无效的小时数")
    elif choice == '0':
        print("👋 退出清理程序")
    else:
        print("❌ 无效选择")

def create_scheduled_task():
    """创建定时任务脚本"""
    
    print(f"\n⏰ 创建定时清理任务")
    print("=" * 30)
    
    # Windows定时任务脚本
    windows_script = """@echo off
echo 开始清理过期未支付订单... %%date%% %%time%%
cd /d "C:\\new\\pet-painting-system"
python cleanup_unpaid_orders.py --auto-cleanup 24
echo 清理任务完成 %%date%% %%time%%
pause
"""
    
    script_file = "cleanup_task.bat"
    
    try:
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(windows_script)
        
        print(f"✅ 创建定时任务脚本: {script_file}")
        print(f"\n📋 使用方法:")
        print(f"1. 双击运行 {script_file}")
        print(f"2. 或在Windows任务计划程序中设置为定时执行")
        print(f"3. 建议每天凌晨执行一次")
        
    except Exception as e:
        print(f"❌ 创建脚本失败: {e}")

def main():
    print("🧹 未支付订单清理工具")
    print("=" * 60)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == '--auto-cleanup':
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
            cleanup_unpaid_orders(hours)
        elif sys.argv[1] == '--stats':
            show_unpaid_statistics()
        elif sys.argv[1] == '--create-task':
            create_scheduled_task()
        else:
            print(f"❌ 未知参数: {sys.argv[1]}")
            print(f"📖 使用方法: python cleanup_unpaid_orders.py [--auto-cleanup <hours>|--stats|--create-task]")
    else:
        # 交互式模式
        manual_cleanup()

if __name__ == "__main__":
    main()
