-- 修复 PostgreSQL 序列（pg_dump 恢复后 id 序列可能不同步，导致保存配置报 UniqueViolation）
-- 在服务器执行: sudo -u postgres psql -d pet_painting -f scripts/database/fix_postgresql_sequences.sql

-- 修复 ai_config 表序列（解决服务器URL、品牌名称等配置保存失败）
SELECT setval(
    pg_get_serial_sequence('ai_config', 'id'),
    COALESCE((SELECT MAX(id) FROM ai_config), 1)
);

-- 修复 user_visits 表序列（解决用户访问记录保存报 UniqueViolation）
SELECT setval(
    pg_get_serial_sequence('user_visits', 'id'),
    COALESCE((SELECT MAX(id) FROM user_visits), 0)
);

-- 修复 orders 表序列（解决创建订单时主键重复 键值"(id)=(4)"已经存在）
SELECT setval(
    pg_get_serial_sequence('orders', 'id'),
    COALESCE((SELECT MAX(id) FROM orders), 1)
);
