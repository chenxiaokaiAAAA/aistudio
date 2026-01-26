#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为加盟商账户表添加厂家ID配置字段
"""

import os
import sys

# 设置输出编码
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sqlite3

def add_franchisee_printer_fields():
    """为加盟商账户表添加厂家ID配置字段"""
    
    print("=" * 80)
    print("为加盟商账户表添加厂家ID配置字段")
    print("=" * 80)
    
    # 查找数据库文件
    db_paths = [
        'instance/pet_painting.db',
        'pet_painting.db',
        'moeart_paintings.db'
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("错误: 找不到数据库文件")
        return False
    
    print(f"使用数据库: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(franchisee_accounts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # 添加 printer_shop_id 字段
        if 'printer_shop_id' not in columns:
            print("\n1. 添加 printer_shop_id 字段...")
            cursor.execute("""
                ALTER TABLE franchisee_accounts 
                ADD COLUMN printer_shop_id VARCHAR(50)
            """)
            conn.commit()
            print("   成功: printer_shop_id 字段添加成功")
        else:
            print("\n1. printer_shop_id 字段已存在，跳过")
        
        # 添加 printer_shop_name 字段
        if 'printer_shop_name' not in columns:
            print("\n2. 添加 printer_shop_name 字段...")
            cursor.execute("""
                ALTER TABLE franchisee_accounts 
                ADD COLUMN printer_shop_name VARCHAR(100)
            """)
            conn.commit()
            print("   成功: printer_shop_name 字段添加成功")
        else:
            print("\n2. printer_shop_name 字段已存在，跳过")
        
        conn.close()
        
        print("\n" + "=" * 80)
        print("字段添加完成！")
        print("=" * 80)
        print("\n说明：")
        print("- printer_shop_id: 加盟商在厂家系统中的影楼编号")
        print("- printer_shop_name: 加盟商在厂家系统中的影楼名称")
        print("- 如果这两个字段为空，将使用 printer_config.py 中的默认配置")
        print("\n使用方法：")
        print("1. 在加盟商管理页面编辑加盟商信息")
        print("2. 填写厂家ID和厂家名称")
        print("3. 该加盟商的订单将使用其专属的厂家ID发送")
        
        return True
        
    except Exception as e:
        print(f"\n错误: 添加字段失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    add_franchisee_printer_fields()

