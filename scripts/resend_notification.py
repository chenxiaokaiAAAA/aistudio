#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('.')

from test_server import app, db, Order, send_order_completion_notification_auto
from datetime import datetime

def resend_notification(order_number):
    """重新发送订单完成通知"""
    
    print(f"📱 重新发送订单完成通知")
    print("=" * 50)
    
    with app.app_context():
        # 查找指定订单
        order = Order.query.filter_by(order_number=order_number).first()
        
        if not order:
            print(f"❌ 未找到订单: {order_number}")
            return False
        
        print(f"✅ 找到订单:")
        print(f"  订单号: {order.order_number}")
        print(f"  客户姓名: {order.customer_name}")
        print(f"  客户电话: {order.customer_phone}")
        print(f"  订单状态: {order.status}")
        print(f"  完成时间: {order.completed_at}")
        print(f"  OpenID: {order.openid}")
        
        # 检查推送条件
        print(f"\n📋 推送条件检查:")
        if not order.openid:
            print(f"❌ 缺少OpenID，无法发送")
            return False
        
        if order.status != 'completed':
            print(f"❌ 订单状态为 {order.status}，不是完成状态")
            return False
        
        if not order.completed_at:
            print(f"❌ 订单没有完成时间")
            return False
        
        print(f"✅ 订单状态正常，可以进行推送")
        
        # 发送订阅消息
        print(f"\n🚀 开始发送订阅消息:")
        print("-" * 30)
        
        try:
            # 调用自动发送函数
            result = send_order_completion_notification_auto(order)
            
            if result:
                print(f"✅ 订阅消息发送成功!")
                print(f"📱 用户 {order.customer_name} 应该会收到通知")
                print(f"🔗 点击后跳转到: /pages/order-detail/order-detail?orderId={order.order_number}")
                print(f"✅ 小程序现在能正确接收orderId参数")
                return True
            else:
                print(f"❌ 订阅消息发送失败")
                return False
                
        except Exception as e:
            print(f"❌ 发送过程出错: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_notification_content():
    """测试通知内容"""
    
    print(f"\n📋 通知内容预览:")
    print("=" * 30)
    
    template_id = "BOy7pDiq-pM1qiJHJfP9jUjAbi9o0bZG5-mEKZbnYT8"
    order_number = "PET17591267387641966"
    
    print(f"模板ID: {template_id}")
    print(f"订单编号: {order_number}")
    print(f"作品名称: 定制产品")
    print(f"制作完成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}")
    print(f"跳转页面: /pages/order-detail/order-detail?orderId={order_number}")
    
    print(f"\n💡 用户看到的消息:")
    print(f"标题: 您的作品已完成")
    print(f"订单号: {order_number}")
    print(f"作品: 定制产品")
    print(f"完成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}")

def main():
    print("📱 订单完成通知重发测试")
    print(f"订单号: PET17591267387641966")
    print("🎯 验证修复后的跳转链接是否能正常工作")
    print("=" * 60)
    
    # 测试通知内容
    test_notification_content()
    
    # 重新发送通知
    success = resend_notification("PET17591267387641966")
    
    print(f"\n📊 发送结果:")
    print("=" * 30)
    
    if success:
        print(f"✅ 通知发送成功!")
        print(f"📱 请检查用户手机是否收到微信订阅消息")
        print(f"👆 用户点击消息后应该能正常进入小程序订单详情页")
        print(f"🔗 不会再出现'加载失败'的问题")
    else:
        print(f"❌ 通知发送失败，请检查日志")
    
    print(f"\n💡 注意事项:")
    print(f"1. 确保用户已经授权订阅消息")
    print(f"2. 确保用户已安装微信小程序")
    print(f"3. 如果是测试环境，可能需要有效的微信配置")

if __name__ == "__main__":
    main()
