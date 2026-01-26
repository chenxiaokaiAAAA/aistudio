#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
优惠券数据库表创建脚本
用于创建用户自主领取优惠券所需的数据库表
"""

import sqlite3
from datetime import datetime, timedelta

def create_coupon_tables():
    """创建优惠券相关数据库表"""
    
    # 连接数据库
    conn = sqlite3.connect('instance/pet_painting.db')
    cursor = conn.cursor()
    
    try:
        print("🔧 开始创建优惠券数据库表...")
        
        # 创建优惠券表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coupons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                code VARCHAR(20) UNIQUE NOT NULL,
                type VARCHAR(20) NOT NULL,
                value REAL NOT NULL,
                min_amount REAL DEFAULT 0.0,
                max_discount REAL,
                total_count INTEGER NOT NULL,
                used_count INTEGER DEFAULT 0,
                per_user_limit INTEGER DEFAULT 1,
                start_time DATETIME NOT NULL,
                end_time DATETIME NOT NULL,
                status VARCHAR(20) DEFAULT 'active',
                description TEXT,
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ 优惠券表 (coupons) 创建成功")
        
        # 创建用户优惠券表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_coupons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id VARCHAR(50) NOT NULL,
                coupon_id INTEGER NOT NULL,
                coupon_code VARCHAR(20) NOT NULL,
                status VARCHAR(20) DEFAULT 'unused',
                order_id VARCHAR(50),
                get_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                use_time DATETIME,
                expire_time DATETIME,
                FOREIGN KEY (coupon_id) REFERENCES coupons (id)
            )
        ''')
        print("✅ 用户优惠券表 (user_coupons) 创建成功")
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_coupons_code ON coupons (code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_coupons_status ON coupons (status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_coupons_time ON coupons (start_time, end_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_coupons_user_id ON user_coupons (user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_coupons_coupon_id ON user_coupons (coupon_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_coupons_status ON user_coupons (status)')
        print("✅ 数据库索引创建成功")
        
        # 插入示例优惠券数据
        insert_sample_coupons(cursor)
        
        conn.commit()
        print("🎉 优惠券数据库表创建完成！")
        
    except Exception as e:
        print(f"❌ 创建数据库表失败: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

def insert_sample_coupons(cursor):
    """插入示例优惠券数据"""
    try:
        # 检查是否已有数据
        cursor.execute('SELECT COUNT(*) FROM coupons')
        count = cursor.fetchone()[0]
        
        if count > 0:
            print("ℹ️ 优惠券表已有数据，跳过示例数据插入")
            return
        
        print("📝 插入示例优惠券数据...")
        
        # 示例优惠券数据
        sample_coupons = [
            {
                'name': '新用户专享券',
                'code': 'NEWUSER10',
                'type': 'cash',
                'value': 10.0,
                'min_amount': 50.0,
                'max_discount': None,
                'total_count': 1000,
                'used_count': 0,
                'per_user_limit': 1,
                'start_time': datetime.now(),
                'end_time': datetime.now() + timedelta(days=30),
                'status': 'active',
                'description': '新用户专享，满50元减10元'
            },
            {
                'name': '限时折扣券',
                'code': 'DISCOUNT20',
                'type': 'discount',
                'value': 20.0,  # 20%折扣
                'min_amount': 100.0,
                'max_discount': 50.0,
                'total_count': 500,
                'used_count': 0,
                'per_user_limit': 2,
                'start_time': datetime.now(),
                'end_time': datetime.now() + timedelta(days=7),
                'status': 'active',
                'description': '限时8折优惠，最高减50元'
            },
            {
                'name': '免费体验券',
                'code': 'FREE49',
                'type': 'free',
                'value': 49.0,
                'min_amount': 49.0,
                'max_discount': None,
                'total_count': 100,
                'used_count': 0,
                'per_user_limit': 1,
                'start_time': datetime.now(),
                'end_time': datetime.now() + timedelta(days=15),
                'status': 'active',
                'description': '免费体验券，49元以下订单免费'
            }
        ]
        
        for coupon in sample_coupons:
            cursor.execute('''
                INSERT INTO coupons (
                    name, code, type, value, min_amount, max_discount,
                    total_count, used_count, per_user_limit,
                    start_time, end_time, status, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                coupon['name'], coupon['code'], coupon['type'], coupon['value'],
                coupon['min_amount'], coupon['max_discount'], coupon['total_count'],
                coupon['used_count'], coupon['per_user_limit'], coupon['start_time'],
                coupon['end_time'], coupon['status'], coupon['description']
            ))
        
        print(f"✅ 成功插入 {len(sample_coupons)} 张示例优惠券")
        
    except Exception as e:
        print(f"❌ 插入示例数据失败: {str(e)}")

def check_tables():
    """检查表是否创建成功"""
    conn = sqlite3.connect('instance/pet_painting.db')
    cursor = conn.cursor()
    
    try:
        # 检查优惠券表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='coupons'")
        coupons_table = cursor.fetchone()
        
        # 检查用户优惠券表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_coupons'")
        user_coupons_table = cursor.fetchone()
        
        if coupons_table and user_coupons_table:
            print("✅ 数据库表检查通过")
            
            # 显示表结构
            print("\n📊 优惠券表结构:")
            cursor.execute("PRAGMA table_info(coupons)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            print("\n📊 用户优惠券表结构:")
            cursor.execute("PRAGMA table_info(user_coupons)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # 显示示例数据
            print("\n🎫 示例优惠券数据:")
            cursor.execute("SELECT name, code, type, value, min_amount FROM coupons LIMIT 3")
            coupons = cursor.fetchall()
            for coupon in coupons:
                print(f"  - {coupon[0]} ({coupon[1]}): {coupon[2]}类型, 面值{coupon[3]}, 最低消费{coupon[4]}")
                
        else:
            print("❌ 数据库表检查失败")
            
    except Exception as e:
        print(f"❌ 检查表失败: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 优惠券数据库表创建工具")
    print("=" * 50)
    
    # 创建表
    create_coupon_tables()
    
    # 检查表
    print("\n🔍 检查数据库表...")
    check_tables()
    
    print("\n✨ 完成！现在可以使用优惠券功能了。")