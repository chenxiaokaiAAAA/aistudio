-- 添加 free_selection_count 字段到 products 表
ALTER TABLE products ADD COLUMN free_selection_count INTEGER DEFAULT 1;

-- 更新现有记录的默认值
UPDATE products SET free_selection_count = 1 WHERE free_selection_count IS NULL;
