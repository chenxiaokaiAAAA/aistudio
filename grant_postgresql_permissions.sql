-- 授予PostgreSQL用户权限
-- 在pgAdmin中连接到pet_painting数据库后执行此脚本

-- 授予schema权限
GRANT ALL ON SCHEMA public TO aistudio_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO aistudio_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO aistudio_user;

-- 授予创建表权限
GRANT CREATE ON SCHEMA public TO aistudio_user;

-- 如果表已存在，授予表权限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO aistudio_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO aistudio_user;

-- 验证权限
SELECT 
    grantee, 
    privilege_type 
FROM information_schema.role_table_grants 
WHERE grantee = 'aistudio_user';
