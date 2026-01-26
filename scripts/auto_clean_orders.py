#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自动清理9月19日之前的测试订单
"""

import sqlite3
import os
from datetime import datetime, date

DATABASE_PATH = os.path.join('instance', 'pet_painting.db')

def auto_clean_orders_before_date():
    """自动清理指定日期之前的订单"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # 先查看要删除的订单
        cursor.execute('''
            SELECT id, order_number, customer_name, price, status, created_at 
            FROM "order" 
            WHERE date(created_at) < '2025-09-19'
        ''')
        
        orders_to_delete = cursor.fetchall()
        
        if not orders_to_delete:
            print("✅ 没有找到9月19日之前的订单")
            return True
        
        print(f"🗑️  自动删除 {len(orders_to_delete)} 个9月19日之前的订单...")
        
        # 获取要删除的订单ID列表
        order_ids = [str(order[0]) for order in orders_to_delete]
        order_numbers = [order[1] for order in orders_to_delete]
        
        # 删除相关的订单图片记录
        cursor.execute(f'''
            DELETE FROM order_image 
            WHERE order_id IN ({','.join(order_ids)})
        ''')
        deleted_images = cursor.rowcount
        print(f"   删除订单图片记录: {deleted_images} 条")
        
        # 删除分佣记录（使用order_number）
        placeholders = ','.join(['?' for _ in order_numbers])
        cursor.execute(f'''
            DELETE FROM commissions 
            WHERE order_id IN ({placeholders})
        ''', order_numbers)
        deleted_commissions = cursor.rowcount
        print(f"   删除分佣记录: {deleted_commissions} 条")
        
        # 删除订单记录
        cursor.execute(f'''
            DELETE FROM "order" 
            WHERE id IN ({','.join(order_ids)})
        ''')
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
        
        cursor.execute('SELECT COUNT(*) FROM "order"')
        remaining_count = cursor.fetchone()[0]
        
        print(f"\n📊 清理后剩余订单数: {remaining_count}")
        
        if remaining_count > 0:
            cursor.execute('''
                SELECT order_number, customer_name, price, status, created_at 
                FROM "order" 
                ORDER BY created_at DESC
            ''')
            
            remaining_orders = cursor.fetchall()
            print("\n📋 剩余订单:")
            print("-" * 80)
            
            for order in remaining_orders:
                order_number, customer_name, price, status, created_at = order
                print(f"   {order_number} | {customer_name} | ¥{price} | {status} | {created_at}")
        
        return remaining_count
        
    except sqlite3.Error as e:
        print(f"❌ 数据库操作失败: {e}")
        return 0
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🧹 自动清理9月19日之前的测试订单")
    print("=" * 60)
    
    if auto_clean_orders_before_date():
        check_remaining_orders()
        print("\n🎉 订单清理完成！")
    else:
        print("\n❌ 订单清理失败")
