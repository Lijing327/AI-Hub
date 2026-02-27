-- 删除所有外键约束（针对已运行过旧脚本的数据库）
-- 执行此脚本后，数据库将无外键约束，与当前迁移脚本策略一致

USE ai_hub;
GO

-- 按名称删除已知的外键（若存在则删除，不存在则跳过）
DECLARE @sql NVARCHAR(500);

-- ticket 相关
IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ticket_kb_article')
BEGIN
    ALTER TABLE ticket DROP CONSTRAINT FK_ticket_kb_article;
    PRINT '已删除 FK_ticket_kb_article';
END
IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ticket_knowledge_article')
BEGIN
    ALTER TABLE ticket DROP CONSTRAINT FK_ticket_knowledge_article;
    PRINT '已删除 FK_ticket_knowledge_article';
END
IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ticket_log_ticket')
BEGIN
    ALTER TABLE ticket_log DROP CONSTRAINT FK_ticket_log_ticket;
    PRINT '已删除 FK_ticket_log_ticket';
END

-- AI 审计表相关
IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ai_message_conversation')
BEGIN
    ALTER TABLE ai_message DROP CONSTRAINT FK_ai_message_conversation;
    PRINT '已删除 FK_ai_message_conversation';
END
IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ai_decision_message')
BEGIN
    ALTER TABLE ai_decision_log DROP CONSTRAINT FK_ai_decision_message;
    PRINT '已删除 FK_ai_decision_message';
END
IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ai_retrieval_message')
BEGIN
    ALTER TABLE ai_retrieval_log DROP CONSTRAINT FK_ai_retrieval_message;
    PRINT '已删除 FK_ai_retrieval_message';
END
IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_ai_response_message')
BEGIN
    ALTER TABLE ai_response DROP CONSTRAINT FK_ai_response_message;
    PRINT '已删除 FK_ai_response_message';
END

-- kb_asset、kb_chunk、kb_attachment 的外键可能为自动命名，按父表查找并删除
DECLARE @fk_name NVARCHAR(128);

IF EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_asset')
BEGIN
    SELECT TOP 1 @fk_name = name FROM sys.foreign_keys WHERE parent_object_id = OBJECT_ID('kb_asset');
    IF @fk_name IS NOT NULL
    BEGIN
        SET @sql = 'ALTER TABLE kb_asset DROP CONSTRAINT ' + QUOTENAME(@fk_name);
        EXEC sp_executesql @sql;
        PRINT '已删除 kb_asset 外键: ' + @fk_name;
    END
END

IF EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_chunk')
BEGIN
    SELECT TOP 1 @fk_name = name FROM sys.foreign_keys WHERE parent_object_id = OBJECT_ID('kb_chunk');
    IF @fk_name IS NOT NULL
    BEGIN
        SET @sql = 'ALTER TABLE kb_chunk DROP CONSTRAINT ' + QUOTENAME(@fk_name);
        EXEC sp_executesql @sql;
        PRINT '已删除 kb_chunk 外键: ' + @fk_name;
    END
END

IF EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_attachment')
BEGIN
    SELECT TOP 1 @fk_name = name FROM sys.foreign_keys WHERE parent_object_id = OBJECT_ID('kb_attachment');
    IF @fk_name IS NOT NULL
    BEGIN
        SET @sql = 'ALTER TABLE kb_attachment DROP CONSTRAINT ' + QUOTENAME(@fk_name);
        EXEC sp_executesql @sql;
        PRINT '已删除 kb_attachment 外键: ' + @fk_name;
    END
END

PRINT '✅ 外键清理完成';
GO
