-- 移除 orders 表中 order_number 字段的唯一约束
-- 支持追加产品、按二级分类分组创建多订单：多个订单记录可使用相同订单号
-- 执行: psql -U aistudio_user -d pet_painting -f scripts/database/remove_order_number_unique_postgresql.sql

ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_order_number_key;
