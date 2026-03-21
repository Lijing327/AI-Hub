
## 一、任务背景

当前 AI-Hub 智能客服系统的知识检索，仅按 `tenant_id` 做过滤，**无法按设备类型（如造型机、浇注机、抛丸机）进行可靠区分**。  
这会导致：

- 不同设备类型的知识混查
    
- 回答可能命中错误设备的处理方案
    
- 后续扩展到更多设备时，知识库边界越来越混乱
    

本次改造目标是：

1. 在**尽量少改数据库结构**的前提下，实现多设备类型知识隔离检索
    
2. 兼容现有知识库与现有接口
    
3. 为后续扩展“设备型号 / 子系统 / 场景”预留能力
    

---

# 二、总体设计原则

本次采用 **A+ 渐进式方案**：

## 方案核心

基于现有 `scope_json`，约定其中的 `设备类型` 字段；  
在知识切片和向量入库时，解析出标准化设备类型并写入 Chroma metadata；  
在检索时增加 `device_type_code` 过滤，并允许“当前设备类型 + 通用知识”共同召回。

---

# 三、实现目标

本次只落地以下能力：

1. 知识条目可标记所属设备类型
    
2. chunk metadata 中包含设备类型信息
    
3. ChatRequest 支持传入设备类型
    
4. QueryService 支持按设备类型过滤
    
5. 未传设备类型时保持现有逻辑不变
    
6. 通用知识可被所有设备类型访问
    
7. 为后续扩展预留统一过滤上下文结构
    

---

# 四、标准约定

## 4.1 设备类型标准码

请不要直接以内文中文自由匹配作为最终过滤值，统一引入标准码：

|中文名称|标准码|
|---|---|
|造型机|`MOULDING_MACHINE`|
|浇注机|`POURING_MACHINE`|
|抛丸机|`SHOT_BLAST_MACHINE`|
|通用|`COMMON`|

---

## 4.2 scope_json 约定格式

知识库文章的 `scope_json` 中，约定包含以下键：

```json
{
  "设备类型": "造型机",
  "设备型号": "YH400/YH500"
}
```

也允许多值：

```json
{
  "设备类型": "造型机,浇注机"
}
```

要求：

1. 支持中英文逗号分隔
    
2. 解析时去掉空格
    
3. 转换为标准码集合
    
4. 若未填写或解析失败，按“通用”处理
    

---

# 五、改造范围

请按以下模块逐项改造。

---

## 5.1 Python 数据模型改造

### 目标

让 Python 侧文章模型能拿到 `scope_json`。

### 修改文件

- `app/schemas/kb_article.py`
    

### 需要完成的事

1. 在 `KbArticle` 或对应 schema 中补充 `scope_json: str | None`
    
2. 如已有 `tags`、`title`、`content` 等字段，保持兼容
    
3. 不要破坏现有序列化逻辑
    

---

## 5.2 知识库仓储改造

### 目标

从数据库查询文章时，把 `scope_json` 一并查出来。

### 修改文件

- `app/repositories/kb_article_repo.py`
    

### 需要完成的事

1. 检查当前文章查询 SQL / ORM 查询逻辑
    
2. 将 `scope_json` 纳入查询结果
    
3. 确保返回 schema 能正常映射
    
4. 若某些接口未用到 `scope_json`，不强制全部暴露，但切片/入库链路必须能拿到
    

---

## 5.3 新增设备类型解析工具

### 目标

统一解析 `scope_json` 中的设备类型，避免逻辑散落在各处。

### 建议新增文件

- `app/utils/device_type_utils.py`
    

### 需要实现的方法

建议实现以下函数：

```python
def parse_device_types_from_scope(scope_json: str | None) -> list[str]:
    """从 scope_json 中解析设备类型并返回标准码列表"""

def normalize_device_type_name(name: str) -> str | None:
    """将中文设备名称映射为标准码"""

def is_common_device_type(device_type_codes: list[str]) -> bool:
    """判断是否属于通用知识"""
```

### 规则要求

1. 支持 `None`、空字符串、非法 JSON
    
2. `设备类型` 缺失时返回 `["COMMON"]`
    
3. 中文值要映射为标准码
    
