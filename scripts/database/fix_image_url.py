#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复冲印系统图片URL错误
检查并修复图片访问地址问题
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order
from printer_client import PrinterSystemClient
from printer_config import PRINTER_SYSTEM_CONFIG
import requests

def check_image_url():
    """检查图片URL可访问性"""
    print("🔍 检查图片URL可访问性...")
    
    with app.app_context():
        order_number = "PET20250917175858D53F"
        order = Order.query.filter_by(order_number=order_number).first()
        
        if not order or not order.hd_image:
            print(f"❌ 订单或高清图片不存在")
            return False
        
        print(f"📋 订单信息:")
        print(f"   - 订单号: {order.order_number}")
        print(f"   - 高清图片: {order.hd_image}")
        
        # 检查图片文件是否存在
        hd_image_path = os.path.join('hd_images', order.hd_image)
        if not os.path.exists(hd_image_path):
            print(f"❌ 图片文件不存在: {hd_image_path}")
            return False
        
        print(f"✅ 图片文件存在: {hd_image_path}")
        
        # 生成图片URL
        printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
        image_url = printer_client._get_file_url(hd_image_path)
        
        print(f"🔗 生成的图片URL: {image_url}")
        
        # 测试URL可访问性
        try:
            response = requests.get(image_url, timeout=10)
            print(f"📊 URL访问测试:")
            print(f"   - 状态码: {response.status_code}")
            print(f"   - 内容类型: {response.headers.get('content-type', 'unknown')}")
            print(f"   - 文件大小: {len(response.content)} bytes")
            
            if response.status_code == 200:
                print(f"  ✅ 图片URL可正常访问")
                return True
            else:
                print(f"  ❌ 图片URL访问失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ❌ 图片URL访问异常: {str(e)}")
            return False

