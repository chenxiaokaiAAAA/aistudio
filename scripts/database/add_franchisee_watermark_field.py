#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
为加盟商账户表添加水印字段的数据库迁移脚本
"""

import os
import sys
from sqlalchemy import text

def add_watermark_field():
    """为 franchisee_accounts 表添加 watermark_path 字段"""
    try:
        from test_server import app, db
        
        with app.app_context():
            from sqlalchemy import inspect
            
            # 检查字段是否已存在
            result = db.session.execute(text("PRAGMA table_info(franchisee_accounts)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'watermark_path' in columns:
                print("✅ watermark_path 字段已存在，跳过迁移")
                return True
            
            # 添加 watermark_path 字段
            print("正在添加 watermark_path 字段...")
            db.session.execute(text("""
                ALTER TABLE franchisee_accounts 
                ADD COLUMN watermark_path VARCHAR(200)
            """))
            db.session.commit()
            
            print("✅ watermark_path 字段添加成功")
            return True
            
    except Exception as e:
        print(f"❌ 添加字段失败: {str(e)}")
        return False

if __name__ == '__main__':
    add_watermark_field()


