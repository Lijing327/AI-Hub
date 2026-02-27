-- 为 kb_article 表添加 source_type、source_id 字段
-- 用于关联工单等来源（如：source_type='ticket', source_id='123'）

USE ai_hub;
GO

IF EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_article')
BEGIN
    -- 添加 source_type 列
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('kb_article') AND name = 'source_type')
    BEGIN
        ALTER TABLE kb_article ADD source_type NVARCHAR(50) NULL;
        PRINT '已为 kb_article 表添加 source_type 字段';
    END
    ELSE
        PRINT 'kb_article 表已存在 source_type 字段';

    -- 添加 source_id 列
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('kb_article') AND name = 'source_id')
    BEGIN
        ALTER TABLE kb_article ADD source_id NVARCHAR(50) NULL;
        PRINT '已为 kb_article 表添加 source_id 字段';
    END
    ELSE
        PRINT 'kb_article 表已存在 source_id 字段';
END
GO
