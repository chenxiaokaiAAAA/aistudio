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

-- 修复 orders 表序列（解决创建订单时主键重复）
SELECT setval(
    pg_get_serial_sequence('orders', 'id'),
    COALESCE((SELECT MAX(id) FROM orders), 1)
);

-- 修复 order_image 表序列（测试工作流、订单图片插入）
SELECT setval(
    pg_get_serial_sequence('order_image', 'id'),
    COALESCE((SELECT MAX(id) FROM order_image), 1)
);

-- 修复 ai_tasks 表序列（AI 任务、API 工作流）
SELECT setval(
    pg_get_serial_sequence('ai_tasks', 'id'),
    COALESCE((SELECT MAX(id) FROM ai_tasks), 1)
);

-- 修复 meitu_api_call_log 表序列（AI 美颜任务调用日志）
SELECT setval(
    pg_get_serial_sequence('meitu_api_call_log', 'id'),
    COALESCE((SELECT MAX(id) FROM meitu_api_call_log), 1)
);

-- 修复 selection_orders 表序列（选片订单）
SELECT setval(
    pg_get_serial_sequence('selection_orders', 'id'),
    COALESCE((SELECT MAX(id) FROM selection_orders), 1)
);

-- 修复 style_image / style_category 表序列（风格配置、工作流关联）
SELECT setval(
    pg_get_serial_sequence('style_image', 'id'),
    COALESCE((SELECT MAX(id) FROM style_image), 1)
);
SELECT setval(
    pg_get_serial_sequence('style_category', 'id'),
    COALESCE((SELECT MAX(id) FROM style_category), 1)
);

-- 修复 operation_logs / coupons / user_coupons（操作日志、优惠券）
SELECT setval(
    pg_get_serial_sequence('operation_logs', 'id'),
    COALESCE((SELECT MAX(id) FROM operation_logs), 1)
);
SELECT setval(
    pg_get_serial_sequence('coupons', 'id'),
    COALESCE((SELECT MAX(id) FROM coupons), 1)
);
SELECT setval(
    pg_get_serial_sequence('user_coupons', 'id'),
    COALESCE((SELECT MAX(id) FROM user_coupons), 1)
);
