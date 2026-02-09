#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端数据库自动迁移脚本

用途：在云端 Linux 服务器上，自动完成：
  1. 加载 .env 配置（不依赖 python-dotenv）
  2. 创建 PostgreSQL 表结构
  3. 可选：从 SQLite 备份迁移数据

使用方法：
  cd /root/project_code
  python scripts/deployment/cloud_db_migrate.py

  # 仅创建表结构（不迁移数据）
  python scripts/deployment/cloud_db_migrate.py --tables-only

  # 创建表并迁移 SQLite 数据
  python scripts/deployment/cloud_db_migrate.py --migrate
"""

import os
import sys
import argparse

# 切换到项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)


def load_env_manual():
    """手动解析 .env 文件，不依赖 python-dotenv"""
    env_path = os.path.join(PROJECT_ROOT, '.env')
    if not os.path.exists(env_path):
        print(f"⚠️  .env 文件不存在: {env_path}")
        return False

    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key:
                    os.environ[key] = value

    print("✅ 已加载 .env 配置")
    return True


def ensure_required_env():
    """确保必要环境变量已设置"""
    # 尝试用 python-dotenv 加载（若已安装）
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(PROJECT_ROOT, '.env'), override=True)
        print("✅ 使用 python-dotenv 加载 .env")
    except ImportError:
        load_env_manual()

    # 迁移脚本执行时，临时设置 SECRET_KEY（若未设置）
    if not os.environ.get('SECRET_KEY'):
        os.environ['SECRET_KEY'] = 'cloud-migrate-temp-key-' + os.urandom(16).hex()
        print("⚠️  未设置 SECRET_KEY，已使用临时值（迁移完成后请在 .env 中设置正式 SECRET_KEY）")

    # 检查 DATABASE_URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url or 'postgresql' not in db_url:
        print("❌ 错误: .env 中未设置 PostgreSQL 的 DATABASE_URL")
        print("   请添加: DATABASE_URL=postgresql://aistudio_user:密码@localhost:5432/pet_painting")
        return False

    print(f"   数据库: {db_url.split('@')[-1] if '@' in db_url else db_url[:50]}...")
    return True


def create_tables():
    """创建 PostgreSQL 表结构"""
    print("\n" + "=" * 60)
    print("创建数据库表结构")
    print("=" * 60)

    try:
        from app import create_app, db
        app = create_app()  # 必须先创建 app，db 才能正确初始化
        import app.models  # 导入所有模型以注册表（此时 app.models 会从 app 获取 db）

        with app.app_context():
            db.create_all()
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"✅ 表结构创建成功！共 {len(tables)} 个表")
            for t in sorted(tables):
                print(f"   - {t}")
        return True
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def migrate_from_sqlite():
    """从 SQLite 迁移数据到 PostgreSQL"""
    sqlite_path = os.path.join(PROJECT_ROOT, 'instance', 'pet_painting.db')
    if not os.path.exists(sqlite_path):
        print(f"\n⚠️  未找到 SQLite 备份: {sqlite_path}")
        print("   跳过数据迁移（仅创建了空表）")
        return True

    print("\n" + "=" * 60)
    print("从 SQLite 迁移数据")
    print("=" * 60)

    try:
        mig_path = os.path.join(PROJECT_ROOT, 'scripts', 'database', 'migrate_sqlite_to_postgresql.py')
        import importlib.util
        spec = importlib.util.spec_from_file_location("migrate_mod", mig_path)
        mig = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mig)
        result = mig.export_sqlite_data(sqlite_path)
        if result:
            export_file, data = result
            mig.import_to_postgresql(export_file=export_file, data=data)
            print("✅ 数据迁移完成")
            return True
        return False
    except Exception as e:
        print(f"⚠️  数据迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description='云端数据库自动迁移')
    parser.add_argument('--tables-only', action='store_true', help='仅创建表结构，不迁移数据')
    parser.add_argument('--migrate', action='store_true', help='创建表后迁移 SQLite 数据')
    args = parser.parse_args()

    print("=" * 60)
    print("云端数据库自动迁移")
    print("=" * 60)

    if not ensure_required_env():
        sys.exit(1)

    if not create_tables():
        sys.exit(1)

    # 默认：若存在 SQLite 备份则迁移
    do_migrate = args.migrate or (not args.tables_only and os.path.exists(
        os.path.join(PROJECT_ROOT, 'instance', 'pet_painting.db')))
    if do_migrate:
        migrate_from_sqlite()
    else:
        print("\n✅ 表结构已就绪，可启动应用")

    print("\n" + "=" * 60)
    print("下一步：")
    print("  1. 确认 .env 中已设置 SECRET_KEY（生产环境必须）")
    print("  2. 运行: pip install python-dotenv  （若未安装）")
    print("  3. 重启应用: sudo systemctl restart aistudio")
    print("=" * 60)


if __name__ == '__main__':
    main()
