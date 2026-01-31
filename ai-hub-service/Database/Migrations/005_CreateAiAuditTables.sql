-- ============================================================
-- AI 对话审计表（P0-1）
-- 执行时间: 2026-01-29
-- 约定:
--   1. conversation_id / message_id 为 UUID (uniqueidentifier)
--   2. 所有时间字段存 UTC，展示时转本地
--   3. 脱敏: is_masked + masked_content 预留
-- ============================================================

-- 1) ai_conversation - 会话主表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ai_conversation')
BEGIN
    CREATE TABLE ai_conversation (
        conversation_id     UNIQUEIDENTIFIER    NOT NULL PRIMARY KEY DEFAULT NEWID(),
        tenant_id           NVARCHAR(64)        NOT NULL,
        user_id             NVARCHAR(64)        NULL,
        channel             NVARCHAR(32)        NOT NULL DEFAULT 'web',  -- web/app/wechat/api
        started_at          DATETIME2           NOT NULL DEFAULT GETUTCDATE(),
        ended_at            DATETIME2           NULL,
        meta_json           NVARCHAR(MAX)       NULL,  -- 设备/版本/IP等扩展信息
        created_at          DATETIME2           NOT NULL DEFAULT GETUTCDATE()
    );

    -- 索引
    CREATE INDEX IX_ai_conversation_tenant_time ON ai_conversation (tenant_id, started_at DESC);
    CREATE INDEX IX_ai_conversation_user_time ON ai_conversation (user_id, started_at DESC);
    CREATE INDEX IX_ai_conversation_channel ON ai_conversation (channel);
END
GO

-- 2) ai_message - 消息表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ai_message')
BEGIN
    CREATE TABLE ai_message (
        message_id          UNIQUEIDENTIFIER    NOT NULL PRIMARY KEY DEFAULT NEWID(),
        conversation_id     UNIQUEIDENTIFIER    NOT NULL,
        role                NVARCHAR(16)        NOT NULL,  -- user/assistant/system
        content             NVARCHAR(MAX)       NOT NULL,
        content_len         INT                 NOT NULL DEFAULT 0,
        is_masked           BIT                 NOT NULL DEFAULT 0,
        masked_content      NVARCHAR(MAX)       NULL,
        created_at          DATETIME2           NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT FK_ai_message_conversation FOREIGN KEY (conversation_id)
            REFERENCES ai_conversation (conversation_id) ON DELETE CASCADE
    );

    -- 索引
    CREATE INDEX IX_ai_message_conv_time ON ai_message (conversation_id, created_at);
    CREATE INDEX IX_ai_message_role_time ON ai_message (role, created_at);
END
GO

-- 3) ai_decision_log - AI 决策过程
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ai_decision_log')
BEGIN
    CREATE TABLE ai_decision_log (
        message_id          UNIQUEIDENTIFIER    NOT NULL PRIMARY KEY,
        intent_type         NVARCHAR(64)        NOT NULL,  -- chat/solution/consult/install/maintain...
        confidence          DECIMAL(5,4)        NOT NULL DEFAULT 0,
        model_name          NVARCHAR(128)       NULL,
        prompt_version      NVARCHAR(32)        NULL,
        use_knowledge       BIT                 NOT NULL DEFAULT 0,
        fallback_reason     NVARCHAR(128)       NULL,  -- no_match/low_confidence/model_error...
        tokens_in           INT                 NULL,
        tokens_out          INT                 NULL,
        created_at          DATETIME2           NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT FK_ai_decision_message FOREIGN KEY (message_id)
            REFERENCES ai_message (message_id) ON DELETE CASCADE
    );

    -- 索引
    CREATE INDEX IX_ai_decision_intent_time ON ai_decision_log (intent_type, created_at);
    CREATE INDEX IX_ai_decision_model ON ai_decision_log (model_name);
    CREATE INDEX IX_ai_decision_fallback ON ai_decision_log (fallback_reason);
END
GO

-- 4) ai_retrieval_log - RAG 命中文档
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
        created_at          DATETIME2           NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT FK_ai_retrieval_message FOREIGN KEY (message_id)
            REFERENCES ai_message (message_id) ON DELETE CASCADE
    );

    -- 索引
    CREATE INDEX IX_ai_retrieval_msg ON ai_retrieval_log (message_id);
    CREATE INDEX IX_ai_retrieval_doc ON ai_retrieval_log (doc_id);
    CREATE INDEX IX_ai_retrieval_score ON ai_retrieval_log (score DESC);
END
GO

-- 5) ai_response - 最终响应
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ai_response')
BEGIN
    CREATE TABLE ai_response (
        message_id          UNIQUEIDENTIFIER    NOT NULL PRIMARY KEY,
        final_answer        NVARCHAR(MAX)       NULL,
        response_time_ms    INT                 NOT NULL DEFAULT 0,
        is_success          BIT                 NOT NULL DEFAULT 1,
        error_type          NVARCHAR(64)        NULL,  -- model_error/timeout/no_match...
        error_detail        NVARCHAR(MAX)       NULL,
        created_at          DATETIME2           NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT FK_ai_response_message FOREIGN KEY (message_id)
            REFERENCES ai_message (message_id) ON DELETE CASCADE
    );

    -- 索引
    CREATE INDEX IX_ai_response_time ON ai_response (response_time_ms);
    CREATE INDEX IX_ai_response_success ON ai_response (is_success);
    CREATE INDEX IX_ai_response_error ON ai_response (error_type);
END
GO

PRINT '✅ AI 审计表创建完成';
