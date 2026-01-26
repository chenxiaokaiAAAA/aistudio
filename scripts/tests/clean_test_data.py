#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
清理分佣管理中的测试数据
"""

import sqlite3
import os
from datetime import datetime

def clean_test_data():
    """清理测试数据"""
    print("🧹 开始清理分佣管理中的测试数据")
    print("=" * 50)
    
    # 数据库路径
    db_path = "instance/pet_painting.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("✅ 数据库连接成功")
        
        # 1. 查看当前数据
        print("\n📊 当前数据统计:")
        
        # 查看推广用户表
        cursor.execute("SELECT COUNT(*) FROM promotion_users")
        promotion_users_count = cursor.fetchone()[0]
        print(f"  推广用户数量: {promotion_users_count}")
        
        # 查看分佣记录表
        cursor.execute("SELECT COUNT(*) FROM commissions")
        commissions_count = cursor.fetchone()[0]
        print(f"  分佣记录数量: {commissions_count}")
        
        # 查看推广访问追踪表
        cursor.execute("SELECT COUNT(*) FROM promotion_tracks")
        tracks_count = cursor.fetchone()[0]
        print(f"  推广访问追踪数量: {tracks_count}")
        
        # 查看订单表中的推广相关数据
        cursor.execute("SELECT COUNT(*) FROM `order` WHERE promotion_code IS NOT NULL OR referrer_user_id IS NOT NULL")
        orders_with_promotion = cursor.fetchone()[0]
        print(f"  包含推广信息的订单数量: {orders_with_promotion}")
        
        # 2. 识别测试数据
        print("\n🔍 识别测试数据:")
        
        # 查找测试用户（包含TEST、test、测试等关键词）
        cursor.execute("""
            SELECT user_id, promotion_code, nickname, create_time 
            FROM promotion_users 
            WHERE user_id LIKE '%TEST%' 
               OR user_id LIKE '%test%' 
               OR user_id LIKE '%测试%'
               OR nickname LIKE '%TEST%'
               OR nickname LIKE '%test%'
               OR nickname LIKE '%测试%'
        """)
        test_users = cursor.fetchall()
        
        if test_users:
            print(f"  发现测试用户: {len(test_users)} 个")
            for user in test_users:
                print(f"    - {user[0]} ({user[2]}) - {user[3]}")
        else:
            print("  未发现明显的测试用户")
        
        # 查找测试分佣记录
        cursor.execute("""
            SELECT c.id, c.order_id, c.referrer_user_id, c.amount, c.create_time
            FROM commissions c
            WHERE c.referrer_user_id LIKE '%TEST%' 
               OR c.referrer_user_id LIKE '%test%'
               OR c.referrer_user_id LIKE '%测试%'
               OR c.order_id LIKE '%TEST%'
               OR c.order_id LIKE '%test%'
        """)
        test_commissions = cursor.fetchall()
        
        if test_commissions:
            print(f"  发现测试分佣记录: {len(test_commissions)} 条")
            for commission in test_commissions:
                print(f"    - ID: {commission[0]}, 订单: {commission[1]}, 推广者: {commission[2]}, 金额: {commission[3]}")
        else:
            print("  未发现明显的测试分佣记录")
        
        # 3. 提供清理选项
        print("\n🧹 清理选项:")
        print("1. 清理所有测试数据（推荐）")
        print("2. 只清理分佣记录")
        print("3. 只清理推广用户")
        print("4. 只清理推广访问追踪")
        print("5. 自定义清理")
        print("0. 退出")
        
        choice = input("\n请选择清理选项 (0-5): ").strip()
        
        if choice == "0":
            print("退出清理")
            return True
        
        elif choice == "1":
            # 清理所有测试数据
            print("\n🗑️ 开始清理所有测试数据...")
            
            # 删除测试分佣记录
            cursor.execute("""
                DELETE FROM commissions 
                WHERE referrer_user_id LIKE '%TEST%' 
                   OR referrer_user_id LIKE '%test%'
                   OR referrer_user_id LIKE '%测试%'
                   OR order_id LIKE '%TEST%'
                   OR order_id LIKE '%test%'
            """)
            deleted_commissions = cursor.rowcount
            print(f"  删除测试分佣记录: {deleted_commissions} 条")
            
            # 删除测试推广访问追踪
            cursor.execute("""
                DELETE FROM promotion_tracks 
                WHERE referrer_user_id LIKE '%TEST%' 
                   OR referrer_user_id LIKE '%test%'
                   OR referrer_user_id LIKE '%测试%'
                   OR visitor_user_id LIKE '%TEST%'
                   OR visitor_user_id LIKE '%test%'
            """)
            deleted_tracks = cursor.rowcount
            print(f"  删除测试推广访问追踪: {deleted_tracks} 条")
            
            # 删除测试推广用户
            cursor.execute("""
                DELETE FROM promotion_users 
                WHERE user_id LIKE '%TEST%' 
                   OR user_id LIKE '%test%' 
                   OR user_id LIKE '%测试%'
                   OR nickname LIKE '%TEST%'
                   OR nickname LIKE '%test%'
                   OR nickname LIKE '%测试%'
            """)
            deleted_users = cursor.rowcount
            print(f"  删除测试推广用户: {deleted_users} 个")
            
            # 清理订单表中的测试推广信息
            cursor.execute("""
                UPDATE `order` 
                SET promotion_code = NULL, referrer_user_id = NULL 
                WHERE promotion_code LIKE '%TEST%' 
                   OR promotion_code LIKE '%test%'
                   OR referrer_user_id LIKE '%TEST%'
                   OR referrer_user_id LIKE '%test%'
            """)
            updated_orders = cursor.rowcount
            print(f"  清理订单中的测试推广信息: {updated_orders} 条")
            
        elif choice == "2":
            # 只清理分佣记录
            cursor.execute("""
                DELETE FROM commissions 
                WHERE referrer_user_id LIKE '%TEST%' 
                   OR referrer_user_id LIKE '%test%'
                   OR referrer_user_id LIKE '%测试%'
                   OR order_id LIKE '%TEST%'
                   OR order_id LIKE '%test%'
            """)
            deleted_commissions = cursor.rowcount
            print(f"删除测试分佣记录: {deleted_commissions} 条")
            
        elif choice == "3":
            # 只清理推广用户
            cursor.execute("""
                DELETE FROM promotion_users 
                WHERE user_id LIKE '%TEST%' 
                   OR user_id LIKE '%test%' 
                   OR user_id LIKE '%测试%'
                   OR nickname LIKE '%TEST%'
                   OR nickname LIKE '%test%'
                   OR nickname LIKE '%测试%'
            """)
            deleted_users = cursor.rowcount
            print(f"删除测试推广用户: {deleted_users} 个")
            
        elif choice == "4":
            # 只清理推广访问追踪
            cursor.execute("""
                DELETE FROM promotion_tracks 
                WHERE referrer_user_id LIKE '%TEST%' 
                   OR referrer_user_id LIKE '%test%'
                   OR referrer_user_id LIKE '%测试%'
                   OR visitor_user_id LIKE '%TEST%'
                   OR visitor_user_id LIKE '%test%'
            """)
            deleted_tracks = cursor.rowcount
            print(f"删除测试推广访问追踪: {deleted_tracks} 条")
            
        elif choice == "5":
            # 自定义清理
            print("\n自定义清理选项:")
            print("请输入要删除的用户ID或推广码（支持模糊匹配）:")
            keyword = input("关键词: ").strip()
            
            if keyword:
                # 删除相关分佣记录
                cursor.execute("DELETE FROM commissions WHERE referrer_user_id LIKE ? OR order_id LIKE ?", 
                             (f'%{keyword}%', f'%{keyword}%'))
                deleted_commissions = cursor.rowcount
                print(f"删除相关分佣记录: {deleted_commissions} 条")
                
                # 删除相关推广用户
                cursor.execute("DELETE FROM promotion_users WHERE user_id LIKE ? OR promotion_code LIKE ?", 
                             (f'%{keyword}%', f'%{keyword}%'))
                deleted_users = cursor.rowcount
                print(f"删除相关推广用户: {deleted_users} 个")
                
                # 删除相关推广访问追踪
                cursor.execute("DELETE FROM promotion_tracks WHERE referrer_user_id LIKE ? OR visitor_user_id LIKE ?", 
                             (f'%{keyword}%', f'%{keyword}%'))
                deleted_tracks = cursor.rowcount
                print(f"删除相关推广访问追踪: {deleted_tracks} 条")
        
        # 提交更改
        conn.commit()
        print("\n✅ 数据清理完成")
        
        # 4. 显示清理后的数据统计
        print("\n📊 清理后数据统计:")
        
        cursor.execute("SELECT COUNT(*) FROM promotion_users")
        promotion_users_count = cursor.fetchone()[0]
        print(f"  推广用户数量: {promotion_users_count}")
        
        cursor.execute("SELECT COUNT(*) FROM commissions")
        commissions_count = cursor.fetchone()[0]
        print(f"  分佣记录数量: {commissions_count}")
        
        cursor.execute("SELECT COUNT(*) FROM promotion_tracks")
        tracks_count = cursor.fetchone()[0]
        print(f"  推广访问追踪数量: {tracks_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 清理过程中发生错误: {e}")
        return False

def main():
    """主函数"""
    print("🧹 分佣管理测试数据清理工具")
    print("=" * 50)
    
    success = clean_test_data()
    
    if success:
        print("\n🎉 清理完成！")
        print("现在分佣管理中的数据应该更加干净了")
    else:
        print("\n❌ 清理失败，请检查错误信息")

if __name__ == '__main__':
    main()
