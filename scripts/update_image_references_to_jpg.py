#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
更新数据库中的图片路径引用：将PNG路径更新为对应的JPG路径
用于处理之前压缩时PNG被转换为JPG的情况
"""

import os
import sys
from pathlib import Path
import sqlite3

# 设置标准输出编码（Windows兼容）
if sys.platform == 'win32':
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

def find_png_jpg_pairs(directory):
    """
    查找目录中PNG和对应JPG的配对
    
    Returns:
        dict: {png_path: jpg_path} 的映射（使用URL格式，如 /static/images/products/xxx.png）
    """
    png_jpg_pairs = {}
    directory = Path(directory)
    
    if not directory.exists():
        print(f"目录不存在: {directory}")
        return png_jpg_pairs
    
    # 扫描所有PNG文件
    for png_file in directory.rglob("*.png"):
        # 检查是否有对应的JPG文件
        jpg_file = png_file.with_suffix('.jpg')
        jpeg_file = png_file.with_suffix('.jpeg')
        
        if jpg_file.exists():
            # 转换为URL格式（/static/images/products/xxx.png）
            png_url = f"/static/{png_file.relative_to(Path('static')).as_posix()}"
            jpg_url = f"/static/{jpg_file.relative_to(Path('static')).as_posix()}"
            png_jpg_pairs[png_url] = jpg_url
            print(f"找到配对: {png_url} -> {jpg_url}")
        elif jpeg_file.exists():
            png_url = f"/static/{png_file.relative_to(Path('static')).as_posix()}"
            jpeg_url = f"/static/{jpeg_file.relative_to(Path('static')).as_posix()}"
            png_jpg_pairs[png_url] = jpeg_url
            print(f"找到配对: {png_url} -> {jpeg_url}")
    
    return png_jpg_pairs

def update_database(db_path, png_jpg_pairs, dry_run=True):
    """更新数据库中的图片路径引用"""
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return 0
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    total_updated = 0
    
    # 更新 products 表
    if 'products' in tables:
        for png_url, jpg_url in png_jpg_pairs.items():
            try:
                cursor.execute("SELECT id, name, image_url FROM products WHERE image_url = ?", (png_url,))
                rows = cursor.fetchall()
                for row in rows:
                    product_id, product_name, old_url = row
                    if dry_run:
                        print(f"[预览] Product #{product_id} ({product_name}): {old_url} -> {jpg_url}")
                        total_updated += 1
                    else:
                        cursor.execute("UPDATE products SET image_url = ? WHERE id = ?", (jpg_url, product_id))
                        print(f"[更新] Product #{product_id} ({product_name}): {old_url} -> {jpg_url}")
                        total_updated += 1
            except Exception as e:
                print(f"更新products表时出错: {str(e)}")
    
    # 更新 product_images 表
    if 'product_images' in tables:
        for png_url, jpg_url in png_jpg_pairs.items():
            try:
                cursor.execute("SELECT id, product_id, image_url FROM product_images WHERE image_url = ?", (png_url,))
                rows = cursor.fetchall()
                for row in rows:
                    img_id, product_id, old_url = row
                    if dry_run:
                        print(f"[预览] ProductImage #{img_id} (Product #{product_id}): {old_url} -> {jpg_url}")
                        total_updated += 1
                    else:
                        cursor.execute("UPDATE product_images SET image_url = ? WHERE id = ?", (jpg_url, img_id))
                        print(f"[更新] ProductImage #{img_id} (Product #{product_id}): {old_url} -> {jpg_url}")
                        total_updated += 1
            except Exception as e:
                print(f"更新product_images表时出错: {str(e)}")
    
    # 更新 style_image 表（SQLAlchemy默认表名）
    style_table_name = None
    for table in tables:
        if 'style' in table.lower() and 'image' in table.lower():
            style_table_name = table
            break
    
    if style_table_name:
        for png_url, jpg_url in png_jpg_pairs.items():
            try:
                cursor.execute(f"SELECT id, name, image_url FROM {style_table_name} WHERE image_url = ?", (png_url,))
                rows = cursor.fetchall()
                for row in rows:
                    img_id, style_name, old_url = row
                    if dry_run:
                        print(f"[预览] StyleImage #{img_id} ({style_name}): {old_url} -> {jpg_url}")
                        total_updated += 1
                    else:
                        cursor.execute(f"UPDATE {style_table_name} SET image_url = ? WHERE id = ?", (jpg_url, img_id))
                        print(f"[更新] StyleImage #{img_id} ({style_name}): {old_url} -> {jpg_url}")
                        total_updated += 1
            except Exception as e:
                print(f"更新{style_table_name}表时出错: {str(e)}")
    else:
        print(f"未找到风格图片表（查找的表: {tables}）")
    
    if not dry_run and total_updated > 0:
        conn.commit()
        print(f"\n数据库已提交，共更新 {total_updated} 条记录")
    elif dry_run:
        print(f"\n预览模式：将更新 {total_updated} 条记录（未实际修改）")
    
    conn.close()
    return total_updated

def delete_png_files(png_jpg_pairs):
    """删除已转换为JPG的PNG文件"""
    deleted_count = 0
    for png_url, jpg_url in png_jpg_pairs.items():
        # 将URL转换为文件路径
        png_path = Path(png_url.lstrip('/static/'))
        full_png_path = Path('static') / png_path
        
        if full_png_path.exists():
            try:
                full_png_path.unlink()
                print(f"  已删除: {full_png_path}")
                deleted_count += 1
            except Exception as e:
                print(f"  删除失败 {full_png_path}: {str(e)}")
    return deleted_count

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='更新数据库中的图片路径引用：将PNG路径更新为JPG路径')
    parser.add_argument('--db', default=None, help='数据库文件路径（默认: 自动查找 pet_painting.db 或 instance/pet_painting.db）')
    parser.add_argument('--execute', action='store_true', help='执行更新（默认是预览模式）')
    parser.add_argument('--delete-png', action='store_true', help='更新后删除原PNG文件（仅在--execute模式下有效）')
    args = parser.parse_args()
    
    # 自动查找数据库文件
    if args.db is None:
        if os.path.exists('instance/pet_painting.db'):
            args.db = 'instance/pet_painting.db'
        elif os.path.exists('pet_painting.db'):
            args.db = 'pet_painting.db'
        else:
            print("错误: 未找到数据库文件，请使用 --db 参数指定")
            return
    
    dry_run = not args.execute
    
    print("=" * 80)
    print("更新数据库图片路径引用")
    print("=" * 80)
    print(f"模式: {'预览模式（不会实际修改）' if dry_run else '执行模式（将修改数据库）'}")
    print(f"数据库: {args.db}")
    print()
    
    # 查找PNG-JPG配对
    print("扫描图片文件...")
    print("-" * 80)
    
    products_pairs = find_png_jpg_pairs('static/images/products')
    styles_pairs = find_png_jpg_pairs('static/images/styles')
    
    all_pairs = {**products_pairs, **styles_pairs}
    
    print(f"\n找到 {len(products_pairs)} 个产品图片配对")
    print(f"找到 {len(styles_pairs)} 个风格图片配对")
    print(f"总计 {len(all_pairs)} 个配对")
    print()
    
    if not all_pairs:
        print("未找到任何PNG-JPG配对，退出。")
        return
    
    # 更新数据库
    print("更新数据库引用...")
    print("-" * 80)
    
    total_updated = update_database(args.db, all_pairs, dry_run)
    
    print()
    print("=" * 80)
    print(f"更新统计: 共 {total_updated} 条记录")
    print("=" * 80)
    
    if not dry_run and total_updated > 0:
        print("\n数据库更新成功！")
        
        # 如果指定了删除PNG，则删除原文件
        if args.delete_png:
            print("\n删除原PNG文件...")
            deleted_count = delete_png_files(all_pairs)
            print(f"\n共删除 {deleted_count} 个PNG文件")
    elif dry_run:
        print("\n这是预览模式，未实际修改数据库。")
        print("使用 --execute 参数来执行实际更新。")
        if args.delete_png:
            print("注意: --delete-png 仅在 --execute 模式下有效。")

if __name__ == '__main__':
    main()
