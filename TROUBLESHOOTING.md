# 故障排查指南

## 404 错误排查

如果访问 `https://localhost:50936/` 出现 404 错误，请按以下步骤排查：

### 1. 检查应用是否正常启动

查看控制台输出，确认：
- ✅ 应用已成功启动
- ✅ 没有数据库连接错误
- ✅ 没有其他异常信息

### 2. 检查数据库连接

确保：
- ✅ SQL Server 服务正在运行（服务器：172.16.15.9）
- ✅ 数据库 `ai_hub` 已创建
- ✅ 连接字符串中的用户名和密码正确
- ✅ 网络可以访问 172.16.15.9

**创建数据库：**
```bash
sqlcmd -S 172.16.15.9 -U sa -P "pQdr2f@K3.Stp6Qs3hkP" -i KnowledgeBase.API/Database/Migrations/001_InitialCreate.sql
```

### 3. 检查正确的访问路径

API 路径都在 `/api/` 下，正确的访问地址：

- **Swagger文档**：`https://localhost:50936/swagger`
- **知识条目API**：`https://localhost:50936/api/knowledgeitems`
- **附件API**：`https://localhost:50936/api/attachments`
- **根路径**：`https://localhost:50936/` （现在会返回API信息）

### 4. 重新启动应用

如果修改了配置，需要：
1. 停止当前运行的应用（Ctrl+C）
2. 重新运行：`dotnet run`

### 5. 检查端口

确认应用使用的端口：
- HTTPS: `https://localhost:50936`
- HTTP: `http://localhost:50937`

如果端口被占用，VS 会自动分配新端口，查看控制台输出确认实际端口。

### 6. 查看详细错误信息

如果应用启动失败，查看控制台输出的详细错误信息，常见问题：

**数据库连接失败：**
```
Cannot open database "ai_hub" requested by the login
```
→ 检查数据库是否存在，执行SQL脚本创建数据库

**表不存在：**
```
Invalid object name 'kb_item'
```
→ 执行SQL脚本创建表结构

**网络连接问题：**
```
A network-related or instance-specific error occurred
```
→ 检查网络连接和防火墙设置

## 快速验证

1. **访问根路径**：`https://localhost:50936/`
   - 应该返回JSON格式的API信息

2. **访问Swagger**：`https://localhost:50936/swagger`
   - 应该显示API文档页面

3. **测试API**：`https://localhost:50936/api/knowledgeitems/search`
   - 应该返回知识条目列表（可能为空）

## 联系支持

如果问题仍未解决，请提供：
- 控制台的完整错误信息
- 应用启动日志
- 数据库连接测试结果
