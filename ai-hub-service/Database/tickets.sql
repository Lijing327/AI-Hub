-- SQL Server (ai_hub) 脚本: database/tickets.sql
-- 创建工单主表
CREATE TABLE [ticket] (
    [ticket_id] UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWID(),
    [tenant_id] NVARCHAR(64) NOT NULL,
    [ticket_no] NVARCHAR(32) NOT NULL,
    [title] NVARCHAR(256) NOT NULL,
    [description] NVARCHAR(MAX),
    [status] NVARCHAR(20) NOT NULL DEFAULT 'pending',
    [priority] NVARCHAR(10) NOT NULL DEFAULT 'medium',
    [source] NVARCHAR(20) NOT NULL DEFAULT 'manual',
    [customer_id] NVARCHAR(64),
    [device_id] NVARCHAR(64),
    [device_mn] NVARCHAR(64),
    [session_id] UNIQUEIDENTIFIER,
    [trigger_message_id] UNIQUEIDENTIFIER,
    [assignee_id] NVARCHAR(64),
    [assignee_name] NVARCHAR(64),
    [created_by] NVARCHAR(64) NOT NULL,
    [created_at] DATETIME NOT NULL DEFAULT GETUTCDATE(),
    [updated_at] DATETIME,
    [closed_at] DATETIME,
    [final_solution_summary] NVARCHAR(MAX),
    [meta_json] NVARCHAR(MAX),
    [kb_article_id] INT
);

-- 创建工单日志表
CREATE TABLE [ticket_log] (
    [log_id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    [ticket_id] UNIQUEIDENTIFIER NOT NULL,
    [action] NVARCHAR(50) NOT NULL,
    [content] NVARCHAR(MAX),
    [operator_id] NVARCHAR(64),
    [operator_name] NVARCHAR(64),
    [next_status] NVARCHAR(20),
    [created_at] DATETIME NOT NULL DEFAULT GETUTCDATE()
);

-- 索引
CREATE INDEX [IX_ticket_tenant_created] ON [ticket] ([tenant_id], [created_at]);
CREATE UNIQUE INDEX [IX_ticket_no] ON [ticket] ([ticket_no]);
CREATE INDEX [IX_ticket_status] ON [ticket] ([status]);
CREATE INDEX [IX_ticket_assignee] ON [ticket] ([assignee_id]);