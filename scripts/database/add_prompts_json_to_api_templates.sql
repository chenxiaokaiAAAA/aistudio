-- 数据库迁移SQL脚本：为 api_templates 表添加 prompts_json 字段
-- 用于支持批量提示词功能

-- 检查字段是否已存在（SQLite不支持IF NOT EXISTS，需要手动检查）
-- 如果字段已存在，请跳过此脚本

-- SQLite
ALTER TABLE api_templates 
ADD COLUMN prompts_json TEXT;

-- 字段说明：
-- prompts_json: 批量提示词（JSON格式），例如：["提示词1", "提示词2"]
-- 如果设置了此字段，将使用此字段创建多个任务
-- 如果未设置，则使用 default_prompt 字段（单个提示词）
