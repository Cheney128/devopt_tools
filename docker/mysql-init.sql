-- MySQL初始化脚本
-- 在容器首次启动时执行

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS switch_manage CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE switch_manage;

-- 授予权限给应用用户
-- 注意：用户已在环境变量中创建，这里只需确保权限正确
GRANT ALL PRIVILEGES ON switch_manage.* TO '${MYSQL_USER}'@'%';

-- 刷新权限
FLUSH PRIVILEGES;

-- 打印初始化完成信息
SELECT 'MySQL initialization completed' AS status;
