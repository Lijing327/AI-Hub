-- 为 users 表添加 role 字段
-- 角色：user（普通用户）/ engineer（工程师）/ admin（管理员）
-- 工程师和管理员可访问 /api/admin/tickets
--
-- 执行后，可将某用户提升为管理员（用于测试）：
--   UPDATE users SET role = 'admin' WHERE account = '你的账号';
-- 然后重新登录以获取含 role 的新 token

USE ai_hub;
GO

IF EXISTS (SELECT * FROM sys.tables WHERE name = 'users')
BEGIN
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('users') AND name = 'role')
    BEGIN
        ALTER TABLE users ADD role NVARCHAR(16) NOT NULL DEFAULT 'user';
        CREATE INDEX IX_users_role ON users (role);
        PRINT '已为 users 表添加 role 字段';
    END
    ELSE
        PRINT 'users 表已存在 role 字段';
END
GO
