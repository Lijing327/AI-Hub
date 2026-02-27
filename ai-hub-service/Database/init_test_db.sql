-- =====================================================
-- AI-Hub 测试环境数据库初始化脚本（完整版）
-- 说明：在测试服务器上执行此脚本，创建 ai_hub_test 数据库及所有表结构
-- 包含所有生产环境表结构
-- =====================================================

-- 1. 创建测试数据库（如果不存在）
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'ai_hub_test')
BEGIN
    CREATE DATABASE ai_hub_test;
    PRINT '已创建数据库 ai_hub_test';
END
ELSE
BEGIN
    PRINT '数据库 ai_hub_test 已存在';
END
GO

USE ai_hub_test;
GO

-- =====================================================
-- 2. 工单相关表 (ticket, ticket_log)
-- =====================================================

-- 工单主表
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

    CREATE INDEX [IX_ticket_tenant_id] ON [dbo].[ticket]([tenant_id]);
    CREATE INDEX [IX_ticket_status] ON [dbo].[ticket]([status]);
    CREATE INDEX [IX_ticket_created_at] ON [dbo].[ticket]([created_at] DESC);
    CREATE INDEX [IX_ticket_ticket_no] ON [dbo].[ticket]([ticket_no]);
    CREATE INDEX [IX_ticket_kb_article_id] ON [dbo].[ticket]([kb_article_id]) WHERE [kb_article_id] IS NOT NULL;

    PRINT '表 [dbo].[ticket] 已创建';
END
GO

-- 工单日志表
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

    CREATE INDEX [IX_ticket_log_ticket_id] ON [dbo].[ticket_log]([ticket_id]);
    CREATE INDEX [IX_ticket_log_created_at] ON [dbo].[ticket_log]([created_at] DESC);

    PRINT '表 [dbo].[ticket_log] 已创建';
END
GO

-- =====================================================
-- 3. 知识库相关表 (kb_article, kb_asset, kb_chunk)
-- =====================================================

-- 知识主表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_article')
BEGIN
    CREATE TABLE kb_article (
        id INT IDENTITY(1,1) PRIMARY KEY,
        tenant_id NVARCHAR(50) NOT NULL,
        title NVARCHAR(500) NOT NULL,
        question_text NVARCHAR(MAX),
        cause_text NVARCHAR(MAX),
        solution_text NVARCHAR(MAX),
        scope_json NVARCHAR(MAX),
        tags NVARCHAR(1000),
        status NVARCHAR(20) NOT NULL DEFAULT 'draft',
        version INT DEFAULT 1,
        created_by NVARCHAR(100),
        created_at DATETIME NOT NULL DEFAULT GETDATE(),
        updated_at DATETIME,
        published_at DATETIME,
        deleted_at DATETIME,
        source_type NVARCHAR(50) NULL,
        source_id NVARCHAR(50) NULL
    );

    CREATE INDEX idx_tenant_id ON kb_article(tenant_id);
    CREATE INDEX idx_status ON kb_article(status);
    CREATE INDEX idx_created_at ON kb_article(created_at);
    CREATE INDEX idx_tenant_status ON kb_article(tenant_id, status);
    CREATE INDEX idx_deleted_at ON kb_article(deleted_at);

    PRINT '表 kb_article 已创建';
END
GO

-- 知识资源表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_asset')
BEGIN
    CREATE TABLE kb_asset (
        id INT IDENTITY(1,1) PRIMARY KEY,
        tenant_id NVARCHAR(50) NOT NULL,
        article_id INT NOT NULL,
        asset_type NVARCHAR(50) NOT NULL,
        file_name NVARCHAR(500) NOT NULL,
        url NVARCHAR(1000) NOT NULL,
        size BIGINT,
        duration INT NULL,
        thumbnail NVARCHAR(1000) NULL,
        created_at DATETIME NOT NULL DEFAULT GETDATE(),
        updated_at DATETIME,
        deleted_at DATETIME
    );

    CREATE INDEX idx_tenant_id ON kb_asset(tenant_id);
    CREATE INDEX idx_article_id ON kb_asset(article_id);
    CREATE INDEX idx_deleted_at ON kb_asset(deleted_at);

    PRINT '表 kb_asset 已创建';
