# -*- coding: utf-8 -*-
"""
添加退款申请相关字段到orders表
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from test_server import app, db
    from sqlalchemy import text
    
    print("开始添加退款申请相关字段到orders表...")
    
    with app.app_context():
        # 检查字段是否已存在
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('orders')]
        
        # 需要添加的字段
        fields_to_add = [
            ('refund_request_reason', 'TEXT'),
            ('refund_request_time', 'DATETIME'),
            ('refund_request_status', 'VARCHAR(20)')
        ]
        
        for field_name, field_type in fields_to_add:
            if field_name not in columns:
                try:
                    sql = f"ALTER TABLE orders ADD COLUMN {field_name} {field_type}"
                    db.session.execute(text(sql))
                    print(f"[OK] 已添加字段: {field_name}")
                except Exception as e:
                    print(f"[WARN] 添加字段 {field_name} 失败: {e}")
            else:
                print(f"[INFO] 字段 {field_name} 已存在，跳过")
        
        db.session.commit()
        print("[OK] 退款申请字段添加完成！")
        
except ImportError as e:
    print(f"[ERROR] 导入失败: {e}")
    print("请确保已正确安装所有依赖，并且数据库已初始化")
except Exception as e:
    print(f"[ERROR] 添加字段失败: {e}")
    import traceback
    traceback.print_exc()
    if 'db' in locals():
        db.session.rollback()
