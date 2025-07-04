-- 修复 MySQL 排序内存错误的数据库优化脚本

-- 1. 为 created_at 列添加索引以提高排序性能
ALTER TABLE openapi_docs ADD INDEX idx_created_at (created_at);

-- 2. 为项目ID和创建时间添加复合索引（可选，进一步优化查询）
ALTER TABLE openapi_docs ADD INDEX idx_project_created (project_id, created_at DESC);

-- 3. 增加 MySQL 服务器内存配置（需要重启 MySQL 服务）
-- 将以下配置添加到 my.cnf 或 my.ini 文件的 [mysqld] 部分：
/*
[mysqld]
sort_buffer_size = 2M
read_buffer_size = 128K
innodb_buffer_pool_size = 1G  # 根据服务器内存调整，建议为可用内存的75%
max_sort_length = 1024
*/

-- 4. 临时会话级别设置（立即生效，但重启后失效）
SET SESSION sort_buffer_size = 2097152;  -- 2MB
SET SESSION read_buffer_size = 131072;   -- 128KB

-- 5. 全局设置（立即生效，但重启后失效）
SET GLOBAL sort_buffer_size = 2097152;   -- 2MB  
SET GLOBAL read_buffer_size = 131072;    -- 128KB

-- 6. 检查当前配置
SHOW VARIABLES LIKE 'sort_buffer_size';
SHOW VARIABLES LIKE 'read_buffer_size';
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';

-- 7. 查看表结构确认索引已添加
SHOW INDEX FROM openapi_docs;