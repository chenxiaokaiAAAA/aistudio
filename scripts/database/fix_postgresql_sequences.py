#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 PostgreSQL 序列（解决 UniqueViolation 错误）
无需 psql，使用 Python 直接执行
"""

import os
import sys

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 加载 .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
if os.path.exists(env_path):
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

database_url = os.environ.get("DATABASE_URL", "")
if not database_url or "postgresql" not in database_url:
    print("❌ 未检测到 PostgreSQL 配置")
    print("   请确保 .env 中设置了 DATABASE_URL=postgresql://...")
    sys.exit(1)

try:
    import psycopg2
    from urllib.parse import urlparse
except ImportError as e:
    print(f"❌ 缺少依赖: {e}")
    sys.exit(1)


def main():
    parsed = urlparse(database_url)
    conn_params = {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/") if parsed.path else "pet_painting",
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
    }

    print("正在连接 PostgreSQL...")
    try:
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        cur = conn.cursor()
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        sys.exit(1)

    # 所有使用自增 id 且在工作流/API 中会插入的表（pg_dump 恢复后序列可能不同步）
    fixes = [
        ("ai_config", "id", 1),
        ("user_visits", "id", 0),
        ("orders", "id", 1),
        ("order_image", "id", 1),
        # AI 任务、测试工作流、API 工作流
        ("ai_tasks", "id", 1),
        # AI 美颜任务（美图 API 调用日志）
        ("meitu_api_call_log", "id", 1),
        # 选片订单、风格图片等
        ("selection_orders", "id", 1),
        ("style_image", "id", 1),
        ("style_category", "id", 1),
        # 其他可能在工作流/配置中插入的表
        ("operation_logs", "id", 1),
        ("coupons", "id", 1),
        ("user_coupons", "id", 1),
    ]

    for table, col, default in fixes:
        try:
            cur.execute(
                "SELECT setval(pg_get_serial_sequence(%s, %s), "
                "COALESCE((SELECT MAX(id) FROM " + table + "), %s))",
                (table, col, default),
            )
            cur.execute("SELECT MAX(id) FROM " + table)  # table 为脚本内固定值，无注入风险
            max_id = cur.fetchone()[0] or 0
            print(f"✅ {table}: 序列已修复 (当前 MAX(id)={max_id})")
        except Exception as e:
            print(f"⚠️  {table}: {e}")

    cur.close()
    conn.close()
    print("\n✅ 序列修复完成")


if __name__ == "__main__":
    main()
