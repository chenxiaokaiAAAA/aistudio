#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟订单创建，测试水印功能
"""

import os
import sys
import uuid
from datetime import datetime
from PIL import Image
import io

def create_test_image():
    """创建一个测试图片"""
    # 创建一个简单的测试图片
    img = Image.new('RGB', (1024, 1536), color='lightblue')
    
    # 添加一些文字
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    
    # 尝试使用默认字体
    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        font = ImageFont.load_default()
    
    draw.text((100, 100), "模拟订单测试", fill='black', font=font)
    draw.text((100, 200), "Simulated Order Test", fill='darkblue', font=font)
    draw.text((100, 300), f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", fill='darkgreen', font=font)
    draw.text((100, 400), "水印功能测试", fill='red', font=font)
    
    # 保存到内存
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='JPEG', quality=95)
    img_buffer.seek(0)
    
    return img_buffer

def simulate_order_creation():
    """模拟订单创建过程"""
    print("模拟订单创建过程")
    print("=" * 50)
    
    # 生成模拟订单号
    order_number = f"SIM_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    print(f"模拟订单号: {order_number}")
    
    # 创建测试图片
    test_image = create_test_image()
    original_filename = f"simulated_{uuid.uuid4().hex[:8]}.jpg"
    original_path = os.path.join('final_works', original_filename)
    
    # 保存原始图片
    with open(original_path, 'wb') as f:
        f.write(test_image.getvalue())
    
    print(f"✅ 创建测试图片: {original_path}")
    
    # 模拟上传效果图的过程
    try:
        # 导入相关函数
        from test_server import add_watermark_to_image
        from werkzeug.utils import secure_filename
        
        # 生成文件名（模拟上传过程）
        filename = secure_filename(f"final_{uuid.uuid4()}_{original_filename}")
        image_path = os.path.join('final_works', filename)
        clean_filename = f"clean_{filename}"
        clean_image_path = os.path.join('final_works', clean_filename)
        
        print(f"模拟文件名: {filename}")
        print(f"有水印版本路径: {image_path}")
        print(f"无水印版本路径: {clean_image_path}")
        
        # 1. 先保存原始无水印版本
        with open(original_path, 'rb') as src, open(clean_image_path, 'wb') as dst:
            dst.write(src.read())
        print(f"✅ 保存原始无水印版本: {clean_filename}")
        
        # 2. 再保存有水印版本
        with open(original_path, 'rb') as src, open(image_path, 'wb') as dst:
            dst.write(src.read())
        print(f"✅ 保存有水印版本: {filename}")
        
        # 3. 自动添加水印
        watermark_path = os.path.join('static/images/shuiyin', 'logo.png')
        if os.path.exists(watermark_path):
            print(f"开始为效果图添加水印: {image_path}")
            try:
                # 验证源文件完整性
                if os.path.getsize(image_path) == 0:
                    print(f"❌ 源文件为空，无法添加水印: {image_path}")
                else:
                    # 添加水印
                    success = add_watermark_to_image(image_path, watermark_path, opacity=0.25, position='tiled')
                    if success:
                        # 验证输出文件
                        if os.path.exists(image_path) and os.path.getsize(image_path) > 0:
                            print(f"✅ 水印添加成功: {filename}")
                            
                            # 检查文件大小
                            final_size = os.path.getsize(image_path)
                            clean_size = os.path.getsize(clean_image_path)
                            print(f"有水印版本大小: {final_size} bytes")
                            print(f"无水印版本大小: {clean_size} bytes")
                            
                            # 验证图片格式
                            try:
                                with Image.open(image_path) as img:
                                    print(f"✅ 有水印图片格式正常: {img.format}, 尺寸: {img.size}")
                            except Exception as e:
                                print(f"❌ 有水印图片格式异常: {str(e)}")
                            
                            try:
                                with Image.open(clean_image_path) as img:
                                    print(f"✅ 无水印图片格式正常: {img.format}, 尺寸: {img.size}")
                            except Exception as e:
                                print(f"❌ 无水印图片格式异常: {str(e)}")
                            
                        else:
                            print(f"❌ 水印处理后文件损坏，尝试重新处理")
                            # 从无水印版本重新处理
                            if os.path.exists(clean_image_path):
                                success = add_watermark_to_image(clean_image_path, watermark_path, image_path, opacity=0.25, position='tiled')
                                if success and os.path.exists(image_path) and os.path.getsize(image_path) > 0:
                                    print(f"✅ 重新处理水印成功: {filename}")
                                else:
                                    print(f"❌ 重新处理水印失败: {filename}")
                            else:
                                print(f"❌ 无水印版本不存在，无法重新处理: {clean_image_path}")
                    else:
                        print(f"❌ 水印添加失败: {filename}")
            except Exception as e:
                print(f"❌ 水印处理异常: {str(e)}")
                # 尝试从无水印版本重新处理
                try:
                    if os.path.exists(clean_image_path):
                        success = add_watermark_to_image(clean_image_path, watermark_path, image_path, opacity=0.25, position='tiled')
                        if success and os.path.exists(image_path) and os.path.getsize(image_path) > 0:
                            print(f"✅ 异常恢复后水印添加成功: {filename}")
                        else:
                            print(f"❌ 异常恢复后水印添加失败: {filename}")
                    else:
                        print(f"❌ 无水印版本不存在，无法恢复: {clean_image_path}")
                except Exception as e2:
                    print(f"❌ 异常恢复失败: {str(e2)}")
        else:
            print(f"❌ 水印文件不存在: {watermark_path}")
        
        # 4. 模拟数据库更新
        print(f"✅ 模拟订单数据库更新: {order_number}")
        print(f"效果图文件名: {filename}")
        
        return {
            'order_number': order_number,
            'filename': filename,
            'clean_filename': clean_filename,
            'image_path': image_path,
            'clean_image_path': clean_image_path
        }
        
    except Exception as e:
        print(f"❌ 模拟订单创建异常: {str(e)}")
        return None
    finally:
        # 清理原始测试文件
        if os.path.exists(original_path):
            os.remove(original_path)
            print(f"🧹 清理原始测试文件: {original_path}")

def test_watermark_access(order_info):
    """测试水印文件访问"""
    if not order_info:
        return
    
    print(f"\n测试水印文件访问")
    print("=" * 30)
    
    filename = order_info['filename']
    
    # 测试本地文件访问
    print(f"测试本地文件访问:")
    print(f"有水印版本: {order_info['image_path']}")
    print(f"无水印版本: {order_info['clean_image_path']}")
    
    for name, path in [('有水印版本', order_info['image_path']), ('无水印版本', order_info['clean_image_path'])]:
        if os.path.exists(path):
            file_size = os.path.getsize(path)
            print(f"✅ {name}存在 ({file_size} bytes)")
            
            try:
                with Image.open(path) as img:
                    print(f"✅ {name}图片格式正常: {img.format}, 尺寸: {img.size}")
            except Exception as e:
                print(f"❌ {name}图片格式异常: {str(e)}")
        else:
            print(f"❌ {name}不存在")

def main():
    # 1. 模拟订单创建
    order_info = simulate_order_creation()
    
    if order_info:
        # 2. 测试水印文件访问
        test_watermark_access(order_info)
        
        print(f"\n✅ 模拟订单创建完成")
        print(f"订单号: {order_info['order_number']}")
        print(f"效果图文件: {order_info['filename']}")
        print(f"无水印版本: {order_info['clean_filename']}")
        print("\n现在可以在后台查看这个模拟订单的水印效果")
    else:
        print(f"\n❌ 模拟订单创建失败")

if __name__ == "__main__":
    main()