#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 添加商家新字段
"""

import sys
import os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db
from sqlalchemy import text

def migrate_merchant_fields():
    """添加商家新字段到数据库"""
    
    with app.app_context():
        try:
            print("开始添加商家新字段...")
            
            # 检查user表结构
            result = db.session.execute(text("PRAGMA table_info(user)"))
            user_columns = [row[1] for row in result.fetchall()]
            print(f"当前user表字段: {user_columns}")
            
            # 需要添加的新字段
            new_fields = [
                ('cooperation_date', 'DATE'),
                ('merchant_address', 'TEXT'),
                ('account_name', 'VARCHAR(100)'),
                ('account_number', 'VARCHAR(50)'),
                ('bank_name', 'VARCHAR(100)')
            ]
            
            # 添加缺失的字段
            for field_name, field_type in new_fields:
                if field_name not in user_columns:
                    print(f"添加字段 {field_name} ({field_type})...")
                    db.session.execute(text(f"ALTER TABLE user ADD COLUMN {field_name} {field_type}"))
                    db.session.commit()
                    print(f"✅ {field_name} 字段添加成功")
                else:
                    print(f"⚠️ {field_name} 字段已存在，跳过")
            
            print("🎉 商家字段迁移完成!")
            
        except Exception as e:
            print(f"❌ 迁移失败: {str(e)}")
            db.session.rollback()
            return False
    
    return True

if __name__ == "__main__":
    print("🚀 开始商家字段数据库迁移...")
    print("=" * 50)
    
    success = migrate_merchant_fields()
    
    print("=" * 50)
    if success:
        print("✅ 迁移完成!")
    else:
        print("❌ 迁移失败!")
