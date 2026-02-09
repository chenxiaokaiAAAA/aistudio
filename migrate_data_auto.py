# -*- coding: utf-8 -*-
"""
自动迁移SQLite数据到PostgreSQL（非交互式）
"""
import os
import sys
import sqlite3
import io

# 设置输出编码为UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 设置环境变量（如果未设置）
if not os.environ.get('DATABASE_URL'):
    os.environ['DATABASE_URL'] = 'postgresql://aistudio_user:a3183683@localhost:5432/pet_painting'

sqlite_path = 'instance/pet_painting.db'

print("=" * 60)
print("SQLite 到 PostgreSQL 数据迁移")
print("=" * 60)

# 检查SQLite数据库
if not os.path.exists(sqlite_path):
    print(f"❌ 错误: SQLite数据库文件不存在: {sqlite_path}")
    sys.exit(1)

# 获取数据库大小
db_size = os.path.getsize(sqlite_path) / (1024 * 1024)
print(f"\nSQLite数据库大小: {db_size:.2f} MB")
print(f"目标数据库: PostgreSQL (pet_painting)")

# 确认
print("\n准备开始迁移...")
print("这将把SQLite中的所有数据迁移到PostgreSQL")
print("开始迁移...\n")

try:
    from app import create_app, db
    from sqlalchemy import inspect, text
    from sqlalchemy.exc import IntegrityError
    
    app = create_app()
    
    with app.app_context():
        # 连接到SQLite
        print("\n" + "=" * 60)
        print("步骤1: 连接SQLite数据库")
        print("=" * 60)
        
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cursor = sqlite_conn.cursor()
        
        # 获取所有表名
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in sqlite_cursor.fetchall()]
        
        print(f"✅ 找到 {len(tables)} 个表")
        
        # 获取PostgreSQL中的表
        inspector = inspect(db.engine)
        pg_tables = set(inspector.get_table_names())
        
        print("\n" + "=" * 60)
        print("步骤2: 开始迁移数据")
        print("=" * 60)
        
        total_imported = 0
        total_errors = 0
        
        # 定义导入顺序（处理外键依赖）
        # 注意：必须先迁移被依赖的表，再迁移依赖表
        import_order = [
            # 基础数据表（无外键依赖）
            'style_category', 'style_subcategories', 'style_image',
            'product_categories', 'product_subcategories', 'products', 'product_sizes',
            'ai_config',
            # 用户和加盟商（可能被其他表依赖）
            'user', 'franchisee_accounts',
            # 依赖user和franchisee_accounts的表
            'selfie_machines',  # 依赖franchisee_accounts
            'staff_users',  # 依赖franchisee_accounts
            'promotion_users',
            # 优惠券（可能被user_coupons依赖）
            'coupons',
            # 订单相关（依赖user, franchisee_accounts等）
            'orders',
            'order_image',  # 依赖orders
            'ai_tasks',  # 依赖orders
            # 商城相关（依赖orders）
            'shop_products', 'shop_orders',  # shop_orders依赖orders
            # 用户优惠券（依赖coupons和orders）
            'user_coupons',  # 依赖coupons
            # 产品选项（依赖product_sizes）
            'product_size_pet_options',  # 依赖product_sizes
        ]
        
        # 获取所有表名
        all_tables = [t for t in import_order if t in tables]
        other_tables = [t for t in tables if t not in import_order]
        final_order = all_tables + other_tables
        
        for table_name in final_order:
            if table_name not in pg_tables:
                print(f"  ⚠️  跳过: {table_name} (PostgreSQL中不存在)")
                continue
            
            try:
                # 获取SQLite表数据
                sqlite_cursor.execute(f"SELECT * FROM {table_name}")
                columns = [description[0] for description in sqlite_cursor.description]
                rows = sqlite_cursor.fetchall()
                
                if not rows:
                    print(f"  ⏭️  跳过: {table_name} (空表)")
                    continue
                
                # 检查PostgreSQL中是否已有数据（断点续传支持）
                try:
                    result = db.session.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                    pg_count = result.scalar()
                    
                    if pg_count == len(rows):
                        print(f"  ✅ 跳过: {table_name} (已迁移, {pg_count} 行)")
                        continue
                    elif pg_count > 0:
                        print(f"  ⚠️  {table_name} 部分迁移 (SQLite: {len(rows)}, PostgreSQL: {pg_count})")
                        print(f"     继续迁移剩余 {len(rows) - pg_count} 行...", end=' ')
                        # 可以选择清空后重新迁移，或者继续追加
                        # 这里选择继续追加（如果遇到重复键错误会自动跳过）
                    else:
                        print(f"  迁移: {table_name} ({len(rows)} 行)...", end=' ')
                except Exception as e:
                    # 如果查询失败，继续迁移
                    print(f"  迁移: {table_name} ({len(rows)} 行)...", end=' ')
                    pg_count = 0
                
                # 获取PostgreSQL表结构（包括列类型信息）
                pg_column_info = {col['name']: col for col in inspector.get_columns(table_name)}
                pg_columns = list(pg_column_info.keys())
                
                # 准备数据
                imported_count = 0
                error_count = 0
                
                # 对于有外键依赖的表，预先查询有效的外键值
                foreign_key_cache = {}
                if table_name in ['ai_tasks', 'order_image', 'shop_orders', 'user_coupons']:
                    # 查询有效的order_id
                    try:
                        result = db.session.execute(text('SELECT id FROM orders'))
                        foreign_key_cache['order_id'] = {row[0] for row in result}
                    except:
                        foreign_key_cache['order_id'] = set()
                
                if table_name == 'product_size_pet_options':
                    # 查询有效的size_id
                    try:
                        result = db.session.execute(text('SELECT id FROM product_sizes'))
                        foreign_key_cache['size_id'] = {row[0] for row in result}
                    except:
                        foreign_key_cache['size_id'] = set()
                
                if table_name == 'user_coupons':
                    # 查询有效的coupon_id
                    try:
                        result = db.session.execute(text('SELECT id FROM coupons'))
                        foreign_key_cache['coupon_id'] = {row[0] for row in result}
                    except:
                        foreign_key_cache['coupon_id'] = set()
                
                for row in rows:
                    try:
                        # 构建插入数据
                        row_data = {}
                        for i, col in enumerate(columns):
                            if col in pg_columns:
                                value = row[i]
                                # 处理None值
                                if value is None:
                                    row_data[col] = None
                                # 处理布尔值
                                elif isinstance(value, (int, bool)) and col in ['is_active', 'is_deleted', 'need_confirmation', 'franchisee_confirmed', 'skipped_production']:
                                    row_data[col] = bool(value)
                                # 处理二进制数据
                                elif isinstance(value, bytes):
                                    # 对于PostgreSQL，二进制数据需要特殊处理
                                    row_data[col] = value
                                # 处理字符串长度限制
                                elif isinstance(value, str):
                                    # 获取列类型信息
                                    col_info = pg_column_info[col]
                                    col_type = str(col_info['type'])
                                    
                                    # 检查是否是String类型且有长度限制
                                    if 'VARCHAR' in col_type or 'CHAR' in col_type:
                                        # 提取长度限制（例如：VARCHAR(100) -> 100）
                                        import re
                                        match = re.search(r'\((\d+)\)', col_type)
                                        if match:
                                            max_length = int(match.group(1))
                                            if len(value) > max_length:
                                                # 截断字符串并添加警告标记
                                                value = value[:max_length]
                                                if error_count < 3:
                                                    print(f"\n    ⚠️  字段 {col} 值被截断 ({len(value)} -> {max_length} 字符)")
                                    
                                    row_data[col] = value
                                else:
                                    row_data[col] = value
                        
                        # 验证外键约束（在插入前检查）
                        skip_row = False
                        for fk_col, valid_ids in foreign_key_cache.items():
                            if fk_col in row_data and row_data[fk_col] is not None:
                                fk_value = row_data[fk_col]
                                # 处理order_id=0的特殊情况（可能是测试数据，但order_id不允许NULL）
                                if fk_col == 'order_id' and fk_value == 0:
                                    # order_id不允许NULL，所以跳过该行
                                    skip_row = True
                                    if error_count < 3:
                                        print(f"\n    ⚠️  跳过行：{fk_col}=0 (无效的订单ID)")
                                    break
                                elif fk_value not in valid_ids:
                                    # 外键值不存在，跳过该行
                                    skip_row = True
                                    if error_count < 3:
                                        print(f"\n    ⚠️  跳过行：{fk_col}={fk_value} 不存在于依赖表")
                                    break
                        
                        if skip_row:
                            error_count += 1
                            continue
                        
                        # 使用ORM方式插入（更可靠）
                        if row_data:
                            # 获取模型类
                            from app.models import *
                            model_class = None
                            
                            # 尝试找到对应的模型类
                            for model in db.Model.__subclasses__():
                                if hasattr(model, '__tablename__') and model.__tablename__ == table_name:
                                    model_class = model
                                    break
                            
                            if model_class:
                                # 使用ORM插入
                                instance = model_class(**row_data)
                                db.session.add(instance)
                                imported_count += 1
                            else:
                                # 如果找不到模型类，使用原始SQL
                                cols = ', '.join([f'"{k}"' for k in row_data.keys()])
                                placeholders = ', '.join(['%s' for _ in row_data.keys()])
                                sql = f'INSERT INTO "{table_name}" ({cols}) VALUES ({placeholders})'
                                
                                values = [v for v in row_data.values()]
                                db.session.execute(text(sql), values)
                                imported_count += 1
                            
                    except IntegrityError as e:
                        # 可能是重复数据或外键约束，跳过
                        error_count += 1
                        error_msg = str(e)
                        if 'duplicate key' in error_msg.lower() or 'unique constraint' in error_msg.lower():
                            # 重复数据，静默跳过
                            pass
                        elif 'foreign key' in error_msg.lower():
                            # 外键约束错误，显示详细信息
                            if error_count <= 3:
                                print(f"\n    ⚠️  外键约束错误（依赖表未迁移）: {error_msg[:200]}")
                        else:
                            if error_count <= 3:
                                print(f"\n    ⚠️  数据完整性错误: {error_msg[:200]}")
                        continue
                    except Exception as e:
                        error_count += 1
                        error_msg = str(e)
                        # 检查是否是字符串长度错误
                        if 'StringDataRightTruncation' in error_msg or 'value too long' in error_msg.lower():
                            if error_count <= 3:
                                print(f"\n    ⚠️  字符串长度超限（已尝试截断但仍失败）: {error_msg[:200]}")
                        else:
                            if error_count <= 3:
                                print(f"\n    ⚠️  行导入失败: {error_msg[:200]}")
                        continue
                
                # 提交批次
                try:
                    db.session.commit()
                    print(f"✅ {imported_count} 行")
                    if error_count > 0:
                        print(f"    ⚠️  {error_count} 行跳过")
                    total_imported += imported_count
                    total_errors += error_count
                except Exception as e:
                    db.session.rollback()
                    print(f"❌ 提交失败: {e}")
                    total_errors += len(rows)
                    
            except Exception as e:
                print(f"❌ 表迁移失败: {e}")
                total_errors += 1
                continue
        
        sqlite_conn.close()
        
        print("\n" + "=" * 60)
        print("迁移完成！")
        print("=" * 60)
        print(f"✅ 成功导入: {total_imported} 行")
        if total_errors > 0:
            print(f"⚠️  跳过/错误: {total_errors} 行")
        print("\n建议: 验证数据完整性后，可以备份SQLite数据库。")
        
except Exception as e:
    print(f"\n❌ 迁移失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
