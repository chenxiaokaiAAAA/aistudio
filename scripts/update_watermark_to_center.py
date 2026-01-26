#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新现有订单的水印为居中模式
"""

import os
import sys
from PIL import Image

def update_watermark_to_center():
    """将现有订单的水印更新为居中模式"""
    filename = "final_6614a788-bc13-42de-8bcd-4e253c6a0cc5_ComfyUI_02470_.png"
    
    print("更新水印为居中模式")
    print("=" * 50)
    
    # 文件路径
    final_path = os.path.join('final_works', filename)
    clean_path = os.path.join('final_works', f'clean_{filename}')
    watermark_path = os.path.join('static/images/shuiyin', 'logo.png')
    
    print(f"原图路径: {clean_path}")
    print(f"水印路径: {watermark_path}")
    print(f"输出路径: {final_path}")
    
    # 检查文件
    if not os.path.exists(clean_path):
        print("❌ 原图不存在")
        return False
    
    if not os.path.exists(watermark_path):
        print("❌ 水印文件不存在")
        return False
    
    try:
        # 导入水印函数
        from test_server import add_watermark_to_image
        
        # 使用居中平铺模式重新添加水印
        print("使用居中平铺模式重新添加水印...")
        success = add_watermark_to_image(
            clean_path,
            watermark_path,
            final_path,
            opacity=0.15,
            position='center_tiled'
        )
        
        if success:
            print("✅ 水印更新成功")
            
            # 检查输出文件
            if os.path.exists(final_path):
                file_size = os.path.getsize(final_path)
                print(f"文件大小: {file_size} bytes")
                
                # 检查图片格式
                try:
                    with Image.open(final_path) as img:
                        print(f"图片格式: {img.format}, 尺寸: {img.size}")
                        print("✅ 水印已更新为居中平铺模式")
                        return True
                except Exception as e:
                    print(f"❌ 图片格式异常: {str(e)}")
                    return False
            else:
                print(f"❌ 输出文件不存在")
                return False
        else:
            print("❌ 水印更新失败")
            return False
        
    except Exception as e:
        print(f"❌ 更新异常: {str(e)}")
        return False

def main():
    success = update_watermark_to_center()
    
    if success:
        print(f"\n✅ 水印已更新为居中平铺模式")
        print("现在水印会:")
        print("- 居中显示在图片中央")
        print("- 自适应图片大小（占图片35%面积）")
        print("- 透明度为15%，不会过于突兀")
        print("- 保持水印的宽高比")
    else:
        print(f"\n❌ 水印更新失败")

if __name__ == "__main__":
    main()
