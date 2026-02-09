# -*- coding: utf-8 -*-
"""
清空PostgreSQL数据库中的数据（用于重新开始迁移）
⚠️ 警告：此操作会删除PostgreSQL中的所有数据！
"""
import os
import sys
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

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("=" * 60)
print("⚠️  清空PostgreSQL数据")
print("=" * 60)
print("\n警告：此操作将删除PostgreSQL数据库中的所有数据！")
print("表结构将保留，但所有数据将被清空。")
print("\n此操作不可逆，请确保您已备份重要数据。")

# 确认操作
confirm = input("\n请输入 'YES' 确认清空数据: ").strip()
if confirm != 'YES':
    print("操作已取消。")
    sys.exit(0)

try:
    from app import create_app, db
    from sqlalchemy import inspect, text
    
    app = create_app()
    
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"\n找到 {len(tables)} 个表")
        print("\n开始清空数据...")
        
        # 禁用外键检查（PostgreSQL使用TRUNCATE CASCADE）
        # 按依赖顺序清空表（从有外键的表开始）
        cleared_count = 0
        error_count = 0
        
        # 先尝试使用TRUNCATE（更快）
        for table_name in tables:
            try:
                # 使用TRUNCATE CASCADE来清空表及其依赖
                db.session.execute(text(f'TRUNCATE TABLE "{table_name}" CASCADE'))
                cleared_count += 1
                print(f"  ✅ {table_name}")
            except Exception as e:
                # 如果TRUNCATE失败，尝试DELETE
                try:
                    db.session.execute(text(f'DELETE FROM "{table_name}"'))
                    cleared_count += 1
                    print(f"  ✅ {table_name} (使用DELETE)")
                except Exception as e2:
                    error_count += 1
                    print(f"  ❌ {table_name}: {e2}")
        
        # 提交更改
        try:
            db.session.commit()
            print(f"\n✅ 清空完成！")
            print(f"   成功清空: {cleared_count} 个表")
            if error_count > 0:
                print(f"   ⚠️  失败: {error_count} 个表")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 提交失败: {e}")
            sys.exit(1)
        
        print("\n现在可以重新运行迁移脚本:")
        print("  python migrate_data_auto.py")
        
except Exception as e:
    print(f"\n❌ 清空失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
