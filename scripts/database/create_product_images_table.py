#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建产品图片表(ProductImage)的数据库迁移脚本
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, ProductImage

def create_product_images_table():
    """创建产品图片表"""
    try:
        with app.app_context():
            # 创建ProductImage表
            db.create_all()
            
            print("✅ ProductImage表创建成功")
            
            # 检查表是否创建成功
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'product_images' in tables:
                print("✅ 确认product_images表已存在")
                
                # 显示表结构
                columns = inspector.get_columns('product_images')
                print("\n📋 product_images表结构:")
                for column in columns:
                    print(f"   - {column['name']}: {column['type']}")
            else:
                print("❌ product_images表创建失败")
                
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        return False
    
    return True

def migrate_existing_images():
    """将现有产品的单张图片迁移到ProductImage表"""
    try:
        with app.app_context():
            from test_server import Product
            
            # 获取所有有图片的产品
            products_with_images = Product.query.filter(Product.image_url.isnot(None), Product.image_url != '').all()
            
            print(f"\n🔄 开始迁移现有产品图片，共{len(products_with_images)}个产品")
            
            migrated_count = 0
            for product in products_with_images:
                # 检查是否已经有ProductImage记录
                existing_images = ProductImage.query.filter_by(product_id=product.id).count()
                
                if existing_images == 0 and product.image_url:
                    # 创建ProductImage记录
                    product_image = ProductImage(
                        product_id=product.id,
                        image_url=product.image_url,
                        sort_order=0,
                        is_active=True
                    )
                    db.session.add(product_image)
                    migrated_count += 1
                    print(f"   ✅ 迁移产品 {product.name} 的图片: {product.image_url}")
            
            if migrated_count > 0:
                db.session.commit()
                print(f"\n✅ 成功迁移 {migrated_count} 个产品的图片到ProductImage表")
            else:
                print("\n📝 没有需要迁移的图片")
                
    except Exception as e:
        print(f"❌ 迁移图片失败: {e}")
        db.session.rollback()
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 开始创建产品图片表...")
    
    # 创建表
    if create_product_images_table():
        print("\n🔄 开始迁移现有图片...")
        # 迁移现有图片
        migrate_existing_images()
        
        print("\n✅ 数据库迁移完成！")
        print("\n📝 使用说明:")
        print("   1. 现在可以在后台管理页面为产品上传多张图片")
        print("   2. 小程序API会返回产品的多张图片数组")
        print("   3. 保持向后兼容，原有的单图字段仍然有效")
    else:
        print("\n❌ 数据库迁移失败！")

