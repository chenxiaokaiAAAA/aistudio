#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扩展优惠券表结构
添加新字段支持团购核销、分享领券等功能
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_server import app, db
from sqlalchemy import text

def extend_coupon_table():
    """扩展Coupon表结构"""
    try:
        with app.app_context():
            # 检查字段是否已存在
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('coupons')]
            
            # 添加新字段（SQLite不支持COMMENT，移除COMMENT子句）
            new_columns = {
                'source_type': "ALTER TABLE coupons ADD COLUMN source_type VARCHAR(20) DEFAULT 'system'",
                'groupon_order_id': "ALTER TABLE coupons ADD COLUMN groupon_order_id VARCHAR(100)",
                'verify_amount': "ALTER TABLE coupons ADD COLUMN verify_amount DECIMAL(10,2)",
                'is_random_code': "ALTER TABLE coupons ADD COLUMN is_random_code BOOLEAN DEFAULT 0",
                'qr_code_url': "ALTER TABLE coupons ADD COLUMN qr_code_url VARCHAR(500)",
                'share_reward_amount': "ALTER TABLE coupons ADD COLUMN share_reward_amount DECIMAL(10,2)",
                'share_reward_type': "ALTER TABLE coupons ADD COLUMN share_reward_type VARCHAR(20)"
            }
            
            for col_name, sql in new_columns.items():
                if col_name not in columns:
                    print(f"添加字段: {col_name}")
                    db.session.execute(text(sql))
                    db.session.commit()
                    print(f"✅ 字段 {col_name} 添加成功")
                else:
                    print(f"⚠️  字段 {col_name} 已存在，跳过")
            
            print("✅ Coupon表结构扩展完成")
            
    except Exception as e:
        print(f"❌ 扩展Coupon表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals() and 'app' in locals():
            try:
                with app.app_context():
                    db.session.rollback()
            except:
                pass

def create_share_record_table():
    """创建ShareRecord表"""
    try:
        with app.app_context():
            # 检查表是否存在
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'share_records' not in tables:
                print("创建ShareRecord表...")
                sql = """
                CREATE TABLE share_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sharer_user_id VARCHAR(50) NOT NULL,
                    shared_user_id VARCHAR(50),
                    share_type VARCHAR(20) DEFAULT 'work',
                    work_id INTEGER,
                    order_id INTEGER,
                    sharer_coupon_id INTEGER,
                    shared_coupon_id INTEGER,
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
                db.session.execute(text(sql))
                db.session.commit()
                print("✅ ShareRecord表创建成功")
            else:
                print("⚠️  ShareRecord表已存在，跳过")
                
    except Exception as e:
        print(f"❌ 创建ShareRecord表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals() and 'app' in locals():
            with app.app_context():
                db.session.rollback()

if __name__ == '__main__':
    print("=" * 50)
    print("开始扩展优惠券表结构...")
    print("=" * 50)
    
    extend_coupon_table()
    create_share_record_table()
    
    print("=" * 50)
    print("✅ 所有操作完成")
    print("=" * 50)
