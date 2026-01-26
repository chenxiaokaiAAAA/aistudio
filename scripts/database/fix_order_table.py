#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def fix_order_table():
    """修复order表结构，添加加盟商相关字段"""
    db_path = os.path.join('instance', 'pet_painting.db')
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查order表结构
        cursor.execute('PRAGMA table_info("order")')
        columns = cursor.fetchall()
        print("修复前的order表结构:")
        for col in columns:
            print(f"  {col}")
        
        # 检查是否有加盟商相关字段
        has_franchisee_id = any(col[1] == 'franchisee_id' for col in columns)
        has_franchisee_deduction = any(col[1] == 'franchisee_deduction' for col in columns)
        
        if not has_franchisee_id or not has_franchisee_deduction:
            print("\n发现缺少加盟商字段，开始修复...")
            
            # 添加franchisee_id字段
            if not has_franchisee_id:
                cursor.execute('ALTER TABLE "order" ADD COLUMN franchisee_id INTEGER')
                print("✅ 添加franchisee_id字段")
            
            # 添加franchisee_deduction字段
            if not has_franchisee_deduction:
                cursor.execute('ALTER TABLE "order" ADD COLUMN franchisee_deduction FLOAT DEFAULT 0.0')
                print("✅ 添加franchisee_deduction字段")
            
            conn.commit()
            print("✅ order表结构修复完成")
        else:
            print("✅ order表结构正确，无需修复")
        
        # 验证修复结果
        cursor.execute('PRAGMA table_info("order")')
        columns = cursor.fetchall()
        print("\n修复后的order表结构:")
        for col in columns:
            print(f"  {col}")
        
        conn.close()
        
    except Exception as e:
        print(f"修复失败: {e}")

if __name__ == '__main__':
    fix_order_table()