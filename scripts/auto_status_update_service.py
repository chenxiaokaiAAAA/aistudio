#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
订单状态自动更新服务
集成到主系统中，定期自动检查并更新订单状态
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order, Commission
from datetime import datetime
import threading
import time

def auto_update_order_status():
    """自动更新订单状态（谨慎模式）"""
    with app.app_context():
        try:
            # 查找所有有发货信息但状态不是已发货的订单
            orders_with_shipping = Order.query.filter(
                Order.shipping_info.isnot(None),
                Order.shipping_info != '',
                ~Order.status.in_(['shipped', 'manufacturing'])
            ).all()
            
            if not orders_with_shipping:
                return 0
            
            updated_count = 0
            
            for order in orders_with_shipping:
                # 检查发货信息是否有效
                if order.shipping_info and order.shipping_info.strip():
                    try:
                        import json
                        shipping_data = json.loads(order.shipping_info)
                        # 更严格的判断：必须有收货人和地址才认为已发货
                        if shipping_data.get('receiver') and shipping_data.get('address'):
                            # 检查收货人和地址是否有效
                            receiver = shipping_data.get('receiver', '').strip()
                            address = shipping_data.get('address', '').strip()
                            
                            if receiver and address and len(receiver) > 0 and len(address) > 1:
                                order.status = 'shipped'
                                order.completed_at = datetime.now()
                                updated_count += 1
                                print(f"  ✅ 更新订单 {order.order_number} 状态为已发货")
                            else:
                                print(f"  ⚠️  订单 {order.order_number} 发货信息不完整，跳过")
                    except:
                        # 如果不是JSON格式，但有内容，也认为已发货
                        if order.shipping_info.strip():
                            order.status = 'shipped'
                            order.completed_at = datetime.now()
                            updated_count += 1
                            print(f"  ✅ 更新订单 {order.order_number} 状态为已发货")
            
            if updated_count > 0:
                db.session.commit()
                print(f"🔄 自动更新了 {updated_count} 个订单状态为已发货")
            
            return updated_count
            
        except Exception as e:
            print(f"❌ 自动更新订单状态失败: {e}")
            db.session.rollback()
            return 0

def start_auto_update_service():
    """启动自动更新服务"""
    def update_loop():
        while True:
            try:
                updated_count = auto_update_order_status()
                if updated_count > 0:
                    print(f"✅ 自动更新服务运行完成，更新了 {updated_count} 个订单")
                time.sleep(300)  # 每5分钟检查一次
            except Exception as e:
                print(f"❌ 自动更新服务异常: {e}")
                time.sleep(60)  # 出错后等待1分钟再重试
    
    # 在后台线程中运行
    update_thread = threading.Thread(target=update_loop, daemon=True)
    update_thread.start()
    print("🚀 订单状态自动更新服务已启动")

# 集成到Flask应用中的函数
def init_auto_update_service():
    """初始化自动更新服务"""
    start_auto_update_service()

if __name__ == '__main__':
    # 测试运行一次
    print("🧪 测试自动更新服务")
    updated_count = auto_update_order_status()
    print(f"✅ 测试完成，更新了 {updated_count} 个订单")
