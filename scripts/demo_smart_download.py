#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能打包下载功能演示
展示新的文件名生成和制作信息功能
"""

import os
import sys
from datetime import datetime

def demo_smart_filename():
    """演示智能文件名生成"""
    print("🎨 智能打包下载功能演示")
    print("=" * 50)
    
    # 示例订单数据
    examples = [
        {
            "order_number": "PET20250919123456ABCD",
            "customer_name": "张三",
            "size": "30x40cm",
            "style_name": "油画风格",
            "product_name": "AI拍照机"
        },
        {
            "order_number": "PET20250919123456EFGH", 
            "customer_name": "李四",
            "size": "20x30cm",
            "style_name": "水彩艺术风格",
            "product_name": "AI拍照机"
        },
        {
            "order_number": "PET20250919123456IJKL",
            "customer_name": "王五",
            "size": "40x50cm", 
            "style_name": "素描风格",
            "product_name": "AI拍照机"
        }
    ]
    
    print("📋 文件名生成示例:")
    print("-" * 50)
    
    for i, order in enumerate(examples, 1):
        print(f"\n示例 {i}:")
        print(f"  订单号: {order['order_number']}")
        print(f"  客户姓名: {order['customer_name']}")
        print(f"  尺寸: {order['size']}")
        print(f"  艺术风格: {order['style_name']}")
        
        # 生成智能文件名
        parts = []
        parts.append(order['order_number'])
        
        # 客户姓名（简化）
        customer_name = order['customer_name'][:2] if len(order['customer_name']) > 2 else order['customer_name']
        parts.append(customer_name)
        
        # 尺寸
        if order['size']:
            size_clean = order['size'].replace('x', 'x').replace('*', 'x').replace('×', 'x')
            parts.append(f"尺寸{size_clean}")
        
        # 艺术风格
        if order['style_name']:
            style_clean = order['style_name'].replace('风格', '').replace('艺术', '')
            if len(style_clean) > 6:
                style_clean = style_clean[:6]
            parts.append(style_clean)
        
        # 组合文件名
        filename = "_".join(parts)
        
        print(f"  📦 ZIP文件名: {filename}.zip")
        print(f"  🖼️  封面图片: {filename}_封面.jpg")
        print(f"  🖼️  附加图片: {filename}_图片2.jpg, {filename}_图片3.jpg")

def demo_production_info():
    """演示制作信息内容"""
    print("\n📄 制作信息文件内容示例:")
    print("=" * 50)
    
    sample_info = """==================================================
AI拍照机制作信息
==================================================
订单号: PET20250919123456ABCD
客户姓名: 张三
联系电话: 13800138000
订单时间: 2025-09-19 12:34:56

制作规格:
--------------------
尺寸: 30x40cm
艺术风格: 油画风格
产品类型: AI拍照机

收货地址:
--------------------
北京市朝阳区xxx街道xxx号

订单状态:
--------------------
当前状态: 待制作

图片信息:
--------------------
封面图片: test_image.jpg
图片总数: 3 张

制作说明:
--------------------
1. 请按照指定尺寸和风格进行制作
2. 确保图片质量和色彩还原度
3. 制作完成后请及时上传效果图
4. 如有疑问请联系客户确认

联系方式:
--------------------
系统: https://moeart.cc
客服: 请通过系统联系

==================================================
生成时间: 2025-09-19 12:34:56
=================================================="""
    
    print(sample_info)

def create_sample_files():
    """创建示例文件"""
    print("\n📝 创建示例文件:")
    print("=" * 30)
    
    # 创建示例制作信息文件
    sample_info = """==================================================
AI拍照机制作信息
==================================================
订单号: PET20250919123456ABCD
客户姓名: 张三
联系电话: 13800138000
订单时间: 2025-09-19 12:34:56

制作规格:
--------------------
尺寸: 30x40cm
艺术风格: 油画风格
产品类型: AI拍照机

收货地址:
--------------------
北京市朝阳区xxx街道xxx号

订单状态:
--------------------
当前状态: 待制作

图片信息:
--------------------
封面图片: test_image.jpg
图片总数: 3 张

制作说明:
--------------------
1. 请按照指定尺寸和风格进行制作
2. 确保图片质量和色彩还原度
3. 制作完成后请及时上传效果图
4. 如有疑问请联系客户确认

联系方式:
--------------------
系统: https://moeart.cc
客服: 请通过系统联系

==================================================
生成时间: 2025-09-19 12:34:56
=================================================="""
    
    with open('sample_production_info.txt', 'w', encoding='utf-8') as f:
        f.write(sample_info)
    
    print("✅ 已创建: sample_production_info.txt")
    
    # 创建示例ZIP文件结构说明
    zip_structure = """ZIP文件结构示例:
PET20250919123456ABCD_张三_尺寸30x40cm_油画.zip
├── 制作信息.txt
├── PET20250919123456ABCD_张三_尺寸30x40cm_油画_封面.jpg
├── PET20250919123456ABCD_张三_尺寸30x40cm_油画_图片2.jpg
└── PET20250919123456ABCD_张三_尺寸30x40cm_油画_图片3.jpg
"""
    
    with open('zip_structure_example.txt', 'w', encoding='utf-8') as f:
        f.write(zip_structure)
    
    print("✅ 已创建: zip_structure_example.txt")

def main():
    """主函数"""
    demo_smart_filename()
    demo_production_info()
    create_sample_files()
    
    print("\n🎯 功能总结:")
    print("=" * 30)
    print("✅ 智能文件名包含订单号、客户、尺寸、风格")
    print("✅ 自动生成详细的制作信息txt文件")
    print("✅ 图片文件重命名为有意义的名称")
    print("✅ 封面图片和附加图片分别标识")
    print("✅ 文件名自动清理特殊字符")
    print("✅ 方便制作人员识别和管理")
    
    print("\n📦 打包内容:")
    print("1. 制作信息.txt - 详细的制作说明和订单信息")
    print("2. 订单号_客户_尺寸_风格_封面.jpg - 封面图片")
    print("3. 订单号_客户_尺寸_风格_图片2.jpg - 附加图片")
    print("4. 订单号_客户_尺寸_风格_图片3.jpg - 更多图片...")
    
    print("\n🚀 使用方法:")
    print("1. 在订单详情页面点击'打包下载全部原图'")
    print("2. 系统自动生成智能命名的ZIP文件")
    print("3. 下载后解压即可看到制作信息和重命名的图片")
    print("4. 制作人员根据制作信息.txt进行制作")

if __name__ == '__main__':
    main()



