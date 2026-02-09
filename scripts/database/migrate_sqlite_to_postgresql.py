# -*- coding: utf-8 -*-
"""
从SQLite迁移数据到PostgreSQL
"""
import os
import sys
import sqlite3
import json
from datetime import datetime

try:
    from sqlalchemy.types import Boolean
except ImportError:
    Boolean = None

def export_sqlite_data(sqlite_path='instance/pet_painting.db'):
    """导出SQLite数据"""
    print("=" * 60)
    print("导出SQLite数据")
    print("=" * 60)
    
    if not os.path.exists(sqlite_path):
        print(f"❌ 错误: SQLite数据库文件不存在: {sqlite_path}")
        return None
    
    try:
        conn = sqlite3.connect(sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"找到 {len(tables)} 个表")
        
        data = {}
        total_rows = 0
        
        for table in tables:
            print(f"  导出表: {table}...", end=' ')
            # 使用双引号包裹表名，避免 order 等 SQL 保留字报错
            cursor.execute(f'SELECT * FROM "{table}"')
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            # 转换为字典列表
            rows_data = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # 处理特殊类型
                    if isinstance(value, bytes):
                        value = value.hex()  # 二进制数据转为十六进制
                    elif value is None:
                        value = None
                    else:
                        value = str(value)
                    row_dict[col] = value
                rows_data.append(row_dict)
            
            data[table] = {
                'columns': columns,
                'rows': rows_data
            }
            total_rows += len(rows_data)
            print(f"✅ {len(rows_data)} 行")
        
        conn.close()
        
        # 保存为JSON
        export_file = f'sqlite_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n✅ 数据导出完成！")
        print(f"   导出文件: {export_file}")
        print(f"   总行数: {total_rows}")
        
        return export_file, data
        
    except Exception as e:
        print(f"\n❌ 导出失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def import_to_postgresql(export_file=None, data=None):
    """导入数据到PostgreSQL"""
    print("\n" + "=" * 60)
    print("导入数据到PostgreSQL")
    print("=" * 60)
    
    # 检查环境变量
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ 错误: 未找到 DATABASE_URL 环境变量")
        print("请先设置环境变量: export DATABASE_URL=postgresql://user:password@host:port/dbname")
        return False
    
    # 加载数据
    if data is None:
        if export_file and os.path.exists(export_file):
            print(f"从文件加载数据: {export_file}")
            with open(export_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            print("❌ 错误: 没有提供数据文件或数据")
            return False
    
    try:
        # 导入Flask应用和模型
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
        from app import create_app, db
        from sqlalchemy import inspect
        
        flask_app = create_app()
        import app.models  # 导入所有模型（app 须为包名，故用 flask_app 存 Flask 实例）
        
        with flask_app.app_context():
            # 获取模型映射（表名 -> 模型类）
            inspector = inspect(db.engine)
            model_map = {}
            
            # 尝试映射表名到模型
            for model_class in db.Model.__subclasses__():
                if hasattr(model_class, '__tablename__'):
                    table_name = model_class.__tablename__
                    model_map[table_name] = model_class
            
            print(f"找到 {len(model_map)} 个模型类")

            # SQLite 表名可能与模型 __tablename__ 不同（如 product_category vs product_categories）
            TABLE_ALIASES = {
                'product_category': 'product_categories',
                'product_subcategory': 'product_subcategories',
            }
            
            # 定义导入顺序（处理外键依赖，父表必须在子表之前）
            # 含 SQLite 可能使用的表名（product_category）与模型表名（product_categories）
            import_order = [
                'style_category', 'style_subcategories', 'style_image',
                'product_categories', 'product_category', 'product_subcategories', 'product_subcategory',
                'products',  # products 依赖 product_categories
                'product_sizes', 'product_size_pet_options',  # 依赖 products
                'product_images', 'product_style_categories', 'product_custom_fields', 'product_bonus_workflows',
                'users', 'franchisee_accounts', 'selfie_machines',
                'promotion_users', 'coupons',
                'user_coupons',  # 依赖 users, coupons
                'orders', 'order_image',
                'ai_tasks', 'ai_config',
                'shop_products', 'shop_product_images', 'shop_product_sizes', 'shop_orders',
            ]
            
            # 获取所有表名
            all_tables = list(data.keys())
            # 先导入有序的表，再导入其他表
            ordered_tables = [t for t in import_order if t in all_tables]
            other_tables = [t for t in all_tables if t not in import_order]
            final_order = ordered_tables + other_tables
            
            total_imported = 0
            
            for table_name in final_order:
                if table_name not in data:
                    continue
                
                table_data = data[table_name]
                columns = table_data['columns']
                rows = table_data['rows']
                
                if not rows:
                    print(f"  跳过空表: {table_name}")
                    continue
                
                # 获取对应的模型类（支持 SQLite 表名与模型表名不一致）
                model_table = TABLE_ALIASES.get(table_name, table_name)
                model_class = model_map.get(model_table)
                if not model_class:
                    print(f"  ⚠️  未找到模型类: {table_name}，跳过")
                    continue
                
                print(f"  导入表: {table_name}...", end=' ')
                
                # 获取模型实际拥有的列（过滤 SQLite 中已删除的列如 multi_pet_additional_price）
                model_columns = {c.name for c in model_class.__table__.columns}
                valid_columns = [c for c in columns if c in model_columns]
                if not valid_columns:
                    print(f"⚠️  无匹配列，跳过")
                    continue

                imported_count = 0
                for row_data in rows:
                    try:
                        # 创建模型实例，仅使用模型存在的列
                        instance_data = {}
                        for col in valid_columns:
                            if col not in row_data:
                                continue
                            value = row_data[col]
                            # 从表结构安全获取列类型（避免 hybrid property 等报错）
                            try:
                                col_obj = model_class.__table__.columns.get(col)
                                col_type = col_obj.type if col_obj else None
                            except Exception:
                                col_type = None
                            # 类型转换（Boolean 必须转为 Python bool，否则 PostgreSQL 报错）
                            if value is None or value == '':
                                instance_data[col] = None
                            elif Boolean and col_type and isinstance(col_type, Boolean):
                                instance_data[col] = value in ('1', 1, True, 'True', 'true')
                            elif col_type and 'Integer' in str(col_type):
                                try:
                                    instance_data[col] = int(value) if value else None
                                except Exception:
                                    instance_data[col] = None
                            elif col_type and ('Float' in str(col_type) or 'Numeric' in str(col_type)):
                                try:
                                    instance_data[col] = float(value) if value else None
                                except Exception:
                                    instance_data[col] = None
                            elif col_type and 'DateTime' in str(col_type):
                                if value:
                                    try:
                                        from datetime import datetime
                                        if isinstance(value, str):
                                            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S']:
                                                try:
                                                    instance_data[col] = datetime.strptime(value, fmt)
                                                    break
                                                except ValueError:
                                                    continue
                                        else:
                                            instance_data[col] = value
                                    except Exception:
                                        instance_data[col] = None
                                else:
                                    instance_data[col] = None
                            else:
                                # 兜底：布尔型列可能未被正确识别，对 is_ 开头的列做转换
                                if isinstance(value, str) and value.lower() in ('1', '0', 'true', 'false') and col and col.startswith('is_'):
                                    instance_data[col] = value in ('1', 'true', 'True')
                                else:
                                    instance_data[col] = value

                        # 创建实例
                        instance = model_class(**instance_data)
                        db.session.add(instance)
                        imported_count += 1
                        
                    except Exception as e:
                        print(f"\n    ⚠️  导入行失败: {e}")
                        continue
                
                # 批量提交
                try:
                    db.session.commit()
                    print(f"✅ {imported_count} 行")
                    total_imported += imported_count
                except Exception as e:
                    db.session.rollback()
                    print(f"❌ 提交失败: {e}")
            
            print(f"\n✅ 数据导入完成！")
            print(f"   总导入行数: {total_imported}")
            
            return True
            
    except Exception as e:
        print(f"\n❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("SQLite 到 PostgreSQL 数据迁移工具")
    print("=" * 60)
    print("\n请选择操作：")
    print("1. 仅导出SQLite数据")
    print("2. 仅导入到PostgreSQL（需要先有导出文件）")
    print("3. 完整迁移（导出+导入）")
    
    choice = input("\n请选择 (1/2/3): ").strip()
    
    if choice == '1':
        sqlite_path = input("SQLite数据库路径 (默认: instance/pet_painting.db): ").strip() or "instance/pet_painting.db"
        export_sqlite_data(sqlite_path)
    elif choice == '2':
        export_file = input("导出文件路径: ").strip()
        import_to_postgresql(export_file=export_file)
    elif choice == '3':
        sqlite_path = input("SQLite数据库路径 (默认: instance/pet_painting.db): ").strip() or "instance/pet_painting.db"
        result = export_sqlite_data(sqlite_path)
        if result:
            export_file, data = result
            print("\n" + "=" * 60)
            input("请按Enter键继续导入到PostgreSQL（确保已设置DATABASE_URL环境变量）...")
            import_to_postgresql(export_file=export_file, data=data)
    else:
        print("❌ 无效的选择")
