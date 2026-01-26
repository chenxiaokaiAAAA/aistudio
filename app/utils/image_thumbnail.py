# -*- coding: utf-8 -*-
"""
图片缩略图生成工具
用于生成预览用的缩略图（长边1920px的JPG）
"""
import os
from PIL import Image
import sys

def generate_thumbnail(original_path, thumbnail_path=None, max_size=1920, quality=85):
    """
    生成缩略图（长边最大1920px的JPG）
    
    Args:
        original_path: 原图路径
        thumbnail_path: 缩略图保存路径（如果为None，则在原图同目录下生成，文件名加_thumb后缀）
        max_size: 最大边长（默认1920px）
        quality: JPEG质量（默认85）
    
    Returns:
        str: 缩略图路径，如果失败返回None
    """
    try:
        if not os.path.exists(original_path):
            print(f"❌ 原图文件不存在: {original_path}")
            return None
        
        # 如果没有指定缩略图路径，自动生成
        if thumbnail_path is None:
            base, ext = os.path.splitext(original_path)
            # 将扩展名改为.jpg（统一使用JPG格式）
            thumbnail_path = f"{base}_thumb.jpg"
        
        # 打开原图
        with Image.open(original_path) as img:
            # 转换为RGB（JPG不支持透明度）
            if img.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 计算新尺寸（保持宽高比，长边不超过max_size）
            width, height = img.size
            if width > max_size or height > max_size:
                if width > height:
                    new_width = max_size
                    new_height = int(height * max_size / width)
                else:
                    new_height = max_size
                    new_width = int(width * max_size / height)
                
                # 使用高质量重采样
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 确保缩略图目录存在
            thumbnail_dir = os.path.dirname(thumbnail_path)
            if thumbnail_dir and not os.path.exists(thumbnail_dir):
                os.makedirs(thumbnail_dir, exist_ok=True)
            
            # 保存缩略图
            img.save(thumbnail_path, 'JPEG', quality=quality, optimize=True)
            
            original_size = os.path.getsize(original_path)
            thumbnail_size = os.path.getsize(thumbnail_path)
            compression_ratio = (1 - thumbnail_size / original_size) * 100 if original_size > 0 else 0
            
            print(f"✅ 缩略图生成成功:")
            print(f"   原图: {original_path} ({original_size / 1024:.2f} KB)")
            print(f"   缩略图: {thumbnail_path} ({thumbnail_size / 1024:.2f} KB)")
            print(f"   压缩率: {compression_ratio:.1f}%")
            print(f"   尺寸: {img.size[0]}x{img.size[1]}")
            
            return thumbnail_path
            
    except Exception as e:
        print(f"❌ 生成缩略图失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def get_thumbnail_path(original_path):
    """
    根据原图路径获取缩略图路径
    
    Args:
        original_path: 原图路径
    
    Returns:
        str: 缩略图路径
    """
    base, ext = os.path.splitext(original_path)
    return f"{base}_thumb.jpg"


def get_original_path(thumbnail_path):
    """
    根据缩略图路径获取原图路径
    
    Args:
        thumbnail_path: 缩略图路径
    
    Returns:
        str: 原图路径
    """
    if thumbnail_path.endswith('_thumb.jpg'):
        return thumbnail_path.replace('_thumb.jpg', '')
    return thumbnail_path
