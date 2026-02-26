-- ============================================================
-- 用户表改造（P0-2）
-- 执行时间：2026-02-26
-- 用途：将 phone 字段改为 account，支持手机号/邮箱/用户名登录
-- ============================================================

-- 1. 重命名字段：phone -> account
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('users') AND name = 'phone')
BEGIN
    EXEC sp_rename 'dbo.users.phone', 'account', 'COLUMN';
    PRINT '✅ 已重命名 users.phone 为 users.account';
END

-- 2. 修改字段长度：NVARCHAR(20) -> NVARCHAR(100)
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('users') AND name = 'account')
BEGIN
    ALTER TABLE users ALTER COLUMN account NVARCHAR(100) NOT NULL;
    PRINT '✅ 已修改 users.account 字段长度为 NVARCHAR(100)';
END

-- 3. 删除旧索引
IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_users_phone')
BEGIN
    DROP INDEX IX_users_phone ON users;
    PRINT '✅ 已删除索引 IX_users_phone';
END

-- 4. 创建新索引
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_users_account')
BEGIN
    CREATE UNIQUE INDEX IX_users_account ON users (account);
    PRINT '✅ 已创建唯一索引 IX_users_account';
END

-- 5. 删除旧的唯一约束（如果有）
DECLARE @constraint_name NVARCHAR(128);
DECLARE constraint_cursor CURSOR FOR
    SELECT name FROM sys.default_constraints
    WHERE parent_object_id = OBJECT_ID('users') AND parent_column_id = (SELECT column_id FROM sys.columns WHERE object_id = OBJECT_ID('users') AND name = 'account');
OPEN constraint_cursor;
FETCH NEXT FROM constraint_cursor INTO @constraint_name;
WHILE @@FETCH_STATUS = 0
BEGIN
    EXEC('ALTER TABLE users DROP CONSTRAINT ' + @constraint_name);
    PRINT '✅ 已删除约束 ' + @constraint_name;
    FETCH NEXT FROM constraint_cursor INTO @constraint_name;
END
CLOSE constraint_cursor;
DEALLOCATE constraint_cursor;

PRINT '========================================================';
PRINT '✅ 用户表改造完成：phone -> account，支持多种登录方式';
PRINT '========================================================';
GO
