# AI-Hub 多设备类型区分改造总结

## 1. 完成结果

本次改造成功实现了AI-Hub智能客服系统的多设备类型知识隔离检索功能。

### 核心改动摘要

1. **实现了设备类型标准体系**
   - 定义了4种设备类型标准码：`MOULDING_MACHINE`、`POURING_MACHINE`、`SHOT_BLAST_MACHINE`、`COMMON`
   - 建立了设备型号到设备类型的自动映射

2. **改造了知识检索核心流程**
   - 在向量元数据中存储设备类型信息
   - 实现了按设备类型过滤的检索逻辑
   - 添加了"两阶段召回"兜底机制

3. **保持了完全向后兼容**
   - 未传设备类型时，系统行为与改造前完全一致
   - 通用知识可被所有设备类型访问

4. **提供了完整的数据迁移方案**
   - 历史数据修复脚本可自动推断设备类型
   - 全量重建脚本可更新向量库

## 2. 变更文件清单

### 修改的文件

1. **app/schemas/kb_article.py**
   - 添加了 `scope_json: str | None` 字段

2. **app/repositories/kb_article_repo.py**
   - 所有查询方法都添加了 `scope_json` 字段
   - 更新了数据映射逻辑

3. **app/utils/ids.py**
   - 更新了 `make_vector_id` 函数支持设备类型
   - 修改了向量ID格式为 `{tenant}:kb:{article_id}:{type}:{device_type}`

4. **app/services/chunker.py**
   - 集成了设备类型解析逻辑
   - 为每个设备类型生成独立的chunk
   - 在chunk文本前添加设备类型前缀

5. **app/services/query_service.py**
   - 扩展了 `query` 方法支持 `device_type_code` 参数
   - 实现了设备类型过滤逻辑
   - 添加了两阶段召回兜底机制

6. **app/schemas/chat.py**
   - 在 `ChatRequest` 中添加了 `device_type_code` 和 `device_model` 字段

7. **app/services/chat_service.py**
   - 在调用 `query_service` 时传递设备类型参数

8. **app/api/v1/chat.py**
   - 更新了API文档说明
   - 添加了示例请求

9. **app/infra/vectorstore/chroma_store.py**
   - 更新了ID重构逻辑以支持设备类型

### 新增的文件

1. **app/utils/device_type_utils.py**
   - 设备类型解析核心工具
   - 支持JSON解析、标准码映射、关键词识别等功能

2. **scripts/fill_device_type_from_existing_data.py**
   - 历史数据修复脚本
   - 可根据标题、tags推断设备类型
   - 支持试运行和批量处理

3. **scripts/rebuild_all_vectors.py**
   - 全量重建向量脚本
   - 支持清空重建和增量重建

4. **tests/test_device_type_utils.py**
   - 设备类型工具单元测试

5. **tests/test_query_service.py**
   - QueryService 单元测试

6. **tests/test_chunker.py**
   - Chunker 单元测试

## 3. 数据与向量影响

### 数据库影响
- **是否需要修改表结构**：否，仅需确保 `scope_json` 字段存在
- **是否需要迁移历史数据**：是，建议运行历史数据修复脚本
- **对现有数据的影响**：无破坏性影响，`scope_json` 为空的文章会被标记为通用

### 向量库影响
- **需要全量重建**：是，新增的设备类型元数据需要重建
- **重建方式**：
  1. 运行 `scripts/fill_device_type_from_existing_data.py` 修复数据
  2. 运行 `scripts/rebuild_all_vectors.py` 重建向量
- **向量ID变更**：是的，新向量将包含设备类型后缀

### 执行步骤
```bash
# 1. 修复历史数据（试运行）
python scripts/fill_device_type_from_existing_data.py --tenant-id default --dry-run

# 2. 修复历史数据（实际执行）
python scripts/fill_device_type_from_existing_data.py --tenant-id default --commit

# 3. 全量重建向量
python scripts/rebuild_all_vectors.py --tenant-id default
```

## 4. 测试结果

### 单元测试覆盖
1. **设备类型解析测试**
   - ✅ 空JSON返回通用
   - ✅ 有效JSON正确解析
   - ✅ 多设备类型支持
   - ✅ 设备型号映射
   - ✅ 关键词提取

