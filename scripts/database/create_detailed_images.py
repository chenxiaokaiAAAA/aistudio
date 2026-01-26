#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

def create_detailed_images():
    """为预览图创建中等质量的详细查看图片"""
    
    print("🖼️ 创建详细查看图片")
    print("=" * 50)
    
    # 输入和输出目录
    original_dir = "static/images/styles"
    compressed_dir = "static/images/styles_compressed"
    detailed_dir = "static/images/styles_detailed"
    
    # 创建详细图片目录
    os.makedirs(detailed_dir, exist_ok=True)
    
    # 查找原始图片
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp']
    original_files = []
    
    for ext in image_extensions:
        pattern = os.path.join(original_dir, ext)
        original_files.extend(glob.glob(pattern))
    
    if not original_files:
        print("❌ 未找到原始图片")
        return
    
    def process_image(input_path):
        """处理单张图片为详细版本"""
        try:
            filename = os.path.basename(input_path)
            name_without_ext = os.path.splitext(filename)[0]
            output_file = os.path.join(detailed_dir, f"{name_without_ext}.jpg")
            
            with Image.open(input_path) as img:
                # 转换为RGB
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                # 计算新的尺寸 - 比压缩版大但比原版小
                max_width = 1200  # 比压缩的750px大，但比原图小
                if img.width > max_width:
                    new_height = int(img.height * max_width / img.width)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
                # 保存为中等质量
                img.save(output_file, 'JPEG', quality=90, optimize=True)
                
                # 计算文件大小
                original_size = os.path.getsize(input_path)
                detailed_size = os.path.getsize(output_file)
                
                return {
                    'file': filename,
                    'original_size': original_size,
                    'detailed_size': detailed_size,
                    'compression_ratio': (1 - detailed_size / original_size) * 100
                }
        
        except Exception as e:
            print(f"处理失败 {input_path}: {e}")
            return None
    
    print(f"📁 处理 {len(original_files)} 张原始图片")
    print(f"🎯 详细图设置: 质量90%, 最大宽度1200px")
    print(f"📤 输出目录: {detailed_dir}")
    print()
    
    # 并发处理
    total_original_size = 0
    total_detailed_size = 0
    success_count = 0
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = []
        
        for image_file in original_files:
            future = executor.submit(process_image, image_file)
            results.append(future)
        
        print("📈 处理进度:")
        print("-" * 40)
        
        for i, future in enumerate(results):
            result = future.result()
            if result:
                print(f"{i+1:3d}/{len(results)} {result['file']:<30} "
                      f"{result['original_size']/1024:6.1f}KB → {result['detailed_size']/1024:6.1f}KB "
                      f"(-{result['compression_ratio']:.1f}%)")
                
                total_original_size += result['original_size']
                total_detailed_size += result['detailed_size']
                success_count += 1
            else:
                print(f"{i+1:3d}/{len(results)} ❌ 处理失败")
    
    # 统计结果
    print(f"\n✅ 详细图片创建完成!")
    print("=" * 35)
    print(f"📊 成功处理: {success_count}/{len(original_files)} 张")
    print(f"💾 原大小: {total_original_size/(1024*1024):.2f} MB")
    print(f"🖼️ 详细图: {total_detailed_size/(1024*1024):.2f} MB")
    print(f"📉 节省空间: {(total_original_size-total_detailed_size)/(1024*1024):.2f} MB")
    print(f"📊 压缩率: {(1-total_detailed_size/total_original_size)*100:.1f}%")
    
    return success_count, total_detailed_size

def calculate_storage_optimization():
    """计算存储空间优化效果"""
    
    print(f"\n💾 存储空间优化方案对比:")
    print("=" * 50)
    
    # 现有数据
    original_size = 230.86  # MB
    compressed_size = 8.42  # MB
    
    print(f"📊 图片存储方案对比:")
    print("-" * 30)
    print(f"方案一 - 只用压缩图:")
    print(f"  预览图: {compressed_size:.1f} MB")
    print(f"  大图: 0 MB")
    print(f"  总计: {compressed_size:.1f} MB ✅ 最小存储")
    print()
    
    print(f"方案二 - 预览+原图:")
    print(f"  预览图: {compressed_size:.1f} MB") 
    print(f"  原图: {original_size:.1f} MB")
    print(f"  总计: {original_size + compressed_size:.1f} MB ⚠️ 存储过大")
    print()
    
    print(f"🎯 推荐方案 - 预览+中等质量大图:")
    # 假设中等质量图片会比原图小约70%
    detailed_size = original_size * 0.3  # 假设压缩到30%
    total_recommended = compressed_size + detailed_size
    
    print(f"  预览图: {compressed_size:.1f} MB")
    print(f"  详细图: {detailed_size:.1f} MB")
    print(f"  总计: {total_recommended:.1f} MB ✅ 平衡方案")
    print(f"  整体压缩率: {(1-total_recommended/original_size)*100:.1f}%")

def create_usage_example():
    """创建使用示例"""
    
    example_code = '''
// 小程序端实现示例

Page({
  data: {
    // 图片列表 - 使用压缩版本作为预览
    imageList: [
      '/static/images/styles_compressed/admin_xxx.jpg',
      '/static/images/styles_compressed/admin_yyy.jpg',
      // ...
    ],
    
    // 对应的详细图片
    detailedImages: [
      '/static/images/styles_detailed/admin_xxx.jpg',
      '/static/images/styles_detailed/admin_yyy.jpg',
      // ...
    ]
  },
  
  // 点击预览图查看详细大图
  previewDetailImage(e) {
    const index = e.currentTarget.dataset.index;
    const compressedUrl = this.data.imageList[index];
    const detailedUrl = this.data.detailedImages[index];
    
    // 使用微信小程序的图片预览功能
    wx.previewImage({
      current: detailedUrl, // 当前显示的是详细图
      urls: this.data.detailedImages // 所有详细图数组
    });
  },
  
  // 长按图片保存
  saveImage(e) {
    const index = e.currentTarget.dataset.index;
    const compressedUrl = this.data.imageList[index];
    const detailedUrl = this.data.detailedImages[index];
    
    wx.showActionSheet({
      itemList: ['保存预览图', '保存详细图'],
      success: (res) => {
        const url = res.tapIndex === 0 ? compressedUrl : detailedUrl;
        
        wx.downloadFile({
          url: url,
          success: function(res) {
            if (res.statusCode === 200) {
              wx.saveImageToPhotosAlbum({
                filePath: res.tempFilePath,
                success: function() {
                  wx.showToast({
                    title: '保存成功',
                    icon: 'success'
                  });
                }
              });
            }
          }
        });
      }
    });
  }
});
'''
    
    with open('miniprogram_image_preview_example.js', 'w', encoding='utf-8') as f:
        f.write(example_code)
    
    print(f"\n📝 已生成使用示例: miniprogram_image_preview_example.js")

def main():
    print("🎯 小程序图片优化方案：预览图 + 详细大图")
    print("🎯 目标: 快速预览 + 高清查看体验")
    print()
    
    # 创建详细图片
    success_count, detailed_size = create_detailed_images()
    
    # 计算优化效果
    calculate_storage_optimization()
    
    # 创建使用示例
    create_usage_example()
    
    print(f"\n🎉 完整方案准备完毕!")
    print(f"💡 现在您可以同时获得快速加载和高质量查看体验")

if __name__ == "__main__":
    main()
