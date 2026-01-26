#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 meitu_api_config 表：
1. 添加缺失的 api_endpoint 字段
2. 修复错误的 API Base URL（将 openapi.meitu.com 更新为 api.yunxiu.meitu.com）
"""
import os
import sys
import sqlite3
from datetime import datetime

# 获取项目根目录
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

def fix_meitu_api_config(db_path=None):
    """修复美图API配置表"""
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
        print("\n🔄 开始修复美图API配置表...")
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meitu_api_config'")
        if not cursor.fetchone():
            print("⚠️  meitu_api_config 表不存在，无需修复")
            conn.close()
            return True
        
        # 检查现有列
        cursor.execute("PRAGMA table_info(meitu_api_config)")
        columns = {column[1]: column for column in cursor.fetchall()}
        column_names = list(columns.keys())
        
        print(f"📋 当前表的列: {', '.join(column_names)}")
        
        # 1. 添加 api_endpoint 字段（如果不存在）
        if 'api_endpoint' not in column_names:
            print("📝 添加 api_endpoint 字段到 meitu_api_config 表...")
            cursor.execute("""
                ALTER TABLE meitu_api_config 
                ADD COLUMN api_endpoint VARCHAR(200) DEFAULT '/openapi/realphotolocal_async'
            """)
            conn.commit()
            print("✅ api_endpoint 字段添加成功")
        else:
            print("✅ api_endpoint 字段已存在")
        
        # 2. 修复错误的API Base URL
        if 'api_base_url' in column_names:
            print("📝 检查并修复错误的API Base URL...")
            cursor.execute("""
                SELECT COUNT(*) FROM meitu_api_config 
                WHERE api_base_url = 'https://openapi.meitu.com' 
                   OR api_base_url LIKE '%openapi.meitu.com%'
            """)
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"发现 {count} 条记录包含错误的API URL，正在修复...")
                cursor.execute("""
                    UPDATE meitu_api_config 
                    SET api_base_url = 'https://api.yunxiu.meitu.com'
                    WHERE api_base_url = 'https://openapi.meitu.com' 
                       OR api_base_url LIKE '%openapi.meitu.com%'
                """)
                conn.commit()
                print("✅ 已修复错误的API Base URL")
            else:
                print("✅ API Base URL 检查通过（无需修复）")
        
        # 3. 确保 api_endpoint 有默认值（如果为空）
        if 'api_endpoint' in column_names:
            cursor.execute("""
                UPDATE meitu_api_config 
                SET api_endpoint = '/openapi/realphotolocal_async'
                WHERE api_endpoint IS NULL OR api_endpoint = ''
            """)
            updated_count = cursor.rowcount
            if updated_count > 0:
                conn.commit()
                print(f"✅ 已为 {updated_count} 条记录设置默认 api_endpoint")
        
        # 验证修复结果
        cursor.execute("PRAGMA table_info(meitu_api_config)")
        columns_after = {column[1]: column for column in cursor.fetchall()}
        
        if 'api_endpoint' in columns_after:
            print("✅ 验证成功：api_endpoint 字段已存在")
        else:
            print("❌ 验证失败：api_endpoint 字段未成功添加")
            conn.close()
            return False
        
        # 显示当前配置
        cursor.execute("SELECT id, api_base_url, api_endpoint, is_active FROM meitu_api_config")
        configs = cursor.fetchall()
        if configs:
            print("\n📋 当前美图API配置:")
            for config_id, api_base_url, api_endpoint, is_active in configs:
                status = "启用" if is_active else "禁用"
                print(f"   - ID: {config_id}, Base URL: {api_base_url}, Endpoint: {api_endpoint}, 状态: {status}")
        
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
    print("修复美图API配置表")
    print("1. 添加 api_endpoint 字段")
    print("2. 修复错误的 API Base URL")
    print("=" * 60)
    
    db_path = sys.argv[1] if len(sys.argv) > 1 else None
    success = fix_meitu_api_config(db_path)
    
    if success:
        print("\n✅ 修复成功！请重启应用以使更改生效。")
        sys.exit(0)
    else:
        print("\n❌ 修复失败！")
        sys.exit(1)
