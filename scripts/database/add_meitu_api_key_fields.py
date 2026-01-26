#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 meitu_api_config 表的 api_key 和 api_secret 字段
如果表中有 app_id 和 secret_id 字段，会将数据迁移到新字段
"""
import os
import sys
import sqlite3
from datetime import datetime

# 获取项目根目录
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

def migrate_database(db_path=None):
    """执行数据库迁移"""
    if db_path is None:
        # 默认数据库路径
        db_path = os.path.join(project_root, 'instance', 'pet_painting.db')
        if not os.path.exists(db_path):
            # 尝试其他可能的路径
            alt_paths = [
                os.path.join(project_root, 'pet_painting.db'),
                os.path.join(project_root, 'instance', 'app.db'),
            ]
            for alt_path in alt_paths:
                if os.path.exists(alt_path):
                    db_path = alt_path
                    break
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    # 备份数据库
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"📦 备份数据库到: {backup_path}")
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✅ 备份完成")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n🔄 开始数据库迁移...")
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meitu_api_config'")
        if not cursor.fetchone():
            print("⚠️  meitu_api_config 表不存在，无需迁移")
            conn.close()
            return True
        
        # 检查现有列
        cursor.execute("PRAGMA table_info(meitu_api_config)")
        columns = {column[1]: column for column in cursor.fetchall()}
        column_names = list(columns.keys())
        
        print(f"📋 当前表的列: {', '.join(column_names)}")
        
        has_api_key = 'api_key' in column_names
        has_api_secret = 'api_secret' in column_names
        has_app_id = 'app_id' in column_names
        has_secret_id = 'secret_id' in column_names
        
        # 添加 api_key 字段（如果不存在）
        if not has_api_key:
            print("📝 添加 api_key 字段到 meitu_api_config 表...")
            cursor.execute("""
                ALTER TABLE meitu_api_config 
                ADD COLUMN api_key VARCHAR(100)
            """)
            
            # 如果存在 app_id 字段，迁移数据
            if has_app_id:
                print("📝 从 app_id 迁移数据到 api_key...")
                cursor.execute("""
                    UPDATE meitu_api_config 
                    SET api_key = app_id 
                    WHERE api_key IS NULL AND app_id IS NOT NULL
                """)
            
            conn.commit()
            print("✅ api_key 字段添加成功")
        else:
            print("✅ api_key 字段已存在")
        
        # 添加 api_secret 字段（如果不存在）
        if not has_api_secret:
            print("📝 添加 api_secret 字段到 meitu_api_config 表...")
            cursor.execute("""
                ALTER TABLE meitu_api_config 
                ADD COLUMN api_secret VARCHAR(100)
            """)
            
            # 如果存在 secret_id 字段，迁移数据
            if has_secret_id:
                print("📝 从 secret_id 迁移数据到 api_secret...")
                cursor.execute("""
                    UPDATE meitu_api_config 
                    SET api_secret = secret_id 
                    WHERE api_secret IS NULL AND secret_id IS NOT NULL
                """)
            
            conn.commit()
            print("✅ api_secret 字段添加成功")
        else:
            print("✅ api_secret 字段已存在")
        
        # 验证字段是否添加成功
        cursor.execute("PRAGMA table_info(meitu_api_config)")
        columns_after = {column[1]: column for column in cursor.fetchall()}
        
        if 'api_key' in columns_after and 'api_secret' in columns_after:
            print("✅ 验证成功：api_key 和 api_secret 字段已添加到 meitu_api_config 表")
        else:
            print("❌ 验证失败：字段未成功添加")
            conn.close()
            return False
        
        conn.close()
        print("\n✅ 数据库迁移完成！")
        return True
        
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"❌ 数据库迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("美图API配置表迁移脚本")
    print("添加 api_key 和 api_secret 字段")
    print("=" * 60)
    
    db_path = sys.argv[1] if len(sys.argv) > 1 else None
    success = migrate_database(db_path)
    
    if success:
        print("\n✅ 迁移成功！")
        sys.exit(0)
    else:
        print("\n❌ 迁移失败！")
        sys.exit(1)
