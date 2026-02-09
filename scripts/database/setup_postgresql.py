# -*- coding: utf-8 -*-
"""
PostgreSQL数据库初始化脚本
用于创建数据库、用户和表结构
"""
import os
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database_and_user():
    """创建数据库和用户"""
    print("=" * 60)
    print("PostgreSQL 数据库初始化")
    print("=" * 60)
    
    # 获取配置
    print("\n请输入PostgreSQL配置信息：")
    host = input("数据库主机 (默认: localhost): ").strip() or "localhost"
    port = input("端口 (默认: 5432): ").strip() or "5432"
    admin_user = input("PostgreSQL管理员用户名 (默认: postgres): ").strip() or "postgres"
    admin_password = input(f"管理员密码: ").strip()
    
    db_name = input("数据库名称 (默认: pet_painting): ").strip() or "pet_painting"
    db_user = input("数据库用户名 (默认: aistudio_user): ").strip() or "aistudio_user"
    db_password = input(f"数据库用户密码: ").strip()
    
    if not db_password:
        print("❌ 错误: 数据库用户密码不能为空")
        return False
    
    try:
        # 连接到PostgreSQL服务器（使用管理员账户）
        print(f"\n正在连接到PostgreSQL服务器 ({host}:{port})...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=admin_user,
            password=admin_password,
            database='postgres'  # 连接到默认数据库
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # 检查数据库是否已存在
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,)
        )
        if cursor.fetchone():
            print(f"⚠️  数据库 '{db_name}' 已存在")
            overwrite = input("是否删除并重新创建? (y/N): ").strip().lower()
            if overwrite == 'y':
                # 断开所有连接
                cursor.execute(
                    sql.SQL("SELECT pg_terminate_backend(pg_stat_activity.pid) "
                           "FROM pg_stat_activity "
                           "WHERE pg_stat_activity.datname = %s "
                           "AND pid <> pg_backend_pid()"),
                    (db_name,)
                )
                cursor.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(db_name)))
                print(f"✅ 已删除数据库 '{db_name}'")
            else:
                print("跳过数据库创建")
                return False
        
        # 创建数据库
        print(f"正在创建数据库 '{db_name}'...")
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
        print(f"✅ 数据库 '{db_name}' 创建成功")
        
        # 检查用户是否已存在
        cursor.execute(
            "SELECT 1 FROM pg_roles WHERE rolname = %s",
            (db_user,)
        )
        if cursor.fetchone():
            print(f"⚠️  用户 '{db_user}' 已存在")
            overwrite = input("是否删除并重新创建? (y/N): ").strip().lower()
            if overwrite == 'y':
                cursor.execute(sql.SQL("DROP USER {}").format(sql.Identifier(db_user)))
                print(f"✅ 已删除用户 '{db_user}'")
            else:
                print("跳过用户创建，只更新密码")
                cursor.execute(
                    sql.SQL("ALTER USER {} WITH PASSWORD %s").format(sql.Identifier(db_user)),
                    (db_password,)
                )
                print(f"✅ 用户密码已更新")
                cursor.close()
                conn.close()
                return True
        
        # 创建用户
        print(f"正在创建用户 '{db_user}'...")
        cursor.execute(
            sql.SQL("CREATE USER {} WITH PASSWORD %s").format(sql.Identifier(db_user)),
            (db_password,)
        )
        print(f"✅ 用户 '{db_user}' 创建成功")
        
        # 授予权限
        print(f"正在授予权限...")
        cursor.execute(
            sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
                sql.Identifier(db_name),
                sql.Identifier(db_user)
            )
        )
        print(f"✅ 权限授予成功")
        
        cursor.close()
        conn.close()
        
        # 连接到新创建的数据库，授予schema权限
        print(f"正在设置schema权限...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=admin_user,
            password=admin_password,
            database=db_name
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        cursor.execute(
            sql.SQL("GRANT ALL ON SCHEMA public TO {}").format(sql.Identifier(db_user))
        )
        cursor.execute(
            sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {}").format(
                sql.Identifier(db_user)
            )
        )
        cursor.execute(
            sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {}").format(
                sql.Identifier(db_user)
            )
        )
        print(f"✅ Schema权限设置成功")
        
        cursor.close()
        conn.close()
        
        # 生成连接字符串
        connection_string = f"postgresql://{db_user}:{db_password}@{host}:{port}/{db_name}"
        
        print("\n" + "=" * 60)
        print("✅ 数据库初始化完成！")
        print("=" * 60)
        print(f"\n数据库连接信息：")
        print(f"  主机: {host}")
        print(f"  端口: {port}")
        print(f"  数据库: {db_name}")
        print(f"  用户: {db_user}")
        print(f"\n连接字符串（用于环境变量）：")
        print(f"  DATABASE_URL={connection_string}")
        print(f"\n请将以上连接字符串添加到环境变量或配置文件中。")
        
        # 保存到文件（可选）
        save = input("\n是否保存连接信息到 .env 文件? (y/N): ").strip().lower()
        if save == 'y':
            env_file = '.env'
            with open(env_file, 'a', encoding='utf-8') as f:
                f.write(f"\n# PostgreSQL配置\n")
                f.write(f"DATABASE_URL={connection_string}\n")
            print(f"✅ 已保存到 {env_file}")
        
        return True
        
    except psycopg2.Error as e:
        print(f"\n❌ PostgreSQL错误: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_tables():
    """创建表结构"""
    print("\n" + "=" * 60)
    print("创建数据库表结构")
    print("=" * 60)
    
    # 检查环境变量
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ 错误: 未找到 DATABASE_URL 环境变量")
        print("请先设置环境变量: export DATABASE_URL=postgresql://user:password@host:port/dbname")
        return False
    
    try:
        # 导入Flask应用和模型
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
        from app import create_app, db
        # 导入所有模型（在模块级别导入）
        import app.models
        
        app = create_app()
        
        with app.app_context():
            print("正在创建表结构...")
            db.create_all()
            print("✅ 表结构创建成功！")
            
            # 显示创建的表
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"\n已创建 {len(tables)} 个表：")
            for table in sorted(tables):
                print(f"  - {table}")
            
            return True
            
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("PostgreSQL 数据库设置工具")
    print("=" * 60)
    print("\n请选择操作：")
    print("1. 创建数据库和用户")
    print("2. 创建表结构（需要先设置DATABASE_URL环境变量）")
    print("3. 执行完整初始化（创建数据库+用户+表结构）")
    
    choice = input("\n请选择 (1/2/3): ").strip()
    
    if choice == '1':
        create_database_and_user()
    elif choice == '2':
        create_tables()
    elif choice == '3':
        if create_database_and_user():
            print("\n" + "=" * 60)
            input("请按Enter键继续创建表结构（确保已设置DATABASE_URL环境变量）...")
            create_tables()
    else:
        print("❌ 无效的选择")
