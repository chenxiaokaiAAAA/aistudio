# -*- coding: utf-8 -*-
"""
快速修复脚本：为 meitu_api_config 表添加缺失的字段
使用方法：python scripts/database/fix_meitu_api_config_fields.py
"""
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 导入必要的模块
from test_server import app, db
from sqlalchemy import text

def fix_meitu_api_config_fields():
    """为 meitu_api_config 表添加缺失的字段"""
    
    with app.app_context():
        try:
            print("=" * 60)
            print("开始修复：为 meitu_api_config 表添加缺失的字段")
            print("=" * 60)
            
            # 检查表是否存在
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='meitu_api_config'"))
            if not result.fetchone():
                print("❌ meitu_api_config 表不存在，跳过修复")
                return False
            
            # 检查现有字段
            result = db.session.execute(text("PRAGMA table_info(meitu_api_config)"))
            columns = [row[1] for row in result.fetchall()]
            print(f"当前表字段: {columns}")
            
            # 需要添加的字段列表
            fields_to_add = [
                ('app_id', 'VARCHAR(100)', '应用ID (APPID)'),
                ('api_key', 'VARCHAR(100)', 'API密钥 (APIKEY)'),
                ('api_secret', 'VARCHAR(100)', 'API密钥 (SECRETID)'),
                ('api_base_url', 'VARCHAR(200)', 'API基础URL'),
                ('api_endpoint', 'VARCHAR(200)', 'API接口路径'),
                ('repost_url', 'VARCHAR(500)', '回调URL'),
                ('enable_in_workflow', 'BOOLEAN DEFAULT 0 NOT NULL', '是否在工作流中启用'),
            ]
            
            added_count = 0
            for field_name, field_type, description in fields_to_add:
                if field_name not in columns:
                    print(f"\n添加字段 {field_name} ({description})...")
                    try:
                        db.session.execute(text(f"ALTER TABLE meitu_api_config ADD COLUMN {field_name} {field_type}"))
                        db.session.commit()
                        print(f"✅ {field_name} 字段添加成功")
                        added_count += 1
                    except Exception as e:
                        print(f"❌ 添加 {field_name} 字段失败: {str(e)}")
                        db.session.rollback()
                else:
                    print(f"✅ {field_name} 字段已存在")
            
            # 设置默认值（如果需要）
            if 'api_base_url' in columns:
                result = db.session.execute(text("SELECT COUNT(*) FROM meitu_api_config WHERE api_base_url IS NULL OR api_base_url = ''"))
                count = result.fetchone()[0]
                if count > 0:
                    print(f"\n为 {count} 条记录设置默认 api_base_url...")
                    db.session.execute(text("UPDATE meitu_api_config SET api_base_url = 'https://api.yunxiu.meitu.com' WHERE api_base_url IS NULL OR api_base_url = ''"))
                    db.session.commit()
                    print("✅ 默认值设置成功")
            
            if 'api_endpoint' in columns:
                result = db.session.execute(text("SELECT COUNT(*) FROM meitu_api_config WHERE api_endpoint IS NULL OR api_endpoint = ''"))
                count = result.fetchone()[0]
                if count > 0:
                    print(f"\n为 {count} 条记录设置默认 api_endpoint...")
                    db.session.execute(text("UPDATE meitu_api_config SET api_endpoint = '/openapi/realphotolocal_async' WHERE api_endpoint IS NULL OR api_endpoint = ''"))
                    db.session.commit()
                    print("✅ 默认值设置成功")
            
            print("\n" + "=" * 60)
            if added_count > 0:
                print(f"✅ 修复完成！共添加了 {added_count} 个字段")
            else:
                print("✅ 所有字段都已存在，无需修复")
            print("=" * 60)
            return True
            
        except Exception as e:
            print(f"\n❌ 修复失败: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("\n🚀 开始执行数据库修复...\n")
    success = fix_meitu_api_config_fields()
    
    if success:
        print("\n✅ 修复脚本执行成功！")
        print("💡 提示：请重启服务以确保所有更改生效")
        sys.exit(0)
    else:
        print("\n❌ 修复脚本执行失败！")
        sys.exit(1)
