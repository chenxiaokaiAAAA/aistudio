# 数据库迁移脚本 - 添加高清图片字段
# 运行此脚本来更新现有数据库

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """迁移数据库，添加高清图片字段"""
    
    db_path = 'pet_painting.db'
    
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在")
        return
    
    # 备份原数据库
    backup_path = f"pet_painting_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    print(f"备份数据库到: {backup_path}")
    
    import shutil
    shutil.copy2(db_path, backup_path)
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查是否已经存在hd_image字段
        cursor.execute("PRAGMA table_info(`order`)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'hd_image' not in columns:
            print("添加hd_image字段...")
            cursor.execute("ALTER TABLE `order` ADD COLUMN hd_image VARCHAR(200)")
            print("hd_image字段添加成功")
        else:
            print("hd_image字段已存在")
        
        # 检查是否需要更新status字段的注释
        print("检查status字段...")
        cursor.execute("PRAGMA table_info(`order`)")
        columns_info = cursor.fetchall()
        
        for column in columns_info:
            if column[1] == 'status':
                print(f"status字段类型: {column[2]}")
                break
        
        # 提交更改
        conn.commit()
        print("数据库迁移完成")
        
    except Exception as e:
        print(f"迁移失败: {str(e)}")
        # 恢复备份
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, db_path)
            print("已恢复备份数据库")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()