4. 多值时返回去重后的标准码列表
    
5. 代码注释使用中文
    

---

## 5.4 Chunker 改造

### 目标

在知识切片时，把设备类型写入 metadata；同时把结构化范围信息拼进 chunk 文本前缀，增强语义。

### 修改文件

- `app/services/chunker.py`
    

### 需要完成的事

#### 1）从文章对象中读取 `scope_json`

- 解析出设备类型标准码列表
    
- 生成以下信息：
    

建议 metadata 至少包含：

```json
{
  "tenant_id": "default",
  "article_id": 123,
  "type": "faq",
  "status": "published",
  "version": 1,
  "device_type_code": "MOULDING_MACHINE",
  "is_common": false
}
```

#### 2）处理多设备类型知识

对于一篇文章若适用于多个设备类型，**优先采用“按设备类型复制 chunk”的方式**，而不是在单条 metadata 中放复杂数组过滤。

例如：

- 原文章适用于：造型机、浇注机
    
- 则为每个 chunk 生成两份向量记录：
    
    - 一份 metadata：`device_type_code=MOULDING_MACHINE`
        
    - 一份 metadata：`device_type_code=POURING_MACHINE`
        

这样检索逻辑更简单、稳定。

#### 3）通用知识处理

如果 scope 为空或显式为通用，则生成：

```json
{
  "device_type_code": "COMMON",
  "is_common": true
}
```

#### 4）增强 chunk 文本

在原 chunk 文本前追加轻量结构化文本前缀，格式类似：

```text
[设备类型:造型机]
[设备型号:YH400/YH500]
标题：xxxx
问题：xxxx
原因：xxxx
处理：xxxx
```

要求：

1. 不要直接拼原始 JSON
    
2. 拼接为自然语言可读文本
    
3. 对 embedding 友好
    
4. 不影响原有 chunk 分段逻辑
    

---

## 5.5 向量入库链路改造

### 目标

确保新增 metadata 能真正写入 Chroma。

### 需要检查的文件

- `app/services/ingest_service.py`
    
- 或当前负责写入向量库的 service / repository
    

### 需要完成的事

1. 检查当前 `add` / `upsert` Chroma 时 metadata 字段是否完整透传
    
2. 确保 `device_type_code`、`is_common` 已实际入库
    
3. 如当前 metadata 字段有白名单，请补充新增字段
    
4. 保持原有 tenant、article_id、tags 等字段不丢失
    

---

## 5.6 QueryService 改造

### 目标

检索时支持按设备类型过滤，同时兼容通用知识。

### 修改文件

- `app/services/query_service.py`
    

### 需要完成的事

#### 1）扩展 query 方法签名

例如：

```python
async def query(
    self,
    tenant_id: str,
    query_text: str,
    top_k: int = 5,
    device_type_code: str | None = None,
):
```

#### 2）过滤规则

- 当 `device_type_code is None` 时：
    
    - 保持现有逻辑，只按 `tenant_id` 过滤
        
- 当 `device_type_code` 有值时：
    
    - 优先召回：
        
        - `device_type_code = 当前值`
            
        - `device_type_code = COMMON`
            

#### 3）关于 Chroma 过滤实现

根据当前 Chroma Python 客户端实际支持能力实现：

优先尝试：

- `$or`
    
- 或分两次查询后合并结果
    

如果当前 Chroma 版本对复杂 where 支持有限，允许采用以下方式：

### 兜底实现方案

方案一：

1. 查当前设备类型
    
2. 再查 COMMON
    
3. 合并结果
    
4. 按分数统一排序
    
5. 截取 top_k
    

### 要求

1. 不要为了图省事，先全库召回再应用层硬过滤
    
2. 优先减少无关设备知识进入候选池
    
3. 保留后续扩展更多过滤条件的结构空间
    

---

## 5.7 增加“两阶段召回”兜底机制

### 目标

避免因为标注不完整，导致严格过滤后查不到结果。

### 修改文件

- `app/services/query_service.py`
    

### 需要完成的逻辑

当传入 `device_type_code` 时：

#### 第一阶段

召回：

- 当前设备类型
    
- COMMON
    

#### 第二阶段兜底

如果第一阶段结果出现以下任一情况：

