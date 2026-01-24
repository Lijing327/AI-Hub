-- 添加软删除字段脚本
-- 为 kb_article 和 kb_asset 表添加 deleted_at 字段
-- 数据库：SQL Server (ai_hub)

USE ai_hub;
GO

-- ============================================
-- 1. 为 kb_article 表添加 deleted_at 字段
-- ============================================
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_article')
BEGIN
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('kb_article') AND name = 'deleted_at')
    BEGIN
        ALTER TABLE kb_article ADD deleted_at DATETIME;
        CREATE INDEX idx_deleted_at ON kb_article(deleted_at);
        PRINT '已为 kb_article 表添加 deleted_at 字段';
    END
    ELSE
    BEGIN
        PRINT 'kb_article 表已存在 deleted_at 字段';
    END
END
GO

-- ============================================
-- 2. 为 kb_asset 表添加 deleted_at 字段
-- ============================================
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_asset')
BEGIN
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('kb_asset') AND name = 'deleted_at')
    BEGIN
        ALTER TABLE kb_asset ADD deleted_at DATETIME;
        CREATE INDEX idx_deleted_at ON kb_asset(deleted_at);
        PRINT '已为 kb_asset 表添加 deleted_at 字段';
    END
    ELSE
    BEGIN
        PRINT 'kb_asset 表已存在 deleted_at 字段';
    END
END
GO

PRINT '软删除字段添加完成！';
PRINT '说明：';
PRINT '  - deleted_at 为 NULL 表示未删除';
PRINT '  - deleted_at 不为 NULL 表示已删除（软删除）';
PRINT '  - 所有查询会自动过滤已删除的记录';
GO
