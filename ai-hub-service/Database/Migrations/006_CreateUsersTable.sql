-- ============================================================
-- 用户表（P0-1）
-- 执行时间: 2026-02-25
-- 用途: 用户认证系统
-- ============================================================

-- 创建用户表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'users')
BEGIN
    CREATE TABLE users (
        id                  NVARCHAR(64)         NOT NULL PRIMARY KEY DEFAULT NEWID(),  -- 用户ID
        phone               NVARCHAR(20)         NOT NULL UNIQUE,                      -- 手机号（唯一）
        password_hash       NVARCHAR(256)        NOT NULL,                            -- 密码哈希
        status              NVARCHAR(16)         NOT NULL DEFAULT 'active',            -- 状态：active/disabled
        created_at          DATETIME2            NOT NULL DEFAULT GETUTCDATE(),       -- 创建时间
        updated_at          DATETIME2            NOT NULL DEFAULT GETUTCDATE()        -- 更新时间
    );

    -- 索引
    CREATE INDEX IX_users_phone ON users (phone);
    CREATE INDEX IX_users_status ON users (status);
    CREATE INDEX IX_users_created_at ON users (created_at DESC);
END
GO

PRINT '✅ 用户表创建完成';
GO