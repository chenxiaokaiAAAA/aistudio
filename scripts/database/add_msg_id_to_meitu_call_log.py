# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为 meitu_api_call_log 表添加 msg_id 字段
使用方法：python scripts/database/add_msg_id_to_meitu_call_log.py
"""
import sys
import os
import json

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 导入必要的模块
from test_server import app, db
from sqlalchemy import text

def migrate_msg_id_field():
    """为 meitu_api_call_log 表添加 msg_id 字段"""
    
    with app.app_context():
        try:
            print("=" * 60)
            print("开始迁移：为 meitu_api_call_log 表添加 msg_id 字段")
            print("=" * 60)
            
            # 检查表是否存在
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='meitu_api_call_log'"))
            if not result.fetchone():
                print("❌ meitu_api_call_log 表不存在，跳过迁移")
                return False
            
            # 检查字段是否已存在
            result = db.session.execute(text("PRAGMA table_info(meitu_api_call_log)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'msg_id' in columns:
                print("✅ msg_id 字段已存在，无需添加")
                
                # 检查是否有记录的 msg_id 为空，但 response_data 中有 msg_id
                print("\n检查是否需要从 response_data 中提取 msg_id...")
                result = db.session.execute(text("""
                    SELECT id, response_data FROM meitu_api_call_log 
                    WHERE msg_id IS NULL AND response_data IS NOT NULL
                """))
                rows = result.fetchall()
                
                if rows:
                    print(f"发现 {len(rows)} 条记录的 msg_id 为空，尝试从 response_data 中提取...")
                    updated_count = 0
                    for row_id, response_data in rows:
                        if response_data:
                            try:
                                data = json.loads(response_data) if isinstance(response_data, str) else response_data
                                if isinstance(data, dict):
                                    msg_id = data.get('msg_id')
                                    if msg_id:
                                        db.session.execute(text("UPDATE meitu_api_call_log SET msg_id = :msg_id WHERE id = :id"), {
                                            'msg_id': msg_id,
                                            'id': row_id
                                        })
                                        updated_count += 1
                            except Exception as e:
                                print(f"⚠️ 处理记录 {row_id} 时出错: {str(e)}")
                                pass
                    
                    if updated_count > 0:
                        db.session.commit()
                        print(f"✅ 已从 {updated_count} 条记录中提取并更新 msg_id")
                    else:
                        print("ℹ️ 没有找到包含 msg_id 的记录")
                else:
                    print("✅ 所有记录的 msg_id 都已存在")
                
                return True
            
            # 添加字段
            print("\n添加 msg_id 字段到 meitu_api_call_log 表...")
            db.session.execute(text("ALTER TABLE meitu_api_call_log ADD COLUMN msg_id VARCHAR(100)"))
            db.session.commit()
            print("✅ msg_id 字段添加成功")
            
            # 从现有的 response_data 中提取 msg_id 并更新到新字段
            print("\n从现有记录中提取 msg_id...")
            result = db.session.execute(text("SELECT id, response_data FROM meitu_api_call_log WHERE response_data IS NOT NULL"))
            all_logs = result.fetchall()
            
            if not all_logs:
                print("ℹ️ 没有找到包含 response_data 的记录")
                return True
            
            print(f"发现 {len(all_logs)} 条记录，开始提取 msg_id...")
            updated_count = 0
            
            for log_id, response_data in all_logs:
                if response_data:
                    try:
                        data = json.loads(response_data) if isinstance(response_data, str) else response_data
                        if isinstance(data, dict):
                            # 尝试从不同位置获取 msg_id
                            msg_id = None
                            
                            # 方式1：直接从 data 中获取
                            if 'msg_id' in data:
                                msg_id = data.get('msg_id')
                            # 方式2：从 data.data 中获取（嵌套结构）
                            elif 'data' in data and isinstance(data['data'], dict):
                                msg_id = data['data'].get('msg_id')
                            # 方式3：从 original_response 中获取
                            elif 'original_response' in data and isinstance(data['original_response'], dict):
                                original = data['original_response']
                                if 'data' in original and isinstance(original['data'], dict):
                                    msg_id = original['data'].get('msg_id')
                            
                            if msg_id:
                                db.session.execute(text("UPDATE meitu_api_call_log SET msg_id = :msg_id WHERE id = :id"), {
                                    'msg_id': msg_id,
                                    'id': log_id
                                })
                                updated_count += 1
                    except Exception as e:
                        print(f"⚠️ 处理记录 {log_id} 时出错: {str(e)}")
                        pass
            
            if updated_count > 0:
                db.session.commit()
                print(f"✅ 已从 {updated_count} 条现有记录中提取并更新 msg_id")
            else:
                print("ℹ️ 没有找到包含 msg_id 的现有记录")
            
            print("\n" + "=" * 60)
            print("✅ 迁移完成！")
            print("=" * 60)
            return True
            
        except Exception as e:
            print(f"\n❌ 迁移失败: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("\n🚀 开始执行数据库迁移...\n")
    success = migrate_msg_id_field()
    
    if success:
        print("\n✅ 迁移脚本执行成功！")
        sys.exit(0)
    else:
        print("\n❌ 迁移脚本执行失败！")
        sys.exit(1)