- 命中数量明显不足
    
- 最高分过低
    
- 无有效结果
    

则自动补一次宽松查询：

- 只按 `tenant_id`
    
- 不加设备类型限制
    

然后：

- 将宽松结果合并进候选集
    
- 在最终结果中标注来源类型（如可行）
    

### 要求

1. 这个逻辑要写清楚注释
    
2. 阈值尽量参数化，不要写死魔法数字
    
3. 若暂时没有完善分数体系，先按“结果数不足”实现也可以
    

---

## 5.8 ChatRequest 改造

### 目标

聊天接口显式接收设备类型。

### 修改文件

- `app/schemas/chat.py`
    

### 需要完成的事

在 `ChatRequest` 中新增字段：

```python
device_type_code: str | None = None
device_model: str | None = None
```

说明：

1. 当前主用 `device_type_code`
    
2. `device_model` 先加上，哪怕暂时未参与过滤，也为后续预留
    
3. 原有 `device_id` 保留，不删
    

---

## 5.9 Chat Service 改造

### 目标

将前端传入的 `device_type_code` 传递到检索层。

### 修改文件

- `app/services/chat_service.py`
    

### 需要完成的事

1. 获取 `request.device_type_code`
    
2. 调用 `query_service.query()` 时透传
    
3. 保留原有审计、上下文逻辑
    
4. 若未传 `device_type_code`，保持原逻辑不变
    

---

## 5.10 Chat API 改造

### 目标

对外 API 可接收并透传设备类型参数。

### 修改文件

- `app/api/v1/chat.py`
    

### 需要完成的事

1. 接收请求体中的 `device_type_code`
    
2. 正常绑定到 `ChatRequest`
    
3. 接口文档 / 示例请求体同步更新
    

建议请求示例：

```json
{
  "message": "设备无法射砂怎么办？",
  "device_id": "YH500-001",
  "device_type_code": "MOULDING_MACHINE",
  "device_model": "YH500"
}
```

---

# 六、前端配合改造要求

这个部分如果当前仓库里有前端，也请一并处理；如果前端不在本仓库，则输出接口对接说明文档。

---

## 6.1 客服前端：传入设备类型

### 目标

用户进入客服或选择设备后，前端将设备类型传给聊天接口。

### 需要完成的事

1. 在进入 AI 客服前，增加设备类型上下文来源：
    
    - 用户显式选择
        
    - 或根据设备型号自动映射
        
2. 调用聊天接口时传：
    
    - `device_type_code`
        
    - `device_model`（如可得）
        

### 设备映射建议

前端或后端维护简单映射关系，例如：

- `YH400 / YH500 / YH600` → `MOULDING_MACHINE`
    
- `JZ-*` → `POURING_MACHINE`
    
- `PW-*` → `SHOT_BLAST_MACHINE`
    

---

## 6.2 知识库编辑前端：设备类型改为受控选择

### 目标

避免录入人员自由填写“设备类型”。

### 需要完成的事

在知识库编辑页面中：

1. 在“适用范围”区域增加设备类型控件
    
2. 采用枚举选择，不允许完全自由输入
    
3. 保存时写入 `scope_json`
    
4. 若当前系统已有 scope 编辑器，则在 UI 层提供快捷项
    

可选项：

- 造型机
    
- 浇注机
    
- 抛丸机
    
- 通用
    

---

# 七、历史数据迁移要求

### 目标

已有知识条目要尽可能补齐设备类型，否则新检索逻辑效果有限。

### 需要完成的事

请新增一个历史数据修复脚本，建议放在：

- `scripts/`
    
- 或 `tools/`
    

例如：

- `scripts/fill_device_type_from_existing_data.py`
    

### 脚本功能

1. 扫描已有 `kb_article`
    
2. 检查 `scope_json` 是否存在设备类型
    
3. 若不存在，可按以下策略补齐：
    
    - 根据标题关键词推断
        
    - 根据 tags 推断
        
    - 实在无法判断则设为 `COMMON`
        
4. 输出修复统计报告：
    
    - 总数
        
    - 自动识别数
        
    - 标记为通用数
        
    - 失败数
        

### 注意

1. 脚本应支持 dry-run
    