END
GO

-- 知识切片表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_chunk')
BEGIN
    CREATE TABLE kb_chunk (
        id INT IDENTITY(1,1) PRIMARY KEY,
        article_id INT NOT NULL,
        chunk_text NVARCHAR(MAX) NOT NULL,
        chunk_index INT NOT NULL,
        chunk_type NVARCHAR(20) DEFAULT 'question',
        created_at DATETIME NOT NULL DEFAULT GETDATE()
    );

    CREATE INDEX idx_article_id ON kb_chunk(article_id);
    CREATE UNIQUE INDEX idx_article_chunk ON kb_chunk(article_id, chunk_index);

    PRINT '表 kb_chunk 已创建';
END
GO

-- =====================================================
-- 4. 用户表 (users)
-- =====================================================

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'users')
BEGIN
    CREATE TABLE users (
        id                  NVARCHAR(64)         NOT NULL PRIMARY KEY DEFAULT NEWID(),
        account              NVARCHAR(100)        NOT NULL UNIQUE,
        password_hash       NVARCHAR(256)        NOT NULL,
        status              NVARCHAR(16)         NOT NULL DEFAULT 'active',
        role                NVARCHAR(16)         NOT NULL DEFAULT 'user',
        device_mn           NVARCHAR(50),
        created_at          DATETIME2            NOT NULL DEFAULT GETUTCDATE(),
        updated_at          DATETIME2            NOT NULL DEFAULT GETUTCDATE()
    );

    CREATE INDEX IX_users_account ON users (account);
    CREATE INDEX IX_users_status ON users (status);
    CREATE INDEX IX_users_role ON users (role);
    CREATE INDEX IX_users_created_at ON users (created_at DESC);

    PRINT '表 users 已创建';
END
GO

-- =====================================================
-- 5. AI 审计日志表
-- =====================================================

-- AI 会话表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ai_conversation')
BEGIN
    CREATE TABLE ai_conversation (
        conversation_id     UNIQUEIDENTIFIER    NOT NULL PRIMARY KEY DEFAULT NEWID(),
        tenant_id           NVARCHAR(64)        NOT NULL,
        user_id             NVARCHAR(64)        NULL,
        channel             NVARCHAR(32)        NOT NULL DEFAULT 'web',
        device_id           NVARCHAR(64)        NULL,
        started_at          DATETIME2           NOT NULL DEFAULT GETUTCDATE(),
        ended_at            DATETIME2           NULL,
        meta_json           NVARCHAR(MAX)       NULL,
        created_at          DATETIME2           NOT NULL DEFAULT GETUTCDATE()
    );

    CREATE INDEX IX_ai_conversation_tenant_time ON ai_conversation (tenant_id, started_at DESC);
    CREATE INDEX IX_ai_conversation_user_time ON ai_conversation (user_id, started_at DESC);
    CREATE INDEX IX_ai_conversation_device_time ON ai_conversation (device_id, started_at DESC);
    CREATE INDEX IX_ai_conversation_channel ON ai_conversation (channel);

    PRINT '表 ai_conversation 已创建';
END
GO

-- AI 消息表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ai_message')
BEGIN
    CREATE TABLE ai_message (
        message_id          UNIQUEIDENTIFIER    NOT NULL PRIMARY KEY DEFAULT NEWID(),
        conversation_id     UNIQUEIDENTIFIER    NOT NULL,
        role                NVARCHAR(16)        NOT NULL,
        content             NVARCHAR(MAX)       NOT NULL,
        content_len         INT                 NOT NULL DEFAULT 0,
        is_masked           BIT                 NOT NULL DEFAULT 0,
        masked_content      NVARCHAR(MAX)       NULL,
        created_at          DATETIME2           NOT NULL DEFAULT GETUTCDATE()
    );

    CREATE INDEX IX_ai_message_conv_time ON ai_message (conversation_id, created_at);
    CREATE INDEX IX_ai_message_role_time ON ai_message (role, created_at);

    PRINT '表 ai_message 已创建';
