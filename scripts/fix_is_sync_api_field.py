# -*- coding: utf-8 -*-
"""
快速修复脚本：为 api_provider_configs 表添加 is_sync_api 字段
"""
import sqlite3
import os
import sys

def fix_database(db_path='instance/pet_painting.db'):
    """修复数据库字段"""
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查字段是否存在
        cursor.execute("PRAGMA table_info(api_provider_configs)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_sync_api' in columns:
            print("✅ is_sync_api 字段已存在，无需修复")
            conn.close()
            return True
        
        # 添加字段
        print("添加 is_sync_api 字段...")
        cursor.execute("""
            ALTER TABLE api_provider_configs 
            ADD COLUMN is_sync_api BOOLEAN DEFAULT 0 NOT NULL
        """)
        conn.commit()
        print("✅ is_sync_api 字段添加成功")
        
        # 根据 api_type 自动设置值
        print("根据 api_type 自动设置 is_sync_api 的值...")
        cursor.execute("""
            UPDATE api_provider_configs 
            SET is_sync_api = 1 
            WHERE api_type = 'gemini-native'
        """)
        conn.commit()
        print("✅ 已根据 api_type 自动设置 is_sync_api 的值")
        
        conn.close()
        print("\n✅ 数据库修复完成！")
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        conn.rollback()
        conn.close()
        return False

if __name__ == '__main__':
    # 尝试多个可能的数据库路径
    possible_paths = [
        'instance/pet_painting.db',
        'pet_painting.db',
        os.path.join('AI-studio', 'instance', 'pet_painting.db'),
        os.path.join('AI-studio', 'pet_painting.db')
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ 未找到数据库文件")
        print("请手动指定数据库路径：")
        print("  python scripts/fix_is_sync_api_field.py <数据库路径>")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    print(f"使用数据库: {db_path}")
    success = fix_database(db_path)
    
    if success:
        print("\n✅ 修复成功！请重启服务器。")
        sys.exit(0)
    else:
        print("\n❌ 修复失败！")
        sys.exit(1)
