-- 快速修复：为 meitu_api_call_log 表添加 msg_id 字段
-- 使用方法：在SQLite工具中执行此SQL，或使用命令行：
-- sqlite3 instance/app.db < fix_msg_id_field.sql

-- 检查字段是否已存在（如果已存在，会报错，可以忽略）
ALTER TABLE meitu_api_call_log ADD COLUMN msg_id VARCHAR(100);

-- 从现有的 response_data 中提取 msg_id 并更新到新字段
-- 注意：SQLite不支持UPDATE中的JSON函数，所以这个需要在Python中执行
-- 或者使用以下方式（如果response_data是简单的JSON格式）：
-- UPDATE meitu_api_call_log 
-- SET msg_id = substr(response_data, 
--                     instr(response_data, '"msg_id":"') + 10,
--                     instr(substr(response_data, instr(response_data, '"msg_id":"') + 10), '"') - 1)
-- WHERE response_data LIKE '%"msg_id"%' AND msg_id IS NULL;
