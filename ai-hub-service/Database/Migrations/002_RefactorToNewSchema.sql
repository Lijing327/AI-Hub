-- 知识库表结构重构脚本
-- 将 kb_item -> kb_article, kb_attachment -> kb_asset
-- 更新 kb_chunk 添加新字段
-- 数据库：SQL Server (ai_hub)

USE ai_hub;
GO

-- ============================================
-- 1. 创建新表结构
-- ============================================

-- 1.1 知识主表：kb_article
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_article')
BEGIN
    CREATE TABLE kb_article (
        id INT IDENTITY(1,1) PRIMARY KEY,
        tenant_id NVARCHAR(50), -- 租户ID（放在前面）
        title NVARCHAR(500) NOT NULL, -- 知识标题
        question_text NVARCHAR(MAX), -- 用户问题/现象描述：尽量贴近用户口语
        cause_text NVARCHAR(MAX), -- 原因分析：可写"可能原因1/2/3"
        solution_text NVARCHAR(MAX), -- 解决步骤：结构化分步更好
        scope_json NVARCHAR(MAX), -- 适用范围：机型/版本/模块/场景（JSON格式）
        tags NVARCHAR(1000), -- 标签（逗号分隔）
        status NVARCHAR(20) NOT NULL DEFAULT 'draft', -- 状态：draft/published/archived
        version INT DEFAULT 1, -- 版本号（整数）
        created_by NVARCHAR(100), -- 创建人
        created_at DATETIME NOT NULL DEFAULT GETDATE(), -- 创建时间
        updated_at DATETIME, -- 更新时间
        published_at DATETIME, -- 发布时间
        deleted_at DATETIME -- 删除时间（软删除标记，NULL表示未删除）
    );

    -- 创建索引
    CREATE INDEX idx_tenant_id ON kb_article(tenant_id);
    CREATE INDEX idx_status ON kb_article(status);
    CREATE INDEX idx_created_at ON kb_article(created_at);
    CREATE INDEX idx_tenant_status ON kb_article(tenant_id, status);
    CREATE INDEX idx_deleted_at ON kb_article(deleted_at);
END
GO

-- 1.2 附件表：kb_asset
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_asset')
BEGIN
    CREATE TABLE kb_asset (
        id INT IDENTITY(1,1) PRIMARY KEY,
        tenant_id NVARCHAR(50), -- 租户ID
        article_id INT NOT NULL, -- 关联的知识条目ID
        asset_type NVARCHAR(50) NOT NULL, -- 资产类型：image/video/pdf/other
        file_name NVARCHAR(500) NOT NULL, -- 文件名
        url NVARCHAR(1000) NOT NULL, -- URL（OSS/本地路径）
        size BIGINT, -- 文件大小（字节）
        duration INT, -- 视频时长（秒，可选）
        created_at DATETIME NOT NULL DEFAULT GETDATE(), -- 创建时间
        deleted_at DATETIME, -- 删除时间（软删除标记，NULL表示未删除）
        FOREIGN KEY (article_id) REFERENCES kb_article(id) ON DELETE CASCADE
    );

    -- 创建索引
    CREATE INDEX idx_tenant_id ON kb_asset(tenant_id);
    CREATE INDEX idx_article_id ON kb_asset(article_id);
    CREATE INDEX idx_asset_type ON kb_asset(asset_type);
    CREATE INDEX idx_deleted_at ON kb_asset(deleted_at);
END
GO

-- 1.3 入库切片表：kb_chunk（更新）
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_chunk')
BEGIN
    -- 添加新字段
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('kb_chunk') AND name = 'tenant_id')
    BEGIN
        ALTER TABLE kb_chunk ADD tenant_id NVARCHAR(50);
        CREATE INDEX idx_tenant_id ON kb_chunk(tenant_id);
    END

    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('kb_chunk') AND name = 'hash')
    BEGIN
        ALTER TABLE kb_chunk ADD hash NVARCHAR(64); -- SHA256 hash用于去重
        CREATE INDEX idx_hash ON kb_chunk(hash);
    END

    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('kb_chunk') AND name = 'source_fields')
    BEGIN
        ALTER TABLE kb_chunk ADD source_fields NVARCHAR(100); -- 来自 question/cause/solution 哪部分
    END

    -- 重命名列（如果存在旧列名）
    IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('kb_chunk') AND name = 'knowledge_item_id')
    BEGIN
        EXEC sp_rename 'kb_chunk.knowledge_item_id', 'article_id', 'COLUMN';
    END
END
ELSE
BEGIN
    -- 如果表不存在，创建新表
    CREATE TABLE kb_chunk (
        id INT IDENTITY(1,1) PRIMARY KEY,
        tenant_id NVARCHAR(50), -- 租户ID
        article_id INT NOT NULL, -- 关联的知识条目ID
        chunk_index INT NOT NULL, -- 块索引
        chunk_text NVARCHAR(MAX) NOT NULL, -- 块文本
        hash NVARCHAR(64), -- 用于去重（SHA256）
        source_fields NVARCHAR(100), -- 来自 question/cause/solution 哪部分
        created_at DATETIME NOT NULL DEFAULT GETDATE(), -- 创建时间
        FOREIGN KEY (article_id) REFERENCES kb_article(id) ON DELETE CASCADE
    );

    -- 创建索引
    CREATE INDEX idx_tenant_id ON kb_chunk(tenant_id);
    CREATE INDEX idx_article_id ON kb_chunk(article_id);
    CREATE INDEX idx_hash ON kb_chunk(hash);
