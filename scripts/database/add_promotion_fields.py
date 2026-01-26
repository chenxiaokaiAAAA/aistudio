#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
为order表添加推广码字段
"""

import sqlite3

def add_promotion_fields():
    """为order表添加推广码字段"""
    instance_path = 'instance/pet_painting.db'
    
    try:
        # 连接数据库
        conn = sqlite3.connect(instance_path)
        cursor = conn.cursor()
        
        # 检查当前字段
        cursor.execute("PRAGMA table_info('order')")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"当前order表字段: {columns}")
        
        # 添加promotion_code字段
        if 'promotion_code' not in columns:
            cursor.execute('ALTER TABLE "order" ADD COLUMN promotion_code VARCHAR(20)')
            print('✅ 添加 promotion_code 字段成功')
        else:
            print('ℹ️  promotion_code 字段已存在')
        
        # 添加referrer_user_id字段
        if 'referrer_user_id' not in columns:
            cursor.execute('ALTER TABLE "order" ADD COLUMN referrer_user_id VARCHAR(50)')
            print('✅ 添加 referrer_user_id 字段成功')
        else:
            print('ℹ️  referrer_user_id 字段已存在')
        
        # 提交更改
        conn.commit()
        
        # 验证字段是否添加成功
        cursor.execute("PRAGMA table_info('order')")
        new_columns = [column[1] for column in cursor.fetchall()]
        print(f"\n更新后order表字段: {new_columns}")
        
        conn.close()
        print('🎉 数据库表结构更新完成！')
        
    except Exception as e:
        print(f'❌ 更新失败: {e}')

if __name__ == '__main__':
    add_promotion_fields()