2. 尽量不要直接覆盖原始值
    
3. 日志写清楚
    

---

# 八、全量重建向量要求

### 目标

让新增 metadata 真正生效。

### 需要完成的事

1. 改造完成后，确认重新执行全量 ingest
    
2. 支持：
    
    - `clear_first = true`
        
    - 重建全部向量
        
3. 若已有 `/api/v1/ingest/all`，则复用
    
4. 若当前全量重建能力不足，请补齐
    

### 验证项

重建后随机抽查 Chroma 中的 metadata，确认存在：

- `device_type_code`
    
- `is_common`
    

---

# 九、测试要求

请补充测试，不要只改代码不验证。

---

## 9.1 单元测试

### 重点测试点

1. `scope_json` 解析
    
2. 中文设备名称转标准码
    
3. 空 scope / 非法 JSON 默认 COMMON
    
4. 多设备类型拆分逻辑
    
5. QueryService 过滤逻辑
    
6. 第一阶段 + 第二阶段兜底逻辑
    

---

## 9.2 集成测试

### 至少覆盖以下场景

#### 场景 1：造型机提问

- 请求传 `MOULDING_MACHINE`
    
- 结果只应包含：
    
    - `MOULDING_MACHINE`
        
    - `COMMON`
        

#### 场景 2：浇注机提问

- 请求传 `POURING_MACHINE`
    
- 结果不应优先混入造型机专属知识
    

#### 场景 3：未传设备类型

- 行为与当前一致
    
- 不应报错
    

#### 场景 4：只有通用知识

- 任意设备类型都可命中
    

#### 场景 5：严格过滤结果不足

- 自动触发兜底召回
    

---

# 十、交付物要求

完成后请输出以下内容，不要只说“已完成”。

## 10.1 输出变更清单

列出：

- 修改了哪些文件
    
- 新增了哪些文件
    
- 每个文件做了什么改动
    

---

## 10.2 输出数据库/数据影响说明

说明：

- 本次是否改表
    
- 是否需要迁移脚本
    
- 是否需要全量重建向量
    

---

## 10.3 输出测试结果

给出：

- 单元测试结果
    
- 集成测试结果
    
- 手工验证结果
    

---

## 10.4 输出风险与待办

说明：

1. 当前方案已解决什么
    
2. 还有哪些未做
    
3. 下一阶段建议
    

---

# 十一、实现约束

请严格遵守以下约束：

1. **优先最小改动，不做大重构**
    
2. **不引入与本任务无关的架构调整**
    
3. **保持向后兼容**
    
4. **代码注释使用中文**
    
5. **不要把 tenant_id 和 device_type 混为一谈**
    
6. **不要把 tags 过滤当主方案**
    
7. **不要依赖“标题里正好写了设备名”这种隐式语义命中**
    
8. **不要只写设计，不落代码**
    
9. **不要只改接口，不重建 ingest 链路**
    
10. **不要只做硬过滤，必须考虑 COMMON 与兜底召回**
    

---

# 十二、验收标准

满足以下条件，才算本任务完成：

1. 聊天请求可传 `device_type_code`
    
2. 向量 metadata 中存在 `device_type_code`
    
3. 检索可按设备类型做过滤
    
4. 通用知识可跨设备命中
    
5. 未传设备类型时保持兼容
    
6. 历史数据有补齐方案
    
7. 全量向量重建方案明确
    
8. 有测试结果，不是口头说明
    

---

# 十三、建议的最终输出格式

请 Claude Code 最终按下面结构汇报：

## 1. 完成结果

- 已完成的功能点
    
- 核心改动摘要
    

## 2. 变更文件清单

- 文件路径
    
- 改动说明
    

## 3. 数据与向量影响

- 是否需要历史数据修复
    
- 是否需要全量重建向量
    
- 如何执行
    

## 4. 测试结果

- 单元测试
    
- 集成测试
    
- 手工验证
    

## 5. 风险与后续建议

- 当前遗留问题
    
- 下一步优化方向
    

---

如果你需要，我下一步可以继续帮你整理一版 **“给 Claude Code 的超短执行提示词版本”**，就是一段更适合直接粘贴到对话框里的精简版。