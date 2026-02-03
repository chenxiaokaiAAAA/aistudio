#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 添加用户权限字段
添加预览权限、Playground使用次数限制等字段
"""

import sys
import os
import sqlite3
from datetime import datetime, date

# 设置编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def migrate_user_permission_fields():
    """添加用户权限字段到数据库"""
    
    # 查找数据库文件
    db_paths = [
        'instance/pet_painting.db',
        'pet_painting.db',
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'instance', 'pet_painting.db')
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("错误: 找不到数据库文件")
        return False
    
    print(f"使用数据库文件: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("开始添加用户权限字段...")
        
        # 检查user表结构
        cursor.execute("PRAGMA table_info(user)")
        user_columns = [row[1] for row in cursor.fetchall()]
        print(f"当前user表字段: {user_columns}")
        
        # 需要添加的新字段
        new_fields = [
            ('can_preview', 'BOOLEAN DEFAULT 1'),  # 预览权限，默认开启
            ('playground_daily_limit', 'INTEGER DEFAULT 0'),  # Playground每日使用次数限制，0表示无限制
            ('playground_used_today', 'INTEGER DEFAULT 0'),  # 今日已使用次数
            ('playground_last_reset_date', 'DATE'),  # 上次重置日期
            ('page_permissions', 'TEXT'),  # 页面权限配置（JSON格式，存储允许访问的页面列表）
            ('permissions', 'TEXT'),  # 其他权限配置（JSON格式）
            ('created_at', 'DATETIME'),  # 创建时间
            ('updated_at', 'DATETIME')  # 更新时间
        ]
        
        # 添加缺失的字段
        for field_name, field_type in new_fields:
            if field_name not in user_columns:
                print(f"添加字段 {field_name} ({field_type})...")
                try:
                    cursor.execute(f"ALTER TABLE user ADD COLUMN {field_name} {field_type}")
                    conn.commit()
                    print(f"成功: {field_name} 字段添加成功")
                except Exception as e:
                    error_msg = str(e).lower()
                    if "duplicate column name" in error_msg or "already exists" in error_msg:
                        print(f"警告: {field_name} 字段已存在，跳过")
                    else:
                        print(f"错误: 添加字段 {field_name} 失败: {str(e)}")
                        raise
            else:
                print(f"警告: {field_name} 字段已存在，跳过")
        
        # 初始化现有用户的默认值
        print("\n初始化现有用户的默认值...")
        try:
            # 设置can_preview默认值为1（如果为NULL）
            cursor.execute("UPDATE user SET can_preview = 1 WHERE can_preview IS NULL")
            # 设置playground_daily_limit默认值为0（如果为NULL）
            cursor.execute("UPDATE user SET playground_daily_limit = 0 WHERE playground_daily_limit IS NULL")
            # 设置playground_used_today默认值为0（如果为NULL）
            cursor.execute("UPDATE user SET playground_used_today = 0 WHERE playground_used_today IS NULL")
            # 设置created_at和updated_at（如果为NULL）
            now = datetime.now().isoformat()
            cursor.execute(f"UPDATE user SET created_at = '{now}' WHERE created_at IS NULL")
            cursor.execute(f"UPDATE user SET updated_at = '{now}' WHERE updated_at IS NULL")
            conn.commit()
            print("成功: 默认值初始化完成")
        except Exception as e:
            conn.rollback()
            print(f"警告: 初始化默认值失败（可忽略）: {str(e)}")
        
        conn.close()
        print("\n完成: 用户权限字段迁移完成!")
        return True
        
    except Exception as e:
        print(f"错误: 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("用户权限字段数据库迁移脚本")
    print("=" * 60)
    print()
    
    if migrate_user_permission_fields():
        print("\n成功: 迁移成功完成！")
        print("现在可以使用管理员账户配置功能了。")
    else:
        print("\n错误: 迁移失败，请检查错误信息。")
        sys.exit(1)
