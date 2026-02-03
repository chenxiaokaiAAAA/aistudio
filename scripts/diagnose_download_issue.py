#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
订单详情下载问题诊断脚本
检查下载封面图片失败的原因
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def diagnose_download_issue():
    """诊断下载问题"""
    print("🔍 订单详情下载问题诊断")
    print("=" * 50)
    
    # 检查配置
    upload_folder = "uploads"
    final_folder = "final_works"
    hd_folder = "hd_images"
    
    print(f"📁 检查目录结构:")
    for folder in [upload_folder, final_folder, hd_folder]:
        if os.path.exists(folder):
            file_count = len([f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))])
            print(f"  ✅ {folder}/ ({file_count} 个文件)")
        else:
            print(f"  ❌ {folder}/ (不存在)")
    
    # 检查示例文件
    print(f"\n📋 检查示例文件:")
    sample_files = []
    
    for folder in [upload_folder, final_folder, hd_folder]:
        if os.path.exists(folder):
            files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
            if files:
                sample_file = files[0]
                sample_files.append((folder, sample_file))
                print(f"  📄 {folder}/{sample_file}")
    
    # 测试URL生成
    print(f"\n🌐 测试URL生成:")
    for folder, filename in sample_files:
        # 下载URL
        download_url = f"/download/{folder.split('_')[0] if '_' in folder else folder}/{filename}"
        print(f"  下载URL: {download_url}")
        
        # 媒体URL
        media_url = f"/media/{folder.split('_')[0] if '_' in folder else folder}/{filename}"
        print(f"  媒体URL: {media_url}")
        
        # 检查文件是否存在
        file_path = os.path.join(folder, filename)
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"  ✅ 文件存在 ({file_size} bytes)")
        else:
            print(f"  ❌ 文件不存在")
        print()
    
    # 检查路由配置
    print(f"🔧 检查路由配置:")
    routes_to_check = [
        "/download/original/<filename>",
        "/download/final/<filename>", 
        "/download/hd/<filename>",
        "/media/original/<filename>",
        "/media/final/<filename>",
        "/media/hd/<filename>"
    ]
    
    for route in routes_to_check:
        print(f"  📍 {route}")
    
    # 检查nginx配置
    print(f"\n⚙️  检查nginx配置:")
    nginx_configs = [
        "nginx.conf",
        "nginx_simple.conf"
    ]
    
    for config_file in nginx_configs:
        if os.path.exists(config_file):
            print(f"  ✅ {config_file} 存在")
            # 检查uploads配置
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'location /uploads/' in content:
                    print(f"    ✅ 包含 /uploads/ 配置")
                if 'location /media/original/' in content:
                    print(f"    ✅ 包含 /media/original/ 配置")
        else:
            print(f"  ❌ {config_file} 不存在")

def test_download_urls():
    """测试下载URL"""
    print(f"\n🧪 测试下载URL:")
    
    # 模拟测试URL
    test_cases = [
        {
            "type": "原图下载",
            "url": "/download/original/test_file.jpg",
            "expected_folder": "uploads"
        },
        {
            "type": "效果图下载", 
            "url": "/download/final/test_file.jpg",
            "expected_folder": "final_works"
        },
        {
            "type": "高清图下载",
            "url": "/download/hd/test_file.jpg", 
            "expected_folder": "hd_images"
        }
    ]
    
    for test_case in test_cases:
        print(f"  🔍 {test_case['type']}: {test_case['url']}")
        print(f"    预期文件夹: {test_case['expected_folder']}")
        
        if os.path.exists(test_case['expected_folder']):
            print(f"    ✅ 文件夹存在")
        else:
            print(f"    ❌ 文件夹不存在")

def suggest_fixes():
    """建议修复方案"""
    print(f"\n💡 修复建议:")
    print("=" * 30)
    
    print("1. 检查文件路径:")
    print("   - 确认 uploads/ 目录存在")
    print("   - 确认文件确实存在于该目录")
    print("   - 检查文件名是否包含特殊字符")
    
    print("\n2. 检查权限:")
    print("   - 确认Web服务器有读取权限")
    print("   - 检查文件权限设置")
    
    print("\n3. 检查nginx配置:")
    print("   - 确认 /download/original/ 路由配置正确")
    print("   - 检查alias路径是否正确")
    
    print("\n4. 检查Flask路由:")
    print("   - 确认 @app.route('/download/original/<filename>') 存在")
    print("   - 确认函数实现完整")
    
    print("\n5. 调试步骤:")
    print("   - 在浏览器中直接访问: http://yourdomain.com/download/original/filename")
    print("   - 检查服务器日志")
    print("   - 使用浏览器开发者工具查看网络请求")

def create_test_script():
    """创建测试脚本"""
    test_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
下载功能测试脚本
"""

import requests
import os

def test_download():
    """测试下载功能"""
    base_url = "http://photogooo"  # 替换为您的域名
    
    # 测试文件（替换为实际存在的文件）
    test_files = [
        "uploads/sample_image.jpg",
        "final_works/sample_final.jpg", 
        "hd_images/sample_hd.jpg"
    ]
    
    for file_path in test_files:
        filename = os.path.basename(file_path)
        
        # 测试下载URL
        download_url = f"{base_url}/download/original/{filename}"
        print(f"测试下载: {download_url}")
        
        try:
            response = requests.get(download_url, timeout=10)
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ 下载成功 ({len(response.content)} bytes)")
            else:
                print(f"❌ 下载失败: {response.text}")
        except Exception as e:
            print(f"❌ 请求异常: {e}")
        print()

if __name__ == '__main__':
    test_download()
'''
    
    with open('test_download_fix.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print(f"\n📝 已创建测试脚本: test_download_fix.py")
    print("   运行此脚本测试下载功能")

def main():
    """主函数"""
    diagnose_download_issue()
    test_download_urls()
    suggest_fixes()
    create_test_script()
    
    print(f"\n🎯 下一步:")
    print("1. 运行 python test_download_fix.py 测试下载")
    print("2. 检查服务器日志")
    print("3. 确认文件路径和权限")
    print("4. 如果问题持续，提供具体错误信息")

if __name__ == '__main__':
    main()



