# kb_asset 表与附件说明

## 一、kb_asset 表是怎么来的

### 1. 表结构来源（迁移脚本）

- **脚本位置**：`ai-hub-service/Database/Migrations/002_RefactorToNewSchema.sql`
- **表名**：由旧表 `kb_attachment` 重构而来（与 `kb_item` → `kb_article` 一起迁移）。

### 2. 表结构定义（当前）

```sql
CREATE TABLE kb_asset (
    id INT IDENTITY(1,1) PRIMARY KEY,
    tenant_id NVARCHAR(50),
    article_id INT NOT NULL,                    -- 关联 kb_article.id
    asset_type NVARCHAR(50) NOT NULL,            -- image/video/pdf/other
    file_name NVARCHAR(500) NOT NULL,            -- 文件名，如 2.mp4
    url NVARCHAR(1000) NOT NULL,                 -- 访问地址（见下文格式）
    size BIGINT,
    duration INT,
    created_at DATETIME NOT NULL DEFAULT GETDATE(),
    deleted_at DATETIME,
    FOREIGN KEY (article_id) REFERENCES kb_article(id) ON DELETE CASCADE
);
```

- **article_id**：对应 `kb_article.id`，表示这条附件属于哪条知识。
- **url**：建议存「可访问的完整 URL」或「以 `/uploads/` 开头的路径」，开发环境示例见下。

### 3. 数据是怎么来的

- **历史数据**：若执行过 `002_RefactorToNewSchema.sql` 且存在旧表 `kb_attachment`，脚本会把 `kb_attachment` 的数据迁移到 `kb_asset`（`file_url` → `url`，`knowledge_item_id` 通过映射转为 `article_id`）。
- **新数据**：通常通过：
  - .NET 后台上传接口写入（若有用到 Asset 相关 API），或
  - 知识库导入/Excel 导入时写入，或
  - 手工在数据库里按 `article_id` 插入/更新。

当前 **Python 侧**只读 `kb_asset`（按 `article_id` 查附件），不写表；写入由 .NET 或导入流程负责。

---

## 二、附件规则（已定）

- **附件根目录**：`D:\01-资料\永红造型线维修视频`（.NET 配置中的 `AttachmentStorage:BasePath`）。
- **目录结构**：该目录下**只有文件、没有子文件夹**，按**文件名**即可精准找到文件。
- **不依赖 kb_asset.url**：Python 侧**不再使用** `kb_asset.url`，而是用 `kb_asset.file_name` + 配置的 `ATTACHMENT_BASE_URL` 拼出访问地址：
  - 公式：`ATTACHMENT_BASE_URL / {URL编码(file_name)}`
  - 开发环境：`ATTACHMENT_BASE_URL` 会被改成 `http://localhost:3000/uploads`，前端通过 Vite 代理到 .NET 5000，.NET 从上述根目录按文件名提供静态文件。
- **kb_asset 表**：只需保证 `article_id`、`file_name`、`asset_type` 等正确；`url` 可留空或随意，接口返回的链接一律按上面规则生成。

---

## 三、开发环境 404 的常见原因

你遇到的 `localhost:3000/uploads/141油泵压力0,斜盘卡住/1.jpg` 报 404，可依次排查：

1. **文件是否在磁盘上存在**  
   确认路径：  
   `D:\01-资料\永红造型线维修视频\141油泵压力0,斜盘卡住\1.jpg`  
   若文件夹或文件名不一致（含空格、逗号、编码等），就会 404。

2. **.NET 是否用了附件目录**  
   确认 `ai-hub-service/appsettings.json` 里：
   - `AttachmentStorage:BasePath` = `D:\\01-资料\\永红造型线维修视频`
   - .NET 启动时该目录存在（Program.cs 里会检查 `Directory.Exists(attachmentBasePath)`），否则只会用 `wwwroot/uploads`，不会从你这盘路径提供文件。

3. **url 中路径与磁盘一致**  
   - 若 `kb_asset.url` 里是「141油泵压力0,斜盘卡住/1.jpg」或对应编码，要保证和磁盘上的文件夹名、文件名一致（逗号、空格等都要一致）。
   - 路径中有中文或特殊字符时，建议存 **URL 编码** 形式，避免浏览器或代理对逗号等字符处理不一致。

4. **前端请求的端口**  
   开发环境应是：前端 3000 → Vite 代理 `/uploads` → .NET 5000；Python 返回的附件地址已被改成 3000，这部分逻辑是对的，只要 .NET 能从 `BasePath` 找到文件即可。

---

## 四、小结

| 项目       | 说明 |
|------------|------|
| 表从哪里来 | 迁移脚本 `002_RefactorToNewSchema.sql` 从 `kb_attachment` 迁到 `kb_asset` |
| 数据从哪来 | 旧表迁移 + .NET/导入/手工维护，Python 只读不写 |
| 附件根目录 | 开发环境：`D:\01-资料\永红造型线维修视频`（.NET 配置） |
| url 建议   | 存 `http://localhost:5000/uploads/子目录/文件名` 或 `uploads/子目录/文件名`（可 URL 编码） |
| 404 排查   | 先确认磁盘上该路径存在，且 .NET 的 `AttachmentStorage:BasePath` 指向该目录 |