END
GO

-- ============================================
-- 2. 数据迁移（如果旧表存在）
-- ============================================

-- 2.1 迁移 kb_item -> kb_article
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_item') 
   AND EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_article')
   AND NOT EXISTS (SELECT * FROM kb_article)
BEGIN
    -- 确保 kb_article 表有 deleted_at 字段
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('kb_article') AND name = 'deleted_at')
    BEGIN
        ALTER TABLE kb_article ADD deleted_at DATETIME;
        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_deleted_at' AND object_id = OBJECT_ID('kb_article'))
        BEGIN
            CREATE INDEX idx_deleted_at ON kb_article(deleted_at);
        END
    END
    
    INSERT INTO kb_article (
        tenant_id, title, question_text, cause_text, solution_text,
        scope_json, tags, status, version, created_by,
        created_at, updated_at, published_at, deleted_at
    )
    SELECT 
        tenant_id, title, question_text, cause_text, solution_text,
        scope_json, tags, status, version, created_by,
        created_at, updated_at, published_at, NULL as deleted_at
    FROM kb_item;
    
    PRINT '数据已从 kb_item 迁移到 kb_article';
END
GO

-- 2.2 迁移 kb_attachment -> kb_asset
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_attachment') 
   AND EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_asset')
   AND EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_article')
   AND NOT EXISTS (SELECT * FROM kb_asset)
BEGIN
    -- 确保 kb_asset 表有 deleted_at 字段
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('kb_asset') AND name = 'deleted_at')
    BEGIN
        ALTER TABLE kb_asset ADD deleted_at DATETIME;
        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_deleted_at' AND object_id = OBJECT_ID('kb_asset'))
        BEGIN
            CREATE INDEX idx_deleted_at ON kb_asset(deleted_at);
        END
    END
    
    -- 创建临时映射表
    DECLARE @ItemToArticleMap TABLE (old_id INT, new_id INT);
    
    -- 建立ID映射（假设ID顺序一致）
    INSERT INTO @ItemToArticleMap (old_id, new_id)
    SELECT 
        ki.id AS old_id,
        ka.id AS new_id
    FROM kb_item ki
    INNER JOIN kb_article ka ON ka.title = ki.title 
        AND ka.created_at = ki.created_at
        AND (ka.tenant_id = ki.tenant_id OR (ka.tenant_id IS NULL AND ki.tenant_id IS NULL));
    
    -- 迁移附件数据
    INSERT INTO kb_asset (
        tenant_id, article_id, asset_type, file_name, url, size, created_at, deleted_at
    )
    SELECT 
        article.tenant_id,  -- 从 kb_article 表获取 tenant_id
        map.new_id AS article_id,
        att.file_type AS asset_type,
        att.file_name,
        att.file_url AS url,
        att.file_size AS size,
        att.created_at,
        NULL as deleted_at
    FROM kb_attachment att
    INNER JOIN @ItemToArticleMap map ON map.old_id = att.knowledge_item_id
    INNER JOIN kb_article article ON article.id = map.new_id;  -- JOIN 到 kb_article 获取 tenant_id
    
    PRINT '数据已从 kb_attachment 迁移到 kb_asset';
END
GO

-- 2.3 更新 kb_chunk（如果存在旧数据）
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_chunk')
   AND EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_article')
BEGIN
    -- 更新 article_id（如果还是 knowledge_item_id）
    IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('kb_chunk') AND name = 'knowledge_item_id')
    BEGIN
        DECLARE @ChunkItemToArticleMap TABLE (old_id INT, new_id INT);
        
        INSERT INTO @ChunkItemToArticleMap (old_id, new_id)
        SELECT 
            ki.id AS old_id,
            ka.id AS new_id
        FROM kb_item ki
        INNER JOIN kb_article ka ON ka.title = ki.title 
            AND ka.created_at = ki.created_at
            AND (ka.tenant_id = ki.tenant_id OR (ka.tenant_id IS NULL AND ki.tenant_id IS NULL));
        
        UPDATE kc
        SET kc.article_id = map.new_id,
            kc.tenant_id = ka.tenant_id
        FROM kb_chunk kc
        INNER JOIN @ChunkItemToArticleMap map ON map.old_id = kc.article_id
        INNER JOIN kb_article ka ON ka.id = map.new_id;
        
        PRINT 'kb_chunk 数据已更新';
    END
END
GO

-- ============================================
-- 3. 清理旧表（可选，建议先备份）
-- ============================================
-- 注意：执行前请先备份数据！
-- 
-- IF EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_attachment')
-- BEGIN
--     DROP TABLE kb_attachment;
-- END
-- GO
-- 
-- IF EXISTS (SELECT * FROM sys.tables WHERE name = 'kb_item')
-- BEGIN
--     DROP TABLE kb_item;
-- END
-- GO

PRINT '表结构重构完成！';
PRINT '新表结构：';
PRINT '  - kb_article (知识主表)';
PRINT '  - kb_asset (附件表)';
PRINT '  - kb_chunk (入库切片表，已更新)';
GO
