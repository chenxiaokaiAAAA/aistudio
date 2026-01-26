#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def compare_products_databases():
    """对比两个数据库的产品数据"""
    
    current_db = 'instance/pet_painting.db'
    backup_db = 'instance/9.29back-pet_painting.db'
    
    print("🔍 对比数据库产品数据")
    print("=" * 60)
    
    # 检查文件是否存在
    if not os.path.exists(current_db):
        print(f"❌ 当前数据库文件不存在: {current_db}")
        return
    
    if not os.path.exists(backup_db):
        print(f"❌ 备份数据库文件不存在: {backup_db}")
        return
    
    try:
        # 连接当前数据库
        current_conn = sqlite3.connect(current_db)
        current_cursor = current_conn.cursor()
        
        # 连接备份数据库
        backup_conn = sqlite3.connect(backup_db)
        backup_cursor = backup_conn.cursor()
        
        print(f"\n📊 当前数据库 ({current_db}):")
        print("-" * 40)
        
        # 检查当前数据库产品
        current_cursor.execute("SELECT id, code, name, description FROM products ORDER BY id;")
        current_products = current_cursor.fetchall()
        
        current_dict = {}
        for product in current_products:
            product_id, code, name, desc = product
            current_dict[product_id] = {'code': code, 'name': name, 'description': desc}
            print(f"   🎁 ID:{product_id:2d} 代码:{code:20} 名称:{name}")
            if desc:
                print(f"               描述: {desc}")
        
        print(f"\n📦 总数: {len(current_products)} 个产品")
        
        print(f"\n📊 备份数据库 ({backup_db}):")
        print("-" * 40)
        
        # 检查备份数据库产品
        backup_cursor.execute("SELECT id, code, name, description FROM products ORDER BY id;")
        backup_products = backup_cursor.fetchall()
        
        backup_dict = {}
        for product in backup_products:
            product_id, code, name, desc = product
            backup_dict[product_id] = {'code': code, 'name': name, 'description': desc}
            print(f"   🎁 ID:{product_id:2d} 代码:{code:20} 名称:{name}")
            if desc:
                print(f"               描述: {desc}")
        
        print(f"\n📦 总数: {len(backup_products)} 个产品")
        
        # 对比分析
        print(f"\n🔍 对比分析:")
        print("-" * 40)
        
        # 找出缺失的产品
        missing_in_current = []
        for product_id in backup_dict:
            if product_id not in current_dict:
                missing_in_current.append(product_id)
        
        # 找出新增的产品
        new_in_current = []
        for product_id in current_dict:
            if product_id not in backup_dict:
                new_in_current.append(product_id)
        
        if missing_in_current:
            print(f"❌ 当前数据库中缺失的产品:")
            for product_id in missing_in_current:
                product = backup_dict[product_id]
                print(f"   🚫 ID:{product_id} 代码:{product['code']} 名称:{product['name']}")
                if product['description']:
                    print(f"               描述: {product['description']}")
        
        if new_in_current:
            print(f"✅ 当前数据库中的新产品:")
            for product_id in new_in_current:
                product = current_dict[product_id]
                print(f"   ➕ ID:{product_id} 代码:{product['code']} 名称:{product['name']}")
                if product['description']:
                    print(f"               描述: {product['description']}")
        
        if not missing_in_current and not new_in_current:
            print(f"✅ 产品数据完全一致")
        
        # 检查产品尺寸
        print(f"\n📏 产品尺寸对比:")
        print("-" * 20)
        
        current_cursor.execute("SELECT COUNT(*) FROM product_sizes;")
        current_sizes = current_cursor.fetchone()[0]
        
        backup_cursor.execute("SELECT COUNT(*) FROM product_sizes;")
        backup_sizes = backup_cursor.fetchone()[0]
        
        print(f"   当前数据库: {current_sizes} 个尺寸")
        print(f"   备份数据库: {backup_sizes} 个尺寸")
        
        if backup_sizes > current_sizes:
            print(f"   ❌ 当前数据库缺少 {backup_sizes - current_sizes} 个产品尺寸")
        
        current_conn.close()
        backup_conn.close()
        
        # 如果有缺失的产品，提供恢复建议
        if missing_in_current:
            print(f"\n💡 恢复建议:")
            print(f"💡 检测到缺失 {len(missing_in_current)} 个产品")
            print(f"💡 建议运行恢复脚本将这些产品重新添加到当前数据库")
        
    except Exception as e:
        print(f"❌ 对比失败: {e}")

