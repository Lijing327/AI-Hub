# 数据库表结构重构迁移指南

## 📋 概述

本次重构将数据库表结构从旧版本迁移到新版本：

| 旧表名 | 新表名 | 说明 |
|--------|--------|------|
| `kb_item` | `kb_article` | 知识主表 |
| `kb_attachment` | `kb_asset` | 附件表 |
| `kb_chunk` | `kb_chunk` | 入库切片表（字段更新） |

## 🔄 主要变化

### 1. kb_item → kb_article

**字段变化：**
- ✅ 字段顺序调整：`tenant_id` 移到最前面
- ✅ 字段名称和类型保持不变
- ✅ 所有业务字段保持一致

### 2. kb_attachment → kb_asset

**字段变化：**
- ✅ 添加 `tenant_id` 字段
- ✅ `knowledge_item_id` → `article_id`
- ✅ `file_type` → `asset_type`（image/video/pdf/other）
- ✅ `file_path` 和 `file_url` 合并为 `url`（支持OSS/本地路径）
- ✅ `file_size` → `size`
- ✅ 新增 `duration`（视频时长，可选）

### 3. kb_chunk 更新

**新增字段：**
- ✅ `tenant_id` - 租户ID
- ✅ `hash` - SHA256 hash（用于去重）
- ✅ `source_fields` - 来源字段（question/cause/solution）
- ✅ `knowledge_item_id` → `article_id`

## 🚀 迁移步骤

### 步骤1：备份数据库

**重要：执行迁移前必须先备份数据库！**

```sql
-- 备份数据库
BACKUP DATABASE ai_hub 
TO DISK = 'D:\Backup\ai_hub_backup_' + CONVERT(VARCHAR, GETDATE(), 112) + '.bak'
WITH FORMAT, COMPRESSION;
```

### 步骤2：执行迁移脚本

```bash
# 使用 sqlcmd 执行迁移脚本
sqlcmd -S 172.16.15.9 -U sa -P "pQdr2f@K3.Stp6Qs3hkP" -i ai-hub-service/Database/Migrations/002_RefactorToNewSchema.sql
```

或在 SQL Server Management Studio 中直接执行 `002_RefactorToNewSchema.sql` 脚本。

### 步骤3：验证迁移结果

```sql
USE ai_hub;

-- 检查新表是否存在
SELECT * FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME IN ('kb_article', 'kb_asset', 'kb_chunk');

-- 检查数据是否迁移成功
SELECT COUNT(*) as article_count FROM kb_article;
SELECT COUNT(*) as asset_count FROM kb_asset;
SELECT COUNT(*) as chunk_count FROM kb_chunk;

-- 检查旧表数据（如果还存在）
SELECT COUNT(*) as old_item_count FROM kb_item;
SELECT COUNT(*) as old_attachment_count FROM kb_attachment;
```

### 步骤4：清理旧表（可选）

**注意：只有在确认新表数据完全正确后，才能删除旧表！**

```sql
-- 删除旧表（谨慎操作！）
-- DROP TABLE kb_attachment;
-- DROP TABLE kb_item;
```

## ⚠️ 注意事项

1. **数据迁移**：迁移脚本会自动将旧表数据迁移到新表
2. **外键关系**：迁移脚本会处理外键关系的更新
3. **索引**：新表会自动创建必要的索引
4. **API兼容性**：后端API路由保持不变，前端无需修改
5. **文件存储**：附件文件物理位置不变，只是数据库记录迁移

## 🔍 迁移后验证清单

- [ ] 新表 `kb_article` 已创建
- [ ] 新表 `kb_asset` 已创建
- [ ] `kb_chunk` 表已更新（添加新字段）
- [ ] 数据已从旧表迁移到新表
- [ ] 数据记录数量一致
- [ ] 外键关系正确
- [ ] 索引已创建
- [ ] 后端服务可以正常启动
- [ ] API接口可以正常访问
- [ ] 前端可以正常显示数据

## 📞 问题排查

如果迁移过程中遇到问题：

1. **数据不一致**：检查迁移脚本中的映射逻辑
2. **外键错误**：确认ID映射关系正确
3. **字段缺失**：检查新表结构是否完整
4. **性能问题**：检查索引是否创建成功

## 🔄 回滚方案

如果需要回滚到旧表结构：

1. 从备份恢复数据库
2. 或手动将数据从新表迁移回旧表（需要编写回滚脚本）

---

**迁移脚本位置**：`ai-hub-service/Database/Migrations/002_RefactorToNewSchema.sql`
