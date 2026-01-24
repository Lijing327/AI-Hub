# 项目重命名说明

## 已完成的工作

✅ 已更新所有代码文件中的命名空间：`KnowledgeBase.API` → `ai_hub_service`
✅ 已更新所有文档中的项目名称引用
✅ 已更新启动脚本中的路径

## 需要手动完成的操作

### 方法一：使用 PowerShell 脚本（推荐）

1. **打开 PowerShell**（以管理员身份运行，避免权限问题）
2. **切换到项目根目录**：
   ```powershell
   cd "d:\00-Project\AI\after-sales-ai"
   ```
3. **运行脚本**：
   ```powershell
   .\rename-files.ps1
   ```

如果遇到执行策略限制，先运行：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 方法二：手动重命名（最简单）

#### 1. 重命名项目文件夹

在文件资源管理器中：
- 找到 `KnowledgeBase.API` 文件夹
- 右键 → 重命名
- 改为 `ai-hub-service`

#### 2. 重命名项目文件

在文件资源管理器中：
- 进入 `ai-hub-service` 文件夹
- 找到 `KnowledgeBase.API.csproj` 文件
- 右键 → 重命名
- 改为 `ai-hub-service.csproj`

### 方法三：使用命令行

在项目根目录打开 PowerShell 或 CMD，执行：

```powershell
# 重命名文件夹
Rename-Item -Path "KnowledgeBase.API" -NewName "ai-hub-service"

# 重命名项目文件
Rename-Item -Path "ai-hub-service\KnowledgeBase.API.csproj" -NewName "ai-hub-service.csproj"
```

### 3. 代码文件说明

**不需要重命名的文件**（文件名描述功能，与项目名无关）：
- `Program.cs` - 程序入口文件
- `ApplicationDbContext.cs` - 数据库上下文
- `KnowledgeItemsController.cs` - 知识条目控制器
- `AttachmentsController.cs` - 附件控制器
- `KnowledgeItemService.cs` - 知识条目服务
- `AttachmentService.cs` - 附件服务
- `IndexService.cs` - 索引服务
- `KnowledgeItem.cs` - 知识条目模型
- `Attachment.cs` - 附件模型
- `KnowledgeChunk.cs` - 知识块模型
- `KnowledgeItemDto.cs` - 知识条目DTO
- `AttachmentDto.cs` - 附件DTO
- 所有接口文件（I开头）

这些文件名描述的是功能/类名，与项目名称无关，保持原样即可。

### 3. 更新解决方案文件（如果存在）

如果项目在解决方案文件中，需要：
1. 在 Visual Studio 中卸载项目
2. 重命名文件夹和项目文件
3. 重新加载项目
4. 更新解决方案文件中的项目引用

### 4. 清理并重新构建

重命名完成后，清理并重新构建项目：

```bash
cd ai-hub-service
dotnet clean
dotnet restore
dotnet build
```

## 验证

重命名完成后，验证以下内容：

1. ✅ 项目可以正常编译
2. ✅ 所有命名空间正确：`ai_hub_service.*`
3. ✅ 应用可以正常启动
4. ✅ Swagger 页面可以正常访问

## 注意事项

- C# 命名空间使用下划线：`ai_hub_service`
- 文件夹名称使用连字符：`ai-hub-service`
- 项目文件名使用连字符：`ai-hub-service.csproj`
