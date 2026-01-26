#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复效果图文件系统中的文件名空格问题
检查实际文件系统中的文件名，找出有空格的文件并重命名
"""

import os
import re
from flask import Flask
from test_server import app, db, Order

def fix_hd_image_filesystem():
    """修复文件系统中的效果图文件名"""
    with app.app_context():
        # 获取HD_FOLDER配置
        hd_folder = app.config.get('HD_FOLDER', 'hd_images')
        # 如果是相对路径，转换为绝对路径
        if not os.path.isabs(hd_folder):
            hd_folder = os.path.join(app.root_path, hd_folder)
        
        print(f"检查文件夹: {hd_folder}")
        
        if not os.path.exists(hd_folder):
            print(f"❌ 文件夹不存在: {hd_folder}")
            return
        
        # 获取所有文件
        all_files = os.listdir(hd_folder)
        print(f"找到 {len(all_files)} 个文件")
        
        fixed_count = 0
        error_count = 0
        skipped_count = 0
        
        for filename in all_files:
            # 跳过目录
            file_path = os.path.join(hd_folder, filename)
            if os.path.isdir(file_path):
                continue
            
            # 检查文件名是否包含空格
            if ' ' not in filename:
                skipped_count += 1
                continue
            
            print(f"\n发现带空格的文件: {filename}")
            
            # 尝试从文件名中提取订单号
            # 格式可能是: PET17683107676612160 effect 002.png
            match = re.match(r'^(PET\d+)\s+effect\s+(\d+)\.(\w+)$', filename, re.IGNORECASE)
            if not match:
                # 尝试其他格式
                match = re.match(r'^(PET\d+)\s+(.+)\.(\w+)$', filename)
                if not match:
                    print(f"  ⚠️ 无法识别文件名格式，跳过: {filename}")
                    skipped_count += 1
                    continue
            
            order_number = match.group(1)
            counter_str = match.group(2) if len(match.groups()) >= 2 else '001'
            file_ext = match.group(3) if len(match.groups()) >= 3 else 'png'
            
            # 尝试解析序号
            try:
                counter = int(counter_str)
            except:
                counter = 1
            
            # 生成新文件名：订单号_effect_序号.扩展名
            new_filename = f"{order_number}_effect_{counter:03d}.{file_ext.lower()}"
            new_file_path = os.path.join(hd_folder, new_filename)
            
            # 如果新文件名已存在，递增序号
            while os.path.exists(new_file_path):
                counter += 1
                new_filename = f"{order_number}_effect_{counter:03d}.{file_ext.lower()}"
                new_file_path = os.path.join(hd_folder, new_filename)
            
            # 重命名文件
            try:
                os.rename(file_path, new_file_path)
                print(f"  ✅ 重命名: {filename} -> {new_filename}")
                
                # 更新数据库中的文件名（如果订单存在）
                order = Order.query.filter_by(order_number=order_number).first()
                if order:
                    # 检查是否当前订单的hd_image就是这个文件
                    if order.hd_image == filename or order.hd_image is None:
                        order.hd_image = new_filename
                        db.session.commit()
                        print(f"  ✅ 数据库已更新: 订单 {order_number}")
                    else:
                        print(f"  ⚠️ 数据库中的文件名不同: {order.hd_image}，未更新")
                
                fixed_count += 1
            except Exception as e:
                print(f"  ❌ 重命名失败: {e}")
                error_count += 1
        
        print(f"\n修复完成:")
        print(f"  - 成功修复: {fixed_count} 个")
        print(f"  - 失败: {error_count} 个")
        print(f"  - 跳过（无空格）: {skipped_count} 个")

if __name__ == '__main__':
    fix_hd_image_filesystem()
