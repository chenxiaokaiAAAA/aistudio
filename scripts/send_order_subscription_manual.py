#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('.')

# 导入必要模块
from test_server import app, db, Order, send_order_completion_notification_auto
import requests

def manual_send_subscription(order_number):
    """手动为订单发送订阅消息"""
    
    print(f"🔍 查找订单: {order_number}")
    print("=" * 50)
    
    with app.app_context():
        # 查找订单
        order = Order.query.filter_by(order_number=order_number).first()
        
        if not order:
            print(f"❌ 未找到订单: {order_number}")
            return False
        
        print(f"✅ 找到订单:")
        print(f"  订单ID: {order.id}")
        print(f"  客户姓名: {order.customer_name}")
        print(f"  客户电话: {order.customer_phone}")
        print(f"  订单状态: {order.status}")
        print(f"  完成时间: {order.completed_at}")
        print(f"  OpenID: {order.openid}")
        print(f"  最终图片: {order.final_image}")
        print(f"  高清图片: {order.hd_image}")
        
        # 检查订单状态
        if order.status != 'completed':
            print(f"\n⚠️ 警告: 订单状态不是 'completed', 当前状态: {order.status}")
            user_input = input("是否仍要继续发送订阅消息? (y/N): ")
            if user_input.lower() != 'y':
                print("❌ 用户取消操作")
                return False
        
        # 检查OpenID
        if not order.openid:
            print(f"\n⚠️ 警告: 订单没有OpenID，将尝试通过手机号查找")
            from test_server import PromotionUser
            promotion_user = PromotionUser.query.filter_by(phone_number=order.customer_phone).first()
            if promotion_user:
                order.openid = promotion_user.open_id
                print(f"✅ 通过手机号找到OpenID: {promotion_user.open_id}")
                db.session.commit()
            else:
                print(f"❌ 无法找到该手机号对应的推广用户")
                return False
        
        # 手动触发订阅消息
        print(f"\n🚀 正在发送订阅消息...")
        print("-" * 30)
        
        try:
            result = send_order_completion_notification_auto(order)
            if result:
                print(f"✅ 订阅消息发送成功!")
            else:
                print(f"❌ 订阅消息发送失败!")
            
            return result
            
        except Exception as e:
            print(f"❌ 发送过程中出现错误: {e}")
            return False

def test_wechat_api():
    """测试微信API连接"""
    
    print(f"\n🌐 测试微信API连接:")
    print("-" * 30)
    
    # 这里需要实际的APP_ID和APP_SECRET，我们从环境变量或配置文件获取
    try:
        import requests
        
        # 获取access_token的测试
        test_url = "https://api.weixin.qq.com/cgi-bin/token"
        
        print("⚠️ 需要真实的APP_ID和APP_SECRET来测试API连接")
        print("请检查test_server.py中的微信小程序配置")
        
        return False
        
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False

def check_order_images(order_number):
    """检查订单图片是否存在"""
    
    print(f"\n📸 检查订单图片文件:")
    print("-" * 30)
    
    with app.app_context():
        order = Order.query.filter_by(order_number=order_number).first()
        
        if not order:
            print(f"❌ 未找到订单")
            return False
        
        images_exist = True
        
        # 检查最终图片
        if order.final_image:
            final_path = os.path.join("final_works", order.final_image)
            if os.path.exists(final_path):
                print(f"✅ 最终图片存在: {final_path}")
            else:
                print(f"❌ 最终图片不存在: {final_path}")
                images_exist = False
        
        # 检查高清图片
        if order.hd_image:
            hd_path = os.path.join("hd_images", order.hd_image)
            if os.path.exists(hd_path):
                print(f"✅ 高清图片存在: {hd_path}")
            else:
                print(f"❌ 高清图片不存在: {hd_path}")
                images_exist = False
        
        return images_exist

def fix_order_completion_time(order_number):
    """修复订单完成时间"""
    
    print(f"\n🔧 修复订单完成时间:")
    print("-" * 30)
    
    with app.app_context():
        order = Order.query.filter_by(order_number=order_number).first()
        
        if not order:
            print(f"❌ 未找到订单")
            return False
        
        # 如果订单状态是completed但没有完成时间，设置完成时间
        if order.status == 'completed' and not order.completed_at:
            from datetime import datetime
            order.completed_at = datetime.now()
            db.session.commit()
            print(f"✅ 已设置订单完成时间: {order.completed_at}")
            return True
        else:
            print(f"ℹ️ 订单完成时间已存在: {order.completed_at}")
            return False

def main():
    if len(sys.argv) < 2:
        print("用法: python send_order_subscription_manual.py <订单号>")
        print("示例: python send_order_subscription_manual.py PET17591262004322198")
        return
    
    order_number = sys.argv[1]
    
    print("🎯 手动发送订单订阅消息工具")
    print("=" * 60)
    
    # 1. 检查图片文件
    images_ok = check_order_images(order_number)
    
    # 2. 修复订单完成时间
    fix_order_completion_time(order_number)
    
    # 3. 测试API连接
    test_wechat_api()
    
    # 4. 发送订阅消息
    success = manual_send_subscription(order_number)
    
    print(f"\n📋 操作总结:")
    print("=" * 30)
    print(f"图片检查: {'✅ 通过' if images_ok else '❌ 失败'}")
    print(f"订阅发送: {'✅ 成功' if success else '❌ 失败'}")
    
    if not success:
        print(f"\n💡 可能的原因:")
        print(f"1. 微信API配置问题 (APP_ID, APP_SECRET)")
        print(f"2. 用户未授权订阅消息")
        print(f"3. 订阅消息模板配置错误")
        print(f"4. 网络连接问题")

if __name__ == "__main__":
    main()
