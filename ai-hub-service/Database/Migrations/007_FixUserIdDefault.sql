-- ============================================================
-- 修复用户表 ID 默认值约束
-- 执行时间：2026-02-26
-- 用途：解决主键冲突问题 - 确保 id 字段使用 NEWID() 自动生成 GUID
-- ============================================================

-- 删除现有的默认约束（如果存在）
IF EXISTS (
    SELECT * FROM sys.default_constraints
    WHERE parent_object_id = OBJECT_ID('users')
    AND column_id IN (
        SELECT column_id
        FROM sys.columns
        WHERE name = 'id'
        AND object_id = OBJECT_ID('users')
    )
)
BEGIN
    DECLARE @constraintName NVARCHAR(128);
    SELECT @constraintName = name
    FROM sys.default_constraints
    WHERE parent_object_id = OBJECT_ID('users')
    AND column_id IN (
        SELECT column_id
        FROM sys.columns
        WHERE name = 'id'
        AND object_id = OBJECT_ID('users')
    );

    EXEC('ALTER TABLE users DROP CONSTRAINT ' + @constraintName);
    PRINT '已删除旧的默认约束：' + @constraintName;
END
GO

-- 添加新的默认约束到 id 字段
IF NOT EXISTS (
    SELECT * FROM sys.default_constraints
    WHERE parent_object_id = OBJECT_ID('users')
    AND name LIKE 'DF__users__id_%'
)
BEGIN
    ALTER TABLE users ADD CONSTRAINT DF_users_Id DEFAULT NEWID() FOR id;
    PRINT '✅ 已成功添加 ID 默认约束：DEFAULT NEWID()';
END
GO

PRINT '';
PRINT '========================================';
PRINT '修复完成！请重新启动应用程序。';
PRINT '========================================';
GO
