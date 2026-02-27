-- =====================================================
-- kb_article 数据诊断脚本
-- 用于排查「测试库有数据但不显示」的问题
-- 查询条件：tenant_id = 'default' AND deleted_at IS NULL
-- =====================================================

USE ai_hub_test;
GO

-- 1. 查看 kb_article 表中 tenant_id 的分布
PRINT '========== tenant_id 分布 ==========';
SELECT 
    ISNULL(tenant_id, '(NULL)') AS tenant_id,
    COUNT(*) AS cnt,
    SUM(CASE WHEN deleted_at IS NULL THEN 1 ELSE 0 END) AS cnt_not_deleted
FROM kb_article
GROUP BY tenant_id;

-- 2. 查看 deleted_at 的分布
PRINT '';
PRINT '========== deleted_at 分布 ==========';
SELECT 
    CASE WHEN deleted_at IS NULL THEN '(NULL-未删除)' ELSE '(已删除)' END AS deleted_status,
    COUNT(*) AS cnt
FROM kb_article
GROUP BY CASE WHEN deleted_at IS NULL THEN 1 ELSE 0 END;

-- 3. 符合查询条件的记录数（tenant_id='default' 且 deleted_at IS NULL）
PRINT '';
PRINT '========== 符合 API 查询条件的记录数 ==========';
SELECT COUNT(*) AS matching_count
FROM kb_article
WHERE tenant_id = 'default' AND deleted_at IS NULL;

-- 4. 若上面为 0，执行下面的修复脚本（014_FixKbArticleTenantForTest.sql）
