#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试微信通知功能
"""

from wechat_notification import send_order_notification

print("=" * 50)
print("测试微信通知功能")
print("=" * 50)
print()

# 测试1: 新订单通知
print("测试1: 发送新订单通知...")
result = send_order_notification(
    order_number="PET20250101001",
    customer_name="张三",
    total_price=99.0,
    source="小程序"
)

if result:
    print("✅ 微信通知发送成功！请查看你的企业微信")
else:
    print("❌ 微信通知发送失败，请检查配置")

print()
print("测试完成！")


