-- =====================================================
-- 修复 kb_article 租户与软删除，使测试环境数据可被 API 查询到
-- 仅用于 ai_hub_test，生产环境慎用
-- 查询条件：tenant_id = 'default' AND deleted_at IS NULL
-- =====================================================

USE ai_hub_test;
GO

-- 将 tenant_id 为 NULL、空字符串或其它值的记录统一改为 'default'（测试环境常用）
-- 若需保留多租户，请勿执行此脚本，改为在请求头传 X-Tenant-Id
UPDATE kb_article 
SET tenant_id = 'default' 
WHERE tenant_id IS NULL 
   OR LTRIM(RTRIM(tenant_id)) = ''
   OR tenant_id <> 'default';

-- 将已软删除的记录恢复（deleted_at 置为 NULL）
-- 若你确定要恢复所有记录，可取消下面注释：
-- UPDATE kb_article SET deleted_at = NULL WHERE deleted_at IS NOT NULL;

PRINT 'kb_article 租户修复完成';
