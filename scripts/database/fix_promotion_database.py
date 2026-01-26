#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复数据库表结构 - 添加推广码字段
"""

from test_server import app, db
import sqlite3

def fix_database_schema():
    """修复数据库表结构"""
    with app.app_context():
        try:
            # 获取数据库文件路径
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            print(f"数据库文件路径: {db_path}")
            
            # 连接数据库
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 检查表结构
            cursor.execute("PRAGMA table_info('order')")
            columns = [column[1] for column in cursor.fetchall()]
            print(f"当前order表字段: {columns}")
            
            # 添加新字段
            if 'promotion_code' not in columns:
                cursor.execute('ALTER TABLE "order" ADD COLUMN promotion_code VARCHAR(20)')
                print('✅ 添加 promotion_code 字段成功')
            else:
                print('ℹ️  promotion_code 字段已存在')
            
            if 'referrer_user_id' not in columns:
                cursor.execute('ALTER TABLE "order" ADD COLUMN referrer_user_id VARCHAR(50)')
                print('✅ 添加 referrer_user_id 字段成功')
            else:
                print('ℹ️  referrer_user_id 字段已存在')
            
            # 提交更改
            conn.commit()
            conn.close()
            
            print('🎉 数据库表结构修复完成！')
            
        except Exception as e:
            print(f'❌ 修复失败: {e}')

if __name__ == '__main__':
    fix_database_schema()
