#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建测试订单和图片
"""

import os
import sys
import shutil
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order, OrderImage

def create_test_order():
    """创建测试订单"""
    with app.app_context():
        print("🔧 创建测试订单...")
        
        # 检查是否已有测试订单
        existing_order = Order.query.filter_by(order_number='TEST_ORDER_001').first()
        if existing_order:
            print("✅ 测试订单已存在")
            return existing_order.id
        
        # 创建测试订单
        test_order = Order(
            order_number='TEST_ORDER_001',
            customer_name='测试用户',
            customer_phone='13800138000',
            size='30x30',
            style_name='威廉国王',
            product_name='艺术钥匙扣',
            price=99.0,
            status='pending',
            source_type='miniprogram',
            shipping_info='{"receiver": "测试用户", "address": "测试地址", "remark": "测试订单"}',
            created_at=datetime.now()
        )
        
        db.session.add(test_order)
        db.session.commit()
        
        print(f"✅ 测试订单创建成功，ID: {test_order.id}")
        
        # 创建测试图片记录
        test_image = OrderImage(
            order_id=test_order.id,
            path='test_image.jpg',
            image_type='original',
            created_at=datetime.now()
        )
        
        db.session.add(test_image)
        db.session.commit()
        
        print(f"✅ 测试图片记录创建成功")
        
        # 复制一个测试图片文件
        test_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'test_image.jpg')
        if not os.path.exists(test_image_path):
            # 找一个现有的图片文件复制
            upload_dir = app.config['UPLOAD_FOLDER']
            for filename in os.listdir(upload_dir):
                if filename.endswith(('.jpg', '.jpeg', '.png')):
                    src_path = os.path.join(upload_dir, filename)
                    shutil.copy2(src_path, test_image_path)
                    print(f"✅ 复制测试图片: {filename} -> test_image.jpg")
                    break
        
        return test_order.id

if __name__ == "__main__":
    create_test_order()