#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动添加 bonus_amount 和 total_amount 字段
运行方法: python add_bonus_fields_manual.py
"""

from test_server import app, db
from sqlalchemy import text

def add_bonus_fields():
    """添加赠送金额字段"""
    with app.app_context():
        try:
            print("正在添加新字段...")
            
            # 检查字段是否已存在
            inspector = db.inspect(db.engine)
            columns = inspector.get_columns('franchisee_recharges')
            column_names = [col['name'] for col in columns]
            
            print(f"当前字段：{column_names}")
            
            # 添加 bonus_amount 字段
            if 'bonus_amount' not in column_names:
                print("添加 bonus_amount 字段...")
                db.session.execute(text("ALTER TABLE franchisee_recharges ADD COLUMN bonus_amount REAL DEFAULT 0.0"))
                print("✅ bonus_amount 字段已添加")
            else:
                print("✅ bonus_amount 字段已存在")
            
            # 添加 total_amount 字段
            if 'total_amount' not in column_names:
                print("添加 total_amount 字段...")
                db.session.execute(text("ALTER TABLE franchisee_recharges ADD COLUMN total_amount REAL"))
                print("✅ total_amount 字段已添加")
            else:
                print("✅ total_amount 字段已存在")
            
            # 更新现有记录
            print("正在更新现有记录...")
            db.session.execute(text("UPDATE franchisee_recharges SET bonus_amount = 0 WHERE bonus_amount IS NULL"))
            db.session.execute(text("UPDATE franchisee_recharges SET total_amount = amount WHERE total_amount IS NULL"))
            
            db.session.commit()
            
            print("\n✅ 字段添加成功！")
            
            # 重新检查字段
            inspector = db.inspect(db.engine)
            columns = inspector.get_columns('franchisee_recharges')
            column_names = [col['name'] for col in columns]
            
            print(f"\n📋 更新后的字段：{column_names}")
            
        except Exception as e:
            print(f"❌ 操作失败: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    print("=" * 60)
    print("添加充值赠送金额字段")
    print("=" * 60)
    print()
    add_bonus_fields()