def restore_missing_products():
    """从备份恢复缺失的产品"""
    
    current_db = 'instance/pet_painting.db'
    backup_db = 'instance/9.29back-pet_painting.db'
    
    print(f"\n🔄 恢复缺失的产品数据")
    print("=" * 50)
    
    try:
        # 连接数据库
        current_conn = sqlite3.connect(current_db)
        current_cursor = current_conn.cursor()
        
        backup_conn = sqlite3.connect(backup_db)
        backup_cursor = backup_conn.cursor()
        
        # 找出缺失的产品
        backup_cursor.execute("SELECT id FROM products ORDER BY id;")
        backup_ids = [row[0] for row in backup_cursor.fetchall()]
        
        current_cursor.execute("SELECT id FROM products ORDER BY id;")
        current_ids = [row[0] for row in current_cursor.fetchall()]
        
        missing_ids = [pid for pid in backup_ids if pid not in current_ids]
        
        if not missing_ids:
            print("✅ 无需恢复，产品数据完整")
            return
        
        print(f"📦 开始恢复 {len(missing_ids)} 个缺失的产品...")
        
        # 恢复每个缺失的产品
        for product_id in missing_ids:
            # 获取产品信息
            backup_cursor.execute("SELECT * FROM products WHERE id = ?;", (product_id,))
            product_data = backup_cursor.fetchone()
            
            if product_data:
                # 插入产品
                current_cursor.execute("""
                    INSERT OR REPLACE INTO products 
                    (id, code, name, description, image_url, is_active, sort_order, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, product_data)
                
                print(f"   ✅ 恢复产品: ID:{product_data[0]} 名称:{product_data[2]}")
        
        # 恢复相关的产品尺寸
        backup_cursor.execute("SELECT * FROM product_sizes WHERE product_id IN ({})".format(
            ','.join(['?' for _ in missing_ids])), missing_ids)
        sizes_data = backup_cursor.fetchall()
        
        for size_data in sizes_data:
            current_cursor.execute("""
                INSERT OR REPLACE INTO product_sizes 
                (id, product_id, size_name, price, printer_product_id, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, size_data)
        
        print(f"   ✅ 恢复产品尺寸: {len(sizes_data)} 个")
        
        # 恢复相关图片
        backup_cursor.execute("SELECT * FROM product_images WHERE product_id IN ({})".format(
            ','.join(['?' for _ in missing_ids])), missing_ids)
        images_data = backup_cursor.fetchall()
        
        for image_data in images_data:
            current_cursor.execute("""
                INSERT OR REPLACE INTO product_images 
                (id, product_id, image_url, sort_order)
                VALUES (?, ?, ?, ?)
            """, image_data)
        
        print(f"   ✅ 恢复产品图片: {len(images_data)} 张")
        
        current_conn.commit()
        
        print(f"🎉 恢复完成!")
        print(f"   恢复了 {len(missing_ids)} 个产品")
        print(f"   恢复了 {len(sizes_data)} 个产品尺寸")
        print(f"   恢复了 {len(images_data)} 张产品图片")
        
        current_conn.close()
        backup_conn.close()
        
    except Exception as e:
        print(f"❌ 恢复失败: {e}")

def main():
    print("🎯 产品数据对比与恢复")
    print("🎯 目标: 找出当前数据库中缺失的产品")
    print()
    
    # 对比数据库
    compare_products_databases()
    
    # 如果用户确认，执行恢复
    print(f"\n💡 如果发现缺失的产品，是否需要自动恢复？")
    print(f"💡 恢复将把备份中缺失的产品复制到当前数据库")

if __name__ == "__main__":
    main()
