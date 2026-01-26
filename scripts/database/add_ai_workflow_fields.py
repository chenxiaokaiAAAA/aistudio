# -*- coding: utf-8 -*-
"""
数据库迁移脚本：添加AI工作流相关字段
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
        
        # 1. 为 style_category 表添加AI工作流字段
        print("\n1. 扩展 style_category 表...")
        try:
            cursor.execute("""
                ALTER TABLE style_category ADD COLUMN workflow_name VARCHAR(200)
            """)
            print("   ✅ 添加 workflow_name")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️  workflow_name 字段已存在，跳过")
            else:
                raise
        
        try:
            cursor.execute("""
                ALTER TABLE style_category ADD COLUMN workflow_file VARCHAR(200)
            """)
            print("   ✅ 添加 workflow_file")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️  workflow_file 字段已存在，跳过")
            else:
                raise
        
        try:
            cursor.execute("""
                ALTER TABLE style_category ADD COLUMN workflow_input_ids TEXT
            """)
            print("   ✅ 添加 workflow_input_ids")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️  workflow_input_ids 字段已存在，跳过")
            else:
                raise
        
        try:
            cursor.execute("""
                ALTER TABLE style_category ADD COLUMN workflow_output_id VARCHAR(50)
            """)
            print("   ✅ 添加 workflow_output_id")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️  workflow_output_id 字段已存在，跳过")
            else:
                raise
        
        try:
            cursor.execute("""
                ALTER TABLE style_category ADD COLUMN workflow_ref_id VARCHAR(50)
            """)
            print("   ✅ 添加 workflow_ref_id")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️  workflow_ref_id 字段已存在，跳过")
            else:
                raise
        
        try:
            cursor.execute("""
                ALTER TABLE style_category ADD COLUMN workflow_ref_image VARCHAR(500)
            """)
            print("   ✅ 添加 workflow_ref_image")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️  workflow_ref_image 字段已存在，跳过")
            else:
                raise
        
        try:
            cursor.execute("""
                ALTER TABLE style_category ADD COLUMN workflow_user_prompt_id VARCHAR(50)
            """)
            print("   ✅ 添加 workflow_user_prompt_id")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️  workflow_user_prompt_id 字段已存在，跳过")
            else:
                raise
        
        try:
            cursor.execute("""
                ALTER TABLE style_category ADD COLUMN workflow_custom_prompt_id VARCHAR(50)
            """)
            print("   ✅ 添加 workflow_custom_prompt_id")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️  workflow_custom_prompt_id 字段已存在，跳过")
            else:
                raise
        
        try:
            cursor.execute("""
                ALTER TABLE style_category ADD COLUMN workflow_custom_prompt_content TEXT
            """)
            print("   ✅ 添加 workflow_custom_prompt_content")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️  workflow_custom_prompt_content 字段已存在，跳过")
            else:
                raise
        
        try:
            cursor.execute("""
                ALTER TABLE style_category ADD COLUMN is_ai_enabled BOOLEAN DEFAULT 0
            """)
            print("   ✅ 添加 is_ai_enabled")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️  is_ai_enabled 字段已存在，跳过")
            else:
                raise
        
        # 2. 为 style_image 表添加AI工作流字段
        print("\n2. 扩展 style_image 表...")
        try:
            cursor.execute("""
                ALTER TABLE style_image ADD COLUMN workflow_name VARCHAR(200)
            """)
            print("   ✅ 添加 workflow_name")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️  workflow_name 字段已存在，跳过")
            else:
                raise
        
        try:
            cursor.execute("""
                ALTER TABLE style_image ADD COLUMN workflow_file VARCHAR(200)
            """)
            print("   ✅ 添加 workflow_file")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️  workflow_file 字段已存在，跳过")
            else:
                raise
        
        try:
            cursor.execute("""
                ALTER TABLE style_image ADD COLUMN workflow_input_ids TEXT
            """)
            print("   ✅ 添加 workflow_input_ids")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️  workflow_input_ids 字段已存在，跳过")
            else:
                raise
        
        try:
            cursor.execute("""
                ALTER TABLE style_image ADD COLUMN workflow_output_id VARCHAR(50)
            """)
            print("   ✅ 添加 workflow_output_id")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️  workflow_output_id 字段已存在，跳过")
            else:
                raise
        
        try:
            cursor.execute("""
                ALTER TABLE style_image ADD COLUMN workflow_ref_id VARCHAR(50)
            """)
            print("   ✅ 添加 workflow_ref_id")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️  workflow_ref_id 字段已存在，跳过")
            else:
                raise
        
        try:
            cursor.execute("""
                ALTER TABLE style_image ADD COLUMN workflow_ref_image VARCHAR(500)
            """)
            print("   ✅ 添加 workflow_ref_image")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️  workflow_ref_image 字段已存在，跳过")
            else:
                raise
        
        try:
            cursor.execute("""
                ALTER TABLE style_image ADD COLUMN workflow_user_prompt_id VARCHAR(50)
            """)
            print("   ✅ 添加 workflow_user_prompt_id")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️  workflow_user_prompt_id 字段已存在，跳过")
            else:
                raise
        
        try:
            cursor.execute("""
                ALTER TABLE style_image ADD COLUMN workflow_custom_prompt_id VARCHAR(50)
            """)
            print("   ✅ 添加 workflow_custom_prompt_id")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️  workflow_custom_prompt_id 字段已存在，跳过")
            else:
                raise
        
        try:
            cursor.execute("""
                ALTER TABLE style_image ADD COLUMN workflow_custom_prompt_content TEXT
            """)
            print("   ✅ 添加 workflow_custom_prompt_content")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️  workflow_custom_prompt_content 字段已存在，跳过")
            else:
                raise
        
        try:
            cursor.execute("""
                ALTER TABLE style_image ADD COLUMN is_ai_enabled BOOLEAN
            """)
            print("   ✅ 添加 is_ai_enabled")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️  is_ai_enabled 字段已存在，跳过")
            else:
                raise
        
        # 3. 创建 ai_tasks 表
        print("\n3. 创建 ai_tasks 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                order_number VARCHAR(50) NOT NULL,
                workflow_name VARCHAR(200),
                workflow_file VARCHAR(200),
                style_category_id INTEGER,
                style_image_id INTEGER,
                input_image_path VARCHAR(500),
                input_image_type VARCHAR(20) DEFAULT 'original',
                comfyui_prompt_id VARCHAR(100),
                comfyui_node_id VARCHAR(50),
                status VARCHAR(20) DEFAULT 'pending',
                output_image_path VARCHAR(500),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                started_at DATETIME,
                completed_at DATETIME,
                estimated_completion_time DATETIME,
                error_message TEXT,
                error_code VARCHAR(50),
                retry_count INTEGER DEFAULT 0,
                processing_log TEXT,
                comfyui_response TEXT,
                notes TEXT,
                FOREIGN KEY (order_id) REFERENCES "order" (id),
                FOREIGN KEY (style_category_id) REFERENCES style_category (id),
                FOREIGN KEY (style_image_id) REFERENCES style_image (id)
            )
        """)
        print("   ✅ ai_tasks 表创建成功")
        
        # 4. 创建 ai_config 表
        print("\n4. 创建 ai_config 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key VARCHAR(50) UNIQUE NOT NULL,
                config_value TEXT,
                description VARCHAR(200),
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("   ✅ ai_config 表创建成功")
        
        # 5. 初始化默认配置
        print("\n5. 初始化默认配置...")
        default_configs = [
            ('comfyui_base_url', 'http://sm003:8188', 'ComfyUI服务器地址'),
            ('comfyui_api_endpoint', '/api/prompt', 'ComfyUI API端点'),
            ('comfyui_timeout', '300', 'ComfyUI请求超时时间（秒）'),
            ('prefer_retouched_image', 'true', '是否优先使用美颜后的图片'),
            ('auto_retry_on_failure', 'false', '失败后是否自动重试'),
            ('max_retry_count', '3', '最大重试次数')
        ]
        
        for config_key, config_value, description in default_configs:
            try:
                cursor.execute("""
                    INSERT INTO ai_config (config_key, config_value, description)
                    VALUES (?, ?, ?)
                """, (config_key, config_value, description))
                print(f"   ✅ 初始化配置: {config_key} = {config_value}")
            except sqlite3.IntegrityError:
                print(f"   ⚠️  配置 {config_key} 已存在，跳过")
        
        conn.commit()
        print("\n✅ 数据库迁移完成！")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 数据库迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("AI工作流数据库迁移脚本")
    print("=" * 60)
    
    # 查找数据库文件
    db_paths = [
        'instance/pet_painting.db',
        '../instance/pet_painting.db',
        os.path.join(os.path.dirname(__file__), '..', 'instance', 'pet_painting.db')
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ 未找到数据库文件，请手动指定路径")
        sys.exit(1)
    
    print(f"📁 数据库路径: {db_path}\n")
    
    if migrate_database(db_path):
        print("\n🎉 迁移成功！")
        sys.exit(0)
    else:
        print("\n💥 迁移失败！")
        sys.exit(1)
