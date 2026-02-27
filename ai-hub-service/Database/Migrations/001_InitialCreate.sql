-- 知识库录入与管理系统 - 数据库初始化脚本
-- 数据库：SQL Server (ai_hub - AI能力统一数据中枢)
-- 服务器：172.16.15.9
-- 说明：ai_hub 是公司所有 AI 能力的统一数据中枢，负责存储 AI 知识、向量、切片、对话及智能体相关数据，与业务系统解耦

-- 创建数据库（如果不存在）
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'ai_hub')
BEGIN
    CREATE DATABASE ai_hub;
END
GO

USE ai_hub;
GO

-- 知识条目表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_item')
BEGIN
    CREATE TABLE kb_item (
        id INT IDENTITY(1,1) PRIMARY KEY,
        title NVARCHAR(500) NOT NULL, -- 标题
        question_text NVARCHAR(MAX), -- 问题描述
        cause_text NVARCHAR(MAX), -- 原因分析
        solution_text NVARCHAR(MAX), -- 解决方案
        scope_json NVARCHAR(MAX), -- 适用范围（JSON格式）
        tags NVARCHAR(1000), -- 标签（逗号分隔）
        status NVARCHAR(20) NOT NULL DEFAULT 'draft', -- 状态：draft/published/archived
        version INT DEFAULT 1, -- 版本号
        tenant_id NVARCHAR(50), -- 租户ID
        created_by NVARCHAR(100), -- 创建人
        created_at DATETIME NOT NULL DEFAULT GETDATE(), -- 创建时间
        updated_at DATETIME, -- 更新时间
        published_at DATETIME -- 发布时间
    );

    -- 创建索引
    CREATE INDEX idx_status ON kb_item(status);
    CREATE INDEX idx_tenant_id ON kb_item(tenant_id);
    CREATE INDEX idx_created_at ON kb_item(created_at);
END
GO

-- 附件表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_attachment')
BEGIN
    CREATE TABLE kb_attachment (
        id INT IDENTITY(1,1) PRIMARY KEY,
        knowledge_item_id INT NOT NULL, -- 关联的知识条目ID
        file_name NVARCHAR(500) NOT NULL, -- 文件名
        file_path NVARCHAR(1000) NOT NULL, -- 文件存储路径
        file_url NVARCHAR(1000) NOT NULL, -- 文件访问URL
        file_type NVARCHAR(50) NOT NULL, -- 文件类型（image/video/pdf等）
        file_size BIGINT, -- 文件大小（字节）
        created_at DATETIME NOT NULL DEFAULT GETDATE() -- 创建时间
        -- 不添加外键，减少约束
    );

    -- 创建索引
    CREATE INDEX idx_knowledge_item_id ON kb_attachment(knowledge_item_id);
END
GO

-- 知识块表（用于向量化）
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_chunk')
BEGIN
    CREATE TABLE kb_chunk (
        id INT IDENTITY(1,1) PRIMARY KEY,
        knowledge_item_id INT NOT NULL, -- 关联的知识条目ID
        chunk_text NVARCHAR(MAX) NOT NULL, -- 块文本内容
        chunk_index INT NOT NULL, -- 块索引（同一知识条目中的顺序）
        created_at DATETIME NOT NULL DEFAULT GETDATE() -- 创建时间
        -- 不添加外键，减少约束
    );

    -- 创建索引
    CREATE INDEX idx_knowledge_item_id ON kb_chunk(knowledge_item_id);
END
GO
