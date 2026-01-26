#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
from PIL import Image
import threading
from concurrent.futures import ThreadPoolExecutor

def compress_image(input_path, output_path, quality=85, max_width=750):
    """压缩单张图片"""
    try:
        with Image.open(input_path) as img:
            # 转换为RGB (JPEG不支持透明度)
            if img.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # 计算新的尺寸
            if img.width > max_width:
                new_height = int(img.height * max_width / img.width)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # 保存压缩图片
            img.save(output_path, 'JPEG', quality=quality, optimize=True)
            
            # 返回压缩信息
            original_size = os.path.getsize(input_path)
            compressed_size = os.path.getsize(output_path)
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            return {
                'file': os.path.basename(input_path),
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': compression_ratio,
                'original_width': img.width,
                'compressed_width': img.width
            }
    
    except Exception as e:
        print(f"压缩失败 {input_path}: {e}")
        return None

def batch_compress_images():
    """批量压缩图片"""
    
    print("🧹 开始批量压缩模板图片")
    print("=" * 50)
    
    # 输入和输出目录
    input_dir = "static/images/styles"
    output_dir = "static/images/styles_compressed"
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 查找所有图片
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp']
    image_files = []
    
    for ext in image_extensions:
        pattern = os.path.join(input_dir, ext)
        image_files.extend(glob.glob(pattern))
    
    if not image_files:
        print("❌ 未找到图片文件")
        return
    
    print(f"📁 找到 {len(image_files)} 张图片")
    print(f"🎯 压缩设置: 质量85%, 最大宽度750px")
    print(f"📤 输出目录: {output_dir}")
    print()
    
    # 并发压缩
    total_original_size = 0
    total_compressed_size = 0
    success_count = 0
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = []
        
        for image_file in image_files:
            filename = os.path.basename(image_file)
            name_without_ext = os.path.splitext(filename)[0]
            output_file = os.path.join(output_dir, f"{name_without_ext}.jpg")
            
            future = executor.submit(compress_image, image_file, output_file, 85, 750)
            results.append(future)
        
        print("📈 压缩进度:")
        print("-" * 30)
        
        for i, future in enumerate(results):
            result = future.result()
            if result:
                print(f"{i+1:3d}/{len(results)} {result['file']:<25} "
                      f"{result['original_size']/1024:6.1f}KB → {result['compressed_size']/1024:6.1f}KB "
                      f"(-{result['compression_ratio']:.1f}%)")
                
                total_original_size += result['original_size']
                total_compressed_size += result['compressed_size']
                success_count += 1
            else:
                print(f"{i+1:3d}/{len(results)} ❌ 压缩失败")
    
    # 统计结果
    print(f"\n✅ 压缩完成!")
    print("=" * 25)
    print(f"📊 成功压缩: {success_count}/{len(image_files)} 张")
    print(f"💾 原大小: {total_original_size/(1024*1024):.2f} MB")
    print(f"🗜️ 压缩后: {total_compressed_size/(1024*1024):.2f} MB")
    print(f"📉 节省空间: {(total_original_size-total_compressed_size)/(1024*1024):.2f} MB")
    print(f"📊 压缩率: {(1-total_compressed_size/total_original_size)*100:.1f}%")
    
    return success_count, total_original_size, total_compressed_size

if __name__ == "__main__":
    batch_compress_images()
