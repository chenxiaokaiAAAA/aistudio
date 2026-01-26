# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为 meitu_api_preset 表添加 style_category_id 字段
运行此脚本前请先备份数据库！
"""

import sqlite3
import os
import sys
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def migrate_database(db_path='instance/pet_painting.db'):
    """执行数据库迁移"""
    
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
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meitu_api_preset'")
        if not cursor.fetchone():
            print("⚠️  meitu_api_preset 表不存在，无需迁移")
            return True
        
        # 检查是否已经有 style_category_id 列
        cursor.execute("PRAGMA table_info(meitu_api_preset)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'style_category_id' in columns:
            print("✅ style_category_id 列已存在，无需迁移")
            return True
        
        # 检查 style_image_id 是否可以为空
        has_nullable_image_id = False
        for col in cursor.execute("PRAGMA table_info(meitu_api_preset)").fetchall():
            if col[1] == 'style_image_id':
                has_nullable_image_id = col[3] == 0  # 0表示可以为NULL
                break
        
        print("✅ 添加 style_category_id 字段...")
        cursor.execute("""
            ALTER TABLE meitu_api_preset 
            ADD COLUMN style_category_id INTEGER
        """)
        print("✅ style_category_id 字段添加成功")
        
        # 如果 style_image_id 不能为空，需要修改为可空
        if not has_nullable_image_id:
            print("⚠️  需要修改 style_image_id 为可空...")
            # SQLite不支持直接修改列，需要重建表
            print("   由于SQLite限制，需要重建表...")
            
            # 获取现有数据
            cursor.execute("SELECT * FROM meitu_api_preset")
            existing_data = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]
            
            # 创建备份表
            backup_table_name = f"meitu_api_preset_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            cursor.execute(f"CREATE TABLE {backup_table_name} AS SELECT * FROM meitu_api_preset")
            print(f"✅ 创建备份表: {backup_table_name}")
            
            # 删除旧表
            cursor.execute("DROP TABLE meitu_api_preset")
            
            # 创建新表（style_image_id 可为空）
            cursor.execute("""
                CREATE TABLE meitu_api_preset (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    style_category_id INTEGER,
                    style_image_id INTEGER,
                    preset_id VARCHAR(100) NOT NULL,
                    preset_name VARCHAR(200),
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (style_category_id) REFERENCES style_category(id),
                    FOREIGN KEY (style_image_id) REFERENCES style_image(id)
                )
            """)
            print("✅ 新表创建完成")
            
            # 恢复数据（如果有）
            if existing_data:
                print(f"📊 恢复 {len(existing_data)} 条数据...")
                for row in existing_data:
                    row_dict = dict(zip(column_names, row))
                    cursor.execute("""
                        INSERT INTO meitu_api_preset 
                        (id, style_category_id, style_image_id, preset_id, preset_name, description, is_active, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row_dict.get('id'),
                        row_dict.get('style_category_id'),
                        row_dict.get('style_image_id'),
                        row_dict.get('preset_id'),
                        row_dict.get('preset_name'),
                        row_dict.get('description'),
                        row_dict.get('is_active', 1),
                        row_dict.get('created_at'),
                        row_dict.get('updated_at')
                    ))
                print("✅ 数据恢复完成")
        
        # 提交更改
        conn.commit()
        print("\n🎉 迁移成功！")
        return True
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("美图API预设表迁移脚本")
    print("添加 style_category_id 字段，支持映射到整个分类")
    print("=" * 60)
    
    # 查找数据库文件
    db_paths = [
        'instance/pet_painting.db',
        '../instance/pet_painting.db',
        os.path.join(os.path.dirname(__file__), '..', '..', 'instance', 'pet_painting.db'),
        'pet_painting.db'
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ 未找到数据库文件，请手动指定路径")
        print("可用路径:")
        for path in db_paths:
            print(f"  - {path}")
        sys.exit(1)
    
    print(f"📁 数据库路径: {db_path}\n")
    
    if migrate_database(db_path):
        print("\n✅ 迁移完成！")
        sys.exit(0)
    else:
        print("\n❌ 迁移失败！")
        sys.exit(1)
