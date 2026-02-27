-- =====================================================
-- AI-Hub 售后工单系统数据库脚本
-- 创建工单主表和日志表
-- =====================================================

USE ai_hub;
GO

-- -----------------------------------------------------
-- 工单主表 (ticket)
-- -----------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[ticket]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[ticket] (
        [ticket_id] UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
        [tenant_id] NVARCHAR(64) NOT NULL,
        [ticket_no] NVARCHAR(32) NOT NULL,
        [title] NVARCHAR(256) NOT NULL,
        [description] NVARCHAR(MAX) NULL,
        [status] NVARCHAR(20) NOT NULL DEFAULT 'pending',
        [priority] NVARCHAR(10) NOT NULL DEFAULT 'medium',
        [source] NVARCHAR(20) NOT NULL DEFAULT 'manual',
        [customer_id] NVARCHAR(64) NULL,
        [device_id] NVARCHAR(64) NULL,
        [device_mn] NVARCHAR(64) NULL,
        [session_id] UNIQUEIDENTIFIER NULL,
        [trigger_message_id] UNIQUEIDENTIFIER NULL,
        [assignee_id] NVARCHAR(64) NULL,
        [assignee_name] NVARCHAR(64) NULL,
        [created_by] NVARCHAR(64) NOT NULL,
        [created_at] DATETIME2 NOT NULL DEFAULT GETDATE(),
        [updated_at] DATETIME2 NULL,
        [closed_at] DATETIME2 NULL,
        [final_solution_summary] NVARCHAR(MAX) NULL,
        [meta_json] NVARCHAR(MAX) NULL,
        [kb_article_id] INT NULL
    );

    -- 索引
    CREATE INDEX [IX_ticket_tenant_id] ON [dbo].[ticket]([tenant_id]);
    CREATE INDEX [IX_ticket_status] ON [dbo].[ticket]([status]);
    CREATE INDEX [IX_ticket_created_at] ON [dbo].[ticket]([created_at] DESC);
    CREATE INDEX [IX_ticket_ticket_no] ON [dbo].[ticket]([ticket_no]);
    CREATE INDEX [IX_ticket_kb_article_id] ON [dbo].[ticket]([kb_article_id]) WHERE [kb_article_id] IS NOT NULL;

    PRINT 'Table [dbo].[ticket] created successfully.';
END
ELSE
BEGIN
    PRINT 'Table [dbo].[ticket] already exists.';
END
GO

-- -----------------------------------------------------
-- 工单日志表 (ticket_log)
-- -----------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[ticket_log]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[ticket_log] (
        [log_id] BIGINT IDENTITY(1,1) PRIMARY KEY,
        [ticket_id] UNIQUEIDENTIFIER NOT NULL,
        [action] NVARCHAR(64) NOT NULL,
        [content] NVARCHAR(MAX) NULL,
        [operator_id] NVARCHAR(64) NOT NULL,
        [operator_name] NVARCHAR(64) NULL,
        [next_status] NVARCHAR(20) NULL,
        [created_at] DATETIME2 NOT NULL DEFAULT GETDATE()
    );

    -- 索引
    CREATE INDEX [IX_ticket_log_ticket_id] ON [dbo].[ticket_log]([ticket_id]);
    CREATE INDEX [IX_ticket_log_created_at] ON [dbo].[ticket_log]([created_at] DESC);

    PRINT 'Table [dbo].[ticket_log] created successfully.';
END
ELSE
BEGIN
    PRINT 'Table [dbo].[ticket_log] already exists.';
END
GO
