#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 meitu_api_config 表中的错误 API Base URL
将 https://openapi.meitu.com 更新为正确的 https://api.yunxiu.meitu.com
"""
import os
import sys
import sqlite3
from datetime import datetime

# 获取项目根目录
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

def fix_meitu_api_urls(db_path=None):
    """修复美图API配置中的错误URL"""
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
        print("\n🔄 开始修复美图API URL...")
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meitu_api_config'")
        if not cursor.fetchone():
            print("⚠️  meitu_api_config 表不存在，无需修复")
            conn.close()
            return True
        
        # 检查是否有 api_base_url 列
        cursor.execute("PRAGMA table_info(meitu_api_config)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'api_base_url' not in columns:
            print("⚠️  api_base_url 列不存在，无需修复")
            conn.close()
            return True
        
        # 查询需要修复的记录
        cursor.execute("""
            SELECT id, api_base_url 
            FROM meitu_api_config 
            WHERE api_base_url = 'https://openapi.meitu.com' 
               OR api_base_url LIKE '%openapi.meitu.com%'
        """)
        records_to_fix = cursor.fetchall()
        
        if not records_to_fix:
            print("✅ 没有需要修复的记录（所有URL都是正确的）")
            conn.close()
            return True
        
        print(f"📋 找到 {len(records_to_fix)} 条需要修复的记录:")
        for record_id, old_url in records_to_fix:
            print(f"   - ID: {record_id}, 当前URL: {old_url}")
        
        # 更新错误的URL
        correct_url = 'https://api.yunxiu.meitu.com'
        cursor.execute("""
            UPDATE meitu_api_config 
            SET api_base_url = ?
            WHERE api_base_url = 'https://openapi.meitu.com' 
               OR api_base_url LIKE '%openapi.meitu.com%'
        """, (correct_url,))
        
        updated_count = cursor.rowcount
        conn.commit()
        
        print(f"✅ 已修复 {updated_count} 条记录的API Base URL")
        print(f"   - 旧URL: https://openapi.meitu.com")
        print(f"   - 新URL: {correct_url}")
        
        # 验证修复结果
        cursor.execute("""
            SELECT COUNT(*) 
            FROM meitu_api_config 
            WHERE api_base_url = 'https://openapi.meitu.com' 
               OR api_base_url LIKE '%openapi.meitu.com%'
        """)
        remaining_count = cursor.fetchone()[0]
        
        if remaining_count == 0:
            print("✅ 验证成功：所有错误的URL已修复")
        else:
            print(f"⚠️  仍有 {remaining_count} 条记录包含错误的URL")
        
        conn.close()
        print("\n✅ 修复完成！")
        return True
        
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"❌ 修复失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("修复美图API配置中的错误URL")
    print("将 https://openapi.meitu.com 更新为 https://api.yunxiu.meitu.com")
    print("=" * 60)
    
    db_path = sys.argv[1] if len(sys.argv) > 1 else None
    success = fix_meitu_api_urls(db_path)
    
    if success:
        print("\n✅ 修复成功！")
        sys.exit(0)
    else:
        print("\n❌ 修复失败！")
        sys.exit(1)
