#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加35.6x45.6cm产品配置
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, ProductSize

def add_new_size():
    """添加35.6x45.6cm产品配置"""
    
    with app.app_context():
        print("🔄 添加35.6x45.6cm产品配置...")
        
        # 检查是否已存在
        existing = ProductSize.query.filter_by(size_name='35.6x45.6cm肌理画框').first()
        if existing:
            print(f"✅ 产品配置已存在: {existing.size_name}")
            return
        
        # 创建新的产品尺寸配置
        new_size = ProductSize(
            size_name='35.6x45.6cm肌理画框',
            price=90.0,  # 你可以调整价格
            is_active=True,
            sort_order=5
        )
        
        db.session.add(new_size)
        db.session.commit()
        
        print(f"✅ 成功添加产品配置: 35.6x45.6cm肌理画框 - ¥90.0")
        
        # 显示所有配置
        print("\n📋 当前所有产品配置:")
        sizes = ProductSize.query.all()
        for s in sizes:
            print(f"ID: {s.id}, 尺寸: {s.size_name}, 价格: {s.price}")

if __name__ == "__main__":
    add_new_size()
