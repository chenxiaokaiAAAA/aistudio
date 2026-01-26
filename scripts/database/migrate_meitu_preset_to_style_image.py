# -*- coding: utf-8 -*-
"""
数据库迁移脚本：将 meitu_api_preset 表的 product_id 改为 style_image_id
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
        
        # 检查是否已经有 style_image_id 列
        cursor.execute("PRAGMA table_info(meitu_api_preset)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'style_image_id' in columns:
            print("✅ style_image_id 列已存在，无需迁移")
            return True
        
        # 检查是否有 product_id 列
        has_product_id = 'product_id' in columns
        
        # 获取现有数据（如果有）
        cursor.execute("SELECT * FROM meitu_api_preset")
        existing_data = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        
        print(f"📊 找到 {len(existing_data)} 条现有记录")
        
        if len(existing_data) > 0:
            print("⚠️  警告：表中存在数据，由于 product_id 和 style_image_id 没有直接映射关系，")
            print("   这些数据将被清空。如果需要保留，请先手动导出数据。")
            response = input("是否继续？(y/n): ")
            if response.lower() != 'y':
                print("❌ 迁移已取消")
                return False
        
        # 创建备份表
        backup_table_name = f"meitu_api_preset_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        cursor.execute(f"CREATE TABLE {backup_table_name} AS SELECT * FROM meitu_api_preset")
        print(f"✅ 创建备份表: {backup_table_name}")
        
        # 删除旧表
        cursor.execute("DROP TABLE meitu_api_preset")
        print("✅ 删除旧表")
        
        # 创建新表（带 style_image_id）
        print("✅ 创建新表结构...")
        cursor.execute("""
            CREATE TABLE meitu_api_preset (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                style_image_id INTEGER NOT NULL,
                preset_id VARCHAR(100) NOT NULL,
                preset_name VARCHAR(200),
                description TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (style_image_id) REFERENCES style_image(id)
            )
        """)
        print("✅ 新表创建完成")
        
        # 提交更改
        conn.commit()
        print("\n🎉 迁移成功！")
        print(f"📝 备份表: {backup_table_name}")
        print("⚠️  注意：原有数据已备份，但未迁移到新表（因为 product_id 和 style_image_id 无法直接映射）")
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
    print("将 product_id 改为 style_image_id")
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
