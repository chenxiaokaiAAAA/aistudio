#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化加盟商充值表（包含赠送金额字段）
运行方法: python init_recharge_table_with_bonus.py
"""

from test_server import app, db, FranchiseeRecharge, FranchiseeAccount
from sqlalchemy import text

def init_recharge_table():
    """初始化充值表"""
    with app.app_context():
        try:
            print("正在创建数据库表...")
            # 创建所有表（包括新字段）
            db.create_all()
            print("✅ 数据库表创建完成")
            
            # 检查表是否存在
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'franchisee_recharges' in tables:
                print("✅ franchisee_recharges 表已创建")
                
                # 检查字段
                columns = inspector.get_columns('franchisee_recharges')
                column_names = [col['name'] for col in columns]
                
                print(f"📋 表包含以下字段：")
                for col in columns:
                    print(f"   - {col['name']} ({col['type']})")
                
                # 检查新字段是否存在
                if 'bonus_amount' in column_names:
                    print("✅ bonus_amount 字段存在")
                else:
                    print("❌ bonus_amount 字段不存在")
                
                if 'total_amount' in column_names:
                    print("✅ total_amount 字段存在")
                else:
                    print("❌ total_amount 字段不存在")
                    
            else:
                print("❌ franchisee_recharges 表未创建")
            
            print("\n🎉 初始化完成！")
            
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    print("=" * 60)
    print("加盟商充值表初始化（含赠送功能）")
    print("=" * 60)
    print()
    init_recharge_table()



