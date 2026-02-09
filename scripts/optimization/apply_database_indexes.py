# -*- coding: utf-8 -*-
"""
应用数据库索引优化
执行索引创建SQL语句
"""
import os
import sys
from pathlib import Path

# 设置项目根目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def apply_indexes():
    """应用数据库索引"""
    # 读取SQL文件
    sql_file = project_root / 'scripts' / 'optimization' / 'database_indexes.sql'
    
    if not sql_file.exists():
        print(f"错误: SQL文件不存在: {sql_file}")
        return False
    
    # 导入必要的模块
    try:
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            db = test_server_module.db
            app = test_server_module.app
        else:
            print("错误: test_server模块未加载")
            return False
    except Exception as e:
        print(f"错误: 无法获取数据库连接: {e}")
        return False
    
    # 读取SQL语句
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 解析SQL语句（忽略注释）
    sql_statements = []
    for line in sql_content.split('\n'):
        line = line.strip()
        if line and not line.startswith('--'):
            # 移除行尾注释
            if '--' in line:
                line = line[:line.index('--')].strip()
            if line:
                sql_statements.append(line)
    
    print(f"找到 {len(sql_statements)} 个索引创建语句")
    
    # 在应用上下文中执行
    with app.app_context():
        success_count = 0
        error_count = 0
        
        for sql in sql_statements:
            try:
                db.session.execute(db.text(sql))
                success_count += 1
                print(f"✅ 创建索引: {sql[:80]}...")
            except Exception as e:
                error_count += 1
                # 如果是索引已存在的错误，不算错误
                error_str = str(e).lower()
                if 'already exists' in error_str or 'duplicate' in error_str:
                    print(f"ℹ️  索引已存在: {sql[:80]}...")
                    success_count += 1
                    error_count -= 1
                else:
                    print(f"❌ 创建索引失败: {sql[:80]}...")
                    print(f"   错误: {e}")
        
        # 提交事务
        try:
            db.session.commit()
            print(f"\n✅ 成功创建 {success_count} 个索引")
            if error_count > 0:
                print(f"⚠️  {error_count} 个索引创建失败")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 提交事务失败: {e}")
            return False

if __name__ == '__main__':
    print("=" * 80)
    print("应用数据库索引优化")
    print("=" * 80)
    
    # 需要先导入test_server来初始化数据库连接
    print("\n提示: 请先启动应用服务器，然后运行此脚本")
    print("或者使用以下方式:")
    print("  python -c \"import sys; sys.path.insert(0, '.'); from test_server import *; exec(open('scripts/optimization/apply_database_indexes.py').read())\"")
    print("\n或者直接在Python交互式环境中:")
    print("  >>> from scripts.optimization.apply_database_indexes import apply_indexes")
    print("  >>> apply_indexes()")
    print("=" * 80)
