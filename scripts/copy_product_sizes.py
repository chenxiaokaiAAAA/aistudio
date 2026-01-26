#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import shutil

def copy_product_sizes_to_instance():
    """将主数据库中的ProductSize数据复制到instance数据库"""
    
    # 连接主数据库
    main_conn = sqlite3.connect('pet_painting.db')
    main_cursor = main_conn.cursor()
    
    # 连接instance数据库
    instance_conn = sqlite3.connect('instance/pet_painting.db')
    instance_cursor = instance_conn.cursor()
    
    print('=== 从主数据库读取ProductSize数据 ===')
    main_cursor.execute('SELECT id, product_id, size_name, price, printer_product_id, is_active, sort_order, created_at FROM product_sizes ORDER BY id')
    sizes = main_cursor.fetchall()
    
    print(f'找到 {len(sizes)} 条ProductSize数据')
    for size in sizes:
        print(f'ID: {size[0]}, 产品ID: {size[1]}, 尺寸: {size[2]}, 价格: {size[3]}, 冲印ID: {size[4]}')
    
    print('\n=== 复制到instance数据库 ===')
    # 清空instance数据库中的ProductSize表
    instance_cursor.execute('DELETE FROM product_sizes')
    print('清空了instance数据库中的ProductSize表')
    
    # 插入数据
    for size in sizes:
        instance_cursor.execute('''
            INSERT INTO product_sizes (id, product_id, size_name, price, printer_product_id, is_active, sort_order, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', size)
        print(f'插入: {size[2]} (¥{size[3]})')
    
    # 提交更改
    instance_conn.commit()
    print(f'\n✅ 成功复制 {len(sizes)} 条ProductSize数据到instance数据库')
    
    # 验证复制结果
    print('\n=== 验证复制结果 ===')
    instance_cursor.execute('SELECT COUNT(*) FROM product_sizes')
    count = instance_cursor.fetchone()[0]
    print(f'instance数据库中现在有 {count} 条ProductSize数据')
    
    main_conn.close()
    instance_conn.close()

if __name__ == "__main__":
    copy_product_sizes_to_instance()
