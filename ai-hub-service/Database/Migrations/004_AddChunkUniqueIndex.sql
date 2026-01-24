-- 为 kb_chunk 表添加唯一索引 UX_kb_chunk_tenant_hash
-- 用于防止同一租户下重复的 chunk（基于 hash 去重）
-- 数据库：SQL Server (ai_hub)

USE ai_hub;
GO

-- 检查并创建唯一索引
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'UX_kb_chunk_tenant_hash' AND object_id = OBJECT_ID('kb_chunk'))
BEGIN
    -- 先清理可能存在的重复数据（保留最早的记录）
    WITH DuplicateChunks AS (
        SELECT 
            id,
            ROW_NUMBER() OVER (
                PARTITION BY tenant_id, hash 
                ORDER BY created_at ASC
            ) AS rn
        FROM kb_chunk
        WHERE hash IS NOT NULL
    )
    DELETE FROM kb_chunk
    WHERE id IN (
        SELECT id FROM DuplicateChunks WHERE rn > 1
    );

    -- 创建唯一索引（允许 hash 为 NULL，因为 NULL 值不参与唯一性约束）
    CREATE UNIQUE INDEX UX_kb_chunk_tenant_hash 
    ON kb_chunk(tenant_id, hash)
    WHERE hash IS NOT NULL;

    PRINT '已创建唯一索引 UX_kb_chunk_tenant_hash';
END
ELSE
BEGIN
    PRINT '唯一索引 UX_kb_chunk_tenant_hash 已存在';
END
GO

PRINT 'Chunk 去重索引添加完成！';
PRINT '说明：';
PRINT '  - 唯一索引作为数据库层面的额外保护（防止重复插入）';
PRINT '  - 逻辑层采用"仅同文章内去重"策略（保留每个hash第一次出现的chunk）';
PRINT '  - 允许不同文章有相同chunk（如通用安全注意事项等）';
PRINT '  - hash 为 NULL 的记录不受此约束限制';
GO
