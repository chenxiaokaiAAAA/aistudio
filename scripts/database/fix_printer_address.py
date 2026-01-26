#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
检查并修复冲印系统发送数据包中的地址错误
重新发送订单 PET20250917175858D53F
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order
from printer_client import PrinterSystemClient
from printer_config import PRINTER_SYSTEM_CONFIG

def check_order_data():
    """检查订单数据"""
    print("🔍 检查订单数据...")
    
    with app.app_context():
        order_number = "PET20250917175858D53F"
        order = Order.query.filter_by(order_number=order_number).first()
        
        if not order:
            print(f"❌ 订单 {order_number} 不存在")
            return None
        
        print(f"✅ 找到订单: {order_number}")
        print(f"📋 订单信息:")
        print(f"   - 订单号: {order.order_number}")
        print(f"   - 客户姓名: {order.customer_name}")
        print(f"   - 客户电话: {order.customer_phone}")
        print(f"   - 收货地址: {order.shipping_info}")
        print(f"   - 产品尺寸: {order.size}")
        print(f"   - 高清图片: {order.hd_image}")
        
        return order

def check_address_format(order):
    """检查地址格式"""
    print(f"\n🏠 检查地址格式...")
    
    if not order.shipping_info:
        print(f"❌ 收货地址为空")
        return False
    
    print(f"当前收货地址: {order.shipping_info}")
    
    # 分析地址格式
    address_parts = order.shipping_info.split()
    print(f"地址分段: {address_parts}")
    
    if len(address_parts) < 2:
        print(f"⚠️  地址信息不完整，可能影响厂家处理")
        return False
    
    # 检查是否包含省市信息
    province = address_parts[0] if len(address_parts) > 0 else ""
    city = address_parts[1] if len(address_parts) > 1 else ""
    
    print(f"   - 省份: {province}")
    print(f"   - 城市: {city}")
    
    if not province or not city:
        print(f"❌ 缺少省市信息")
        return False
    
    print(f"✅ 地址格式检查通过")
    return True

def fix_address_format(order):
    """修复地址格式"""
    print(f"\n🔧 修复地址格式...")
    
    if not order.shipping_info:
        print(f"❌ 无法修复：收货地址为空")
        return False
    
    # 当前地址
    current_address = order.shipping_info
    print(f"当前地址: {current_address}")
    
    # 尝试解析地址
    address_parts = current_address.split()
    
    if len(address_parts) >= 2:
        province = address_parts[0]
        city = address_parts[1]
        district = address_parts[2] if len(address_parts) > 2 else ""
        street = " ".join(address_parts[3:]) if len(address_parts) > 3 else ""
        
        # 构建标准格式地址
        if district and street:
            standard_address = f"{province} {city} {district} {street}"
        elif district:
            standard_address = f"{province} {city} {district}"
        else:
            standard_address = f"{province} {city}"
        
        print(f"修复后地址: {standard_address}")
        
        # 更新订单地址
        order.shipping_info = standard_address
        db.session.commit()
        
        print(f"✅ 地址格式已修复")
        return True
    else:
        print(f"❌ 地址格式无法修复")
        return False

def test_printer_data_build(order):
    """测试冲印系统数据构建"""
    print(f"\n🧪 测试冲印系统数据构建...")
    
    try:
        # 创建冲印系统客户端
        printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
        
        # 检查高清图片文件
        hd_image_path = os.path.join('hd_images', order.hd_image)
        if not os.path.exists(hd_image_path):
            print(f"❌ 高清图片文件不存在: {hd_image_path}")
            return False
        
        print(f"✅ 高清图片文件存在: {hd_image_path}")
        
        # 构建订单数据
        order_data = printer_client._build_order_data(order, hd_image_path)
        
        print(f"✅ 订单数据构建成功")
        print(f"📋 构建的数据:")
        print(f"   - 订单号: {order_data.get('order_no')}")
        print(f"   - 客户姓名: {order_data.get('shipping_receiver', {}).get('name')}")
        print(f"   - 客户电话: {order_data.get('shipping_receiver', {}).get('mobile')}")
        
        # 检查收货人信息
        shipping_receiver = order_data.get('shipping_receiver', {})
        print(f"   - 省份: {shipping_receiver.get('province')}")
        print(f"   - 城市: {shipping_receiver.get('city')}")
        print(f"   - 区县: {shipping_receiver.get('city_part')}")
        print(f"   - 街道: {shipping_receiver.get('street')}")
        
        # 检查产品信息
        if order_data.get('sub_orders'):
            sub_order = order_data['sub_orders'][0]
            print(f"   - 产品ID: {sub_order.get('product_id')}")
            print(f"   - 产品名称: {sub_order.get('product_name')}")
            
            # 检查图片信息
            if sub_order.get('photos'):
                photo = sub_order['photos'][0]
                print(f"   - 图片URL: {photo.get('file_url')}")
                print(f"   - 图片尺寸: {photo.get('width')} x {photo.get('height')}")
        
        return order_data
        
    except Exception as e:
        print(f"❌ 数据构建失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def resend_order_with_fix():
    """重新发送订单（修复地址问题）"""
    print(f"\n🚀 重新发送订单到冲印系统...")
    
    with app.app_context():
        order_number = "PET20250917175858D53F"
        order = Order.query.filter_by(order_number=order_number).first()
        
        if not order:
            print(f"❌ 订单 {order_number} 不存在")
            return False
        
        try:
            # 创建冲印系统客户端
            printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
            
            # 检查高清图片文件
            hd_image_path = os.path.join('hd_images', order.hd_image)
            if not os.path.exists(hd_image_path):
                print(f"❌ 高清图片文件不存在: {hd_image_path}")
                return False
            
            print(f"📤 开始发送订单到冲印系统...")
            print(f"   - 订单号: {order.order_number}")
            print(f"   - 客户: {order.customer_name}")
            print(f"   - 地址: {order.shipping_info}")
            print(f"   - 图片: {order.hd_image}")
            
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
    print("🔧 冲印系统地址错误修复工具")
    print("=" * 50)
    
    # 1. 检查订单数据
    order = check_order_data()
    if not order:
        return
    
    # 2. 检查地址格式
    address_ok = check_address_format(order)
    
    # 3. 如果地址有问题，尝试修复
    if not address_ok:
        print(f"\n🔧 尝试修复地址格式...")
        fix_success = fix_address_format(order)
        if not fix_success:
            print(f"❌ 地址修复失败，请手动检查订单地址")
            return
    
    # 4. 测试数据构建
    order_data = test_printer_data_build(order)
    if not order_data:
        print(f"❌ 数据构建失败，无法发送")
        return
    
    # 5. 确认是否重新发送
    print(f"\n❓ 是否重新发送订单到冲印系统？")
    confirm = input("输入 y 确认发送，其他键取消: ").strip().lower()
    
    if confirm == 'y':
        # 6. 重新发送订单
        success = resend_order_with_fix()
        
        if success:
            print(f"\n🎉 订单发送成功!")
            print(f"厂家应该能正常接收订单数据了")
        else:
            print(f"\n💥 订单发送失败!")
            print(f"请检查错误信息并联系技术支持")
    else:
        print(f"\n❌ 用户取消发送")

if __name__ == '__main__':
    main()
