#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
手动更新物流信息的脚本
"""

import sqlite3
import json
from datetime import datetime

def update_logistics_manually():
    """手动更新物流信息"""
    
    # 厂家提供的物流信息
    logistics_data = {
        "company": "顺丰速运",
        "tracking_number": "SF3282127155569",
        "status": "已发货",
        "remark": "厂家发货",
        "update_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    print("📦 厂家提供的物流信息:")
    print(f"  快递公司: {logistics_data['company']}")
    print(f"  快递单号: {logistics_data['tracking_number']}")
    print(f"  状态: {logistics_data['status']}")
    print(f"  更新时间: {logistics_data['update_time']}")
    
    print("\\n请提供正确的订单号，我将帮您更新物流信息...")
    print("订单号格式应该是: PET20250917192632FC98 这样的格式")
    
    # 这里需要您提供正确的订单号
    correct_order_number = input("请输入正确的订单号: ").strip()
    
    if not correct_order_number:
        print("❌ 未提供订单号")
        return
    
    try:
        conn = sqlite3.connect('pet_painting.db')
        cursor = conn.cursor()
        
        # 查找订单
        cursor.execute('SELECT id, order_number, status FROM "order" WHERE order_number = ?', (correct_order_number,))
        order = cursor.fetchone()
        
        if order:
            order_id, order_number, current_status = order
            print(f"✅ 找到订单: {order_number}")
            print(f"  当前状态: {current_status}")
            
            # 更新物流信息
            cursor.execute('''
                UPDATE "order" 
                SET logistics_info = ?, status = ?, completed_at = ?
                WHERE id = ?
            ''', (
                json.dumps(logistics_data, ensure_ascii=False),
                'shipped',
                datetime.now(),
                order_id
            ))
            
            conn.commit()
            print("✅ 物流信息更新成功！")
            
        else:
            print(f"❌ 未找到订单: {correct_order_number}")
            
            # 显示最近的订单供参考
            cursor.execute('SELECT order_number FROM "order" ORDER BY id DESC LIMIT 5')
            recent_orders = cursor.fetchall()
            print("\\n最近的5个订单号:")
            for order in recent_orders:
                print(f"  {order[0]}")
        
        conn.close()
        
    except Exception as e:
        print(f"更新失败: {str(e)}")

if __name__ == '__main__':
    update_logistics_manually()