def check_server_paths():
    """检查服务器路径配置"""
    print(f"\n🔍 检查服务器路径配置...")
    
    # 检查当前配置
    base_url = PRINTER_SYSTEM_CONFIG.get('file_access_base_url')
    print(f"当前基础URL: {base_url}")
    
    # 检查可能的路径
    possible_paths = [
        f"{base_url}/public/hd/",
        f"{base_url}/static/hd/",
        f"{base_url}/hd_images/",
        f"{base_url}/uploads/hd/",
        f"{base_url}/media/hd/",
    ]
    
    print(f"可能的图片路径:")
    for path in possible_paths:
        print(f"  - {path}")
    
    # 测试每个路径
    test_image = "hd_8b6230e1-840a-4e9d-9df8-f85f7866d0cf_-2.jpg"
    
    for path in possible_paths:
        test_url = f"{path}{test_image}"
        try:
            response = requests.get(test_url, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ 找到正确路径: {test_url}")
                return test_url
            else:
                print(f"  ❌ 路径不可用: {test_url} (状态码: {response.status_code})")
        except Exception as e:
            print(f"  ❌ 路径测试失败: {test_url} - {str(e)}")
    
    return None

def fix_image_url_config():
    """修复图片URL配置"""
    print(f"\n🔧 修复图片URL配置...")
    
    # 检查服务器路径
    correct_path = check_server_paths()
    
    if not correct_path:
        print(f"❌ 未找到正确的图片路径")
        return False
    
    # 提取基础URL
    base_url = correct_path.replace("/public/hd/", "").replace("/static/hd/", "").replace("/hd_images/", "").replace("/uploads/hd/", "").replace("/media/hd/", "")
    
    print(f"✅ 找到正确的基础URL: {base_url}")
    
    # 更新配置文件
    try:
        config_file = 'printer_config.py'
        
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找并替换file_access_base_url
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "'file_access_base_url':" in line:
                old_line = line
                lines[i] = f"    'file_access_base_url': '{base_url}',  # 外部可访问的文件基础URL"
                print(f"✅ 配置文件已更新:")
                print(f"   原: {old_line.strip()}")
                print(f"   新: {lines[i].strip()}")
                break
        
        # 写回文件
        new_content = '\n'.join(lines)
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ 配置文件已保存")
        return True
        
    except Exception as e:
        print(f"❌ 更新配置文件失败: {str(e)}")
        return False

def test_fixed_url():
    """测试修复后的URL"""
    print(f"\n🧪 测试修复后的URL...")
    
    # 重新导入配置
    try:
        import importlib
        import printer_config
        importlib.reload(printer_config)
        from printer_config import PRINTER_SYSTEM_CONFIG
        
        # 测试图片URL生成
        printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
        
        with app.app_context():
            order_number = "PET20250917175858D53F"
            order = Order.query.filter_by(order_number=order_number).first()
            
            if order and order.hd_image:
                hd_image_path = os.path.join('hd_images', order.hd_image)
                image_url = printer_client._get_file_url(hd_image_path)
                
                print(f"🔗 修复后的图片URL: {image_url}")
                
                # 测试访问
                try:
                    response = requests.get(image_url, timeout=10)
                    if response.status_code == 200:
                        print(f"✅ 修复后的URL可正常访问")
                        return True
                    else:
                        print(f"❌ 修复后的URL仍无法访问: {response.status_code}")
                        return False
                except Exception as e:
                    print(f"❌ 修复后的URL访问异常: {str(e)}")
                    return False
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def resend_order_with_fixed_url():
    """使用修复后的URL重新发送订单"""
    print(f"\n🚀 使用修复后的URL重新发送订单...")
    
    with app.app_context():
        order_number = "PET20250917175858D53F"
        order = Order.query.filter_by(order_number=order_number).first()
        
        if not order:
            print(f"❌ 订单 {order_number} 不存在")
            return False
        
        try:
            # 重新导入配置
            import importlib
            import printer_config
            importlib.reload(printer_config)
            from printer_config import PRINTER_SYSTEM_CONFIG
            
            # 创建冲印系统客户端
            printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
            
            # 检查高清图片文件
            hd_image_path = os.path.join('hd_images', order.hd_image)
            if not os.path.exists(hd_image_path):
                print(f"❌ 高清图片文件不存在: {hd_image_path}")
                return False
            
            # 生成图片URL并测试
            image_url = printer_client._get_file_url(hd_image_path)
            print(f"🔗 图片URL: {image_url}")
            
            # 测试URL可访问性
            try:
                response = requests.get(image_url, timeout=10)
                if response.status_code != 200:
                    print(f"❌ 图片URL仍无法访问: {response.status_code}")
                    return False
                print(f"✅ 图片URL可访问")
            except Exception as e:
                print(f"❌ 图片URL访问异常: {str(e)}")
                return False
            
            print(f"📤 开始发送订单到冲印系统...")
            
            # 发送订单
            success = printer_client.send_order_to_printer(order, order.hd_image, order)
            
            if success:
                print(f"✅ 订单发送成功!")
                print(f"📊 发送状态: {order.printer_send_status}")
                print(f"⏰ 发送时间: {order.printer_send_time}")
                
                if order.printer_response_data:
                    print(f"📄 厂家响应:")
                    print(f"   {order.printer_response_data}")
            else:
                print(f"❌ 订单发送失败!")
                print(f"📊 发送状态: {order.printer_send_status}")
                print(f"❌ 错误信息: {order.printer_error_message}")
                
                if order.printer_response_data:
                    print(f"📄 厂家响应:")
                    print(f"   {order.printer_response_data}")
            
            # 提交数据库更改
            db.session.commit()
            print(f"💾 数据库已更新")
            
            return success
            
        except Exception as e:
            print(f"❌ 发送过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.commit()
            return False

def main():
    """主函数"""
    print("🔧 冲印系统图片URL错误修复工具")
    print("=" * 50)
    
    # 1. 检查当前图片URL
    url_ok = check_image_url()
    
    if not url_ok:
        # 2. 检查服务器路径
        print(f"\n🔍 检查服务器路径...")
        correct_path = check_server_paths()
        
        if correct_path:
            # 3. 修复配置
            print(f"\n🔧 修复配置...")
            fix_success = fix_image_url_config()
            
            if fix_success:
                # 4. 测试修复后的URL
                test_success = test_fixed_url()
                
                if test_success:
                    # 5. 重新发送订单
                    print(f"\n❓ 是否重新发送订单到冲印系统？")
                    confirm = input("输入 y 确认发送，其他键取消: ").strip().lower()
                    
                    if confirm == 'y':
                        success = resend_order_with_fixed_url()
                        
                        if success:
                            print(f"\n🎉 订单发送成功!")
                            print(f"厂家应该能正常访问图片了")
                        else:
                            print(f"\n💥 订单发送失败!")
                            print(f"请检查错误信息")
                    else:
                        print(f"\n❌ 用户取消发送")
                else:
                    print(f"\n❌ URL修复失败")
            else:
                print(f"\n❌ 配置修复失败")
        else:
            print(f"\n❌ 未找到正确的图片路径")
            print(f"请检查服务器配置或联系技术支持")
    else:
        print(f"\n✅ 图片URL正常，问题可能在其他地方")
        print(f"请检查厂家系统的其他配置")

if __name__ == '__main__':
    main()
