#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移除 PostgreSQL orders 表中 order_number 字段的唯一约束
支持追加产品、按二级分类分组创建多订单：多个订单记录可使用相同订单号
"""

import os
import sys

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    import psycopg2
    from urllib.parse import urlparse
except ImportError:
    print("请安装: pip install psycopg2-binary")
    sys.exit(1)


def get_db_params():
    """从 DATABASE_URL 解析连接参数"""
    url = os.environ.get("DATABASE_URL")
    if not url or "postgresql" not in url:
        print("请设置环境变量: DATABASE_URL=postgresql://user:password@host:port/dbname")
        return None
    parsed = urlparse(url)
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/") or "pet_painting",
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
    }


def remove_unique_constraint():
    """移除 order_number 的唯一约束"""
    params = get_db_params()
    if not params:
        return False

    try:
        conn = psycopg2.connect(**params)
        conn.autocommit = True
        cur = conn.cursor()

        # 查找 orders 表上 order_number 相关的唯一约束（PostgreSQL 默认名为 orders_order_number_key）
        cur.execute("""
            SELECT conname FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            WHERE t.relname = 'orders' AND c.contype = 'u'
        """)
        rows = cur.fetchall()

        # 过滤出包含 order_number 的约束（单列唯一约束名通常为 orders_order_number_key）
        to_drop = []
        for (conname,) in rows:
            if "order_number" in conname.lower() or conname == "orders_order_number_key":
                to_drop.append(conname)

        if not to_drop:
            # 尝试直接删除默认约束名
            to_drop = ["orders_order_number_key"]

        for conname in to_drop:
            try:
                cur.execute(f'ALTER TABLE orders DROP CONSTRAINT IF EXISTS "{conname}"')
                print(f"已移除约束: {conname}")
            except psycopg2.Error as e:
                if "does not exist" in str(e):
                    print(f"约束 {conname} 不存在，跳过")
                else:
                    raise

        cur.close()
        conn.close()
        print("[成功] 已移除 order_number 的唯一约束")
        return True

    except Exception as e:
        print(f"[失败] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("移除 PostgreSQL orders 表 order_number 唯一约束")
    print("=" * 60)
    success = remove_unique_constraint()
    sys.exit(0 if success else 1)
