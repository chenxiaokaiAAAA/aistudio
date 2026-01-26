#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复订单状态脚本
将已回传快递信息的订单状态从 processing 改为 shipped
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order
from datetime import datetime

def fix_order_status(order_number):
    """修复指定订单的状态"""
    with app.app_context():
        order = Order.query.filter_by(order_number=order_number).first()
        
        if not order:
            print(f"❌ 订单 {order_number} 不存在")
            return False
        
        print(f"📦 订单信息:")
        print(f"  订单号: {order.order_number}")
        print(f"  当前状态: {order.status}")
        print(f"  物流信息: {order.logistics_info}")
        
        # 检查是否有物流信息
        if order.logistics_info:
            import json
            try:
                logistics_data = json.loads(order.logistics_info)
                print(f"  物流详情: {logistics_data}")
                
                # 如果订单有物流信息但状态是 processing，改为 shipped
                if order.status == 'processing' and logistics_data.get('tracking_number'):
                    print(f"\n⚠️  订单有物流信息但状态是处理中，将更新为已发货")
                    order.status = 'shipped'
                    
                    # 如果 completed_at 为空，设置当前时间
                    if not order.completed_at:
                        order.completed_at = datetime.now()
                    
                    db.session.commit()
                    print(f"✅ 订单状态已更新为: {order.status}")
                    return True
                elif order.status == 'shipped':
                    print(f"✅ 订单状态已经是已发货")
                    return True
                else:
                    print(f"⚠️  订单状态: {order.status}，无需修改")
                    return False
            except Exception as e:
                print(f"❌ 解析物流信息失败: {str(e)}")
                return False
        else:
            print(f"⚠️  订单没有物流信息")
            return False

if __name__ == '__main__':
    # 修复订单 PET17622410280001
    order_number = 'PET17622410280001'
    print(f"🔧 开始修复订单状态: {order_number}")
    print("=" * 50)
    
    success = fix_order_status(order_number)
    
    if success:
        print(f"\n✅ 修复完成!")
    else:
        print(f"\n❌ 修复失败或订单状态无需修改")



