# -*- coding: utf-8 -*-
"""
创建PostgreSQL表结构
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

print("=" * 60)
print("创建 PostgreSQL 表结构")
print("=" * 60)

try:
    from app import create_app, db
    import app.models  # 导入所有模型
    
    app = create_app()
    
    with app.app_context():
        print("\n正在创建表结构...")
        db.create_all()
        print("✅ 表结构创建成功！")
        
        # 显示创建的表
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"\n✅ 已创建 {len(tables)} 个表：")
        for table in sorted(tables):
            print(f"   - {table}")
        
        print("\n" + "=" * 60)
        print("✅ 完成！现在可以开始使用PostgreSQL数据库了。")
        print("=" * 60)
        
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
