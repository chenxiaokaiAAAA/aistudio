# -*- coding: utf-8 -*-
"""
从 bk-photo 项目导入 API 服务商配置
"""
import sys
import os
import sqlite3
from datetime import datetime

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def import_api_configs_from_bkphoto(bkphoto_db_path, target_db_path=None):
    """
    从 bk-photo 项目的数据库导入 API 配置到 AI-studio 项目
    
    Args:
        bkphoto_db_path: bk-photo 项目的数据库文件路径
        target_db_path: AI-studio 项目的数据库文件路径（如果为None，则从test_server获取）
    """
    print("=" * 60)
    print("开始从 bk-photo 导入 API 服务商配置")
    print("=" * 60)
    
    # 1. 连接 bk-photo 数据库
    if not os.path.exists(bkphoto_db_path):
        print(f"❌ 错误：bk-photo 数据库文件不存在: {bkphoto_db_path}")
        return False
    
    print(f"📂 连接 bk-photo 数据库: {bkphoto_db_path}")
    bkphoto_conn = sqlite3.connect(bkphoto_db_path)
    bkphoto_cursor = bkphoto_conn.cursor()
    
    # 2. 查询 bk-photo 中的 API 配置
    try:
        # 先检查表是否存在
        bkphoto_cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='api_configs'
        """)
        if not bkphoto_cursor.fetchone():
            print("❌ bk-photo 数据库中不存在 'api_configs' 表")
            print("   请确认数据库文件是否正确")
            return False
        
        bkphoto_cursor.execute("""
            SELECT id, name, api_type, host_overseas, host_domestic, api_key,
                   draw_endpoint, result_endpoint, file_upload_endpoint, model_name,
                   is_active, is_default, enable_retry, created_at, updated_at
            FROM api_configs
            ORDER BY id
        """)
        bkphoto_configs = bkphoto_cursor.fetchall()
        
        print(f"✅ 从 bk-photo 读取到 {len(bkphoto_configs)} 条 API 配置")
        
        if len(bkphoto_configs) == 0:
            print("⚠️  bk-photo 中没有 API 配置数据")
            return False
        
    except sqlite3.OperationalError as e:
        print(f"❌ 查询 bk-photo 数据库失败: {str(e)}")
        print("   可能原因：表名不是 'api_configs' 或数据库结构不同")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. 连接 AI-studio 数据库
    if target_db_path is None:
        # 尝试从 test_server 获取数据库路径
        try:
            from test_server import app
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if db_uri.startswith('sqlite:///'):
                target_db_path = db_uri.replace('sqlite:///', '')
                # 如果是相对路径，需要转换为绝对路径
                if not os.path.isabs(target_db_path):
                    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    target_db_path = os.path.join(script_dir, target_db_path)
            else:
                target_db_path = None
        except Exception as e:
            print(f"⚠️  无法从 test_server 获取数据库路径: {str(e)}")
            target_db_path = None
        
        # 如果无法从配置获取，尝试自动查找
        if not target_db_path:
            script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            possible_paths = [
                os.path.join(script_dir, 'pet_painting.db'),  # 根目录
                os.path.join(script_dir, 'instance', 'pet_painting.db'),  # instance 目录
                os.path.join(script_dir, 'instance', 'database.db'),  # 备用
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    target_db_path = path
                    print(f"✅ 自动找到数据库文件: {path}")
                    break
            
            if not target_db_path:
                # 默认使用根目录的 pet_painting.db
                target_db_path = os.path.join(script_dir, 'pet_painting.db')
                print(f"⚠️  使用默认数据库路径: {target_db_path}")
    
    # 确保目录存在
    target_dir = os.path.dirname(target_db_path)
    if target_dir and not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
    
    print(f"📂 连接 AI-studio 数据库: {target_db_path}")
    target_conn = sqlite3.connect(target_db_path)
    target_cursor = target_conn.cursor()
    
    # 4. 检查目标表是否存在，如果不存在则创建
    try:
        target_cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_provider_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                api_type VARCHAR(50) DEFAULT 'nano-banana',
                host_overseas VARCHAR(200),
                host_domestic VARCHAR(200),
                api_key VARCHAR(500),
                draw_endpoint VARCHAR(200) DEFAULT '/v1/draw/nano-banana',
                result_endpoint VARCHAR(200) DEFAULT '/v1/draw/result',
                file_upload_endpoint VARCHAR(200) DEFAULT '/v1/file/upload',
                model_name VARCHAR(100),
                is_active BOOLEAN DEFAULT 1,
                is_default BOOLEAN DEFAULT 0,
                enable_retry BOOLEAN DEFAULT 1,
                priority INTEGER DEFAULT 0,
                description TEXT,
                created_at DATETIME,
                updated_at DATETIME
            )
        """)
        target_conn.commit()
        print("✅ 目标表已创建或已存在")
    except Exception as e:
        print(f"❌ 创建目标表失败: {str(e)}")
        return False
    
    # 5. 查询目标数据库中已存在的配置（避免重复导入）
    target_cursor.execute("SELECT id, name FROM api_provider_configs")
    existing_configs = {row[1]: row[0] for row in target_cursor.fetchall()}
    print(f"📋 目标数据库中已有 {len(existing_configs)} 条配置")
    
    # 6. 导入配置
    imported_count = 0
    skipped_count = 0
    updated_count = 0
    
    for config in bkphoto_configs:
        (config_id, name, api_type, host_overseas, host_domestic, api_key,
         draw_endpoint, result_endpoint, file_upload_endpoint, model_name,
         is_active, is_default, enable_retry, created_at, updated_at) = config
        
        # 检查是否已存在（按名称）
        if name in existing_configs:
            # 更新现有配置
            print(f"🔄 更新配置: {name} (ID: {existing_configs[name]})")
            target_cursor.execute("""
                UPDATE api_provider_configs SET
                    api_type = ?,
                    host_overseas = ?,
                    host_domestic = ?,
                    api_key = ?,
                    draw_endpoint = ?,
                    result_endpoint = ?,
                    file_upload_endpoint = ?,
                    model_name = ?,
                    is_active = ?,
                    is_default = ?,
                    enable_retry = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                api_type or 'nano-banana',
                host_overseas,
                host_domestic,
                api_key,
                draw_endpoint or '/v1/draw/nano-banana',
                result_endpoint or '/v1/draw/result',
                file_upload_endpoint or '/v1/file/upload',
                model_name,
                1 if is_active else 0,
                1 if is_default else 0,
                1 if enable_retry else 0,
                datetime.now().isoformat(),
                existing_configs[name]
            ))
            updated_count += 1
        else:
            # 插入新配置
            print(f"➕ 导入配置: {name}")
            target_cursor.execute("""
                INSERT INTO api_provider_configs (
                    name, api_type, host_overseas, host_domestic, api_key,
                    draw_endpoint, result_endpoint, file_upload_endpoint, model_name,
                    is_active, is_default, enable_retry, priority, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name,
                api_type or 'nano-banana',
                host_overseas,
                host_domestic,
                api_key,
                draw_endpoint or '/v1/draw/nano-banana',
                result_endpoint or '/v1/draw/result',
                file_upload_endpoint or '/v1/file/upload',
                model_name,
                1 if is_active else 0,
                1 if is_default else 0,
                1 if enable_retry else 0,
                0,  # priority 默认为0
                created_at or datetime.now().isoformat(),
                updated_at or datetime.now().isoformat()
            ))
            imported_count += 1
    
    target_conn.commit()
    
    # 7. 关闭连接
    bkphoto_conn.close()
    target_conn.close()
    
    # 8. 输出结果
    print("=" * 60)
    print("导入完成！")
    print(f"✅ 新增配置: {imported_count} 条")
    print(f"🔄 更新配置: {updated_count} 条")
    print(f"⏭️  跳过配置: {skipped_count} 条")
    print("=" * 60)
    
    return True


