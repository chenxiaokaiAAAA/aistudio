#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复效果图文件名中的空格问题
将旧的文件名格式（包含空格）重命名为新格式（订单号_effect_序号.扩展名）
"""

import os
import re
from flask import Flask
from test_server import app, db, Order

def fix_hd_image_filenames():
    """修复所有订单的效果图文件名"""
    with app.app_context():
        # 获取所有有hd_image的订单
        orders = Order.query.filter(Order.hd_image.isnot(None)).all()
        
        print(f"找到 {len(orders)} 个有效果图的订单")
        
        fixed_count = 0
        error_count = 0
        
        for order in orders:
            old_filename = order.hd_image
            if not old_filename:
                continue
            
            # 检查文件名是否包含空格
            if ' ' not in old_filename:
                print(f"订单 {order.order_number} 的文件名已正确: {old_filename}")
                continue
            
            # 获取文件扩展名
            file_ext = os.path.splitext(old_filename)[1] or '.png'
            file_ext = file_ext.lower()
            
            # 生成新文件名：订单号_effect_序号.扩展名
            order_number = order.order_number
            base_name = f"{order_number}_effect"
            
            # 检查是否已存在同名文件，如果存在则递增序号
            counter = 1
            new_filename = f"{base_name}_{counter:03d}{file_ext}"
            # 获取HD_FOLDER配置（默认是hd_images）
            hd_folder = app.config.get('HD_FOLDER', os.path.join(app.root_path, 'hd_images'))
            # 如果是相对路径，转换为绝对路径
            if not os.path.isabs(hd_folder):
                hd_folder = os.path.join(app.root_path, hd_folder)
            new_file_path = os.path.join(hd_folder, new_filename)
            
            # 如果文件已存在，递增序号
            while os.path.exists(new_file_path):
                counter += 1
                new_filename = f"{base_name}_{counter:03d}{file_ext}"
                new_file_path = os.path.join(hd_folder, new_filename)
            
            # 旧文件路径（同样使用hd_folder）
            old_file_path = os.path.join(hd_folder, old_filename)
            
            # 如果旧文件存在，重命名
            if os.path.exists(old_file_path):
                try:
                    os.rename(old_file_path, new_file_path)
                    order.hd_image = new_filename
                    db.session.commit()
                    print(f"✅ 订单 {order.order_number}: {old_filename} -> {new_filename}")
                    fixed_count += 1
                except Exception as e:
                    print(f"❌ 订单 {order.order_number} 重命名失败: {e}")
                    error_count += 1
            else:
                print(f"⚠️ 订单 {order.order_number} 的文件不存在: {old_file_path}")
                # 即使文件不存在，也更新数据库中的文件名
                order.hd_image = new_filename
                db.session.commit()
                fixed_count += 1
        
        print(f"\n修复完成:")
        print(f"  - 成功修复: {fixed_count} 个")
        print(f"  - 失败: {error_count} 个")

if __name__ == '__main__':
    fix_hd_image_filenames()
