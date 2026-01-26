#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
删除已转换为JPG的PNG文件
"""

import os
from pathlib import Path

def delete_pngs_with_jpg(directory):
    """删除目录中已有对应JPG的PNG文件"""
    directory = Path(directory)
    if not directory.exists():
        print(f"目录不存在: {directory}")
        return 0
    
    deleted_count = 0
    for png_file in directory.rglob("*.png"):
        jpg_file = png_file.with_suffix('.jpg')
        jpeg_file = png_file.with_suffix('.jpeg')
        
        if jpg_file.exists() or jpeg_file.exists():
            try:
                png_file.unlink()
                print(f"已删除: {png_file}")
                deleted_count += 1
            except Exception as e:
                print(f"删除失败 {png_file}: {str(e)}")
    
    return deleted_count

if __name__ == '__main__':
    print("=" * 80)
    print("删除已转换为JPG的PNG文件")
    print("=" * 80)
    
    products_deleted = delete_pngs_with_jpg('static/images/products')
    styles_deleted = delete_pngs_with_jpg('static/images/styles')
    
    print()
    print("=" * 80)
    print(f"删除统计:")
    print(f"  产品图片: {products_deleted} 个PNG文件")
    print(f"  风格图片: {styles_deleted} 个PNG文件")
    print(f"  总计: {products_deleted + styles_deleted} 个PNG文件")
    print("=" * 80)

