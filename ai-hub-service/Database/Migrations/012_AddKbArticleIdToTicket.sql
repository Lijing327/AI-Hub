-- 为 ticket 表添加 kb_article_id 字段
-- 用于工单转知识库时关联已创建的文章，防止重复转换
-- 注意：每步后用 GO 分隔批次，确保 DDL 生效后再执行下一步

USE ai_hub;
GO

-- 1. 添加列
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'ticket')
   AND NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('ticket') AND name = 'kb_article_id')
BEGIN
    ALTER TABLE ticket ADD kb_article_id INT NULL;
    PRINT '已为 ticket 表添加 kb_article_id 字段';
END
ELSE IF EXISTS (SELECT * FROM sys.tables WHERE name = 'ticket')
    PRINT 'ticket 表已存在 kb_article_id 字段';
GO

-- 2. 创建索引（不添加外键，减少约束）
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'ticket')
   AND EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('ticket') AND name = 'kb_article_id')
   AND NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_ticket_kb_article_id' AND object_id = OBJECT_ID('ticket'))
BEGIN
    CREATE INDEX IX_ticket_kb_article_id ON ticket(kb_article_id) WHERE kb_article_id IS NOT NULL;
    PRINT '已创建索引 IX_ticket_kb_article_id';
END
GO
