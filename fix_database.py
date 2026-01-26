# -*- coding: utf-8 -*-
"""
临时脚本：添加 free_selection_count 字段
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # 检查字段是否已存在
        result = db.session.execute(text("PRAGMA table_info(products)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'free_selection_count' in columns:
            print("OK: free_selection_count field already exists")
        else:
            # 添加字段
            print("Adding free_selection_count field...")
            db.session.execute(text("ALTER TABLE products ADD COLUMN free_selection_count INTEGER DEFAULT 1"))
            db.session.execute(text("UPDATE products SET free_selection_count = 1 WHERE free_selection_count IS NULL"))
            db.session.commit()
            print("OK: free_selection_count field added successfully")
    except Exception as e:
        print(f"错误: {e}")
        db.session.rollback()