def find_bkphoto_database():
    """自动查找 bk-photo 项目的数据库文件"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
    
    # 可能的数据库路径（优先查找 pet_painting.db，因为这是 bk-photo 的默认数据库）
    possible_paths = [
        # 优先查找 instance/pet_painting.db（最常见）
        os.path.join(project_root, 'bk-photo', 'instance', 'pet_painting.db'),
        os.path.join(project_root, '..', 'bk-photo', 'instance', 'pet_painting.db'),
        # 其次查找根目录的 pet_painting.db
        os.path.join(project_root, 'bk-photo', 'pet_painting.db'),
        os.path.join(project_root, '..', 'bk-photo', 'pet_painting.db'),
        # 最后查找 database.db（备用）
        os.path.join(project_root, 'bk-photo', 'instance', 'database.db'),
        os.path.join(project_root, '..', 'bk-photo', 'instance', 'database.db'),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ 找到数据库文件: {path}")
            return os.path.normpath(path)
    
    return None


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='从 bk-photo 导入 API 服务商配置')
    parser.add_argument('--bkphoto-db', type=str, default=None,
                       help='bk-photo 项目的数据库文件路径（如果不指定，将自动查找）')
    parser.add_argument('--target-db', type=str, default=None,
                       help='AI-studio 项目的数据库文件路径（默认从test_server获取）')
    
    args = parser.parse_args()
    
    # 如果没有指定 bk-photo 数据库路径，尝试自动查找
    if not args.bkphoto_db:
        print("🔍 正在自动查找 bk-photo 数据库文件...")
        args.bkphoto_db = find_bkphoto_database()
        if not args.bkphoto_db:
            print("❌ 无法自动找到 bk-photo 数据库文件")
            print("   请手动指定路径：")
            print("   python scripts/database/import_api_provider_configs_from_bkphoto.py --bkphoto-db \"路径\\database.db\"")
            sys.exit(1)
        print(f"✅ 找到数据库文件: {args.bkphoto_db}")
    else:
        # 转换为绝对路径
        if not os.path.isabs(args.bkphoto_db):
            # 相对于脚本文件的路径
            script_dir = os.path.dirname(os.path.abspath(__file__))
            args.bkphoto_db = os.path.join(script_dir, '..', '..', '..', args.bkphoto_db)
            args.bkphoto_db = os.path.normpath(args.bkphoto_db)
    
    print(f"📂 bk-photo 数据库路径: {args.bkphoto_db}")
    print(f"📂 AI-studio 数据库路径: {args.target_db or '自动检测'}")
    print()
    
    success = import_api_configs_from_bkphoto(args.bkphoto_db, args.target_db)
    
    if success:
        print("\n✅ 导入成功！")
        sys.exit(0)
    else:
        print("\n❌ 导入失败！")
        sys.exit(1)
