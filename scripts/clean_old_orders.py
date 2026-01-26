#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
查看和清理历史测试订单
"""

import sqlite3
import os
from datetime import datetime, date

DATABASE_PATH = os.path.join('instance', 'pet_painting.db')

def check_orders_before_date():
    """查看指定日期之前的订单"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # 查看所有订单的创建时间
        cursor.execute("""
            SELECT order_id, customer_name, total_price, status, create_time 
            FROM "order" 
            ORDER BY create_time DESC
        """)
        
        orders = cursor.fetchall()
        
        print(f"📊 数据库中的订单总数: {len(orders)}")
        print("\n📋 订单列表:")
        print("-" * 80)
        
        # 统计9月19日之前和之后的订单
        before_count = 0
        after_count = 0
        
        for order in orders:
            order_id, customer_name, total_price, status, create_time = order
            order_date = datetime.fromisoformat(create_time).date()
            
            if order_date < date(2025, 9, 19):
                before_count += 1
                print(f"🔴 {order_id} | {customer_name} | ¥{total_price} | {status} | {create_time} (9月19日前)")
            else:
                after_count += 1
                print(f"🟢 {order_id} | {customer_name} | ¥{total_price} | {status} | {create_time} (9月19日后)")
        
        print("-" * 80)
        print(f"📈 统计结果:")
        print(f"   9月19日之前的订单: {before_count} 个")
        print(f"   9月19日及之后的订单: {after_count} 个")
        
        return before_count, after_count
        
    except sqlite3.Error as e:
        print(f"❌ 数据库操作失败: {e}")
        return 0, 0
    finally:
        if conn:
            conn.close()

def clean_orders_before_date():
    """清理指定日期之前的订单"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # 先查看要删除的订单
        cursor.execute("""
            SELECT order_id, customer_name, total_price, status, create_time 
            FROM "order" 
            WHERE date(create_time) < '2025-09-19'
        """)
        
        orders_to_delete = cursor.fetchall()
        
        if not orders_to_delete:
            print("✅ 没有找到9月19日之前的订单")
            return True
        
        print(f"🗑️  准备删除 {len(orders_to_delete)} 个9月19日之前的订单:")
        print("-" * 60)
        
        for order in orders_to_delete:
            order_id, customer_name, total_price, status, create_time = order
            print(f"   {order_id} | {customer_name} | ¥{total_price} | {status} | {create_time}")
        
        print("-" * 60)
        
        # 确认删除
        confirm = input("确认删除这些订单吗？(y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ 取消删除操作")
            return False
        
        # 开始删除
        print("🔄 开始删除订单...")
        
        # 删除相关的订单图片记录
        cursor.execute("""
            DELETE FROM order_image 
            WHERE order_id IN (
                SELECT order_id FROM "order" 
                WHERE date(create_time) < '2025-09-19'
            )
        """)
        deleted_images = cursor.rowcount
        print(f"   删除订单图片记录: {deleted_images} 条")
        
        # 删除分佣记录
        cursor.execute("""
            DELETE FROM commissions 
            WHERE order_id IN (
                SELECT order_id FROM "order" 
                WHERE date(create_time) < '2025-09-19'
            )
        """)
        deleted_commissions = cursor.rowcount
        print(f"   删除分佣记录: {deleted_commissions} 条")
        
        # 删除订单记录
        cursor.execute("""
            DELETE FROM "order" 
            WHERE date(create_time) < '2025-09-19'
        """)
        deleted_orders = cursor.rowcount
        print(f"   删除订单记录: {deleted_orders} 条")
        
        conn.commit()
        
        print(f"✅ 清理完成！")
        print(f"   删除订单: {deleted_orders} 个")
        print(f"   删除图片记录: {deleted_images} 条")
        print(f"   删除分佣记录: {deleted_commissions} 条")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ 数据库操作失败: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def check_remaining_orders():
    """检查清理后剩余的订单"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM "order"
        """)
        remaining_count = cursor.fetchone()[0]
        
        print(f"\n📊 清理后剩余订单数: {remaining_count}")
        
        if remaining_count > 0:
            cursor.execute("""
                SELECT order_id, customer_name, total_price, status, create_time 
                FROM "order" 
                ORDER BY create_time DESC
                LIMIT 10
            """)
            
            remaining_orders = cursor.fetchall()
            print("\n📋 剩余订单（最近10个）:")
            print("-" * 80)
            
            for order in remaining_orders:
                order_id, customer_name, total_price, status, create_time = order
                print(f"   {order_id} | {customer_name} | ¥{total_price} | {status} | {create_time}")
        
        return remaining_count
        
    except sqlite3.Error as e:
        print(f"❌ 数据库操作失败: {e}")
        return 0
    finally:
        if conn:
            conn.close()

def main():
    """主函数"""
    print("🧹 订单数据清理工具")
    print("=" * 60)
    
    # 1. 查看当前订单情况
    print("1️⃣ 查看当前订单情况...")
    before_count, after_count = check_orders_before_date()
    
    if before_count == 0:
        print("✅ 没有需要清理的订单")
        return
    
    print(f"\n2️⃣ 准备清理 {before_count} 个9月19日之前的测试订单...")
    
    # 2. 执行清理
    if clean_orders_before_date():
        # 3. 检查清理结果
        print("\n3️⃣ 检查清理结果...")
        check_remaining_orders()
        
        print("\n🎉 订单清理完成！")
        print("💡 提示: 建议重启应用以确保数据同步")
    else:
        print("\n❌ 订单清理失败")

if __name__ == "__main__":
    main()