2. **QueryService测试**
   - ✅ 无设备类型时的原有逻辑
   - ✅ 有设备类型的过滤逻辑
   - ✅ 兜底机制触发条件
   - ✅ 结果合并逻辑

3. **Chunker测试**
   - ✅ 设备类型信息写入metadata
   - ✅ 多设备类型生成多个chunk
   - ✅ 文本前缀增强
   - ✅ 设备类型推断

### 集成测试场景

#### 场景1：造型机提问
```python
# 请求
device_type_code: "MOULDING_MACHINE"

# 期望结果
- 只返回 MOULDING_MACHINE 和 COMMON 的知识
- 优先显示造型机专用解决方案
```

#### 场景2：浇注机提问
```python
# 请求
device_type_code: "POURING_MACHINE"

# 期望结果
- 不返回造型机专用知识
- 可能返回通用知识
- 相关度高的是浇注机解决方案
```

#### 场景3：未传设备类型
```python
# 请求
device_type_code: None

# 期望结果
- 行为与改造前完全一致
- 检索所有租户下的知识
```

#### 场景4：只有通用知识
```python
# 数据
scope_json: '{"设备类型": "通用"}'

# 期望结果
- 任意设备类型都可命中
- 在所有设备类型的查询中都会出现
```

#### 场景5：严格过滤结果不足
```python
# 情况
- 按设备类型过滤结果 < top_k
- 最高分 < 0.5

# 期望结果
- 自动触发兜底召回
- 合并宽松查询结果
- 标注来源类型
```

## 5. 风险与后续建议

### 当前遗留问题（最小上线版已覆盖部分）
1. **数据库字段**：确保 `kb_article` 表有 `scope_json` 字段（TEXT/JSON类型）
2. ~~**前端适配**~~：**售后 H5 智能客服**已传 `device_model`，Python 侧解析为检索用 `device_type_code`
3. ~~**知识录入**~~：**知识编辑页**有设备类型下拉；**Excel 导入**可选整表设备类型
4. **发布→向量**：`.NET` 在 **发布知识** 成功后会请求 Python `POST /api/v1/ingest/article/{id}`（需配置 `AiHubAi:BaseUrl`）；未配置时发布仍成功但向量不更新
5. **历史数据**：存量知识若从未重建向量，需按 §3 执行修复脚本 + 全量/批量重建

### 下一阶段优化建议
1. **前端改造**
   - 客服界面增加设备类型选择
   - 设备型号自动映射到设备类型
   - 知识库编辑界面改为受控选择

2. **功能扩展**
   - 支持更多过滤维度（设备型号、子系统、场景）
   - 优化兜底机制的阈值配置
   - 添加设备类型统计报表

3. **性能优化**
   - 为设备类型字段添加数据库索引
   - 优化多设备类型chunk的生成效率
   - 考虑使用更高效的向量数据库

4. **数据治理**
   - 建立设备类型数据字典
   - 定期检查和修正设备类型标注
   - 建立设备型号映射规则的可视化管理

## 6. 注意事项

1. **向后兼容性**：所有改造都保持了向后兼容，未传设备类型时行为不变
2. **兜底机制**：严格过滤后会自动宽松查询，确保不会出现无结果的情况
3. **数据迁移**：必须执行历史数据修复和全量重建，否则新功能不生效
4. **测试验证**：上线前请务必运行所有测试，特别是集成测试场景
5. **性能监控**：上线后关注检索延迟和准确率指标

## 7. 最小上线可用版（MVP）清单

| 环节 | 要求 |
|------|------|
| 配置 | `appsettings` 中配置 **AiHubAi:BaseUrl**（Python 服务根地址，与工单转知识库一致），保证发布后能写入 Chroma |
| 录入 | **新建/编辑**：选设备类型后保存、发布；**Excel 导入**：选设备类型再上传，草稿后 **批量发布** |
| 向量 | 发布后自动单条 ingest；**存量**或失败时仍可用 `scripts/rebuild_all_vectors.py` / ingest 批量接口补救 |
| 客服 | 用户 **先选设备**（`model` 含 YH/JZ/PW 等可映射前缀或表内型号），再提问；未识别型号则行为同「未指定设备」 |
| 运维 | 首次上线建议对历史 `scope_json` 跑 `fill_device_type_from_existing_data.py` 并全量重建向量（见 §3） |