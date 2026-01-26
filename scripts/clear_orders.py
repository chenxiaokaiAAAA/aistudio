#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清空订单数据库中的所有订单数据
"""
import os
import sys
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order, OrderImage

def clear_all_orders():
    """清空所有订单数据"""
    with app.app_context():
        try:
            # 统计订单数量
            order_count = Order.query.count()
            order_image_count = OrderImage.query.count()
            
            print("=" * 60)
            print("订单数据统计")
            print("=" * 60)
            print(f"订单数量: {order_count}")
            print(f"订单图片数量: {order_image_count}")
            print()
            
            if order_count == 0:
                print("✅ 数据库中已经没有订单数据")
                return
            
            # 确认操作
            print("⚠️  警告：此操作将删除所有订单数据！")
            print(f"将删除 {order_count} 条订单记录和 {order_image_count} 条订单图片记录")
            print()
            confirm = input("确认删除？(输入 'YES' 确认): ")
            
            if confirm != 'YES':
                print("❌ 操作已取消")
                return
            
            print()
            print("正在删除订单数据...")
            
            # 删除订单图片
            deleted_images = OrderImage.query.delete()
            print(f"✅ 已删除 {deleted_images} 条订单图片记录")
            
            # 删除订单
            deleted_orders = Order.query.delete()
            print(f"✅ 已删除 {deleted_orders} 条订单记录")
            
            # 提交事务
            db.session.commit()
            
            print()
            print("=" * 60)
            print("✅ 订单数据清空完成！")
            print("=" * 60)
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 删除订单时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    clear_all_orders()
