# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为 api_provider_configs 表添加 is_sync_api 字段
运行此脚本前请先备份数据库！
"""

import sqlite3
import os
import sys
from datetime import datetime

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def migrate_database(db_path=None):
    """执行数据库迁移"""
    
    # 尝试从环境变量或默认路径获取数据库路径
    if not db_path:
        # 尝试多个可能的数据库路径
        possible_paths = [
            'instance/pet_painting.db',
            'pet_painting.db',
            os.path.join(project_root, 'instance', 'pet_painting.db'),
            os.path.join(project_root, 'pet_painting.db')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                db_path = path
                break
        
        if not db_path:
            print("❌ 未找到数据库文件，请手动指定数据库路径")
            print("可能的路径：")
            for path in possible_paths:
                print(f"  - {path}")
            return False
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    # 备份数据库
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"📦 备份数据库到: {backup_path}")
    import shutil
    shutil.copy2(db_path, backup_path)
    print("✅ 数据库备份完成")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n🔄 开始数据库迁移...")
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='api_provider_configs'")
        if not cursor.fetchone():
            print("⚠️  api_provider_configs 表不存在，无需迁移")
            conn.close()
            return True
        
        # 检查是否已经有 is_sync_api 列
        cursor.execute("PRAGMA table_info(api_provider_configs)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_sync_api' in columns:
            print("✅ is_sync_api 列已存在，无需迁移")
            conn.close()
            return True
        
        # 添加 is_sync_api 字段
        print("📝 添加 is_sync_api 字段到 api_provider_configs 表...")
        cursor.execute("""
            ALTER TABLE api_provider_configs 
            ADD COLUMN is_sync_api BOOLEAN DEFAULT 0 NOT NULL
        """)
        
        conn.commit()
        print("✅ is_sync_api 字段添加成功")
        
        # 根据 api_type 自动设置 is_sync_api 的值
        # gemini-native 通常是同步API
        print("📝 根据 api_type 自动设置 is_sync_api 的值...")
        cursor.execute("""
            UPDATE api_provider_configs 
            SET is_sync_api = 1 
            WHERE api_type = 'gemini-native'
        """)
        conn.commit()
        print("✅ 已根据 api_type 自动设置 is_sync_api 的值（gemini-native 类型设为同步API）")
        
        # 验证字段是否添加成功
        cursor.execute("PRAGMA table_info(api_provider_configs)")
        columns_after = [column[1] for column in cursor.fetchall()]
        if 'is_sync_api' in columns_after:
            print("✅ 验证成功：is_sync_api 字段已添加到 api_provider_configs 表")
        else:
            print("❌ 验证失败：is_sync_api 字段未成功添加")
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
    print("API服务商配置表迁移脚本")
    print("=" * 60)
    print("\n此脚本将为 api_provider_configs 表添加 is_sync_api 字段")
    print("该字段用于区分同步API和异步API\n")
    
    # 如果提供了命令行参数，使用该路径
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = None
    
    success = migrate_database(db_path)
    
    if success:
        print("\n✅ 迁移成功！")
        sys.exit(0)
    else:
        print("\n❌ 迁移失败！")
        sys.exit(1)

