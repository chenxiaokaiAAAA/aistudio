#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
导出17-19号3天的所有访问数据
包括用户信息、订单信息、推广信息等
"""

import sqlite3
import json
import csv
from datetime import datetime, timedelta

def export_october_17_19_data():
    """导出10月17-19号的所有访问数据"""
    
    print("📊 导出10月17-19号的所有访问数据")
    print("=" * 80)
    
    db_file = 'instance/pet_painting.db'
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 1. 查询17-19号期间的所有订单
        print("📋 1. 查询17-19号期间的所有订单:")
        print("-" * 60)
        
        cursor.execute('''
            SELECT order_number, customer_name, customer_phone, 
                   promotion_code, referrer_user_id, price, status, 
                   created_at, openid, source_type, product_name, size
            FROM "order" 
            WHERE DATE(created_at) BETWEEN '2025-10-17' AND '2025-10-19'
            ORDER BY created_at DESC
        ''')
        
        orders = cursor.fetchall()
        
        print(f"找到 {len(orders)} 个订单")
        
        # 2. 查询17-19号期间的推广用户注册
        print(f"\n📋 2. 查询17-19号期间的推广用户注册:")
        print("-" * 60)
        
        cursor.execute('''
            SELECT user_id, promotion_code, phone_number, nickname, 
                   eligible_for_promotion, total_orders, create_time
            FROM promotion_users 
            WHERE DATE(create_time) BETWEEN '2025-10-17' AND '2025-10-19'
            ORDER BY create_time DESC
        ''')
        
        promotion_users = cursor.fetchall()
        
        print(f"找到 {len(promotion_users)} 个推广用户注册")
        
        # 3. 查询17-19号期间的推广追踪记录
        print(f"\n📋 3. 查询17-19号期间的推广追踪记录:")
        print("-" * 60)
        
        try:
            cursor.execute('''
                SELECT id, promotion_code, referrer_user_id, visitor_user_id, 
                       visit_time, create_time
                FROM promotion_tracks 
                WHERE DATE(visit_time) BETWEEN '2025-10-17' AND '2025-10-19'
                ORDER BY visit_time DESC
            ''')
            
            promotion_tracks = cursor.fetchall()
            print(f"找到 {len(promotion_tracks)} 个推广追踪记录")
        except Exception as e:
            print(f"推广追踪记录查询失败: {e}")
            promotion_tracks = []
        
        # 4. 查询17-19号期间的用户访问记录（如果有的话）
        print(f"\n📋 4. 查询17-19号期间的用户访问记录:")
        print("-" * 60)
        
        try:
            cursor.execute('''
                SELECT id, session_id, openid, user_id, visit_type, 
                       is_authorized, is_registered, has_ordered, 
                       visit_time, promotion_code, referrer_user_id
                FROM user_visits 
                WHERE DATE(visit_time) BETWEEN '2025-10-17' AND '2025-10-19'
                ORDER BY visit_time DESC
            ''')
            
            user_visits = cursor.fetchall()
            print(f"找到 {len(user_visits)} 个用户访问记录")
        except Exception as e:
            print(f"用户访问记录查询失败: {e}")
            user_visits = []
        
        # 5. 导出订单数据到CSV
        print(f"\n📋 5. 导出订单数据到CSV:")
        print("-" * 60)
        
        if orders:
            # 准备订单数据
            order_data = []
            for order in orders:
                order_number, customer_name, customer_phone, promotion_code, referrer_user_id, price, status, created_at, openid, source_type, product_name, size = order
                
                order_data.append({
                    '订单号': order_number,
                    '客户姓名': customer_name,
                    '客户电话': customer_phone,
                    '推广码': promotion_code or '',
                    '推广者ID': referrer_user_id or '',
                    '价格': price,
                    '状态': status,
                    '创建时间': created_at,
                    'OpenID': openid or '',
                    '来源类型': source_type,
                    '产品名称': product_name or '',
                    '尺寸': size or ''
                })
            
            # 导出到CSV
            csv_filename = f'orders_2025-10-17_to_2025-10-19_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['订单号', '客户姓名', '客户电话', '推广码', '推广者ID', '价格', '状态', '创建时间', 'OpenID', '来源类型', '产品名称', '尺寸']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(order_data)
            print(f"✅ 订单数据已导出到: {csv_filename}")
        
        # 6. 导出推广用户数据到CSV
        print(f"\n📋 6. 导出推广用户数据到CSV:")
        print("-" * 60)
        
        if promotion_users:
            # 准备推广用户数据
            promotion_data = []
            for user in promotion_users:
                user_id, promotion_code, phone_number, nickname, eligible_for_promotion, total_orders, create_time = user
                
                promotion_data.append({
                    '用户ID': user_id,
                    '推广码': promotion_code or '',
                    '手机号': phone_number or '',
                    '昵称': nickname or '',
                    '推广资格': '是' if eligible_for_promotion else '否',
                    '总订单数': total_orders,
                    '注册时间': create_time
                })
            
            # 导出到CSV
            csv_filename = f'promotion_users_2025-10-17_to_2025-10-19_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['用户ID', '推广码', '手机号', '昵称', '推广资格', '总订单数', '注册时间']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(promotion_data)
            print(f"✅ 推广用户数据已导出到: {csv_filename}")
        
        # 7. 导出推广追踪数据到CSV
        print(f"\n📋 7. 导出推广追踪数据到CSV:")
        print("-" * 60)
        
        if promotion_tracks:
            # 准备推广追踪数据
            track_data = []
            for track in promotion_tracks:
                track_id, promotion_code, referrer_user_id, visitor_user_id, visit_time, create_time = track
                
                track_data.append({
                    '追踪ID': track_id,
                    '推广码': promotion_code or '',
                    '推广者ID': referrer_user_id or '',
                    '访问者ID': visitor_user_id or '',
                    '访问时间': visit_time,
                    '创建时间': create_time
                })
            
            # 导出到CSV
            csv_filename = f'promotion_tracks_2025-10-17_to_2025-10-19_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['追踪ID', '推广码', '推广者ID', '访问者ID', '访问时间', '创建时间']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(track_data)
            print(f"✅ 推广追踪数据已导出到: {csv_filename}")
        
        # 8. 导出用户访问数据到CSV
        print(f"\n📋 8. 导出用户访问数据到CSV:")
        print("-" * 60)
        
        if user_visits:
            # 准备用户访问数据
            visit_data = []
            for visit in user_visits:
                visit_id, session_id, openid, user_id, visit_type, is_authorized, is_registered, has_ordered, visit_time, promotion_code, referrer_user_id = visit
                
                visit_data.append({
                    '访问ID': visit_id,
                    '会话ID': session_id,
                    'OpenID': openid or '',
                    '用户ID': user_id or '',
                    '访问类型': visit_type,
                    '已授权': '是' if is_authorized else '否',
                    '已注册': '是' if is_registered else '否',
                    '已下单': '是' if has_ordered else '否',
                    '访问时间': visit_time,
                    '推广码': promotion_code or '',
                    '推广者ID': referrer_user_id or ''
                })
            
            # 导出到CSV
            csv_filename = f'user_visits_2025-10-17_to_2025-10-19_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['访问ID', '会话ID', 'OpenID', '用户ID', '访问类型', '已授权', '已注册', '已下单', '访问时间', '推广码', '推广者ID']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(visit_data)
            print(f"✅ 用户访问数据已导出到: {csv_filename}")
        
        # 9. 生成综合报告
        print(f"\n📋 9. 生成综合报告:")
        print("-" * 60)
        
        report = {
            '导出时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '查询期间': '2025-10-17 到 2025-10-19',
            '数据统计': {
                '订单总数': len(orders),
                '推广用户注册数': len(promotion_users),
                '推广追踪记录数': len(promotion_tracks),
                '用户访问记录数': len(user_visits)
            },
            '订单详情': order_data if orders else [],
            '推广用户详情': promotion_data if promotion_users else [],
            '推广追踪详情': track_data if promotion_tracks else [],
            '用户访问详情': visit_data if user_visits else []
        }
        
        # 导出JSON报告
        json_filename = f'october_17_19_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"✅ 综合报告已导出到: {json_filename}")
        
        # 10. 显示详细统计
        print(f"\n📊 详细统计:")
        print("-" * 60)
        
        print(f"📅 2025年10月17-19日数据统计:")
        print(f"   订单总数: {len(orders)}")
        print(f"   推广用户注册数: {len(promotion_users)}")
        print(f"   推广追踪记录数: {len(promotion_tracks)}")
        print(f"   用户访问记录数: {len(user_visits)}")
        
        if orders:
            print(f"\n📋 订单详情:")
            for i, order in enumerate(orders):
                order_number, customer_name, customer_phone, promotion_code, referrer_user_id, price, status, created_at, openid, source_type, product_name, size = order
                print(f"   {i+1}. {order_number} | {customer_name} | {customer_phone} | ¥{price} | {status} | {created_at}")
        
        if promotion_users:
            print(f"\n👥 推广用户详情:")
            for i, user in enumerate(promotion_users):
                user_id, promotion_code, phone_number, nickname, eligible_for_promotion, total_orders, create_time = user
                print(f"   {i+1}. {user_id} | {promotion_code} | {nickname} | {phone_number} | {create_time}")
        
        conn.close()
        
        print(f"\n✅ 数据导出完成！")
        print(f"📁 导出的文件:")
        if orders:
            print(f"   - 订单数据CSV文件")
        if promotion_users:
            print(f"   - 推广用户数据CSV文件")
        if promotion_tracks:
            print(f"   - 推广追踪数据CSV文件")
        if user_visits:
            print(f"   - 用户访问数据CSV文件")
        print(f"   - 综合报告JSON文件")
        
        return report
        
    except Exception as e:
        print(f"❌ 导出数据失败: {str(e)}")
        return None

def main():
    print("📊 导出10月17-19号的所有访问数据")
    print("目标: 获取这3天的所有用户信息、订单信息、推广信息")
    print("=" * 80)
    
    # 导出数据
    report = export_october_17_19_data()
    
    if report:
        print(f"\n🎉 数据导出成功！")
        print(f"📊 总计导出:")
        print(f"   - {report['数据统计']['订单总数']} 个订单")
        print(f"   - {report['数据统计']['推广用户注册数']} 个推广用户")
        print(f"   - {report['数据统计']['推广追踪记录数']} 个推广追踪记录")
        print(f"   - {report['数据统计']['用户访问记录数']} 个用户访问记录")
    else:
        print(f"\n❌ 数据导出失败！")

if __name__ == "__main__":
    main()