END
GO

-- AI 决策日志
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ai_decision_log')
BEGIN
    CREATE TABLE ai_decision_log (
        message_id          UNIQUEIDENTIFIER    NOT NULL PRIMARY KEY,
        intent_type         NVARCHAR(64)        NOT NULL,
        confidence          DECIMAL(5,4)        NOT NULL DEFAULT 0,
        model_name          NVARCHAR(128)       NULL,
        prompt_version      NVARCHAR(32)        NULL,
        use_knowledge       BIT                 NOT NULL DEFAULT 0,
        fallback_reason     NVARCHAR(128)       NULL,
        tokens_in           INT                 NULL,
        tokens_out          INT                 NULL,
        created_at          DATETIME2           NOT NULL DEFAULT GETUTCDATE()
    );

    CREATE INDEX IX_ai_decision_intent_time ON ai_decision_log (intent_type, created_at);
    CREATE INDEX IX_ai_decision_model ON ai_decision_log (model_name);
    CREATE INDEX IX_ai_decision_fallback ON ai_decision_log (fallback_reason);

    PRINT '表 ai_decision_log 已创建';
END
GO

-- AI 检索日志
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ai_retrieval_log')
BEGIN
    CREATE TABLE ai_retrieval_log (
        id                  BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        message_id          UNIQUEIDENTIFIER    NOT NULL,
        doc_id              NVARCHAR(64)        NOT NULL,
        doc_title           NVARCHAR(256)       NULL,
        score               DECIMAL(8,6)        NOT NULL DEFAULT 0,
        rank                INT                 NOT NULL DEFAULT 0,
        chunk_id            NVARCHAR(64)        NULL,
        created_at          DATETIME2           NOT NULL DEFAULT GETUTCDATE()
    );

    CREATE INDEX IX_ai_retrieval_msg ON ai_retrieval_log (message_id);
    CREATE INDEX IX_ai_retrieval_doc ON ai_retrieval_log (doc_id);
    CREATE INDEX IX_ai_retrieval_score ON ai_retrieval_log (score DESC);

    PRINT '表 ai_retrieval_log 已创建';
END
GO

-- AI 响应表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ai_response')
BEGIN
    CREATE TABLE ai_response (
        message_id          UNIQUEIDENTIFIER    NOT NULL PRIMARY KEY,
        final_answer        NVARCHAR(MAX)       NULL,
        response_time_ms    INT                 NOT NULL DEFAULT 0,
        is_success          BIT                 NOT NULL DEFAULT 1,
        error_type          NVARCHAR(64)        NULL,
        error_detail        NVARCHAR(MAX)       NULL,
        created_at          DATETIME2           NOT NULL DEFAULT GETUTCDATE()
    );

    CREATE INDEX IX_ai_response_time ON ai_response (response_time_ms);
    CREATE INDEX IX_ai_response_success ON ai_response (is_success);
    CREATE INDEX IX_ai_response_error ON ai_response (error_type);

    PRINT '表 ai_response 已创建';
END
GO

-- =====================================================
-- 完成
-- =====================================================

PRINT '====================================================='
PRINT '测试数据库 ai_hub_test 初始化完成！'
PRINT '====================================================='
PRINT '已创建表：'
PRINT '  - ticket, ticket_log (工单)'
PRINT '  - kb_article, kb_asset, kb_chunk (知识库)'
PRINT '  - users (用户)'
PRINT '  - ai_conversation, ai_message (AI 会话/消息)'
PRINT '  - ai_decision_log, ai_retrieval_log, ai_response (AI 审计)'
PRINT '====================================================='
PRINT ''
PRINT '验证：'
PRINT '  SELECT name FROM sys.tables WHERE type = ''U'' ORDER BY name;'
PRINT '====================================================='
GO
