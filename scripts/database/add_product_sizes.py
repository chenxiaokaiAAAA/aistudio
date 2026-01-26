#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
添加产品尺寸配置
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Product, ProductSize

def add_product_sizes():
    with app.app_context():
        print("📦 添加产品尺寸配置...")
        
        # 获取所有产品
        products = Product.query.all()
        print(f"找到 {len(products)} 个产品")
        
        # 为每个产品添加尺寸配置
        for product in products:
            print(f"\n处理产品: {product.name}")
            
            if product.name == "梵高油画框":
                sizes = [
                    {"size_name": "30x40cm", "printer_product_id": "1", "price": 50.0},
                    {"size_name": "40x50cm", "printer_product_id": "2", "price": 80.0},
                    {"size_name": "50x70cm", "printer_product_id": "3", "price": 120.0},
                    {"size_name": "70x100cm", "printer_product_id": "4", "price": 180.0}
                ]
            elif "桌摆框" in product.name:
                sizes = [
                    {"size_name": "A4尺寸", "printer_product_id": "5", "price": 60.0},
                    {"size_name": "A3尺寸", "printer_product_id": "6", "price": 90.0},
                    {"size_name": "A2尺寸", "printer_product_id": "7", "price": 130.0}
                ]
            else:
                # 默认尺寸配置
                sizes = [
                    {"size_name": "标准尺寸", "printer_product_id": "1", "price": 50.0}
                ]
            
            # 添加尺寸配置
            for size_data in sizes:
                # 检查是否已存在
                existing = ProductSize.query.filter_by(
                    product_id=product.id,
                    printer_product_id=size_data["printer_product_id"]
                ).first()
                
                if not existing:
                    product_size = ProductSize(
                        product_id=product.id,
                        size_name=size_data["size_name"],
                        printer_product_id=size_data["printer_product_id"],
                        price=size_data["price"],
                        is_active=True,
                        sort_order=len(ProductSize.query.filter_by(product_id=product.id).all()) + 1
                    )
                    db.session.add(product_size)
                    print(f"  ✅ 添加尺寸: {size_data['size_name']} (¥{size_data['price']})")
                else:
                    print(f"  ⚠️  尺寸已存在: {size_data['size_name']}")
        
        # 提交更改
        db.session.commit()
        
        print("\n🎉 产品尺寸配置添加完成！")
        
        # 统计最终数据
        total_sizes = ProductSize.query.count()
        print(f"\n📊 最终统计:")
        print(f"  产品尺寸配置: {total_sizes} 个")
        
        # 显示所有尺寸配置
        print("\n📋 所有尺寸配置:")
        all_sizes = ProductSize.query.join(Product).all()
        for size in all_sizes:
            print(f"  {size.product.name} -> {size.size_name} (¥{size.price}) [ID:{size.printer_product_id}]")

if __name__ == "__main__":
    add_product_sizes()
