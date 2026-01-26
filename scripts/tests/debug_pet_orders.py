#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('.')

from test_server import app, db, Order
import sqlite3

def debug_pet_orders():
    """调试PET用户订单问题"""
    
    print("🔍 调试PET05372用户订单问题")
    print("=" * 50)
    
    with app.app_context():
        # 1. 查询所有PET开头的订单
        pet_orders = Order.query.filter(Order.order_number.like('PET%')).order_by(Order.created_at.desc()).all()
        
        print(f"📊 数据库中的所有PET订单 (共{len(pet_orders)}个):")
        print("-" * 60)
        
        for i, order in enumerate(pet_orders):
            print(f"{i+1}. {order.order_number}")
            print(f"   客户: {order.customer_name}")
            print(f"   手机: {order.customer_phone}")
            print(f"   状态: {order.status}")
            print(f"   来源: {order.source_type}")
            print(f"   OpenID: {order.openid[:20] if order.openid else 'None'}...")
            print(f"   创建: {order.created_at}")
            print()
        
        # 2. 分析查询条件问题
        print("🔧 API查询条件分析:")
        print("-" * 30)
        
        # 模拟小程序调用 (只传phone)
        test_phone = "18760053720"  # 假设的测试手机号
        
        print(f"测试条件1: 只按手机号查询")
        orders_phone_only = Order.query.filter(
            Order.customer_phone.like(f'%{test_phone}%'),
            Order.source_type == 'miniprogram'
        ).all()
        print(f"结果: 找到 {len(orders_phone_only)} 个订单")
        
        print(f"测试条件2: 当前API严格条件")
        orders_strict = Order.query.filter(
            Order.customer_phone.like(f'%{test_phone}%'),
            Order.source_type == 'miniprogram',
            Order.openid == 'test_openid'  # 示例openid
        ).all()
        print(f"结果: 找到 {len(orders_strict)} 个订单")
        
        # 3. 检查可能匹配的用户订单
        print(f"\n🎯 可能的用户订单:")
        print("-" * 30)
        
        # 查找mobile号相似的订单
        possible_phones = [
            "18760053720",  # 完整11位
            "53720",        # 最后5位
            "1876005372",   # 前10位
        ]
        
        for phone_part in possible_phones:
            matching_orders = Order.query.filter(
                Order.customer_phone.like(f'%{phone_part}%')
            ).all()
            
            if matching_orders:
                print(f"手机号包含 '{phone_part}' 的订单:")
                for order in matching_orders:
                    print(f"  ✅ {order.order_number} - {order.customer_name} - {order.customer_phone} - {order.source_type}")
        
        return {
            'total_pet_orders': len(pet_orders),
            'phone_only_matches': len(orders_phone_only),
            'strict_matches': len(orders_strict)
        }

def analyze_api_issue():
    """分析API问题"""
    
    print(f"\n🔍 API问题分析:")
    print("=" * 30)
    
    print(f"问题1: 参数不匹配")
    print(f"  ❌ 小程序发送: phone=xxx")
    print(f"  ❌ 服务器要求: phone=xxx AND openid=xxx")
    print(f"  ❌ 结果: API返回400错误'缺少用户openid参数'")
    
    print(f"\n问题2: 查询条件过严")
    print(f"  ❌ 要求: source_type = 'miniprogram'")
    print(f"  ❌ 要求: openid 必须完全匹配")
    print(f"  ❌ 结果: 很多订单查不到")
    
    print(f"\n解决方案:")
    print(f"1. 修改API参数要求，使openid可选")
    print(f"2. 调整查询条件，更灵活匹配")
    print(f"3. 添加调试日志")

def fix_api():
    """修复API问题"""
    
    print(f"\n🔧 API修复方案:")
    print("=" * 30)
    
    print(f"建议修改 /api/miniprogram/orders GET 接口:")
    print(f"")
    print(f"当前代码:")
    print(f"  if not openid:")
    print(f"      return jsonify({'status': 'error', 'message': '缺少用户openid参数'}), 400")
    print(f"")
    print(f"修改为:")
    print(f"  # openid现在是可选的")
    print(f"  orders = Order.query.filter(")
    print(f"      Order.customer_phone.like(f'%{{phone}}%'),")
    print(f"      Order.source_type == 'miniprogram'")
    print(f"  ).filter(")
    print(f"      Order.openid == openid if openid else True")
    print(f"  ).order_by(Order.created_at.desc()).all()")

def main():
    print("🔍 PET用户订单查询问题完整诊断")
    print("问题: 小程序我的订单页面显示为空")
    print("用户: PET05372")
    print("=" * 60)
    
    # 调试订单
    result = debug_pet_orders()
    
    # 分析问题
    analyze_api_issue()
    
    # 修复方案
    fix_api()
    
    print(f"\n📋 结论:")
    print("=" * 30)
    print(f"✅ 问题根源: API参数要求不匹配")
    print(f"✅ 解决方案: 修改API使openid参数可选")
    print(f"✅ 当前影响: 所有用户在'我的订单'页面都会看到空列表")

if __name__ == "__main__":
    main()
