#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
压缩 static 目录中超过 1MB 的文件
"""

import os
import sys
from pathlib import Path
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("警告: PIL/Pillow 未安装，图片压缩功能将不可用")
    print("请运行: pip install Pillow")
import shutil

def get_file_size_mb(file_path):
    """获取文件大小（MB）"""
    return os.path.getsize(file_path) / (1024 * 1024)

def compress_image(input_path, output_path, quality=85, max_size_mb=1.0):
    """
    压缩图片文件（仅支持图片格式）
    
    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径
        quality: JPEG 质量（1-100）
        max_size_mb: 目标最大文件大小（MB）
    
    Returns:
        (success, original_size_mb, compressed_size_mb, compressed_file_path)
    """
    try:
        original_size = os.path.getsize(input_path)
        original_size_mb = original_size / (1024 * 1024)
        
        # 只处理图片文件
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        if not HAS_PIL:
            return False, original_size_mb, 0, None
        
        if input_path.suffix.lower() not in image_extensions:
            # 不是图片文件，跳过
            return False, original_size_mb, 0, None
        
        # 使用 PIL 压缩图片，保持原文件格式
        if input_path.suffix.lower() in image_extensions:
            with Image.open(input_path) as img:
                original_ext = input_path.suffix.lower()
                output_path_str = str(output_path)
                
                # 根据原文件格式选择压缩方式
                if original_ext in ['.png']:
                    # PNG格式：保持PNG格式，使用optimize压缩
                    # 先尝试不改变尺寸，只优化压缩
                    temp_path = output_path_str + '.tmp'
                    
                    # 尝试不同的压缩级别
                    for compress_level in range(9, 0, -1):  # 9是最小压缩，1是最大压缩
                        img.save(temp_path, 'PNG', compress_level=compress_level, optimize=True)
                        compressed_size = os.path.getsize(temp_path)
                        compressed_size_mb = compressed_size / (1024 * 1024)
                        
                        if compressed_size_mb <= max_size_mb:
                            # 压缩成功，替换原文件
                            if os.path.exists(output_path_str):
                                os.remove(output_path_str)
                            os.rename(temp_path, output_path_str)
                            return True, original_size_mb, compressed_size_mb, Path(output_path_str)
                    
                    # 如果还是太大，尝试缩小尺寸
                    # 先检查最后一次压缩的结果
                    if os.path.exists(temp_path):
                        compressed_size = os.path.getsize(temp_path)
                        compressed_size_mb = compressed_size / (1024 * 1024)
                    
                    if compressed_size_mb > max_size_mb:
                        scale = 0.9
                        while compressed_size_mb > max_size_mb and scale > 0.5:
                            new_size = (int(img.width * scale), int(img.height * scale))
                            resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
                            resized_img.save(temp_path, 'PNG', compress_level=9, optimize=True)
                            compressed_size = os.path.getsize(temp_path)
                            compressed_size_mb = compressed_size / (1024 * 1024)
                            scale -= 0.1
                        
                        if os.path.exists(output_path_str):
                            os.remove(output_path_str)
                        os.rename(temp_path, output_path_str)
                        return True, original_size_mb, compressed_size_mb, Path(output_path_str)
                    
                    # 如果所有压缩级别都试过了还是太大，使用最后一次的结果
                    if os.path.exists(temp_path):
                        if os.path.exists(output_path_str):
                            os.remove(output_path_str)
                        os.rename(temp_path, output_path_str)
                        return True, original_size_mb, compressed_size_mb, Path(output_path_str)
                    
                    # 清理临时文件
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    
                    # 如果压缩失败，返回False
                    return False, original_size_mb, 0, None
                
                elif original_ext in ['.jpg', '.jpeg']:
                    # JPG格式：保持JPG格式，调整质量
                    # 转换为 RGB 模式（如果需要）
                    if img.mode != 'RGB':
                        if img.mode in ('RGBA', 'LA', 'P'):
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            if img.mode == 'P':
                                img = img.convert('RGBA')
                            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                            img = background
                        else:
                            img = img.convert('RGB')
                    
                    # 尝试不同的质量值
                    current_quality = quality
                    while current_quality >= 50:
                        img.save(output_path_str, 'JPEG', quality=current_quality, optimize=True)
                        compressed_size = os.path.getsize(output_path_str)
                        compressed_size_mb = compressed_size / (1024 * 1024)
                        
                        if compressed_size_mb <= max_size_mb:
                            return True, original_size_mb, compressed_size_mb, Path(output_path_str)
                        
                        current_quality -= 5
                    
                    # 如果还是太大，尝试缩小尺寸
                    if compressed_size_mb > max_size_mb:
                        scale = 0.9
                        while compressed_size_mb > max_size_mb and scale > 0.5:
                            new_size = (int(img.width * scale), int(img.height * scale))
                            resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
                            resized_img.save(output_path_str, 'JPEG', quality=current_quality, optimize=True)
                            compressed_size = os.path.getsize(output_path_str)
                            compressed_size_mb = compressed_size / (1024 * 1024)
                            scale -= 0.1
                    
                    return True, original_size_mb, compressed_size_mb, Path(output_path_str)
                
                elif original_ext in ['.webp']:
                    # WebP格式：保持WebP格式
                    current_quality = quality
                    while current_quality >= 50:
                        img.save(output_path_str, 'WEBP', quality=current_quality, method=6)
                        compressed_size = os.path.getsize(output_path_str)
                        compressed_size_mb = compressed_size / (1024 * 1024)
                        
                        if compressed_size_mb <= max_size_mb:
                            return True, original_size_mb, compressed_size_mb, Path(output_path_str)
                        
                        current_quality -= 5
                    
                    # 如果还是太大，尝试缩小尺寸
                    if compressed_size_mb > max_size_mb:
                        scale = 0.9
                        while compressed_size_mb > max_size_mb and scale > 0.5:
                            new_size = (int(img.width * scale), int(img.height * scale))
                            resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
                            resized_img.save(output_path_str, 'WEBP', quality=current_quality, method=6)
                            compressed_size = os.path.getsize(output_path_str)
                            compressed_size_mb = compressed_size / (1024 * 1024)
                            scale -= 0.1
                    
                    return True, original_size_mb, compressed_size_mb, Path(output_path_str)
        else:
            # 不应该到达这里（已经在上面检查了）
            return False, original_size_mb, 0, None
            
    except Exception as e:
        print(f"  压缩失败: {str(e)}")
        return False, original_size_mb, 0, None

def find_large_files(directory, min_size_mb=1.0):
    """查找目录中超过指定大小的图片文件"""
    large_files = []
    directory_path = Path(directory)
    
    # 只处理图片文件
    image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    
    if not directory_path.exists():
        print(f"错误: 目录不存在: {directory}")
        return large_files
    
    print(f"正在扫描目录: {directory}")
    print(f"查找超过 {min_size_mb}MB 的图片文件（jpg, jpeg, png, webp）...")
    print("-" * 80)
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file
            # 只处理图片文件
            if file_path.suffix.lower() not in image_extensions:
                continue
            try:
                size_mb = get_file_size_mb(file_path)
                if size_mb > min_size_mb:
                    large_files.append((file_path, size_mb))
            except Exception as e:
                print(f"无法读取文件 {file_path}: {str(e)}")
    
    return large_files

def compress_large_files(directory='static', min_size_mb=1.0, dry_run=False):
    """
    压缩目录中超过指定大小的文件
    
    Args:
        directory: 要扫描的目录
        min_size_mb: 最小文件大小（MB），超过此大小的文件将被压缩
        dry_run: 如果为 True，只显示将要压缩的文件，不实际压缩
    """
    print("=" * 80)
    print("压缩大文件工具")
    print("=" * 80)
    print(f"目录: {directory}")
    print(f"最小文件大小: {min_size_mb}MB")
    print(f"模式: {'预览模式（不会实际压缩）' if dry_run else '执行模式（将压缩文件）'}")
    print("=" * 80)
    
    # 查找大文件
    large_files = find_large_files(directory, min_size_mb)
    
    if not large_files:
        print("\n没有找到超过指定大小的文件")
        return
    
    print(f"\n找到 {len(large_files)} 个超过 {min_size_mb}MB 的文件:")
    print("-" * 80)
    
    total_original_size = 0
    total_compressed_size = 0
    success_count = 0
    fail_count = 0
    total_files = len(large_files)
    
    for idx, (file_path, size_mb) in enumerate(sorted(large_files, key=lambda x: x[1], reverse=True), 1):
        print(f"\n[{idx}/{total_files}] 文件: {file_path}")
        print(f"  大小: {size_mb:.2f} MB")
        print(f"  进度: {idx/total_files*100:.1f}%")
        
        if dry_run:
            print(f"  [PREVIEW] 将压缩（预览模式）")
            total_original_size += size_mb
        else:
            # 创建备份
            backup_path = file_path.with_suffix(file_path.suffix + '.bak')
            try:
                shutil.copy2(file_path, backup_path)
                print(f"  [OK] 已创建备份: {backup_path.name}")
            except Exception as e:
                print(f"  [ERROR] 创建备份失败: {str(e)}")
                fail_count += 1
                continue
            
            # 压缩文件
            output_path = file_path
            success, original_size, compressed_size, compressed_file_path = compress_image(file_path, output_path)
            
            if success:
                compression_ratio = (1 - compressed_size / original_size) * 100
                print(f"  [OK] 压缩成功")
                print(f"    原始大小: {original_size:.2f} MB")
                print(f"    压缩后大小: {compressed_size:.2f} MB")
                print(f"    压缩率: {compression_ratio:.1f}%")
                
                # 如果压缩后文件更小，删除备份
                if compressed_size < original_size:
                    try:
                        backup_path.unlink()
                        print(f"  [OK] 已删除备份（压缩成功）")
                    except:
                        pass
                    total_original_size += original_size
                    total_compressed_size += compressed_size
                    success_count += 1
                else:
                    # 压缩后文件更大，恢复原文件
                    shutil.copy2(backup_path, file_path)
                    backup_path.unlink()
                    print(f"  [WARNING] 压缩后文件更大，已恢复原文件")
                    fail_count += 1
            else:
                # 压缩失败，恢复原文件
                try:
                    shutil.copy2(backup_path, file_path)
                    backup_path.unlink()
                    print(f"  [ERROR] 压缩失败，已恢复原文件")
                except:
                    pass
                fail_count += 1
    
    print("\n" + "=" * 80)
    print("压缩完成统计：")
    print(f"  处理的文件数: {len(large_files)}")
    if not dry_run:
        print(f"  成功压缩: {success_count}")
        print(f"  失败/跳过: {fail_count}")
        print(f"  原始总大小: {total_original_size:.2f} MB")
        print(f"  压缩后总大小: {total_compressed_size:.2f} MB")
        if total_original_size > 0:
            total_saved = total_original_size - total_compressed_size
            total_ratio = (1 - total_compressed_size / total_original_size) * 100
            print(f"  节省空间: {total_saved:.2f} MB ({total_ratio:.1f}%)")
            print(f"  完成进度: {success_count + fail_count}/{total_files} ({((success_count + fail_count)/total_files*100):.1f}%)")
    print("=" * 80)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='压缩 static 目录中超过 1MB 的文件')
    parser.add_argument('--directory', '-d', default='static', help='要扫描的目录（默认: static）')
    parser.add_argument('--min-size', '-s', type=float, default=1.0, help='最小文件大小（MB，默认: 1.0）')
    parser.add_argument('--execute', '-e', action='store_true', help='执行压缩（默认是预览模式）')
    
    args = parser.parse_args()
    
    compress_large_files(
        directory=args.directory,
        min_size_mb=args.min_size,
        dry_run=not args.execute
    )

