#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def restore_electronic_product():
    """恢复电子档产品"""
    
    current_db = 'instance/pet_painting.db'
    backup_db = 'instance/9.29back-pet_painting.db'
    
    print("🔄 恢复电子档产品")
    print("=" * 50)
    
    try:
        # 连接数据库
        current_conn = sqlite3.connect(current_db)
        current_cursor = current_conn.cursor()
        
        backup_conn = sqlite3.connect(backup_db)
        backup_cursor = backup_conn.cursor()
        
        print("📦 开始恢复电子档产品 (ID:9)...")
        
        # 获取电子档产品信息
        backup_cursor.execute("SELECT * FROM products WHERE id = 9;")
        product_data = backup_cursor.fetchone()
        
        if product_data:
            # 插入电子档产品
            current_cursor.execute("""
                INSERT OR REPLACE INTO products 
                (id, code, name, description, image_url, is_active, sort_order, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, product_data)
            
            print(f"   ✅ 恢复产品:")
            print(f"      ID: {product_data[0]}")
            print(f"      代码: {product_data[1]}")
            print(f"      名称: {product_data[2]}")
            print(f"      描述: {product_data[3]}")
            print(f"      图片: {product_data[4]}")
            print(f"      状态: {'启用' if product_data[5] else '禁用'}")
        
        # 恢复电子档相关的产品尺寸
        backup_cursor.execute("SELECT * FROM product_sizes WHERE product_id = 9;")
        sizes_data = backup_cursor.fetchall()
        
        for size_data in sizes_data:
            current_cursor.execute("""
                INSERT OR REPLACE INTO product_sizes 
                (id, product_id, size_name, price, printer_product_id, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, size_data)
            
            print(f"   ✅ 恢复尺寸: {size_data[2]} - ¥{size_data[3]}")
        
        # 恢复电子档相关的产品图片
        backup_cursor.execute("SELECT * FROM product_images WHERE product_id = 9;")
        images_data = backup_cursor.fetchall()
        
        for image_data in images_data:
            current_cursor.execute("""
                INSERT OR REPLACE INTO product_images 
                (id, product_id, image_url, sort_order)
                VALUES (?, ?, ?, ?)
            """, image_data)
        
        print(f"   ✅ 恢复图片: {len(images_data)} 张")
        
        # 提交更改
        current_conn.commit()
        
        print(f"\n🎉 电子档产品恢复完成!")
        print(f"   ✅ 已恢复电子档产品")
        print(f"   ✅ 已恢复相关尺寸 {len(sizes_data)} 个")
        print(f"   ✅ 已恢复相关图片 {len(images_data)} 张")
        
        # 验证恢复结果
        current_cursor.execute("SELECT COUNT(*) FROM products;")
        total_products = current_cursor.fetchone()[0]
        print(f"\n📊 当前数据库产品总数: {total_products}")
        
        current_cursor.execute("SELECT id, name FROM products ORDER BY id;")
        all_products = current_cursor.fetchall()
        print(f"📦 当前产品列表:")
        for prod in all_products:
            print(f"   🎁 ID:{prod[0]} - {prod[1]}")
        
        current_conn.close()
        backup_conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 恢复失败: {e}")
        return False

def check_restoration():
    """检查恢复后的情况"""
    
    db_file = 'instance/pet_painting.db'
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        print(f"\n🔍 验证恢复结果")
        print("-" * 30)
        
        # 检查电子档产品
        cursor.execute("SELECT * FROM products WHERE code = 'photo';")
        electronic_product = cursor.fetchone()
        
        if electronic_product:
            print(f"✅ 电子档产品已恢复:")
            print(f"   ID: {electronic_product[0]}")
            print(f"   代码: {electronic_product[1]}")
            print(f"   名称: {electronic_product[2]}")
            print(f"   描述: {electronic_product[3]}")
            
            # 检查相关尺寸
            cursor.execute("SELECT size_name, price FROM product_sizes WHERE product_id = ?;", (electronic_product[0],))
            sizes = cursor.fetchall()
            print(f"   📏 尺寸规格 {len(sizes)} 个:")
            for size in sizes:
                print(f"      - {size[0]}: ¥{size[1]}")
        else:
            print("❌ 电子档产品未找到")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")

def main():
    print("🎯 恢复电子档产品")
    print("🎯 问题: 用户在数据迁移后丢失了电子档产品")
    print()
    
    # 执行恢复
    success = restore_electronic_product()
    
    if success:
        # 验证恢复结果
        check_restoration()
        
        print(f"\n🎉 恢复完成!")
        print(f"💡 现在可以访问产品配置页面查看电子档产品")
        print(f"💡 用户下单时应该能看到电子档选项了")
    else:
        print(f"\n❌ 恢复失败")

if __name__ == "__main__":
    main()
