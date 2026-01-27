#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加产品额外赠送工作流配置表的数据库迁移脚本
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test_server import app, db
from sqlalchemy import text

def add_product_bonus_workflow_table():
    """创建产品额外赠送工作流配置表"""
    with app.app_context():
        try:
            # 检查表是否已存在
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'product_bonus_workflows' not in existing_tables:
                # 创建表
                db.engine.execute(text("""
                    CREATE TABLE product_bonus_workflows (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER NOT NULL,
                        workflow_type VARCHAR(20) NOT NULL DEFAULT 'api_template',
                        api_template_id INTEGER,
                        style_image_id INTEGER,
                        workflow_name VARCHAR(200),
                        workflow_description TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        sort_order INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (product_id) REFERENCES products(id),
                        FOREIGN KEY (api_template_id) REFERENCES api_templates(id),
                        FOREIGN KEY (style_image_id) REFERENCES style_image(id)
                    )
                """))
                print("[成功] 产品额外赠送工作流配置表创建成功")
            else:
                print("[信息] 产品额外赠送工作流配置表已存在")
            
            # 检查唯一约束是否存在
            try:
                # 检查并创建唯一约束（产品+API模板+工作流类型）
                db.engine.execute(text("""
                    CREATE UNIQUE INDEX IF NOT EXISTS _product_api_template_uc 
                    ON product_bonus_workflows(product_id, api_template_id, workflow_type)
                    WHERE api_template_id IS NOT NULL
                """))
                print("[成功] 产品+API模板唯一约束创建成功")
            except Exception as e:
                print(f"[警告] 产品+API模板唯一约束可能已存在: {e}")
            
            try:
                # 检查并创建唯一约束（产品+风格图片+工作流类型）
                db.engine.execute(text("""
                    CREATE UNIQUE INDEX IF NOT EXISTS _product_style_image_uc 
                    ON product_bonus_workflows(product_id, style_image_id, workflow_type)
                    WHERE style_image_id IS NOT NULL
                """))
                print("[成功] 产品+风格图片唯一约束创建成功")
            except Exception as e:
                print(f"[警告] 产品+风格图片唯一约束可能已存在: {e}")
            
            print("[完成] 数据库迁移完成")
            
        except Exception as e:
            print(f"[失败] 数据库迁移失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    add_product_bonus_workflow_table()
