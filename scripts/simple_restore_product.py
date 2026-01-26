#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def restore_electronic_product_simple():
    """简单恢复电子档产品"""
    
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
        
        # 1. 恢复products表中的电子档产品
        print("📦 恢复电子档产品...")
        backup_cursor.execute("SELECT * FROM products WHERE id = 9;")
        product_data = backup_cursor.fetchone()
        
        if product_data:
            current_cursor.execute("""
                INSERT INTO products 
                (id, code, name, description, image_url, is_active, sort_order, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, product_data)
            print(f"   ✅ 产品恢复成功: {product_data[2]}")
        
        # 2. 恢复product_sizes表中的相关尺寸
        print("📏 恢复产品尺寸...")
        backup_cursor.execute("SELECT * FROM product_sizes WHERE product_id = 9;")
        sizes_data = backup_cursor.fetchall()
        
        for size_data in sizes_data:
            try:
                current_cursor.execute("""
                    INSERT INTO product_sizes 
                    (id, product_id, size_name, price, printer_product_id, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, size_data)
                print(f"   ✅ 尺寸恢复成功: {size_data[2]} - ¥{size_data[3]}")
            except Exception as e:
                print(f"   ⚠️ 尺寸跳过: {e}")
        
        # 3. 恢复product_images表中的相关图片
        print("📸 恢复产品图片...")
        backup_cursor.execute("SELECT * FROM product_images WHERE product_id = 9;")
        images_data = backup_cursor.fetchall()
        
        for image_data in images_data:
            try:
                current_cursor.execute("""
                    INSERT INTO product_images 
                    (id, product_id, image_url, sort_order)
                    VALUES (?, ?, ?, ?)
                """, image_data)
                print(f"   ✅ 图片恢复成功: {image_data[2]}")
            except Exception as e:
                print(f"   ⚠️ 图片跳过: {e}")
        
        # 提交事务
        current_conn.commit()
        
        print(f"\n🎉 恢复完成!")
        print(f"   ✅ 电子档产品已恢复")
        print(f"   ✅ 恢复了 {len(sizes_data)} 个产品尺寸")
        print(f"   ✅ 恢复了 {len(images_data)} 张产品图片")
        
        # 验证结果
        current_cursor.execute("SELECT id, code, name FROM products WHERE code = 'photo';")
        result = current_cursor.fetchone()
        if result:
            print(f"\n✅ 验证成功: ID:{result[0]} 代码:{result[1]} 名称:{result[2]}")
        
        current_conn.close()
        backup_conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 恢复失败: {e}")
        print(f"错误详情: {str(e)}")
        return False

def main():
    print("🎯 简单恢复电子档产品")
    print()
    
    success = restore_electronic_product_simple()
    
    if success:
        print(f"\n🎉 电子档产品恢复成功!")
        print(f"💡 请访问产品配置页面验证: http://localhost:8000/admin/sizes")
    else:
        print(f"\n❌ 恢复失败，请检查错误信息")

if __name__ == "__main__":
    main()
