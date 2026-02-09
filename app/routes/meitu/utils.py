# -*- coding: utf-8 -*-
"""
美图模块工具函数
"""

import logging
import os

logger = logging.getLogger(__name__)


def get_table_columns(db, table_name):
    """获取表的所有列名（兼容PostgreSQL和SQLite）"""
    try:
        database_url = os.environ.get("DATABASE_URL", "")
        is_postgresql = database_url.startswith("postgresql://") or database_url.startswith(
            "postgres://"
        )

        if is_postgresql:
            # PostgreSQL: 使用 information_schema
            result = db.session.execute(
                db.text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = :table_name AND table_schema = 'public'
                """),
                {"table_name": table_name},
            ).fetchall()
            columns = {row[0]: row for row in result}
        else:
            # SQLite: 使用 PRAGMA
            result = db.session.execute(db.text(f"PRAGMA table_info({table_name})")).fetchall()
            columns = {row[1]: row for row in result}

        return columns
    except Exception as e:
        logger.warning(f"获取表结构失败: {str(e)}")
        return {}
