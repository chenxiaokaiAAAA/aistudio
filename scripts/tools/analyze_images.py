#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob

def analyze_template_images():
    """分析模板图片的文件大小"""
    
    print("📸 模板图片大小分析")
    print("=" * 50)
    
    # 查找样式图片目录
    styles_dir = "static/images/styles"
    if not os.path.exists(styles_dir):
        print(f"❌ 目录不存在: {styles_dir}")
        return
    
    # 支持的图片格式
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp']
    
    all_images = []
    total_size = 0
    
    for ext in image_extensions:
        pattern = os.path.join(styles_dir, ext)
        images = glob.glob(pattern)
        images.extend(glob.glob(os.path.join(styles_dir, ext.upper())))
        
        for image_path in images:
            if os.path.isfile(image_path):
                file_size = os.path.getsize(image_path)
                file_name = os.path.basename(image_path)
                
                all_images.append({
                    'name': file_name,
                    'size': file_size,
                    'path': image_path
                })
                total_size += file_size
    
    # 排序
    all_images.sort(key=lambda x: x['size'], reverse=True)
    
    # 显示详细信息
    print(f"📊 统计信息:")
    print(f"总图片数: {len(all_images)}")
    print(f"总大小: {total_size / (1024 * 1024):.2f} MB")
    print(f"平均大小: {total_size / len(all_images) / 1024:.1f} KB")
    print(f"最大文件: {all_images[0]['size'] / 1024:.1f} KB")
    print(f"最小文件: {all_images[-1]['size'] / 1024:.1f} KB")
    
    print(f"\n📋 详细列表:")
    print("-" * 50)
    
    for i, img in enumerate(all_images[:20]):  # 显示前20个
        size_kb = img['size'] / 1024
        print(f"{i+1:2d}. {img['name']:<30} {size_kb:6.1f} KB")
    
    if len(all_images) > 20:
        print(f"... (还有 {len(all_images) - 20} 个文件)")
    
    # 大小分布统计
    print(f"\n📈 大小分布:")
    print("-" * 30)
    
    ranges = [
        (0, 50, "小文件 (0-50KB)"),
        (50, 100, "中小文件 (50-100KB)"),
        (100, 200, "中文件 (100-200KB)"),
        (200, 500, "大文件 (200-500KB)"),
        (500, 1000, "很大文件 (500KB-1MB)"),
        (1000, float('inf'), "超大文件 (>1MB)")
    ]
    
    for min_kb, max_kb, label in ranges:
        count = sum(1 for img in all_images 
                   if min_kb <= img['size'] / 1024 < max_kb)
        percentage = (count / len(all_images)) * 100 if all_images else 0
        print(f"{label:<20}: {count:3d} 个 ({percentage:5.1f}%)")
    
    return all_images, total_size

def recommend_compression_strategy():
    """推荐压缩策略"""
    
    print(f"\n🎯 压缩优化建议:")
    print("=" * 40)
    
    print(f"📱 小程序图片优化策略:")
    print(f"   🎯 目标文件大小: 30-80KB")
    print(f"   📏 尺寸建议: 750x ?px (小程序屏幕宽度)")
    print(f"   📐 比例: 建议使用 3:4 或 4:5 比例")
    print(f"   🗃️ 格式: WebP > JPEG > PNG")
    print(f"   📊 质量: JPEG 质量 75-85%")
    
    print(f"\n💡 优化建议:")
    print(f"   1. 图片尺寸缩小到750px宽度")
    print(f"   2. JPEG质量设置为80%")
    print(f"   3. 批量压缩工具推荐: TinyPNG, ImageOptim")
    print(f"   4. 使用WebP格式可再节省30-50%")
    print(f"   5. 考虑懒加载和渐进式加载")

def create_compression_script():
    """创建压缩脚本"""
    
    script_content = '''#!/usr/bin/env python3
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
                'compression_ratio': compression_ratio
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
    image_extensions = ['*.jpg', '*.jpeg', '.png', '.webp']
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

if __name__ == "__main__":
    batch_compress_images()
'''
    
    with open('batch_compile_images.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"\n📝 已生成压缩脚本: batch_compile_images.py")
    print(f"💡 使用方法: python batch_compile_images.py")

def main():
    images, total_size = analyze_template_images()
    recommend_compression_strategy()
    
    # 创建压缩脚本
    create_compression_script()
    
    print(f"\n🚀 快速开始优化:")
    print(f"1. 安装依赖: pip install Pillow")
    print(f"2. 运行压缩: python batch_compile_images.py")
    print(f"3. 检查结果: 查看 static/images/styles_compressed/")
    print(f"4. 测试效果: 在小程序中加载压缩后的图片")

if __name__ == "__main__":
    main()
